---
description: Monta uma lista de empresas do Google Maps (segmento + cidade) com WhatsApp, planilha e relatório
---

A pessoa quer uma lista de empresas. Pedido dela: **$ARGUMENTS**

Siga o `CLAUDE.md` deste repositório. Fale em português simples. Pense como um bom SDR montando a lista:
o objetivo é uma lista **útil para prospecção**, não a maior lista possível.

1. **Entender o pedido.** Separe:
   - **segmento** (ex.: "estúdios de pilates", "escritórios de contabilidade");
   - **cidade com UF** (ex.: "Curitiba PR"). Se a cidade tiver nome comum a vários estados e faltar a UF,
     pergunte. Se faltar segmento ou cidade, pergunte só isso;
   - **quantidade** desejada, se a pessoa disser ("quero 60"). Se não disser, não invente: use o que vier;
   - se quer **e-mail** (`--email`: visita o site de cada empresa, deixa a busca mais lenta);
   - se quer **Instagram/Facebook/LinkedIn** (`--redes-sociais`: abre só a página inicial do site de cada empresa);
   - **opções avançadas, só se a pessoa pedir:** em volta de um ponto (`--ponto LAT,LON --raio KM`), modo rápido
     (`--modo-rapido`, precisa de `--ponto`; até 21 por consulta, menos dados, beta), tempo máximo
     (`--tempo-maximo N` minutos), proxies (`--proxies-arquivo ARQ`, só com arquivo que a pessoa forneceu).
     Veja a tabela em `docs/instalacao.md`.
   Se o pedido estiver vazio, pergunte: "Qual segmento, em qual cidade, e mais ou menos quantas empresas?".

2. **Montar a estratégia da busca.** O Google Maps mostra um número limitado de empresas por busca.
   - **Cidade pequena ou pedido pequeno** (até umas 20 empresas): uma consulta para a cidade basta.
   - **Cidade grande ou quantidade maior:** faça a cidade inteira **mais 3 a 5 bairros** onde esse segmento
     costuma estar (centro, bairros comerciais e de maior renda), no formato `"Bairro, Cidade UF"`.
     Use só bairros que você tem certeza que existem; se não tiver, pergunte à pessoa quais bairros prefere.
   - Profundidade: 1 por padrão; 2 só se a pessoa quer muitas empresas e aceita esperar mais.

3. **Mostrar o plano antes de rodar**, curto: as consultas (cidade + bairros), quantidade final, com ou sem
   e-mail. Avise uma vez que coletar do Google Maps pode contrariar os termos do Google e que contatos de
   empresas envolvem LGPD. Peça confirmação se forem **mais de 3 consultas**, profundidade acima de 1 ou
   com e-mail. Caso contrário, siga.

4. **Tela ao lado (Claude Desktop):** se o painel Browser estiver disponível, abra (ou mantenha aberta) a
   tela do kit (`kit-de-leads` do `.claude/launch.json`; veja o `CLAUDE.md`). Ela mostra o andamento desta
   busca ao vivo e, no fim, o mapa com as empresas.

5. **Conferir a máquina** se for a primeira busca da conversa: `python3 scripts/kit.py verificar`
   (Windows: `py scripts\kit.py verificar`). Se faltar algo, sugira `/leads-instalar` e pare.

6. **Rodar** (um comando só, sem inventar flags):

   `python3 scripts/kit.py buscar --segmentos "SEGMENTO" --cidades "Cidade UF" "Bairro 1, Cidade UF" "Bairro 2, Cidade UF" --quantidade N`

   Tire `--quantidade` se a pessoa não pediu um número. Acrescente `--email` e/ou `--profundidade N` se
   combinado. Para mais de 30 consultas o kit recusa; só use `--limite` se a pessoa pedir de propósito,
   depois de avisar do risco. Avise que pode levar alguns minutos; o kit mostra o andamento.

7. **Limpar o que não é do segmento.** O kit imprime "Categorias encontradas". Se aparecerem categorias que
   claramente não são o que a pessoa pediu (ex.: pediu pilates e vieram "Academia", "Personal trainer"),
   diga quais vai tirar e rode, **sem coletar de novo**:

   `python3 scripts/kit.py refinar --pasta resultados/busca-AAAAMMDD-HHMMSS --excluir-categorias "Categoria 1" "Categoria 2" --quantidade N`

   (use exatamente o caminho da pasta e os nomes de categoria que o kit imprimiu). Na dúvida sobre uma
   categoria, mantenha e pergunte.

8. **Entregar** com os números que o kit imprimiu (não estime):
   - quantas empresas na lista e quantas com WhatsApp (celular), fixo, site e e-mail; quantas duplicadas e
     quantas fora do segmento foram removidas;
   - se pediu N e vieram menos, diga com clareza e sugira mais bairros;
   - o caminho do `relatorio.html` (duplo clique: busca, filtros, botão de WhatsApp, funciona sem internet),
     do `leads-excel.csv` (Excel em português) e do painel `resultados/painel.html` (todas as buscas).
     Se houve corte por quantidade, a lista inteira está em `todas-excel.csv`.
   Não cole a lista inteira no chat. Se a pessoa pedir exemplos, mostre poucas linhas.
   Se vier 0 empresas, explique as causas e siga o "O que tentar" que o kit mostrou, um passo de cada vez.

9. **Próximos passos que valem oferecer** (sem fazer sem pedir): dividir em mais bairros para aumentar a
   lista; buscar e-mails (`--email`); ajudar a escrever uma primeira mensagem de prospecção a partir do
   segmento. Na primeira lista que der certo na conversa, lembre uma vez que o motor é o projeto aberto do
   gosom (github.com/gosom/google-maps-scraper) e que dar uma estrela lá apoia o autor.
