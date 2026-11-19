"""Identidade visual do kit: cores, tipografia, marca e ícones (desenhos próprios, sem dependências).

Usado pelo relatório (gerar_relatorio.py) e pelo painel de buscas (painel.py). Nada aqui busca
fonte, imagem ou script na internet: tudo fica dentro do próprio arquivo HTML.
"""
import html

ESTILO_BASE = """
:root{
  --serifa:"Iowan Old Style","Palatino Linotype","Book Antiqua",Palatino,Georgia,serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --fundo:#F5F2EC; --fundo-vidro:rgba(245,242,236,.9); --papel:#FFFFFF; --papel-2:#FAF8F4;
  --tinta:#14212A; --suave:#56656D; --linha:#E7E1D6; --borda-campo:#D6CEC0; --trilho:#EEE8DD;
  --marca:#0F6B62; --marca-forte:#0B544D; --marca-suave:#E3F0ED; --marca-texto:#FFFFFF;
  --zap:#137A45; --zap-texto:#FFFFFF; --zap-suave:#E1F2E7; --zap-forte:#0D5A32;
  --ouro:#A87A1F; --foco:#0F6B62; --aviso-fundo:#FFF3DC; --aviso-texto:#5A3B00;
  --av0:#E1ECF7; --av1:#F5E5D6; --av2:#E2F0E3; --av3:#ECE3F3; --av4:#F6E1E4; --av5:#E2EDEA; --av-tinta:#1C2A32;
  --sombra:0 1px 2px rgba(20,33,42,.04),0 10px 24px -16px rgba(20,33,42,.22);
  --brilho:rgba(15,107,98,.11);
}
@media (prefers-color-scheme: dark){
  :root{
    --fundo:#0D1316; --fundo-vidro:rgba(13,19,22,.88); --papel:#141C20; --papel-2:#182227;
    --tinta:#E8EEF0; --suave:#9FB0B7; --linha:#243238; --borda-campo:#33454D; --trilho:#22313A;
    --marca:#5FC9BD; --marca-forte:#86DCD2; --marca-suave:#163735; --marca-texto:#052320;
    --zap:#35B36F; --zap-texto:#04170C; --zap-suave:#163A27; --zap-forte:#86DEA9;
    --ouro:#E2B65A; --foco:#86DCD2; --aviso-fundo:#33270F; --aviso-texto:#FBE3B0;
    --av0:#1F3142; --av1:#3B2C20; --av2:#1F3526; --av3:#2D2439; --av4:#3B2429; --av5:#20322F; --av-tinta:#E8EEF0;
    --sombra:none; --brilho:rgba(95,201,189,.07);
  }
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;color:var(--tinta);font:16px/1.55 var(--sans);
  background:radial-gradient(1100px 420px at 8% -8%,var(--brilho),transparent 62%),var(--fundo);background-color:var(--fundo)}
.pagina{max-width:1200px;margin:0 auto;padding:30px 20px 56px}
.marca{display:flex;align-items:center;gap:10px;color:var(--marca-forte);font-size:.76rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase}
.marca svg{width:28px;height:28px;color:var(--marca)}
h1{font:600 clamp(1.7rem,3.2vw,2.4rem)/1.15 var(--serifa);letter-spacing:-.015em;margin:14px 0 6px}
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
