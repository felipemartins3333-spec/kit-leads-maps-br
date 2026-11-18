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
   - Docker Desktop no Windows ou no Mac: você não consegue instalar sozinho. Guie a pessoa pela página
     oficial citada no guia, peça para ela abrir o Docker Desktop quando terminar e espere a confirmação.
   - Depois de cada correção, rode `kit.py verificar` de novo.

3. **Preparar o motor.** Rode `python3 scripts/kit.py preparar` (baixa ~2 GB; avise antes).

4. **Teste pequeno.** Avise uma vez que coletar do Google Maps pode contrariar os termos do Google e que
   contatos de empresas envolvem LGPD. Rode `python3 scripts/kit.py testar` (no máximo 3 consultas). Ele pode
   ficar vários minutos em silêncio: avise que é normal.

5. **Entregar.** Diga:
   - o que foi instalado (só o que você instalou de fato);
   - onde ficou a pasta do kit;
   - o resultado do teste, usando só os números de `resultados/relatorio-teste.txt` (sem nomes, telefones
     ou e-mails de empresas). Se vier 0 linhas, explique as causas que o kit mostrou;
   - como fazer uma busca simples, com um exemplo do `docs/instalacao.md` ("Como fazer uma busca");
   - onde abrir o relatório: `resultados/busca-.../relatorio.html` (duplo clique, funciona sem internet).

Não invente comandos nem flags. Se algo falhar e o guia não cobrir, explique o erro em português simples
e pare antes de tentar alternativas que mexam no sistema.

Pedido adicional da pessoa (se houver): $ARGUMENTS
