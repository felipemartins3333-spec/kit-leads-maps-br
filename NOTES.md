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

### 2026-11-13 — Ambiente de teste (Fase 1)
- Ambiente: contêiner Linux na nuvem (x86_64, 4 CPUs, 15 GiB RAM), Docker 29.9.2, Python 3.13.
- Imagem `gosom/google-maps-scraper`: 2,06 GB, download em ~22 s. Versão do motor
  (`-version`): `v1.18.2-146aefe`. Digest: `sha256:6af44cb9f339...`.
- Flags confirmadas com `-h` da imagem: `-input`, `-results`, `-depth`, `-email`, `-lang`,
  `-c` (padrão 1), `-exit-on-inactivity`, `-version`, `-json`, `-resume`, `-proxies`,
  `-fast-mode`, `-geo`, `-radius`, `-zoom`.
- **Teste 1 (sem e-mail): NÃO MEDIDO.** Falhou por rede antes de coletar qualquer coisa
  (ver erros abaixo). Zero linhas. O tempo de 7 s é o da falha, não de coleta.
- **Teste 2 (com e-mail): NÃO EXECUTADO** (mesmo bloqueio).
- Taxas de preenchimento: sem dados ainda. Nenhum número será inventado.

## Erros encontrados e como foram resolvidos (vira o troubleshooting)

1. **Docker instalado, mas "failed to connect to the docker API ... docker.sock".**
   Causa: o cliente existia, mas o serviço (daemon) não estava rodando. Solução neste
   ambiente: iniciar `dockerd` em segundo plano. Para o usuário final, o equivalente é
   "abra o Docker Desktop e espere o ícone ficar verde".
2. **`ERR_NAME_NOT_RESOLVED` em `www.google.com/maps/...` (teste 1, 3 consultas, 0 linhas).**
   Causa: o contêiner do motor não tem acesso à internet livre. Neste ambiente de nuvem a
   saída é filtrada por proxy que só libera registros de pacotes; `curl` para o Google
   Maps também recebe `CONNECT tunnel failed, response 403`. NÃO é falha do kit nem do
   motor. Não resolvido aqui: exige rodar em máquina com internet normal. Para o usuário
   final, a mesma mensagem pode indicar falta de internet, DNS bloqueado, VPN ou rede
   corporativa com firewall.
   - O motor termina com código 0 mesmo sem coletar nada: um script nosso NÃO pode
     confiar no código de saída e deve checar se o CSV tem linhas.
   - O arquivo de resultado é criado vazio (0 bytes) mesmo na falha.
3. **Telemetria do motor.** O gosom envia estatísticas anônimas de uso para a PostHog
   (`eu.i.posthog.com`); aparece como erro no log quando o host está bloqueado. O README
   dele documenta o desligamento com a variável `DISABLE_TELEMETRY=1`. Decisão: nossos
   scripts passam `-e DISABLE_TELEMETRY=1` por padrão e o material avisa isso com
   transparência. (A eficácia da variável ainda precisa ser confirmada num teste real.)

## Decisões da Fase 1
- 2026-11-13: a coleta real do Google Maps não pode ser validada neste ambiente de
  nuvem. Pendente decisão do Felipe sobre onde rodar (ver relatório da Fase 1).
- O teste usa `-lang pt-BR` (a URL gerada leva `hl=pt-BR`). Se `pt-BR` for aceito pelo
  Google, a confirmação vem no primeiro teste real.

## Limites honestos (rascunho vivo)
- Scraping do Google Maps pode contrariar os termos do Google.
- Dados de contato envolvem LGPD.
- Sem promessa de volume nem de resultado. Taxas de preenchimento serão medidas na Fase 1.
