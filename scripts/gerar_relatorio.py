#!/usr/bin/env python3
"""Gera UM arquivo HTML com a lista de leads: abre com duplo clique, funciona offline.

- Sem CDN, sem fontes remotas, sem scripts externos.
- Os dados ficam dentro do próprio arquivo. A página declara uma política de segurança
  (CSP) que proíbe qualquer conexão de rede: nada é enviado para a internet.
- Tabela com busca, filtros (telefone, WhatsApp, site, e-mail), ordenação e botão de WhatsApp.
- No celular a tabela vira cartões.

Entrada: o CSV "-tratados.csv" gerado por scripts/tratar_csv.py.

Uso:
  python3 -I scripts/gerar_relatorio.py resultados/demo-leads-tratados.csv --saida examples/demo-relatorio.html
"""
import argparse
import csv
import html
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visual  # noqa: E402

csv.field_size_limit(sys.maxsize)

CAMPOS = ["nome", "categoria", "endereco", "telefone", "tipo_telefone", "whatsapp", "site",
          "email", "emails", "nota", "avaliacoes", "status", "link_maps", "fonte"]

MODELO = (Path(__file__).resolve().parent / "modelo_relatorio.html").read_text(encoding="utf-8")


def json_seguro_para_html(obj):
    """JSON que pode ser colocado dentro de <script> sem fechar a tag nem quebrar o parser."""
    txt = json.dumps(obj, ensure_ascii=False)
    return (txt.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
               .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def ler_linhas(caminho):
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        leitor = csv.DictReader(f)
        return [{c: (r.get(c) or "") for c in CAMPOS} for r in leitor]


def lista_consultas_html(consultas, maximo=12):
    consultas = [c for c in (consultas or []) if c.strip()]
    if not consultas:
        return ""
    itens = "".join(f"<li>{html.escape(c)}</li>" for c in consultas[:maximo])
    if len(consultas) > maximo:
        itens += f"<li>+{len(consultas) - maximo} consultas</li>"
    return f'<ul class="consultas" aria-label="Buscas desta lista">{itens}</ul>'


def gerar(linhas, titulo, consultas=None):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    trocas = [
        ("__ESTILO_BASE__", visual.ESTILO_BASE),
        ("__MARCA__", visual.MARCA_SVG),
        ("__ICONE_BUSCA__", visual.icone_svg("busca")),
        ("__ICONE_LIMPAR__", visual.icone_svg("limpar")),
        ("__ICONE_COPIAR__", visual.icone_svg("copiar")),
        ("__ICONE_BAIXAR__", visual.icone_svg("baixar")),
        ("__ICONES_JSON__", json_seguro_para_html(visual.ICONES)),
        ("__TITULO__", html.escape(titulo)),
        ("__GERADO__", agora),
        ("__TOTAL__", str(len(linhas))),
        ("__CONSULTAS__", lista_consultas_html(consultas)),
    ]
    pagina = MODELO
    for marcador, valor in trocas:
        pagina = pagina.replace(marcador, valor)
    # Os dados entram por último, para que nenhum texto vindo do CSV seja tratado como marcador.
    return pagina.replace("__DADOS__", json_seguro_para_html(linhas))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help="CSV tratado (saída de tratar_csv.py, '-tratados.csv')")
    ap.add_argument("--saida", help="arquivo HTML de saída (padrão: ao lado da entrada)")
    ap.add_argument("--titulo", default="Lista de leads", help="título da página")
    ap.add_argument("--consultas", help="arquivo com as consultas da busca (aparecem no topo da página)")
    a = ap.parse_args(argv)
    entrada = Path(a.entrada)
    if not entrada.exists():
        print(f"Não achei o arquivo: {entrada}", file=sys.stderr)
        return 1
    linhas = ler_linhas(entrada)
    if not linhas:
        print("O CSV não tem linhas de dados; nada para mostrar.", file=sys.stderr)
        return 1
    saida = Path(a.saida) if a.saida else entrada.with_suffix(".html")
    saida.parent.mkdir(parents=True, exist_ok=True)
    consultas = None
    if a.consultas and Path(a.consultas).exists():
        consultas = [c.strip() for c in Path(a.consultas).read_text(encoding="utf-8-sig").splitlines()
                     if c.strip() and not c.strip().startswith("#")]
    saida.write_text(gerar(linhas, a.titulo, consultas), encoding="utf-8")
    print(f"Relatório gerado: {saida} ({len(linhas)} empresas, {saida.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
