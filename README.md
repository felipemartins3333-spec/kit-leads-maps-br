# kit-leads-maps-br (rascunho)

[![testes](https://github.com/felipemartins3333-spec/kit-leads-maps-br/actions/workflows/testes.yml/badge.svg)](https://github.com/felipemartins3333-spec/kit-leads-maps-br/actions/workflows/testes.yml)

> Em construção. O nome do repositório é provisório.

Kit em português do Brasil que transforma **"segmento + cidade"** em uma lista de empresas
para prospecção comercial, usando o Google Maps como fonte.

Feito para SDRs, líderes comerciais, fundadores e times B2B, inclusive quem não é técnico.

## Comece aqui

**Jeito mais fácil:** abra este repositório num **Codespace** (botão *Code → Codespaces*). Ele já vem
com Docker e Claude Code. No terminal, rode `python3 scripts/kit.py verificar` e siga o que ele disser.

**No seu computador, com o Claude fazendo o trabalho:** instale o Docker e o Claude (app Claude
Desktop ou Claude Code) e cole o prompt abaixo. O guia completo, com Windows, Mac e Linux, está em
[`docs/instalacao.md`](docs/instalacao.md).

```text
Quero montar listas de empresas do Google Maps com este kit:
https://github.com/felipemartins3333-spec/kit-leads-maps-br

Deixe o kit funcionando neste computador, do começo ao fim:

1. Baixe o repositório (git clone; se não houver Git, me peça para baixar o ZIP pelo GitHub).
   Antes de qualquer comando, leia o CLAUDE.md e o docs/instalacao.md do próprio kit.
   Use só os comandos que estão lá e nas documentações oficiais citadas. Não invente nenhum.
2. Rode o verificador do kit ("python3 scripts/kit.py verificar"; no Windows,
   "py scripts\kit.py verificar") e me diga, em uma frase, o que já existe e o que falta.
3. Resolva sozinho o que for seguro e ficar dentro da pasta do kit. O que mexer no sistema
   (instalar Docker, Python ou Git, usar sudo ou administrador): junte tudo, me mostre a lista
   e peça UMA confirmação. Se faltar o Docker, instale pelos comandos oficiais do
   docs/instalacao.md; antes, me mostre o resumo da licença do Docker Desktop e espere meu "sim".
4. Prepare o motor ("kit.py preparar") e rode o teste pequeno ("kit.py testar", no máximo
   3 consultas).
5. Confirme que funcionou pelo relatório do teste (resultados/relatorio-teste.txt), não só
   pela mensagem final.

Quando terminar, me diga:
- o que foi instalado (só o que você instalou de verdade);
- onde ficou a pasta do kit e como atualizá-lo no futuro ("kit.py atualizar");
- as duas formas de usar: a tela no navegador (rode "kit.py abrir" e me mostre o link)
  e pedir para você em português (o comando /leads-buscar);
- onde abrir o resultado de uma busca: o relatório HTML (duplo clique) e a planilha para Excel;
- os números do teste, sem nomes, telefones, e-mails ou sites de empresas.

Se algo der errado, explique em português simples e pare antes de tentar alternativas
que mexam no sistema.
```

No Claude Desktop: abra uma conversa nova de código, escolha uma pasta para o kit e cole o prompt.

**Duas formas de usar, depois de instalado:**

1. **Pela tela no navegador:** rode `python3 scripts/kit.py abrir`, clique no link, preencha o segmento, a
   cidade, os bairros e a quantidade, e acompanhe a busca. Os relatórios e as planilhas ficam ali mesmo.
2. **Pedindo ao Claude:** `/leads-buscar 60 estúdios de pilates em Curitiba PR`. Ele divide por bairros,
   limpa o que não é do segmento e entrega o relatório.

## Como funciona (visão geral)

```
segmento + cidade  ->  motor de coleta (Docker)  ->  CSV  ->  camada Brasil  ->  lista pronta
                       gosom/google-maps-scraper         telefone +55, WhatsApp, Excel,
                       (imagem oficial)                  relatório HTML, pontuação
```

- **Motor:** a imagem oficial `gosom/google-maps-scraper` (MIT). Veja `CREDITS.md`.
- **Camada Brasil (este repositório):** scripts em Python (só biblioteca padrão), skill e
  comandos do Claude Code em PT-BR, relatório HTML, exemplos e documentação.

## Status

| Fase | O quê | Situação |
|------|-------|----------|
| 0 | Fundação do repositório | feita |
| 1 | Motor rodando e validado | **feita**: teste real em 19/11/2026 (Claude Desktop + prompt oficial, num Codespace): 60 empresas em 139 s sem e-mail; 56 em 328 s com e-mail; 100% com telefone, ~70% com site, 21% com e-mail. Detalhes em `NOTES.md` |
| 2a | Camada Brasil que não depende de dados reais (tratamento do CSV, relatório HTML, planejador de consultas) | feita, testada só com dados fictícios |
| 2b | Pontuação de lead, CNPJ (experimental), guardrails de LGPD | pendente: depende das taxas reais de preenchimento |
| 3a | Instalação: `scripts/kit.py` (Windows/Mac/Linux/Codespace), Codespace pronto, prompt de instalação, comando `/leads-instalar` | feita; **não testada em Windows, Mac nem Codespace real** |
| 3b | Comando `/leads-buscar`, skill `leads-maps-br`, testes automáticos em Linux/Windows/Mac (GitHub Actions) e formulário "Relatar problema" | feita; coleta real ainda não validada |

## Ver a demonstração (dados 100% fictícios)

Abra `examples/demo-relatorio.html` com duplo clique. Funciona sem internet.

Para gerar de novo a partir do CSV de demonstração (precisa só de Python 3):

```bash
python3 -I scripts/tratar_csv.py examples/demo-leads.csv
python3 -I scripts/gerar_relatorio.py resultados/demo-leads-tratados.csv --saida examples/demo-relatorio.html --consultas examples/demo-consultas.txt
```

## O que tem aqui

| Arquivo | Para quê |
|---------|----------|
| `scripts/kit.py` | **comando principal**: `abrir` (tela no navegador), `verificar`, `preparar`, `testar`, `buscar`, `refinar`, `atualizar`, `limpar`, `painel` |
| `scripts/interface.py` e `scripts/modelo_interface.html` | a **tela de busca** no navegador (servidor local em 127.0.0.1, com chave no link) |
| `scripts/painel.py` | **painel das suas buscas** (`resultados/painel.html`): cada busca num cartão, com números e atalhos |
| `scripts/visual.py` e `scripts/modelo_relatorio.html` | identidade visual (cores, tipografia, ícones próprios) e modelo do relatório |
| `docs/instalacao.md` | instalação: Codespace, Windows, Mac, Linux, com ou sem Claude |
| `.devcontainer/` | Codespace já pronto (Python, Docker, Claude Code) |
| `.claude/commands/` | comandos do Claude Code: `/leads-instalar` e `/leads-buscar` |
| `.claude/skills/leads-maps-br/` | skill: o Claude entende pedidos como "lista de dentistas em Salvador" |
| `.github/` | testes automáticos (Linux, Windows, Mac) e formulário "Relatar problema" |
| `docs/teste-no-chromebook.md` | passo a passo do Docker no Linux Debian (Chromebook) |
| `scripts/resumo_teste.py` | relatório só com números, que pode ser colado no chat sem expor dados |
| `scripts/tratar_csv.py` | telefones +55, celular x fixo, link do WhatsApp, deduplicação, CSV para Excel |
| `scripts/gerar_relatorio.py` | relatório HTML de arquivo único, com busca e filtros |
| `scripts/planejar_consultas.py` | combina segmentos x cidades e gera o arquivo de consultas |
| `tests/` | testes (`python3 -I -m unittest discover -s tests`) |
| `NOTES.md` | decisões, medições, erros e suposições ainda não confirmadas |
| `docs/desenvolvimento.md` | regras para quem altera o kit |

## Avisos importantes (leia antes de usar)

- **Termos do Google.** Coletar dados do Google Maps de forma automatizada pode contrariar
  os termos de uso do Google. O risco é seu. Este kit não dá garantia de que vai funcionar
  sempre nem de que o Google não vai limitar o seu acesso.
- **LGPD.** Telefones e e-mails de empresas podem identificar pessoas (sócios, MEIs,
  profissionais liberais). Tratar esses dados exige base legal, finalidade clara e
  respeito a quem pedir para não ser contatado. Isto não é aconselhamento jurídico.
- **Sem promessas.** Quantidade e qualidade dos contatos variam por segmento e cidade.
  Muitas empresas não têm telefone, site ou e-mail no Maps. Os números reais medidos
  nos testes estarão em `NOTES.md` e na seção "Limites honestos" do material final.

## Licença e créditos

MIT, em nome de Felipe Martins Muniz (`LICENSE`). Créditos ao motor em `CREDITS.md`.
