"""Identidade visual do kit: cores, tipografia, marca e ícones (desenhos próprios, sem dependências).

Usado pelo relatório (gerar_relatorio.py) e pelo painel de buscas (painel.py). Nada aqui busca
fonte, imagem ou script na internet: tudo fica dentro do próprio arquivo HTML.
"""
import base64
import html
from pathlib import Path

ESTILO_BASE = """
:root{
  --serifa:"Archivo Largo","Archivo",system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
  --sans:"Archivo",system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --fundo:#EEF1EC; --fundo-vidro:rgba(238,241,236,.92); --papel:#FFFFFF; --papel-2:#F6F8F5;
  --tinta:#1B2622; --suave:#55635D; --linha:#DCE2DC; --borda-campo:#C9D2CB; --trilho:#E3E8E3;
  --marca:#0F6B62; --marca-forte:#0A5049; --marca-suave:#E1EFEB; --marca-texto:#FFFFFF;
  --acao:#C2410C; --acao-forte:#9A3412; --acao-texto:#FFFFFF;
  --zap:#137A45; --zap-texto:#FFFFFF; --zap-suave:#E1F2E7; --zap-forte:#0D5A32;
  --ouro:#9A6B12; --foco:#C2410C; --aviso-fundo:#FDF0E2; --aviso-texto:#6B2C06;
  --av0:#DDE9F2; --av1:#F3E3D3; --av2:#DDEEDF; --av3:#E8E0F0; --av4:#F3DEE1; --av5:#DCEBE7; --av-tinta:#1B2622;
  --sombra:0 1px 0 rgba(27,38,34,.04),0 12px 32px -20px rgba(27,38,34,.28);
  --raio-g:22px; --raio:12px; --raio-p:8px;
}
@media (prefers-color-scheme: dark){
  :root{
    --fundo:#0E1412; --fundo-vidro:rgba(14,20,18,.9); --papel:#161E1B; --papel-2:#1B2521;
    --tinta:#E6ECE8; --suave:#9DADA5; --linha:#26332E; --borda-campo:#35443E; --trilho:#22302B;
    --marca:#5FC9BD; --marca-forte:#86DCD2; --marca-suave:#153532; --marca-texto:#052320;
    --acao:#FB8A4C; --acao-forte:#FDAA7A; --acao-texto:#2A0E02;
    --zap:#35B36F; --zap-texto:#04170C; --zap-suave:#163A27; --zap-forte:#86DEA9;
    --ouro:#E2B65A; --foco:#FB8A4C; --aviso-fundo:#33210F; --aviso-texto:#FBDDC0;
    --av0:#1F3142; --av1:#3B2C20; --av2:#1F3526; --av3:#2D2439; --av4:#3B2429; --av5:#20322F; --av-tinta:#E6ECE8;
    --sombra:none;
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--tinta);font:16px/1.55 var(--sans);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;
  background:var(--fundo)}
.pagina{max-width:1200px;margin:0 auto;padding:30px 20px 56px}
.marca{display:flex;align-items:center;gap:9px;color:var(--tinta);font:700 1rem/1 var(--serifa);letter-spacing:-.01em}
.marca svg{width:28px;height:28px;color:var(--marca)}
h1{font:800 clamp(1.9rem,3.6vw,2.75rem)/1.04 var(--serifa);letter-spacing:-.03em;margin:18px 0 10px;max-width:18ch}
.sub{margin:0;color:var(--suave)}
.consultas{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0 0;padding:0;list-style:none}
.consultas li{padding:4px 12px;border-radius:99px;background:var(--papel);border:1px solid var(--linha);font-size:.85rem;color:var(--suave)}
.aviso{margin:16px 0 0;padding:12px 16px;border-radius:14px;background:var(--aviso-fundo);color:var(--aviso-texto);font-size:.95rem}
.botao{display:inline-flex;align-items:center;justify-content:center;gap:8px;font:500 .95rem/1.1 var(--sans);min-height:42px;padding:10px 16px;
  border-radius:12px;border:1px solid var(--borda-campo);background:var(--papel);color:var(--tinta);cursor:pointer;text-decoration:none;
  transition:border-color .15s,background .15s,transform .05s}
.botao:hover{border-color:var(--marca);background:var(--marca-suave)}
.botao:active{transform:translateY(1px)}
.botao svg{width:17px;height:17px;flex:0 0 auto}
.botao.principal{background:var(--marca);border-color:var(--marca);color:var(--marca-texto);font-weight:600}
.botao.principal:hover{background:var(--marca-forte);border-color:var(--marca-forte)}
.botao.acao{background:var(--acao);border-color:var(--acao);color:var(--acao-texto);font-weight:650}
.botao.acao:hover{background:var(--acao-forte);border-color:var(--acao-forte)}
.botoes{display:flex;flex-wrap:wrap;gap:8px}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--foco);outline-offset:2px}
.rodape{margin-top:40px;padding-top:18px;border-top:1px solid var(--linha);color:var(--suave);font-size:.86rem;max-width:84ch}
.rodape p{margin:8px 0}
.credito{font-weight:600;color:var(--tinta)}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

# Ícones desenhados para o kit (traços simples num quadro 24x24).
ICONES = {
    "busca": ["M10.5 17a6.5 6.5 0 1 0 0-13 6.5 6.5 0 0 0 0 13z", "M15.5 15.5 20 20"],
    "globo": ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M3.5 9h17M3.5 15h17",
              "M12 3c2.4 2.5 3.6 5.5 3.6 9s-1.2 6.5-3.6 9c-2.4-2.5-3.6-5.5-3.6-9S9.6 5.5 12 3z"],
    "envelope": ["M4 6h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z", "M3.5 7l8.5 6 8.5-6"],
    "pino": ["M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11z",
             "M12 12.3a2.3 2.3 0 1 0 0-4.6 2.3 2.3 0 0 0 0 4.6z"],
    "conversa": ["M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.4-4.2A8 8 0 1 1 20 11.5z", "M8.5 11.5h.01M12 11.5h.01M15.5 11.5h.01"],
    "copiar": ["M10 8h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2z",
               "M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"],
    "baixar": ["M12 4v11", "M7.5 10.5 12 15l4.5-4.5", "M5 20h14"],
    "limpar": ["M6 6l12 12", "M18 6 6 18"],
    "planilha": ["M5 4h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z", "M4 9.5h16M4 14.5h16M10 4v16"],
    "relogio": ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M12 7.5V12l3 2"],
    "telefone": ["M6.6 3.5h2.8l1.4 3.8-1.9 1.3a10.5 10.5 0 0 0 5.5 5.5l1.3-1.9 3.8 1.4v2.8a2 2 0 0 1-2.2 2A16 16 0 0 1 4.6 5.7a2 2 0 0 1 2-2.2z"],
    "expandir": ["M4 9V4h5", "M20 9V4h-5", "M4 15v5h5", "M20 15v5h-5"],
    "centralizar": ["M12 19.5a7.5 7.5 0 1 0 0-15 7.5 7.5 0 0 0 0 15z", "M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3",
                    "M12 14.2a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4z"],
    "lixeira": ["M4 7h16", "M10 11v6M14 11v6", "M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12", "M9 7V4h6v3"],
    "alvo": ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z", "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M12 12h.01"],
    "abrir": ["M14 4h6v6", "M20 4l-9 9", "M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"],
}

MARCA_SVG = ('<svg viewBox="0 0 32 32" aria-hidden="true">'
             '<rect x="1" y="1" width="30" height="30" rx="9" fill="currentColor"/>'
             '<path d="M16 25s-6.2-5.6-6.2-10.4a6.2 6.2 0 0 1 12.4 0C22.2 19.4 16 25 16 25z" style="fill:var(--papel)"/>'
             '<circle cx="16" cy="14.6" r="2.3" fill="currentColor"/></svg>')


def icone_svg(nome):
    """Ícone como texto HTML (para as partes geradas pelo Python)."""
    caminhos = "".join(f'<path d="{html.escape(d)}"/>' for d in ICONES[nome])
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{caminhos}</svg>')


def _fontes():
    """Fonte Archivo (Omnibus-Type, OFL-1.1) embutida em base64, sem Google Fonts. Um arquivo variável
    serve para duas famílias: "Archivo" (largura normal, textos) e "Archivo Largo" (títulos, mais larga)."""
    arq = Path(__file__).resolve().parent / "vendor" / "archivo" / "archivo-latin-wdth-normal.woff2"
    if not arq.exists():
        return ""
    dados = base64.b64encode(arq.read_bytes()).decode("ascii")
    fonte = 'src:url(data:font/woff2;base64,%s) format("woff2")' % dados
    return ('@font-face{font-family:"Archivo";font-style:normal;font-weight:100 900;font-stretch:100%%;font-display:swap;%s}\n'
            '@font-face{font-family:"Archivo Largo";font-style:normal;font-weight:100 900;font-stretch:118%%;font-display:swap;%s}'
            % (fonte, fonte))


ESTILO_BASE = _fontes() + "\n" + ESTILO_BASE
