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

---

## Rodada 3 (2026-11-18) — Fase 3a: instalação

### Correções de fato (eu tinha dito diferente antes)
- **Claude Desktop tem versão Linux (beta)**, para Debian 12+ / Ubuntu 22.04+, x86_64 ou arm64
  (code.claude.com/docs/en/desktop-linux). Antes eu disse que só existia para Mac e Windows.
- **O kit do vzbaggio não instala o Docker sozinho.** O `SETUP.md` dele lista o Docker Desktop
  como pré-requisito (com link) e o comando de setup só confere `docker ps`. O "automático" é
  o que vem depois do Docker. O nosso segue o mesmo princípio.

### Fontes oficiais lidas nesta rodada
- Claude Code (code.claude.com/docs/en/setup): requisitos macOS 13+, Windows 10 1809+,
  Ubuntu 20.04+, Debian 10+; **4 GB+ de RAM**; x64 ou ARM64. Instalação: `curl -fsSL
  https://claude.ai/install.sh | bash` (Mac/Linux/WSL), `irm https://claude.ai/install.ps1 | iex`
  (PowerShell). O app Desktop também roda o Claude Code.
- Docker Desktop Windows (docs/docker, windows-install): backend WSL 2 padrão, **8 GB de RAM**.
  Mac (mac-install): **4 GB de RAM**, versão atual do macOS e as duas anteriores; instaladores
  separados para Apple silicon e Intel.
- Codespace: feature `ghcr.io/devcontainers/features/docker-in-docker:4` (README do
  devcontainers/features), imagem `mcr.microsoft.com/devcontainers/python:3.13-trixie` (README do
  devcontainers/images), feature `ghcr.io/anthropics/devcontainer-features/claude-code:1`, que
  precisa de Node (por isso `ghcr.io/devcontainers/features/node:1`, como o README dela recomenda).

### Decisões
- **`scripts/kit.py` é o ponto de entrada único** (`verificar`, `preparar`, `testar`, `buscar`),
  em Python puro, para rodar igual em Windows, Mac, Linux e Codespace. O `teste-real.sh` virou
  um atalho para ele.
- Montagens do Docker com `--mount` (em vez de `-v`), porque caminhos do Windows têm `:`; se o
  caminho tiver vírgula, o kit volta para `-v`. O contêiner ganha `--name` para poder ser parado
  se passar de 30 min (matar o `docker run` não para o contêiner).
- `chown` pós-coleta só no Linux (no Windows/Mac o Docker Desktop já entrega os arquivos com o
  usuário certo — suposição, não testado).
- `CLAUDE.md` agora orienta quem **instala e usa** o kit (o Claude do cliente lê esse arquivo).
  As regras de desenvolvimento foram para `docs/desenvolvimento.md`, sem perder nenhuma.
- `buscar` grava cada busca em `resultados/busca-AAAAMMDD-HHMMSS/` com `relatorio.html`,
  `leads-excel.csv` e `leads-tratados.csv`. Profundidade padrão 1; acima de 3, aviso.

### Verificado aqui
- 46 testes `unittest` passando (inclui 13 novos do `kit.py`: comando montado, flags,
  montagem somente leitura, vírgula no caminho, mensagens de erro do Docker no Windows/Mac/Linux,
  limite de 3 consultas no teste).
- `kit.py verificar` nesta máquina detectou corretamente "Docker instalado, serviço desligado".
- `kit.py testar --mostrar-comando` e `buscar --mostrar-comando`: comandos montados conferidos
  (só flags confirmadas com `-h`, `DISABLE_TELEMETRY=1`, sem porta publicada).

### NÃO verificado (precisa do teste real)
- Nenhuma coleta de verdade pelo `kit.py` (exige Google Maps).
- `.devcontainer/devcontainer.json` não foi construído aqui: só o JSON foi validado.
- Windows e Mac: nada testado (RAM via `ctypes`/`sysctl`, `--mount` com caminho do Windows,
  mensagens de erro reais do Docker Desktop).
- Se o Docker do Codespace já está pronto no momento do `postCreateCommand` (por isso ele tem
  `|| true`: se falhar, a pessoa roda `kit.py verificar` de novo).

## Rodada 4 (2026-11-18) — testes em Windows/Mac (CI), formulário de problema, Fase 3b

- **GitHub Actions** (`.github/workflows/testes.yml`): roda os testes em ubuntu, windows e macos
  (Python 3.13) e o mínimo (Python 3.9) num contêiner `python:3.9-slim`: o 1º run falhou porque
  o Ubuntu 26.04 do GitHub não oferece mais o 3.9 (`setup-python`: "version '3.9' ... was not found").
  Nesse 1º run, **Windows, Mac e Linux (3.13) passaram em todos os testes**. Cobre a camada do kit; **não** coleta do Google
  (os servidores do GitHub não são o ambiente do cliente, e o Mac do Actions não tem Docker).
- Novos testes que dependem do sistema real: leitura de memória (`/proc/meminfo`, `sysctl`,
  `ctypes` no Windows), `verificar` sem quebrar, fluxo completo da demo (CSV → Excel com BOM →
  HTML com CSP) e montagem do comando com caminhos do próprio sistema.
- **Python mínimo passou de 3.8 para 3.9**, porque 3.9 é o menor que o CI testa (decisão:
  só prometer o que é testado).
- **Formulário "Relatar problema"** (`.github/ISSUE_TEMPLATE/problema.yml`): pede sistema, forma
  de instalação, saída do `verificar` e o `relatorio-teste.txt`; exige confirmar que não há dados
  de empresas. É o "beta" possível sem outros computadores: os primeiros usuários relatam.
- **Fase 3b:** comando `/leads-buscar` (pedido em português → plano → confirmação quando é grande
  → `kit.py buscar` → números + caminhos) e skill `leads-maps-br` (roteia para os comandos).
- **Decisão de material:** o material público cita só o gosom (motor) e este kit. A linha de
  "kits consultados como referência" fica no `CREDITS.md`, por transparência.

## Rodada 5 (2026-11-18) — 1º teste do Felipe no Codespace (sem coleta)

Medido no Codespace dele: x86_64, 7942 MB de RAM, 28 GB livres, **Python 3.12.16, sem Docker,
sem `claude`**. Os três comandos do `kit.py` rodaram e pararam corretamente em "falta Docker".

- **Erro encontrado (troubleshooting):** o Codespace abriu SEM a nossa configuração (Python 3.12
  em vez do 3.13 do `devcontainer.json`), ou seja, em contêiner de recuperação. Causa provável,
  confirmada no `install.sh` oficial do recurso docker-in-docker: com o padrão `moby: true` ele
  aborta no Debian trixie ("The 'moby' option is not supported on debian 'trixie'"). Correção:
  `"moby": false` (Docker CE, suportado no trixie segundo o mesmo script). Ainda não confirmado
  num Codespace novo.
- Removido `hostRequirements.memory = 8gb`: a máquina padrão de 2 núcleos reporta 7942 MB e o
  requisito poderia forçar uma máquina maior (mais cota). A padrão basta.
- `kit.py verificar` agora detecta Codespace sem Docker (`CODESPACES=true`) e manda reconstruir
  o contêiner, em vez de mandar instalar o Docker.
- **Claude Code:** o instalador oficial funcionou no Codespace (versão 2.1.327, em
  `~/.local/bin/claude`), mas ao digitar `claude` o terminal voltou sem mostrar nada. Causa
  ainda desconhecida; não bloqueia o teste do kit.
- Lição: eu não consegui construir o Codespace na sessão de desenvolvimento; o 1º teste real da
  configuração foi o do Felipe. Deveria ter marcado isso como risco maior.

## Rodada 6 (2026-11-18) — Codespace de gravação de vídeos (Claude Desktop)

Objetivo do Felipe: gravar vídeos com o Claude Desktop tendo só um Chromebook de 2 GB.

- **Pesquisa (fontes no fim da conversa / docs/gravacao-videos.md):** Claude Desktop tem versão
  Linux beta (Debian 12+/Ubuntu 22.04+, amd64/arm64; a página não informa RAM mínima; sem Computer
  Use nem ditado no Linux). Cota gratuita do Codespaces: 120 horas-núcleo/mês (~60 h em 2 núcleos).
  Oracle Always Free: relatos de redução para 2 OCPU/12 GB em 15/06/2026 (conflitante com páginas
  antigas). Azure: US$ 200 por 30 dias, exige cartão. "RAM virtual na nuvem" para o Chromebook não
  existe.
- **Escolha do Felipe: opção 1.** Configuração separada `.devcontainer/video/` (a dos clientes
  continua leve): `python:3.13-bookworm` + docker-in-docker (`moby: false`) + `desktop-lite`
  (área de trabalho Fluxbox via noVNC na porta 6080, privada no Codespace) + Claude Code +
  `--shm-size=1g` (recomendado pelo desktop-lite para apps que travam) + instalação do Claude
  Desktop pelo `postCreateCommand`.
- Bookworm em vez de trixie nesta configuração: os dois recursos (desktop-lite e docker-in-docker)
  são mais antigos/testados no bookworm; o Claude Desktop exige Debian 12+, então bookworm serve.
- **Instalador** (`.devcontainer/video/instalar-claude-desktop.sh`): comandos da documentação
  oficial, com `apt-get -y` e conferência automática da impressão digital publicada
  (31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE). **Defeito achado em teste:** `gpg --with-colons`
  também lista as subchaves, e a 1ª versão compararia todas as digitais juntas (falharia com a chave
  verdadeira). Corrigido para ler só a chave principal; provado com a chave pública do Docker
  (lê 9DC858229FC7DD38854AE2D88D81803C0EBFCD88 e ignora a subchave).
- **Não testado:** o Codespace de gravação nunca foi construído; `downloads.claude.ai` é bloqueado
  na sessão de desenvolvimento, então a chave real e o pacote não foram baixados aqui. Se o Electron
  do Claude Desktop vai abrir dentro do contêiner (sem GPU) é a maior incógnita.
- **Decisão do Felipe (mesmo dia):** a configuração de gravação SAIU do kit. O kit fica só com o
  que é do cliente. O "computador Claude na nuvem" (área de trabalho + Claude Desktop) vai para um
  repositório próprio, reutilizável em qualquer projeto. O vídeo do kit passa a mostrar o fluxo real
  do cliente: Claude Desktop + prompt de instalação.

## Rodada 7 (2026-11-19) — comparação com gosom e vzbaggio; atualizar, limpar, progresso, versão fixa

- **Comparação (ideias, sem copiar):** faltava em nós (A) atualizar o kit/motor, (C) mostrar
  andamento durante a coleta, (D) limpar/desinstalar e (E) fixar a versão do motor; (B) redes
  sociais (Instagram/Facebook/LinkedIn lidos do site) fica para a Fase 2b, opcional. Grade de
  coordenadas, `-resume` e proxies ficam fora por agora. O prompt do vzbaggio não traz "como
  atualizar"; o nosso agora traz.
- **(E) Versão fixa:** Docker Hub em 19/11/2026: `latest` = v1.19.0 (15/11), v1.18.3, **v1.18.2**
  (digest 6af44cb9f339, a mesma que baixamos e cujo `-h` conferimos). arm64 existe a partir da
  v1.18.0 (v1.17.x só amd64). O kit fixa `gosom/google-maps-scraper:v1.18.2`; o `latest` já tinha
  mudado 4 dias depois do nosso teste, o que confirma o risco.
- **(C) Progresso:** `Popen` + espera de 20 s mostrando tempo e linhas no CSV (se o motor gravar
  durante a coleta; não sabemos se grava aos poucos ou só no fim — a mensagem cobre os dois casos).
  Ctrl+C agora para o contêiner (antes, matar o `docker run` deixava o motor rodando).
- **(A) `kit.py atualizar`:** `git pull --ff-only` só se não houver arquivos do kit alterados;
  pasta de ZIP recebe instrução para baixar de novo; depois de atualizar, o `preparar` roda com o
  código novo (que pode fixar outra versão do motor).
- **(D) `kit.py limpar`:** lista o que vai remover e exige digitar "sim" (ou `--sim`); `--antigas`
  remove só versões que não são a fixa; nunca apaga `resultados/`.
- 60 testes passando (8 novos: versão fixa, progresso com processo falso escrevendo CSV,
  atualizar com repositório git de teste incluindo "não apagar mudanças da pessoa", limpar sem
  confirmação não remove nada, `--antigas` preserva a versão atual).

## Rodada 8 (2026-11-19) — 2ª comparação completa (painel e skill do vzbaggio; results/recovery do gosom)

- Achados e o que foi feito (implementação própria, sem copiar):
  - Painel do vzbaggio tem indicadores de qualidade dos contatos, filtro por categoria e "copiar
    para Sheets". **Feito no nosso HTML:** cartões (empresas, WhatsApp, telefone, site, e-mail, com %
    da lista filtrada), filtro por categoria (ordenado por quantidade) e botão "Copiar para Google
    Sheets" (TSV, com proteção contra fórmula e alternativa quando a área de transferência falha).
  - Skill do gosom trata "0 resultados" com passos a tentar e avisa que contato ausente não quer
    dizer que a empresa não tem. **Feito:** `kit.py` mostra "O que tentar, nesta ordem" (texto,
    esperar e reduzir, nome mais comum ou bairros, só depois profundidade) e o relatório diz que
    ausência = "a coleta não encontrou".
  - Skill do gosom sugere estrela no repositório após o 1º sucesso. **Feito (crédito):** `kit.py
    buscar` e `/leads-buscar` lembram, uma vez, que o motor é do gosom.
  - Dica de cidade grande: dividir por bairros (`docs/instalacao.md`, `/leads-buscar`).
- **Não feito, de propósito:** mapa com pinos (precisaria baixar mapas da internet; o relatório é
  offline e com CSP sem rede), interface web, proxies, grade de coordenadas, e-mail ligado por padrão
  (o vzbaggio liga; nós mantemos desligado porque deixa tudo mais lento e mais "raspagem").
- Verificado no Chromium local: cartões batem com o CSV da demo (20; 10 WhatsApp 50%; 16 telefone
  80%; 13 site 65%; 7 e-mail 35%), filtro "Contador" = 3, área de transferência com cabeçalho +
  linhas separadas por tab, 0 requisições externas, 0 erros de JS, 0 px de rolagem lateral em 390 px.

## Rodada 9 (2026-11-19) — redesenho visual (relatório, painel, terminal)

- **Relatório** (`scripts/modelo_relatorio.html` + `scripts/visual.py`): tipografia com serifa do
  sistema nos títulos (sem fonte da internet), cartões de qualidade com barra, consultas da busca no
  topo, barra de ferramentas fixa (desktop), filtros em pílula, avatar com iniciais, ações com ícones
  desenhados para o kit (sem logotipo de terceiros; o botão de WhatsApp usa um balão genérico),
  domínio do site no botão, estrela e "N avaliações", modo escuro próprio, versão para impressão.
  Contraste: menor par 4,95:1 (claro) e 5,97:1 (escuro), todos ≥ 4,5:1.
- **Painel** (`scripts/painel.py`, `kit.py painel`): `resultados/painel.html` com um cartão por busca
  (data, consultas, empresas, WhatsApp/site/e-mail com %, atalhos). Sem JavaScript; CSP sem rede.
  `kit.py buscar` atualiza o painel ao fim.
- **Terminal:** título com fio "KIT DE LEADS · …", margem, `[ok]/[aviso]/[falta]` coloridos e
  andamento numa linha que se atualiza (relógio a cada 2 s, contagem do CSV a cada 10 s). Só quando
  a saída é um terminal de pessoa (`isatty`) e sem `NO_COLOR`; quando o Claude lê a saída, nada de
  cor nem `\r`. No Windows, liga o modo de cores do console (VT) e desliga se falhar.
- Verificado no Chromium local (claro, escuro, 390 px): 0 requisições externas, 0 erros de JS,
  0 px de rolagem lateral; botões do painel abrem o relatório certo. 65 testes passando (5 novos:
  painel com busca/vazio, terminal com e sem cor, margem, consulta maliciosa vira texto).
- Não testado: aparência do terminal no Windows e no Mac reais (só simulado aqui com `script`).

## Rodada 10 (2026-11-19) — ideias do vídeo do vzbaggio (sem copiar) e Docker automático

- **Fonte:** transcrição e prints do vídeo público do Victor Baggio (12 min). Pontos fortes observados:
  o Claude dividiu "pilates em Curitiba" em cidade + 5 bairros, removeu categorias fora do segmento,
  escolheu 60 dos 103 pelo contato mais completo e ofereceu buscar redes sociais. Ele diz no vídeo
  que às vezes a busca demora "20, 30, 40 minutos" (dado dele, não medido por nós).
- **Feito (implementação própria):**
  - `--quantidade N` em `buscar`: as N com contato mais completo (WhatsApp 4, telefone 2, site 2,
    e-mail 2, nota 1; empate por avaliações e nota). Não é "pontuação de lead" (Fase 2b). A lista
    inteira fica em `todas-*.csv`.
  - `--excluir-categorias` / `--so-categorias` (sem acento e sem caixa) e **`kit.py refinar`**, que
    refaz a lista a partir do `bruto.csv` sem coletar de novo. O kit imprime as categorias encontradas.
  - `/leads-buscar` reescrito: estratégia (cidade + 3–5 bairros quando grande), plano com confirmação,
    limpeza de categorias com `refinar`, entrega com números e próximos passos.
  - Relatório: cartão **Nota média** (18 com nota → 4,4 na demo; conferido).
- **Correção de fato — Docker:** eu tinha dito que no Windows/Mac o Claude "só pode guiar". A
  documentação oficial do Docker (lida em 19/11/2026) tem **instalação por linha de comando**:
  Windows `"Docker Desktop Installer.exe" install --user` (modo por usuário, **sem administrador**;
  WSL 2 ≥ 2.1.5 é pré-requisito e `wsl --install` pede administrador e pode reiniciar); Mac
  `sudo hdiutil attach` + `.../Contents/MacOS/install` + `detach`; flag `--accept-license` nos dois.
  O kit agora instala sozinho por esses comandos, com uma confirmação.
- **Licença do Docker Desktop (importante para público B2B):** pelo resumo oficial, gratuito para uso
  pessoal, educação, open source não comercial e empresas com **< 250 funcionários e < US$ 10 mi/ano**;
  empresas maiores precisam de assinatura. O Claude mostra isso e só usa `--accept-license` com o "sim"
  da pessoa. Linux usa Docker Engine (sem essa licença). Entra nos "Limites honestos" do material.
- Pré-requisito oficial do Windows lista edições Pro/Enterprise/Education para o backend WSL 2, mas a
  mesma página diz que Home roda containers Linux. **Não testado** em Windows Home.
- 73 testes passando (8 novos: escolher melhores, filtrar categorias, contar categorias, refinar com
  e sem quantidade, pasta sem bruto, quantidade inválida).
