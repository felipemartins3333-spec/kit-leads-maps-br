#!/usr/bin/env python3
"""Resumo de um teste real: SOMENTE números, tempos, versão do motor e ambiente.

Nunca escreve nome, telefone, e-mail ou site de empresa no relatório, para que ele possa
ser colado no chat sem expor dados. Só usa a biblioteca padrão.

Uso:
  python3 -I scripts/resumo_teste.py                  # gera resultados/relatorio-teste.txt
  python3 -I scripts/resumo_teste.py --linhas ARQUIVO # só imprime quantas linhas de dados
"""
import argparse
import csv
import sys
from pathlib import Path

# Campos do CSV do motor podem ser enormes (avaliações em JSON).
csv.field_size_limit(sys.maxsize)

VAZIOS = {"", "[]", "null", "none", "nan", "{}", "0", "0.0"}


def ler_linhas(caminho):
    """Lê o CSV com o módulo csv (certo mesmo com quebras de linha dentro de campos)."""
    p = Path(caminho)
    if not p.exists() or p.stat().st_size == 0:
        return []
    with p.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def preenchido(valor, nulos_extra=()):
    v = (valor or "").strip().lower()
    return v not in VAZIOS and v not in nulos_extra


def percentuais(linhas):
    n = len(linhas)
    if n == 0:
        return None
    # "0" só conta como vazio em nota; em telefone/site/e-mail "0" nunca é dado útil também.
    def pct(campo):
        ok = sum(1 for r in linhas if preenchido(r.get(campo)))
        return ok, 100.0 * ok / n
    ids = [r.get("place_id", "") for r in linhas if (r.get("place_id") or "").strip()]
    return {
        "linhas": n,
        "telefone": pct("phone"),
        "site": pct("website"),
        "email": pct("emails"),
        "nota": pct("review_rating"),
        "place_id_repetidos": len(ids) - len(set(ids)),
        "colunas": len(linhas[0]),
    }


def ler_chave_valor(caminho):
    d = {}
    p = Path(caminho)
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            if "=" in ln:
                k, v = ln.split("=", 1)
                d[k.strip()] = v.strip()
    return d


def ler_medicoes(caminho):
    campos = ["teste", "lang", "email", "segundos", "linhas_csv", "codigo_saida", "arquivo"]
    res = []
    p = Path(caminho)
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            partes = ln.split("\t")
            if len(partes) == len(campos):
                res.append(dict(zip(campos, partes)))
    return res


def fmt(par):
    ok, pc = par
    return f"{ok} ({pc:.1f}%)"


def gerar_relatorio(pasta):
    pasta = Path(pasta)
    amb = ler_chave_valor(pasta / "ambiente.txt")
    meds = ler_medicoes(pasta / "medicoes.tsv")
    out = ["RELATÓRIO DO TESTE REAL (somente números; sem dados de empresas)", ""]
    out.append("== Ambiente ==")
    for k in ("data", "so", "arquitetura", "ram_mb", "disco_livre_gb", "docker",
              "motor_versao", "imagem_digest", "python"):
        if k in amb:
            out.append(f"{k}: {amb[k]}")
    out += ["", "== Medições =="]
    if not meds:
        out.append("Nenhuma medição encontrada (o teste não rodou até o fim).")
    for m in meds:
        out.append(f"\n[{m['teste']}] idioma={m['lang']} email={m['email']} "
                   f"tempo={m['segundos']}s código_saída={m['codigo_saida']}")
        est = percentuais(ler_linhas(pasta / m["arquivo"]))
        if est is None:
            out.append("  linhas de dados: 0  (nada coletado)")
            continue
        out.append(f"  linhas de dados: {est['linhas']}   colunas: {est['colunas']}")
        out.append(f"  com telefone: {fmt(est['telefone'])}   sem: {est['linhas'] - est['telefone'][0]}")
        out.append(f"  com site:     {fmt(est['site'])}   sem: {est['linhas'] - est['site'][0]}")
        out.append(f"  com e-mail:   {fmt(est['email'])}   sem: {est['linhas'] - est['email'][0]}")
        out.append(f"  com nota:     {fmt(est['nota'])}")
        out.append(f"  place_id repetidos: {est['place_id_repetidos']}")
    out += ["", "Observações: 'preenchido' = campo não vazio (e diferente de [], null, 0).",
            "Teste com 3 consultas, -depth 1, sem proxy: os números NÃO representam volume real."]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", default="resultados", help="pasta com medicoes.tsv e os CSVs")
    ap.add_argument("--linhas", metavar="ARQUIVO", help="só imprime a contagem de linhas de dados")
    a = ap.parse_args(argv)
    if a.linhas:
        print(len(ler_linhas(a.linhas)))
        return 0
    rel = gerar_relatorio(a.pasta)
    destino = Path(a.pasta) / "relatorio-teste.txt"
    destino.write_text(rel, encoding="utf-8")
    print(rel)
    print(f"Relatório salvo em: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
