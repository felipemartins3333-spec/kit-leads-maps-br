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

---

## Rodada 2 (2026-11-13) — higiene, preparação do teste real e Fase 2a

### Git
- Autor dos commits 3303f7d e 93d754f reescrito para o e-mail noreply do GitHub (novos hashes
  19a471a e 8a33af8). Um único `push --force-with-lease` autorizado, só na `main`, já usado.
  A 1ª tentativa foi recusada pelo `--lease` (eu digitei o hash esperado errado) e nada mudou
  no remoto; a 2ª, com o hash real, passou. Nenhum outro force push sem nova autorização.

### Incidente de processo (sem efeito, registrado por transparência)
- Ao gravar `docs/teste-no-chromebook.md` com um heredoc `<<'EOF'`, o texto continha um `EOF`
  (do comando oficial do Docker) que encerrou o heredoc antes da hora, e o resto do texto foi
  interpretado pelo shell, o que incluía comandos `sudo apt ...`. O comando travou e foi
  interrompido. Verificado depois: sem entrada nova em `/var/log/apt/history.log` nem em
  `dpkg.log`, `/etc/apt/keyrings` e `sources.list.d` intactos, nenhum contêiner novo, `dockerd`
  e a imagem do motor seguem como estavam. Lição: arquivos com blocos de shell dentro vão pela
  ferramenta de escrita de arquivos, nunca por heredoc. O guia foi regravado inteiro.

### Docker vs. binário do gosom — avaliação SÓ por documentação (nada foi baixado)
Fontes lidas: README, Dockerfile, Makefile, `.github/workflows/*`, `MacOS instructions.md` do
repositório do gosom (clone raso, versão atual). A página de releases devolveu HTTP 403 daqui.

Fatos lidos:
- README: "download the binary release for your platform" (link para /releases).
- `Makefile` (`cross-compile`): só gera linux **amd64**, darwin **amd64** e windows **amd64**.exe.
  Não há alvo arm64 (nem linux/arm64, nem macOS Apple Silicon).
- CI: `publish.yml` só publica **imagens Docker** (linux/amd64 e linux/arm64). `build.yml` só
  compila para `/dev/null`. Nenhum workflow publica binários, então qualquer binário em
  /releases seria subido à mão (não verificado).
- `Dockerfile` (final: debian trixie-slim): o navegador é o Chromium do Playwright em
  `/opt/browsers`, mais estas bibliotecas de sistema: libnss3, libnspr4, libatk1.0-0,
  libatk-bridge2.0-0, libcups2, libdrm2, libdbus-1-3, libxkbcommon0, libatspi2.0-0, libx11-6,
  libxcomposite1, libxdamage1, libxext6, libxfixes3, libxrandr2, libgbm1, libpango-1.0-0,
  libcairo2, libasound2.
- README (trecho de compilação): "First run downloads required browser libraries for Playwright".
- `MacOS instructions.md`: o caminho documentado para Mac é instalar Homebrew + Go e compilar.
  O README avisa que o comando Docker pode não funcionar no macOS.

Respostas às perguntas:
1. *O binário roda sem Docker em Linux x86_64?* Em tese sim (há alvo linux-amd64 no Makefile),
   mas **não confirmado**: não consegui ver os arquivos de releases.
2. *O que ele exige?* O Chromium do Playwright (baixado na 1ª execução; tamanho NÃO medido) e
   as bibliotecas acima instaladas por `apt` (precisa de administrador). Em Chromebook/ARM
   não há binário previsto no Makefile.

Comparação de atrito para o usuário final (o que é fato × o que é hipótese):
| | Docker (imagem oficial) | Binário |
|---|---|---|
| Instalação | instalar Docker (Debian: ~6 comandos oficiais, grupo `docker` equivale a root) | baixar binário + `apt` de ~19 bibliotecas + download do Chromium |
| Tamanho | imagem 2,06 GB em disco (576 MB de conteúdo, medido na Rodada 1) | binário: não sei; Chromium: não medido |
| ARM (Chromebook/Apple Silicon) | imagem existe para arm64 (CI) | sem alvo arm64 no Makefile |
| Reprodutibilidade | alta: mesmo ambiente sempre | menor: depende do sistema do usuário |
| Windows/Mac (público provável) | exige Docker Desktop (virtualização/WSL2) — hipótese de maior atrito | Windows: há alvo `.exe`; Mac: só Intel pronto, ou compilar com Go |
| Isolamento | roda em contêiner | roda direto no sistema |

Recomendação PRELIMINAR (a validar com testes reais, não decide nada): manter o **Docker como
caminho principal** (reprodutível, cobre arm64, é o que o README do gosom recomenda) e tratar o
binário como **plano B**, a ser testado só depois de sabermos o que existe em /releases. Risco
a medir cedo: o público de SDRs usa muito Windows/Mac; o atrito de Docker Desktop pode pesar
mais que o tamanho da imagem.

### Fase 2a — contrato, decisões e suposições
- **Contrato de colunas:** as 36 colunas do README do gosom conferem, nome a nome e na ordem,
  com `CsvHeaders()` em `gmaps/entry.go` do código-fonte (lido, não copiado).
- **Decisões:** dedupe por `place_id` e depois por telefone E.164 (filiais que dividem o mesmo
  telefone viram uma só; contagem das removidas é exibida; 0800 nunca deduplica). Link
  `wa.me` só para celular (fixo não ganha). CSV Excel sem a coluna E.164 (o Excel converteria
  `+5577...` em notação científica), com `;`, BOM UTF-8, nota com vírgula e proteção contra
  fórmula (`=`, `+`, `-`, `@` no início viram texto). Na demo (`fonte = DEMO`) o botão de
  WhatsApp e o mailto são desativados, para ninguém mandar mensagem a um número que possa existir.
- **Relatório HTML:** arquivo único, sem CDN/fonte remota; CSP `connect-src 'none'` impede
  qualquer envio de dados; dados embutidos com `<`, `>` e `&` escapados.
- **SUPOSIÇÕES a confirmar com o CSV real (nada disso foi visto em dado real):**
  1. formato do campo `emails` (aceito qualquer separador/lista JSON por regex);
  2. nota ausente vem vazia ou "0" (tratamos os dois como "sem nota");
  3. `phone` vem no formato "(77) 99999-0001" ou "+55 ..." e só traz UM número;
  4. `place_id` vem preenchido na maioria das linhas;
  5. `-lang pt-BR` é aceito (o script repete com `pt` se vier 0 linhas, mas 0 linhas também
     pode ser bloqueio/rede, não idioma);
  6. a lista de DDDs válidos é do plano de numeração público, de memória (não buscada agora);
  7. 8 dígitos começando com 6–9 (celular antigo sem o 9) é tratado como inválido, não convertido;
  8. `DISABLE_TELEMETRY=1` realmente desliga a telemetria (só a documentação diz).
- **Verificações feitas (aqui, sem rede externa):** 33 testes `unittest` passando (telefone com/sem
  DDD, +55, parênteses, 0800, fixo de 8, celular de 9, inválidos; e-mail; dedupe; Excel; planejador).
  Relatório HTML aberto no Chromium local: 0 requisições externas, 0 erros de JS, filtros e busca
  batendo com os números do CSV, 0 px de rolagem horizontal em 390 px, contraste mínimo 5,27:1.
  `scripts/teste-real.sh --so-checar` testado, inclusive os caminhos "sem Docker", "serviço
  desligado" e "sem permissão" (simulados). O fluxo completo do `teste-real.sh` NÃO foi executado
  (exigiria o Google Maps); só será validado no Chromebook.
- **Riscos abertos:** (a) `teste-real.sh` é Bash: não roda em Windows puro (exigiria WSL/Git Bash);
  (b) o `chown` pós-teste (imagem do motor como `--entrypoint`) foi testado aqui com arquivo de dono diferente e funcionou, mas só como root; no Chromebook, com usuário comum, ainda não;
  (c) Docker em Crostini (Linux do Chromebook) pode falhar em alguns aparelhos, não testado.
