# kit-leads-maps-br (rascunho)

> Rascunho da Fase 0. O nome do repositório é provisório e o conteúdo será
> reescrito ao longo das próximas fases.

Kit em português do Brasil que transforma **"segmento + cidade"** em uma lista de empresas
para prospecção comercial, usando o Google Maps como fonte.

Feito para SDRs, líderes comerciais, fundadores e times B2B, inclusive quem não é técnico.

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
| 1 | Motor rodando e validado | **parcial**: imagem baixada e flags confirmadas; coleta real pendente (a nuvem não alcança o Google Maps). O teste real será feito num Chromebook |
| 2a | Camada Brasil que não depende de dados reais (tratamento do CSV, relatório HTML, planejador de consultas) | feita, testada só com dados fictícios |
| 2b | Pontuação de lead, CNPJ (experimental), guardrails de LGPD | pendente: depende das taxas reais de preenchimento |
| 3 | Skill e comandos em PT-BR | pendente |

## Ver a demonstração (dados 100% fictícios)

Abra `examples/demo-relatorio.html` com duplo clique. Funciona sem internet.

Para gerar de novo a partir do CSV de demonstração (precisa só de Python 3):

```bash
python3 -I scripts/tratar_csv.py examples/demo-leads.csv
python3 -I scripts/gerar_relatorio.py resultados/demo-leads-tratados.csv --saida examples/demo-relatorio.html
```

## O que tem aqui

| Arquivo | Para quê |
|---------|----------|
| `docs/teste-no-chromebook.md` | passo a passo do teste real, em português simples |
| `scripts/teste-real.sh` | roda o teste (3 consultas, `-depth 1`, sem proxy) e mede o tempo |
| `scripts/resumo_teste.py` | relatório só com números, que pode ser colado no chat sem expor dados |
| `scripts/tratar_csv.py` | telefones +55, celular x fixo, link do WhatsApp, deduplicação, CSV para Excel |
| `scripts/gerar_relatorio.py` | relatório HTML de arquivo único, com busca e filtros |
| `scripts/planejar_consultas.py` | combina segmentos x cidades e gera o arquivo de consultas |
| `tests/` | testes (`python3 -I -m unittest discover -s tests`) |
| `NOTES.md` | decisões, medições, erros e suposições ainda não confirmadas |

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
