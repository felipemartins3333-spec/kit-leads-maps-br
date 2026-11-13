#!/usr/bin/env python3
"""Trata o CSV do motor (esquema do gosom) e deixa a lista pronta para prospecção.

O que faz:
  - limpa os campos úteis (nome, categoria, endereço, site, nota, avaliações...);
  - normaliza telefones brasileiros para +55, separa celular de fixo e de 0800;
  - cria link do WhatsApp (wa.me) SOMENTE para celular;
  - descarta e-mails lixo (imagens, placeholders, no-reply, domínios de exemplo);
  - remove duplicados por place_id e por telefone;
  - gera 2 arquivos: um CSV padrão (UTF-8, vírgula) e um CSV para Excel brasileiro
    (separador ';', UTF-8 com BOM, decimal com vírgula).

Só usa a biblioteca padrão.

Uso:
  python3 -I scripts/tratar_csv.py resultados/teste2-com-email.csv
  python3 -I scripts/tratar_csv.py ENTRADA.csv --ddd-padrao 77 --saida-pasta resultados
"""
import argparse
import csv
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

csv.field_size_limit(sys.maxsize)

# DDDs existentes no Brasil (plano de numeração). Fonte: lista pública de códigos de área.
DDDS_VALIDOS = {
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "21", "22", "24", "27", "28",
    "31", "32", "33", "34", "35", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "51", "53", "54", "55",
    "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "71", "73", "74", "75", "77", "79",
    "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "91", "92", "93", "94", "95", "96", "97", "98", "99",
}

# ----------------------------------------------------------------- telefone


def _vazio(original="", motivo=""):
    return {"original": original, "tipo": "vazio" if not original else "invalido",
            "ddd": "", "numero": "", "e164": "", "formatado": "", "whatsapp": "",
            "motivo": motivo}


def normalizar_telefone(bruto, ddd_padrao=None):
    """Devolve um dict com tipo ('celular', 'fixo', '0800', 'invalido', 'vazio'),
    e164 (+55...), formatado, whatsapp (só celular) e motivo (quando inválido)."""
    original = (bruto or "").strip()
    if not original:
        return _vazio()
    digitos = re.sub(r"\D", "", original)
    if not digitos:
        return _vazio(original, "sem dígitos")

    # 0800 (ligação gratuita): 0800 + 7 dígitos. Não vira +55 nem WhatsApp.
    if re.fullmatch(r"0800\d{7}", digitos):
        d = digitos
        r = _vazio(original)
        r.update(tipo="0800", numero=d[1:], formatado=f"0800 {d[4:7]} {d[7:]}")
        return r

    com_mais55 = original.lstrip().startswith("+55")
    if digitos.startswith("0055"):          # 00 = prefixo internacional
        digitos = digitos[2:]
        com_mais55 = True
    resto = digitos
    # "55" só é código do país se veio com "+" ou se o tamanho (12/13) só cabe com ele.
    # Assim "(55) 3220-1234" (DDD 55, Santa Maria/RS) não perde o DDD.
    if digitos.startswith("55") and (com_mais55 or len(digitos) in (12, 13)):
        resto = digitos[2:]
    # prefixo de tronco "0" antes do DDD, ex.: 077 3421-1234
    if resto.startswith("0") and len(resto) in (11, 12):
        resto = resto[1:]

    if len(resto) in (10, 11):
        ddd, num = resto[:2], resto[2:]
    elif len(resto) in (8, 9):
        if not ddd_padrao:
            return _vazio(original, "sem DDD")
        ddd, num = str(ddd_padrao), resto
    else:
        return _vazio(original, "quantidade de dígitos inválida")

    if ddd not in DDDS_VALIDOS:
        return _vazio(original, f"DDD {ddd} não existe")
    if len(set(num)) == 1:
        return _vazio(original, "número com todos os dígitos iguais")

    if len(num) == 9:
        if num[0] != "9":
            return _vazio(original, "celular com 9 dígitos precisa começar com 9")
        tipo = "celular"
        formatado = f"({ddd}) {num[:5]}-{num[5:]}"
    else:  # 8 dígitos
        if num[0] not in "2345":
            return _vazio(original, "8 dígitos começando com 6-9 (celular antigo sem o 9): não convertido")
        tipo = "fixo"
        formatado = f"({ddd}) {num[:4]}-{num[4:]}"

    e164 = f"+55{ddd}{num}"
    return {"original": original, "tipo": tipo, "ddd": ddd, "numero": num, "e164": e164,
            "formatado": formatado,
            "whatsapp": f"https://wa.me/55{ddd}{num}" if tipo == "celular" else "",
            "motivo": ""}


# ------------------------------------------------------------------- e-mail

_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_EXT_ARQUIVO = {"png", "jpg", "jpeg", "gif", "svg", "webp", "avif", "ico", "css", "js",
                "woff", "woff2", "ttf", "eot", "pdf", "mp4"}
# Heurística nossa (não é lista oficial): domínios que aparecem em código de site, não em contatos.
_DOMINIOS_LIXO = {"sentry.io", "sentry-next.wixpress.com", "sentry.wixpress.com", "wixpress.com",
                  "domain.com", "dominio.com", "dominio.com.br", "seudominio.com.br",
                  "seusite.com.br", "meusite.com.br", "suaempresa.com.br", "yourdomain.com"}
_DOMINIOS_EXEMPLO = {"example.com", "example.org", "example.net"}
_LOCAIS_LIXO = {"email", "seuemail", "seu-email", "youremail", "nome", "name", "seunome",
                "usuario", "user", "teste", "test", "exemplo", "example", "fulano", "xxxx", "xxxxx"}
_NOREPLY = re.compile(r"^(no[-_.]?reply|do[-_.]?not[-_.]?reply|nao[-_.]?responda)", re.I)


def email_eh_lixo(email, permitir_exemplo=False):
    local, _, dominio = email.partition("@")
    tld = dominio.rsplit(".", 1)[-1]
    if tld in _EXT_ARQUIVO:
        return True
    if dominio in _DOMINIOS_LIXO:
        return True
    if dominio in _DOMINIOS_EXEMPLO and not permitir_exemplo:
        return True
    if local in _LOCAIS_LIXO or _NOREPLY.match(local):
        return True
    if len(email) > 254 or len(local) > 64 or ".." in email:
        return True
    return False


def limpar_emails(texto, permitir_exemplo=False):
    """Extrai e-mails de um texto (vírgulas, ';', colchetes JSON...) e remove lixo e repetidos."""
    vistos, saida = set(), []
    for achado in _RE_EMAIL.findall(texto or ""):
        e = achado.lower().strip(".")
        if e.startswith("u003e"):          # resto de escape JSON (">") colado no começo
            e = e[5:]
        if not _RE_EMAIL.fullmatch(e):
            continue
        if e in vistos:
            continue
        vistos.add(e)
        if not email_eh_lixo(e, permitir_exemplo):
            saida.append(e)
    return saida


# --------------------------------------------------------------- outros campos

_ESPACOS = re.compile(r"\s+")


def limpar_texto(v):
    return _ESPACOS.sub(" ", (v or "").replace("\x00", "")).strip()


def limpar_site(v):
    v = limpar_texto(v)
    if not v:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", v):
        v = "https://" + v
    partes = urlsplit(v)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        return ""
    consulta = [(k, val) for k, val in parse_qsl(partes.query, keep_blank_values=True)
                if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(consulta), ""))


def numero_ou_vazio(v, inteiro=False):
    v = limpar_texto(v).replace(",", ".")
    if not v:
        return ""
    try:
        f = float(v)
    except ValueError:
        return ""
    if inteiro:
        return str(int(f))
    return "" if f == 0 else f"{f:g}"


# ----------------------------------------------------------------- tratamento

COLUNAS_PADRAO = ["nome", "categoria", "endereco", "telefone", "tipo_telefone", "telefone_e164",
                  "whatsapp", "site", "email", "emails", "nota", "avaliacoes", "status",
                  "latitude", "longitude", "link_maps", "place_id", "fonte"]
COLUNAS_EXCEL = ["nome", "categoria", "endereco", "telefone", "tipo_telefone", "whatsapp",
                 "site", "email", "emails", "nota", "avaliacoes", "status", "link_maps", "fonte"]


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def tratar(linhas, ddd_padrao=None):
    """Recebe linhas no esquema do gosom; devolve (linhas_tratadas, estatisticas)."""
    est = {"lidas": 0, "sem_nome": 0, "duplicadas_place_id": 0, "duplicadas_telefone": 0,
           "finais": 0, "celular": 0, "fixo": 0, "0800": 0, "telefone_invalido": 0,
           "sem_telefone": 0, "emails_descartados": 0, "com_email": 0, "com_site": 0}
    vistos_place, vistos_tel, saida = set(), set(), []
    for r in linhas:
        est["lidas"] += 1
        nome = limpar_texto(r.get("title"))
        if not nome:
            est["sem_nome"] += 1
            continue
        place_id = limpar_texto(r.get("place_id"))
        if place_id and place_id in vistos_place:
            est["duplicadas_place_id"] += 1
            continue
        tel = normalizar_telefone(r.get("phone"), ddd_padrao)
        if tel["e164"] and tel["e164"] in vistos_tel:
            est["duplicadas_telefone"] += 1
            continue
        if place_id:
            vistos_place.add(place_id)
        if tel["e164"]:
            vistos_tel.add(tel["e164"])

        fonte = limpar_texto(r.get("fonte")) or "GOOGLE_MAPS"
        brutos = _RE_EMAIL.findall(r.get("emails") or "")
        emails = limpar_emails(r.get("emails"), permitir_exemplo=(fonte == "DEMO"))
        est["emails_descartados"] += max(0, len(set(e.lower() for e in brutos)) - len(emails))

        site = limpar_site(r.get("website"))
        if tel["tipo"] in ("celular", "fixo", "0800"):
            est[tel["tipo"]] += 1
        elif tel["tipo"] == "invalido":
            est["telefone_invalido"] += 1
        else:
            est["sem_telefone"] += 1
        est["com_email"] += 1 if emails else 0
        est["com_site"] += 1 if site else 0

        saida.append({
            "nome": nome,
            "categoria": limpar_texto(r.get("category")),
            "endereco": limpar_texto(r.get("address")),
            "telefone": tel["formatado"],
            "tipo_telefone": tel["tipo"] if tel["tipo"] != "vazio" else "",
            "telefone_e164": tel["e164"],
            "whatsapp": tel["whatsapp"],
            "site": site,
            "email": emails[0] if emails else "",
            "emails": " | ".join(emails),
            "nota": numero_ou_vazio(r.get("review_rating")),
            "avaliacoes": numero_ou_vazio(r.get("review_count"), inteiro=True),
            "status": limpar_texto(r.get("status")),
            "latitude": limpar_texto(r.get("latitude")),
            "longitude": limpar_texto(r.get("longitude")),
            "link_maps": limpar_texto(r.get("link")),
            "place_id": place_id,
            "fonte": fonte,
        })
    est["finais"] = len(saida)
    return saida, est


def _blindar_planilha(v):
    """Evita 'injeção de fórmula' no Excel: texto que começa com = + - @ vira texto puro."""
    return "'" + v if v and v[0] in "=+-@\t\r" else v


def para_excel_br(linha):
    out = {}
    for c in COLUNAS_EXCEL:
        v = linha.get(c, "")
        if c == "nota":
            v = v.replace(".", ",")
        out[c] = _blindar_planilha(v)
    return out


def salvar(saida, pasta, prefixo):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    padrao = pasta / f"{prefixo}-tratados.csv"
    excel = pasta / f"{prefixo}-excel.csv"
    with padrao.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_PADRAO)
        w.writeheader()
        w.writerows(saida)
    with excel.open("w", newline="", encoding="utf-8-sig") as f:   # BOM para o Excel acertar os acentos
        w = csv.DictWriter(f, fieldnames=COLUNAS_EXCEL, delimiter=";")
        w.writeheader()
        w.writerows(para_excel_br(l) for l in saida)
    return padrao, excel


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help="CSV do motor (esquema do gosom)")
    ap.add_argument("--saida-pasta", default="resultados", help="pasta de saída (padrão: resultados)")
    ap.add_argument("--prefixo", help="prefixo dos arquivos (padrão: nome do arquivo de entrada)")
    ap.add_argument("--ddd-padrao", help="DDD a usar quando o telefone vier sem DDD (ex.: 77)")
    a = ap.parse_args(argv)

    entrada = Path(a.entrada)
    if not entrada.exists():
        print(f"Não achei o arquivo: {entrada}", file=sys.stderr)
        return 1
    linhas = ler_csv(entrada)
    if not linhas:
        print("O arquivo não tem nenhuma linha de dados (o motor pode ter saído sem coletar nada).",
              file=sys.stderr)
        return 1
    saida, est = tratar(linhas, a.ddd_padrao)
    padrao, excel = salvar(saida, a.saida_pasta, a.prefixo or entrada.stem)
    print(f"Linhas lidas: {est['lidas']} | finais: {est['finais']}")
    print(f"Removidas: {est['duplicadas_place_id']} duplicadas por place_id, "
          f"{est['duplicadas_telefone']} por telefone, {est['sem_nome']} sem nome")
    print(f"Telefones: {est['celular']} celular, {est['fixo']} fixo, {est['0800']} 0800, "
          f"{est['telefone_invalido']} inválidos, {est['sem_telefone']} sem telefone")
    print(f"E-mails: {est['com_email']} linhas com e-mail útil, {est['emails_descartados']} e-mails lixo descartados")
    print(f"Arquivo padrão (UTF-8, vírgula): {padrao}")
    print(f"Arquivo para Excel brasileiro (;  UTF-8 com BOM): {excel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
