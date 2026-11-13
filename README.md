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
| 1 | Motor rodando e validado | pendente |
| 2 | Camada Brasil (relatório, CSV, planejador, pontuação, LGPD) | pendente |
| 3 | Skill e comandos em PT-BR | pendente |

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
