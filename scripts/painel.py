#!/usr/bin/env python3
"""Painel das suas buscas: uma página (resultados/painel.html) com todas as buscas feitas.

Cada busca vira um cartão com os números (empresas, WhatsApp, site, e-mail) e atalhos para o
relatório e a planilha. Abre com duplo clique, funciona sem internet e não usa JavaScript.

Uso:
  python3 -I scripts/painel.py                 # gera resultados/painel.html
  python3 -I scripts/painel.py --pasta OUTRA   # outra pasta de resultados
"""
import argparse
import csv
import html
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visual  # noqa: E402

csv.field_size_limit(sys.maxsize)
PADRAO_PASTA = re.compile(r"^busca-(\d{8})-(\d{6})$")

ESTILO_PAINEL = """
.resumo-geral{display:flex;flex-wrap:wrap;gap:10px 22px;margin:14px 0 0;color:var(--suave)}
.resumo-geral strong{color:var(--tinta);font-variant-numeric:tabular-nums}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;margin-top:26px}
.cartao{display:flex;flex-direction:column;background:var(--papel);border:1px solid var(--linha);border-radius:18px;padding:18px;box-shadow:var(--sombra)}
.cartao-topo{display:flex;align-items:center;gap:8px;color:var(--suave);font-size:.85rem}
.cartao-topo svg{width:16px;height:16px}
.cartao h2{font:600 1.15rem/1.3 var(--serifa);margin:10px 0 4px}
.mais-consultas{color:var(--suave);font-size:.86rem;margin:0}
.numeros{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:16px 0}
.numero{background:var(--papel-2);border:1px solid var(--linha);border-radius:12px;padding:8px 10px}
.numero b{display:block;font:600 1.2rem/1.1 var(--serifa);font-variant-numeric:tabular-nums;white-space:nowrap}
.numero small{font:500 .78rem/1 var(--sans);color:var(--suave)}
.numero span{display:block;font-size:.74rem;color:var(--suave);margin-top:2px}
.numero i{display:block;height:3px;margin-top:8px;border-radius:99px;background:var(--trilho);overflow:hidden}
.numero i>u{display:block;height:100%;background:var(--marca);text-decoration:none}
.numero.zap i>u{background:var(--zap)}
.cartao .botoes{margin-top:auto}
.vazio-painel{margin-top:26px;padding:28px;border:1px dashed var(--borda-campo);border-radius:18px;background:var(--papel);max-width:720px}
.vazio-painel h2{font:600 1.25rem/1.3 var(--serifa);margin:0 0 8px}
code{font:500 .9em/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--papel-2);border:1px solid var(--linha);border-radius:8px;padding:2px 6px}
@media (max-width:520px){.numeros{grid-template-columns:repeat(2,minmax(0,1fr))}}
"""


def ler_busca(pasta):
    """Lê uma pasta busca-AAAAMMDD-HHMMSS. Devolve dict ou None se não for uma busca completa."""
    m = PADRAO_PASTA.match(pasta.name)
    tratados = pasta / "leads-tratados.csv"
    if not m or not tratados.exists():
        return None
    try:
        quando = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    except ValueError:
        return None
    with tratados.open(newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f))
    consultas = []
    arq = pasta / "consultas.txt"
    if arq.exists():
        consultas = [c.strip() for c in arq.read_text(encoding="utf-8-sig").splitlines() if c.strip()]
    n = len(linhas)
    return {
        "pasta": pasta.name, "quando": quando, "consultas": consultas, "empresas": n,
        "zap": sum(1 for l in linhas if (l.get("whatsapp") or "").startswith("https://wa.me/")),
        "site": sum(1 for l in linhas if (l.get("site") or "").strip()),
        "email": sum(1 for l in linhas if (l.get("email") or "").strip()),
        "tem_relatorio": (pasta / "relatorio.html").exists(),
        "tem_excel": (pasta / "leads-excel.csv").exists(),
    }


def coletar(pasta_resultados):
    pasta_resultados = Path(pasta_resultados)
    if not pasta_resultados.exists():
        return []
    buscas = [b for b in (ler_busca(p) for p in pasta_resultados.iterdir() if p.is_dir()) if b]
    return sorted(buscas, key=lambda b: b["quando"], reverse=True)


def _numero(rotulo, valor, total, classe=""):
    pct = round(100 * valor / total) if total else 0
    return (f'<div class="numero {classe}"><b>{valor} <small>{pct}%</small></b><span>{html.escape(rotulo)}</span>'
            f'<i><u style="width:{pct}%"></u></i></div>')


def cartao(b):
    titulo = b["consultas"][0] if b["consultas"] else b["pasta"]
    extra = len(b["consultas"]) - 1
    total = b["empresas"]
    botoes = []
    if b["tem_relatorio"]:
        botoes.append(f'<a class="botao principal" href="{html.escape(b["pasta"])}/relatorio.html">'
                      f'{visual.icone_svg("abrir")}Abrir relatório</a>')
    if b["tem_excel"]:
        botoes.append(f'<a class="botao" href="{html.escape(b["pasta"])}/leads-excel.csv">'
                      f'{visual.icone_svg("planilha")}Planilha</a>')
    return (
        '<article class="cartao">'
        f'<div class="cartao-topo">{visual.icone_svg("relogio")}{b["quando"]:%d/%m/%Y às %H:%M}</div>'
        f'<h2>{html.escape(titulo)}</h2>'
        + (f'<p class="mais-consultas">+ {extra} consulta{"s" if extra > 1 else ""}</p>' if extra > 0 else "")
        + '<div class="numeros">'
        + f'<div class="numero"><b>{total}</b><span>empresas</span><i><u style="width:{100 if total else 0}%"></u></i></div>'
        + _numero("WhatsApp", b["zap"], total, "zap")
        + _numero("site", b["site"], total)
        + _numero("e-mail", b["email"], total)
        + '</div>'
        + (f'<div class="botoes">{"".join(botoes)}</div>' if botoes else
           '<p class="mais-consultas">Relatório e planilha não encontrados nesta pasta.</p>')
        + '</article>'
    )


def gerar_html(buscas, comando_python="python3"):
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    if buscas:
        total = sum(b["empresas"] for b in buscas)
        corpo = (f'<div class="resumo-geral"><span><strong>{len(buscas)}</strong> busca{"s" if len(buscas) > 1 else ""}</span>'
                 f'<span><strong>{total}</strong> empresas no total</span>'
                 f'<span>atualizado em {agora}</span></div>'
                 f'<section class="grade" aria-label="Buscas">{"".join(cartao(b) for b in buscas)}</section>')
    else:
        exemplo = html.escape(f'{comando_python} scripts/kit.py buscar --segmentos "academias" --cidades "Salvador BA"')
        corpo = ('<div class="vazio-painel"><h2>Nenhuma busca ainda</h2>'
                 '<p>Faça a primeira busca e ela aparece aqui:</p>'
                 f'<p><code>{exemplo}</code></p>'
                 '<p>Ou, no Claude: <code>/leads-buscar academias em Salvador BA</code></p></div>')
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none'; base-uri 'none'">
<meta name="referrer" content="no-referrer">
<meta name="color-scheme" content="light dark">
<title>Suas buscas · Kit de Leads</title>
<style>{visual.ESTILO_BASE}{ESTILO_PAINEL}</style>
</head>
<body>
<div class="pagina">
  <header class="topo">
    <div class="marca">{visual.MARCA_SVG}<span>Kit de Leads · Google Maps</span></div>
    <h1>Suas buscas</h1>
    <p class="sub">Todas as listas que você montou com o kit, da mais nova para a mais antiga.</p>
  </header>
  {corpo}
  <footer class="rodape">
    <p>Os dados ficam só no seu computador, na pasta <code>resultados/</code>. Esta página não envia nada para a internet.</p>
    <p>Coletar dados do Google Maps pode contrariar os termos do Google; contatos de empresas envolvem LGPD.
    Motor de coleta: <span class="credito">gosom/google-maps-scraper</span> (código aberto, licença MIT).</p>
  </footer>
</div>
</body>
</html>
"""


def gerar_painel(pasta_resultados, comando_python="python3"):
    pasta_resultados = Path(pasta_resultados)
    pasta_resultados.mkdir(parents=True, exist_ok=True)
    destino = pasta_resultados / "painel.html"
    destino.write_text(gerar_html(coletar(pasta_resultados), comando_python), encoding="utf-8")
    return destino


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pasta", default="resultados", help="pasta de resultados (padrão: resultados)")
    a = ap.parse_args(argv)
    destino = gerar_painel(a.pasta)
    print(f"Painel gerado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
