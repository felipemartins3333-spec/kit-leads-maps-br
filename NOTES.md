# NOTES — decisões, problemas e medições

Este arquivo alimenta a seção "Limites honestos" e o troubleshooting do material final.
Regra: registrar fatos medidos, não impressões. Data no formato AAAA-MM-DD.

## Decisões

### 2026-11-13 — Arquitetura
- Camada Brasil própria sobre a imagem Docker oficial do gosom. Sem copiar o código dele.
- Scripts em Python só com biblioteca padrão (público não técnico: nada de `pip install`).
- Usar a **CLI** do gosom via `docker run` (arquivo de consultas -> CSV). Sem subir servidor
  web nem API, logo sem porta exposta. Se um dia for preciso servidor, publicar só em
  `127.0.0.1` (`-p 127.0.0.1:8080:8080`).
- Resultados em pasta ignorada pelo git (`.gitignore` cobre `resultados/`, `*.csv`, etc.).
- Testes: no máximo 3 consultas, `-depth 1`, sem proxy.

### 2026-11-13 — O que aprendi lendo as referências (ideias, não cópia)
- gosom: o README atual documenta a CLI com `docker run`, volume de cache do Playwright e
  flags como `-input`, `-results`, `-depth`, `-email`, `-exit-on-inactivity`. **Todas serão
  reconfirmadas com `-h` da imagem na Fase 1 antes de qualquer uso.**
- O gosom já tem uma skill própria (exige Docker e Node.js). A nossa difere: Python puro,
  PT-BR, foco em prospecção brasileira (WhatsApp, CNPJ, LGPD).
- Kit do Mahanaicoach: na versão atual trocou o gosom por motor próprio; não é uma camada
  sobre a imagem oficial. Ou seja, não serve de modelo de arquitetura, só de organização.
- Kit do vzbaggio: usa o gosom por API web atrás de nginx, com painel. Nosso caminho é
  mais simples (CLI, sem servidor).

## Medições
(vazio — Fase 1)

## Erros encontrados e como foram resolvidos (vira o troubleshooting)
(vazio — Fase 1)

## Limites honestos (rascunho vivo)
- Scraping do Google Maps pode contrariar os termos do Google.
- Dados de contato envolvem LGPD.
- Sem promessa de volume nem de resultado. Taxas de preenchimento serão medidas na Fase 1.
