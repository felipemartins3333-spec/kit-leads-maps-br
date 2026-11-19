---
name: leads-maps-br
description: Monta listas de empresas brasileiras do Google Maps para prospecção (segmento + cidade), com telefone +55, link de WhatsApp, site, e-mail, planilha para Excel e relatório HTML. Use quando a pessoa pedir, em português, coisas como "lista de dentistas em Salvador", "leads de academias em Vitória da Conquista", "empresas do Google Maps com WhatsApp", "prospecção por cidade", ou quiser instalar ou testar este kit.
---

# Kit de leads do Google Maps (Brasil)

Este repositório transforma "segmento + cidade" em lista de empresas. O motor é a imagem oficial
`gosom/google-maps-scraper`; a camada brasileira é o `scripts/kit.py`. Quem pede costuma não ser técnico:
português simples, um passo por vez. As regras completas estão no `CLAUDE.md` da raiz.

## Qual fluxo seguir

| A pessoa quer… | Faça |
|---|---|
| instalar, configurar, "deixar funcionando", testar | siga `.claude/commands/leads-instalar.md` |
| uma lista de empresas | siga `.claude/commands/leads-buscar.md`, com o pedido dela |
| abrir ou entender um resultado | aponte `resultados/busca-.../relatorio.html` e `leads-excel.csv` |
| algo que deu errado | `python3 scripts/kit.py verificar` e a tabela "Problemas comuns" de `docs/instalacao.md` |

## Comandos válidos (não invente outros)

- `python3 scripts/kit.py verificar` · `preparar` · `testar`
- `python3 scripts/kit.py buscar --segmentos "..." --cidades "Cidade UF" [--email] [--profundidade N] [--ddd-padrao NN]`
- `python3 scripts/kit.py buscar --consultas arquivo.txt` (uma consulta por linha)
- `--quantidade N` (as N de contato mais completo) · `python3 scripts/kit.py refinar --pasta resultados/busca-... --excluir-categorias "..."` (sem coletar de novo)
- `python3 scripts/kit.py painel` (todas as buscas em `resultados/painel.html`)
- `python3 scripts/kit.py atualizar` (kit + motor) · `python3 scripts/kit.py limpar` (pede confirmação)
- No Windows: `py scripts\kit.py ...`

## Lembretes que valem sempre

- Avisar uma vez: o scraping do Google Maps pode contrariar os termos do Google; contatos de empresas
  envolvem LGPD. Sem promessa de volume.
- Começar pequeno (o kit já usa profundidade 1 e no máximo 30 consultas). Uma busca por vez.
- Pedir confirmação antes de qualquer mudança no sistema (instalar programas, `sudo`, administrador).
- Os dados ficam em `resultados/`, na máquina da pessoa. Não colar a lista inteira no chat.
- O kit não abre porta e já desliga a telemetria do motor.
