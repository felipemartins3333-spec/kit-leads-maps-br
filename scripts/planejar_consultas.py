#!/usr/bin/env python3
"""Planejador de consultas: combina segmentos x cidades e gera o arquivo de consultas do motor.

Não acessa a internet. Cada linha gerada tem o formato "segmento em Cidade UF", por exemplo
"clínicas odontológicas em Vitória da Conquista BA".

Uso:
  python3 -I scripts/planejar_consultas.py \\
      --segmentos "clínicas odontológicas" "escritórios de contabilidade" \\
      --cidades "Vitória da Conquista BA" "Salvador/BA" \\
      --saida resultados/consultas.txt

  python3 -I scripts/planejar_consultas.py --segmentos-arquivo segmentos.txt --cidades-arquivo cidades.txt

Cada consulta vira uma busca no Google Maps: mais consultas = mais tempo e mais risco de o
Google limitar o seu acesso. Por segurança, o padrão é no máximo 30 consultas por arquivo.
"""
import argparse
import re
import sys
from pathlib import Path

UFS = {"AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
       "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"}
LIMITE_PADRAO = 30
LIMITE_TESTE = 3


def _espacos(s):
    return re.sub(r"\s+", " ", s or "").strip()


def normalizar_segmento(s):
    s = _espacos(s)
    s = re.sub(r"\s+em$", "", s, flags=re.I)     # "dentistas em" -> "dentistas"
    return s


def normalizar_cidade(s):
    """Aceita 'Cidade UF', 'Cidade/UF', 'Cidade - UF', 'Cidade, UF'. Devolve (texto, tem_uf)."""
    s = _espacos(s)
    m = re.match(r"^(.*?)[\s,/\-–]+([A-Za-z]{2})$", s)
    if m and m.group(2).upper() in UFS:
        cidade = _espacos(m.group(1).rstrip(",-–/ "))
        if cidade:
            return f"{cidade} {m.group(2).upper()}", True
    return s, False


def montar(segmentos, cidades):
    """Devolve (consultas, avisos). Ordem: cidade por cidade, para dar para rodar aos poucos."""
    avisos, vistos, consultas = [], set(), []
    segs = []
    for s in segmentos:
        n = normalizar_segmento(s)
        if not n:
            continue
        if "#!#" in n:
            raise ValueError(f"O segmento {n!r} contém '#!#', que é reservado pelo motor.")
        if n.lower() not in {x.lower() for x in segs}:
            segs.append(n)
    cids = []
    for c in cidades:
        n, tem_uf = normalizar_cidade(c)
        if not n:
            continue
        if "#!#" in n:
            raise ValueError(f"A cidade {n!r} contém '#!#', que é reservado pelo motor.")
        if not tem_uf:
            avisos.append(f"A cidade {n!r} está sem UF: o Google pode escolher uma cidade de mesmo nome em outro estado. "
                          f"Prefira escrever, por exemplo, '{n} BA'.")
        if n.lower() not in {x.lower() for x in cids}:
            cids.append(n)
    for cid in cids:
        for seg in segs:
            q = f"{seg} em {cid}"
            if q.lower() not in vistos:
                vistos.add(q.lower())
                consultas.append(q)
    return consultas, avisos


def ler_lista(caminho):
    linhas = Path(caminho).read_text(encoding="utf-8-sig").splitlines()
    return [l.strip() for l in linhas if l.strip() and not l.strip().startswith("#")]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--segmentos", nargs="+", default=[], metavar="SEGMENTO")
    ap.add_argument("--cidades", nargs="+", default=[], metavar="CIDADE_UF")
    ap.add_argument("--segmentos-arquivo", help="arquivo com um segmento por linha")
    ap.add_argument("--cidades-arquivo", help="arquivo com uma cidade por linha")
    ap.add_argument("--saida", default="resultados/consultas.txt", help="arquivo de consultas a gerar")
    ap.add_argument("--limite", type=int, default=LIMITE_PADRAO,
                    help=f"máximo de consultas no arquivo (padrão {LIMITE_PADRAO})")
    ap.add_argument("--teste", action="store_true",
                    help=f"modo teste: aceita no máximo {LIMITE_TESTE} consultas")
    a = ap.parse_args(argv)

    segmentos = list(a.segmentos) + (ler_lista(a.segmentos_arquivo) if a.segmentos_arquivo else [])
    cidades = list(a.cidades) + (ler_lista(a.cidades_arquivo) if a.cidades_arquivo else [])
    if not segmentos or not cidades:
        print("Informe pelo menos 1 segmento e 1 cidade (--segmentos / --cidades).", file=sys.stderr)
        return 2
    try:
        consultas, avisos = montar(segmentos, cidades)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2

    limite = LIMITE_TESTE if a.teste else a.limite
    if len(consultas) > limite:
        print(f"Foram geradas {len(consultas)} consultas, mais que o limite de {limite}.\n"
              f"Reduza segmentos/cidades ou, se for de propósito, aumente com --limite. "
              f"Lembre: quanto mais consultas, mais tempo e mais risco de bloqueio pelo Google. Nada foi salvo.",
              file=sys.stderr)
        return 1

    saida = Path(a.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text("\n".join(consultas) + "\n", encoding="utf-8")
    for av in avisos:
        print(f"[aviso] {av}", file=sys.stderr)
    print(f"{len(consultas)} consultas salvas em {saida}:")
    for c in consultas:
        print(f"  - {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
