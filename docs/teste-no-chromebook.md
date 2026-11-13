# Teste real no Chromebook (passo a passo)

Objetivo: rodar o kit uma vez na sua máquina, com **3 consultas**, para medir tempo e
quantos contatos vêm preenchidos. No fim você cola um relatório **só com números** no chat.

> **Antes de começar.** Coletar dados do Google Maps de forma automática pode contrariar
> os termos de uso do Google, e telefones/e-mails de empresas podem ser dados pessoais
> (LGPD). Este teste é pequeno de propósito: 3 consultas, sem proxy. Isto não é
> aconselhamento jurídico.

**Tempo total estimado:** não sabemos ainda. Medir isso é justamente o objetivo do teste.
**Espaço:** a imagem do motor tem cerca de **2 GB**. O script exige **5 GB livres** antes de
baixar (folga nossa para o Docker descompactar). Ele confere isso sozinho e para se faltar.

---

## Passo 1 — Ligar o Linux no Chromebook

Na Ajuda do Chromebook, procure por **"Configurar o Linux no Chromebook"** e siga o roteiro
(geralmente em *Configurações → Avançado → Desenvolvedores → Ambiente de desenvolvimento
Linux → Ativar*; os nomes dos menus mudam conforme a versão do ChromeOS). Quando perguntar
o tamanho do disco do Linux, escolha **pelo menos 10 GB**.

Ao terminar, abre uma janela preta chamada **Terminal**. Todos os comandos abaixo são
digitados (ou colados) nela.

## Passo 2 — Ver se o seu Linux serve para o Docker

```bash
cat /etc/os-release
```

```bash
uname -m
```

```bash
df -h ~
```

O que olhar:

- Em `/etc/os-release`, procure `VERSION_CODENAME`. A documentação oficial do Docker
  diz que o Docker Engine no Debian é suportado nas versões **Trixie (13)** e
  **Bookworm (12)**. Se aparecer outra (por exemplo `bullseye`), o caminho do Docker pode
  não funcionar: vá direto para a seção *"Se o Docker não funcionar"* no fim deste guia.
- `uname -m`: `x86_64` ou `aarch64` servem (a imagem do motor existe para os dois).
- `df -h ~`: confira se a coluna **Avail** tem pelo menos 5G.

## Passo 3 — Instalar o Docker (documentação oficial)

Fonte: *Install Docker Engine on Debian* (docs.docker.com/engine/install/debian/), método
"apt repository". Os comandos abaixo são os da documentação oficial; se a Docker mudar o
roteiro, a página oficial vale mais que este texto.

**3.1 — Remover pacotes não oficiais que atrapalham** (se não tiver nenhum, o `apt` só avisa):

```bash
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-doc docker-buildx podman-docker containerd runc | cut -f1)
```

**3.2 — Adicionar o repositório oficial do Docker:**

```bash
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

```bash
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```

```bash
sudo apt update
```

**3.3 — Instalar:**

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**3.4 — Ver se o serviço está ligado** (se não estiver, o segundo comando liga):

```bash
sudo systemctl status docker
```

```bash
sudo systemctl start docker
```

**3.5 — Testar com o `hello-world`** (baixa uma imagem minúscula e imprime uma mensagem):

```bash
sudo docker run hello-world
```

Se aparecer *"Hello from Docker!"*, o Docker funciona. Se deu erro, vá para *"Se o Docker não
funcionar"*.

> Não sabemos se o Docker roda no ambiente Linux do seu modelo de Chromebook: ele roda
> dentro de uma máquina virtual do ChromeOS e isso pode falhar em alguns aparelhos. É uma
> das coisas que este teste vai descobrir. Anote a mensagem de erro, se houver.

## Passo 4 — Usar o Docker sem escrever `sudo`

Fonte: *Linux post-installation steps for Docker Engine* (docs.docker.com/engine/install/linux-postinstall/).
A própria Docker avisa: quem está no grupo `docker` ganha, na prática, poderes de administrador
nessa máquina. Num Chromebook pessoal isso costuma ser aceitável; decida por você.

```bash
sudo groupadd docker
```

(se responder que o grupo já existe, está tudo certo)

```bash
sudo usermod -aG docker $USER
```

```bash
newgrp docker
```

Teste (sem `sudo`):

```bash
docker run hello-world
```

Se continuar com *permission denied*, feche o Terminal, abra de novo e repita o teste.

## Passo 5 — Baixar o kit e conferir a máquina

```bash
sudo apt install git
```

```bash
git clone https://github.com/felipemartins3333-spec/kit-leads-maps-br
```

```bash
cd kit-leads-maps-br
```

Primeiro só a conferência (não baixa nem coleta nada):

```bash
bash scripts/teste-real.sh --so-checar
```

Ele diz, em português simples, o que está ok e o que falta (Docker desligado, sem permissão,
pouco espaço...).

## Passo 6 — Rodar o teste real

```bash
bash scripts/teste-real.sh
```

O que ele faz: baixa a imagem oficial (só se houver espaço), roda o **Teste 1** (sem
e-mail) e o **Teste 2** (com e-mail) com `-depth 1`, sem proxy, com a telemetria do motor
desligada, e mede o tempo de cada um. Se o Teste 1 vier com 0 linhas usando `-lang pt-BR`,
ele repete com `-lang pt` e registra qual funcionou.

As consultas ficam em `examples/consultas-teste.txt` (3 linhas). Pode trocar pelos seus
segmentos e cidades, mas **mantenha no máximo 3 linhas**.

Pode demorar vários minutos e o Terminal pode ficar parado em silêncio durante a coleta.
Isso é normal; espere o script avisar "Pronto".

## Passo 7 — Mandar o resultado

Abra `resultados/relatorio-teste.txt` e cole o conteúdo no chat:

```bash
cat resultados/relatorio-teste.txt
```

Esse relatório tem **somente números, tempos e versões**: nenhum nome, telefone ou e-mail
de empresa. **Não cole** os arquivos `.csv` nem os `.log` sem olhar antes: eles têm dados
de empresas. A pasta `resultados/` é ignorada pelo git, então nada disso vai para o GitHub.

---

## Se o Docker não funcionar (plano B: binário do motor)

Só use se o Docker não rodar de jeito nenhum. **Este plano B ainda não foi testado por nós.**
O que a documentação do gosom diz e o que ainda é dúvida:

- O README do gosom informa que existe "binary release" na página de releases
  (github.com/gosom/google-maps-scraper/releases). Eu não consegui abrir essa página daqui,
  então **não sei quais arquivos ela oferece** para cada versão.
- O `Makefile` dele só compila para Linux **amd64**, macOS amd64 e Windows amd64. Se o seu
  Chromebook for ARM (`uname -m` mostra `aarch64`), pode não haver binário pronto.
- O binário precisa do navegador Chromium via Playwright, que é baixado na primeira
  execução (o README diz isso no trecho de compilação), e de bibliotecas do sistema. A lista
  que a imagem oficial instala está no `Dockerfile` do gosom (`libnss3`, `libgbm1`,
  `libasound2` e outras). Sem elas o navegador não abre.

Se o seu caso for esse, pare e me avise com a saída de `uname -m` e `cat /etc/os-release`:
vamos decidir juntos antes de tentar.
