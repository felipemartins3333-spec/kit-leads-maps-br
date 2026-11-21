---
description: Instala e testa o kit de leads neste computador, passo a passo e em português simples
---

Você vai deixar o kit de leads funcionando nesta máquina para alguém que provavelmente não é técnico.
Siga o `CLAUDE.md` e o `docs/instalacao.md` deste repositório. Fale em português simples.

1. **Conferir a máquina.** Rode `python3 scripts/kit.py verificar` (no Windows: `py scripts\kit.py verificar`;
   se nem o Python existir, diga isso e siga a parte "Python" do Caminho C em `docs/instalacao.md`).
   Resuma em uma frase o que está ok e o que falta.

2. **Resolver só o que falta**, pelo `docs/instalacao.md`:
   - Antes de qualquer mudança no sistema (instalar programa, `sudo`, administrador, grupo `docker`),
     mostre a lista do que vai rodar e peça confirmação **uma vez**.
   - Docker faltando: instale pelos comandos oficiais da parte "B1. Instalar o Docker" do
     `docs/instalacao.md` (Windows: WSL + instalador "por usuário"; Mac: `hdiutil` + `install`; Linux:
     Docker Engine). **Antes**, mostre o resumo da licença do Docker Desktop que está no guia e só use
     `--accept-license` depois do "sim" da pessoa. Se o Windows pedir para reiniciar (WSL), avise e
     combine de continuar depois.
   - Depois de cada correção, rode `kit.py verificar` de novo.

3. **Preparar o motor.** Rode `python3 scripts/kit.py preparar` (baixa ~2 GB; avise antes).

4. **Teste pequeno.** Avise uma vez que coletar do Google Maps pode contrariar os termos do Google e que
   contatos de empresas envolvem LGPD. Rode `python3 scripts/kit.py testar` (no máximo 3 consultas). Ele mostra o
   andamento a cada 20 segundos e pode levar vários minutos: avise que é normal.

5. **Entregar.** Diga:
   - o que foi instalado (só o que você instalou de fato);
   - onde ficou a pasta do kit e que, no futuro, `kit.py atualizar` traz a versão nova;
   - o resultado do teste, usando só os números de `resultados/relatorio-teste.txt` (sem nomes, telefones
     ou e-mails de empresas). Se vier 0 linhas, explique as causas que o kit mostrou;
   - as duas formas de usar: a tela e o `/leads-buscar` em português. No Claude Desktop, abra a tela no painel
     Browser ao lado da conversa (`kit-de-leads` do `.claude/launch.json`; veja o `CLAUDE.md`); fora dele, `kit.py abrir`;
   - onde abrir o relatório: `resultados/busca-.../relatorio.html` (duplo clique, funciona sem internet).

Não invente comandos nem flags. Se algo falhar e o guia não cobrir, explique o erro em português simples
e pare antes de tentar alternativas que mexam no sistema.

Pedido adicional da pessoa (se houver): $ARGUMENTS
