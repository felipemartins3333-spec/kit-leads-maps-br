---
description: Monta uma lista de empresas do Google Maps (segmento + cidade) com WhatsApp, planilha e relatório
---

A pessoa quer uma lista de empresas. Pedido dela: **$ARGUMENTS**

Siga o `CLAUDE.md` deste repositório. Fale em português simples.

1. **Entender o pedido.** Separe:
   - **segmentos** (ex.: "clínicas odontológicas", "escritórios de contabilidade");
   - **cidades com UF** (ex.: "Vitória da Conquista BA"). Se faltar a UF e a cidade tiver nome comum a
     vários estados, pergunte. Se faltar segmento ou cidade, pergunte só isso;
   - se quer **e-mail** (`--email`, mais lento) e o **tamanho** (padrão: profundidade 1).
   Se o pedido estiver vazio, pergunte: "Qual segmento e qual cidade?".

2. **Mostrar o plano antes de rodar**, em 3 linhas: quantas consultas (segmentos × cidades), com ou sem
   e-mail, profundidade. Avise uma vez que coletar do Google Maps pode contrariar os termos do Google e que
   contatos de empresas envolvem LGPD. Peça confirmação se forem **mais de 3 consultas**, profundidade
   acima de 1 ou com e-mail (demora mais). Caso contrário, siga.

3. **Conferir a máquina** se for a primeira busca da conversa: `python3 scripts/kit.py verificar`
   (Windows: `py scripts\kit.py verificar`). Se faltar algo, sugira `/leads-instalar` e pare.

4. **Rodar** (um comando só, sem inventar flags):

   `python3 scripts/kit.py buscar --segmentos "SEGMENTO 1" "SEGMENTO 2" --cidades "CIDADE UF"`

   acrescentando `--email` e/ou `--profundidade N` se combinado. Para mais de 30 consultas o kit recusa;
   só use `--limite` se a pessoa pedir de propósito, depois de avisar do risco. Avise que o terminal pode
   ficar alguns minutos em silêncio.

5. **Entregar** com os números que o kit imprimiu (não estime):
   - quantas empresas, quantas com celular/WhatsApp, fixo, site e e-mail;
   - o caminho do `relatorio.html` (duplo clique: busca, filtros e botão de WhatsApp, funciona sem
     internet) e do `leads-excel.csv` (abre no Excel em português).
   Não cole a lista inteira no chat. Se a pessoa pedir exemplos, mostre poucas linhas.
   Se vier 0 empresas, explique as causas que o kit mostrou e sugira esperar e tentar com menos consultas.
