# CLAUDE.md — como instalar e operar este kit

Este repositório é um kit, em português do Brasil, que transforma **"segmento + cidade"** em
uma lista de empresas do Google Maps pronta para prospecção (telefone +55, WhatsApp, site,
e-mail, planilha para Excel e relatório HTML). O motor de coleta é a imagem Docker oficial
`gosom/google-maps-scraper` (MIT, veja `CREDITS.md`).

Quem usa costuma NÃO ser técnico. Fale em português simples, um passo de cada vez.

## Para instalar

Siga `docs/instalacao.md` (ou o comando `/leads-instalar`). O caminho é sempre:

1. `python3 scripts/kit.py verificar` (no Windows: `py scripts\kit.py verificar`): diz o que falta.
2. Resolver só o que faltar, pelo `docs/instalacao.md`.
3. `python3 scripts/kit.py preparar`: baixa a imagem do motor (~2 GB).
4. `python3 scripts/kit.py testar`: teste pequeno (3 consultas) com relatório só de números.

## Regras para quem opera o kit (inclusive você, Claude)

1. **Não invente comandos.** Use só os do `scripts/kit.py`, do `docs/instalacao.md` e das
   documentações oficiais citadas lá. Não rode o motor "por fora" com flags novas.
2. **Peça confirmação antes de mudar o sistema:** instalar Docker, Python ou Git, usar
   `sudo`/administrador, colocar o usuário no grupo `docker`. Mostre o que vai rodar e por quê.
   Comandos do `kit.py` dentro da pasta do kit podem rodar direto. Para instalar o Docker, use só os comandos
   oficiais de `docs/instalacao.md` (B1) e, antes, mostre o resumo da licença do Docker Desktop (grátis para
   empresas com menos de 250 funcionários e menos de US$ 10 milhões por ano; maiores pagam): só use
   `--accept-license` com o "sim" da pessoa.
3. **Avise uma vez, sem drama:** coletar dados do Google Maps de forma automática pode
   contrariar os termos do Google, e telefones/e-mails de empresas podem ser dados pessoais
   (LGPD: finalidade clara, base legal, respeitar quem pedir para não ser contatado). Não é
   aconselhamento jurídico.
4. **Sem promessa de volume ou de resultado.** Muitas empresas não têm telefone, site ou
   e-mail no Maps. Mostre os números que o kit medir, não estimativas.
5. **Comece pequeno.** Primeiro o `testar` (3 consultas, `-depth 1`). Busca maior só quando o
   usuário pedir; avise que mais consultas e mais profundidade = mais tempo e mais risco de o
   Google limitar o acesso. Uma busca por vez.
6. **Confira o CSV, não o código de saída.** O motor sai com código 0 mesmo sem coletar nada;
   o `kit.py` já conta as linhas. Se vier 0 linhas, explique as causas que ele mostra.
7. **Dados ficam na máquina.** Tudo vai para `resultados/` (fora do git). Não envie listas para
   serviços externos e não cole a lista inteira no chat sem o usuário pedir. Para pedir ajuda,
   use `resultados/relatorio-teste.txt`, que só tem números.
8. **Rede.** O kit não abre porta nenhuma. Não suba a interface web do motor; se o usuário
   insistir, publique só em `127.0.0.1`.
9. **Telemetria do motor desligada:** o `kit.py` já passa `DISABLE_TELEMETRY=1`.
10. **Versão do motor fixa.** O kit usa uma versão testada do motor (`VERSAO_MOTOR` no `kit.py`). Não troque
    para "latest" nem para outra versão; para receber versões novas, use `kit.py atualizar`.

## Comandos úteis

No Claude Code: `/leads-instalar` (instalar e testar) e `/leads-buscar dentistas em Salvador BA` (lista).

| Para | Comando |
|------|---------|
| Ver o que falta | `python3 scripts/kit.py verificar` |
| Baixar o motor | `python3 scripts/kit.py preparar` |
| Teste pequeno | `python3 scripts/kit.py testar` |
| Busca | `python3 scripts/kit.py buscar --segmentos "academias" --cidades "Salvador BA"` |
| Busca com e-mail | acrescente `--email` (mais lento: visita o site de cada empresa) |
| Atualizar o kit e o motor | `python3 scripts/kit.py atualizar` |
| Lista com N empresas (as de contato mais completo) | acrescente `--quantidade 60` |
| Tirar categorias fora do segmento, sem coletar de novo | `python3 scripts/kit.py refinar --pasta resultados/busca-... --excluir-categorias "Academia"` |
| Ver todas as buscas (painel) | `python3 scripts/kit.py painel` → abre `resultados/painel.html` |
| Liberar espaço (remover o motor) | `python3 scripts/kit.py limpar` (pede confirmação; não apaga `resultados/`) |

No Windows, troque `python3` por `py` e as barras `/` por `\`.

## Para quem desenvolve o kit

Leia também `docs/desenvolvimento.md`: aquelas regras valem para qualquer alteração no código
ou na documentação.
