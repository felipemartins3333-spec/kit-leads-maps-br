# Instalação do kit de leads

Escolha **um** caminho:

| Caminho | Para quem | O que precisa instalar |
|---------|-----------|------------------------|
| **A. Codespace** (GitHub no navegador) | quem não quer instalar nada, ou tem computador fraco | nada: Docker e Claude Code já vêm prontos |
| **B. Seu computador + Claude** | quem quer rodar na própria máquina, com o Claude fazendo o trabalho | Docker e Claude (o resto o Claude faz) |
| **C. Seu computador, sem Claude** | quem prefere digitar os comandos | Docker, Python e o kit |

> **Antes de começar.** Coletar dados do Google Maps de forma automática pode contrariar os
> termos de uso do Google. Telefones e e-mails de empresas podem ser dados pessoais (LGPD):
> use com finalidade clara e respeite quem pedir para não ser contatado. Isto não é
> aconselhamento jurídico. O kit não promete volume: muitas empresas não têm telefone, site
> ou e-mail no Maps.

**Espaço e memória:** a imagem do motor tem cerca de **2 GB** (o kit pede **5 GB livres**
antes de baixar). Para o navegador do motor, recomendamos **3 GB de RAM ou mais** (estimativa
nossa). O Claude Code pede **4 GB+** e o Docker Desktop no Windows pede **8 GB** (documentações
oficiais de cada um).

---

## Caminho A — Codespace (nada para instalar)

1. Abra a página do repositório no GitHub e clique em **Code → Codespaces → Create codespace on main**.
2. Espere alguns minutos: o Codespace já vem com **Python, Docker e Claude Code** (configurado em
   `.devcontainer/devcontainer.json`).
3. No terminal que aparece embaixo, rode:

```bash
python3 scripts/kit.py verificar
```

```bash
python3 scripts/kit.py preparar
```

```bash
python3 scripts/kit.py testar
```

Quer que o Claude conduza? No mesmo terminal digite `claude`, faça login e cole o
[prompt de instalação](#prompt-de-instalação-para-colar-no-claude).

Dois cuidados honestos:
- O Codespace roda em servidores na nuvem. O Google tende a desconfiar mais desse tipo de
  conexão, então pode vir menos resultado (ou nenhum) do que viria da internet de casa.
- O Codespace é pensado para desenvolvimento e tem cota de horas no GitHub. Confira os termos
  e a cota da sua conta antes de usar com frequência.

---

## Caminho B — Seu computador + Claude

### B1. Instalar o Docker

O Docker é o único programa que o Claude **não consegue instalar sozinho** no Windows e no Mac:
o instalador oficial tem janelas, pede permissão de administrador e às vezes reinício.

- **Windows:** Docker Desktop, pela página oficial *Install Docker Desktop on Windows*
  (docs.docker.com/desktop/setup/install/windows-install/). Requisitos oficiais: WSL 2 ligado e
  8 GB de RAM.
- **Mac:** Docker Desktop, pela página oficial *Install Docker Desktop on Mac*
  (docs.docker.com/desktop/setup/install/mac-install/). Há um instalador para chip Apple (M1, M2…)
  e outro para chip Intel. Requisitos oficiais: pelo menos 4 GB de RAM e uma das três versões
  mais recentes do macOS.
- **Linux (Debian):** siga o Passo 3 e o Passo 4 de `docs/teste-no-chromebook.md` (comandos da
  documentação oficial). **Ubuntu:** página oficial *Install Docker Engine on Ubuntu*
  (docs.docker.com/engine/install/ubuntu/). No Linux, o Claude pode rodar esses comandos por
  você, mas vai pedir sua confirmação antes, porque mexem no sistema.

Depois de instalar, **abra o Docker Desktop** (Windows/Mac) e espere ele terminar de iniciar.

### B2. Instalar o Claude

Escolha um (documentação oficial: code.claude.com/docs/en/setup):

- **App Claude Desktop** (sem terminal): baixe em claude.com/download (Windows e Mac). No Linux
  existe uma versão **beta** para Debian 12+ e Ubuntu 22.04+ (code.claude.com/docs/en/desktop-linux).
- **Claude Code no terminal:**

  Mac, Linux ou WSL:

  ```bash
  curl -fsSL https://claude.ai/install.sh | bash
  ```

  Windows (PowerShell):

  ```powershell
  irm https://claude.ai/install.ps1 | iex
  ```

  Depois, abra um terminal novo e digite `claude`.

### B3. Colar o prompt

Abra o Claude e cole o [prompt de instalação](#prompt-de-instalação-para-colar-no-claude). Ele
baixa o kit, confere a máquina, instala o que faltar (pedindo confirmação para mudanças no
sistema) e roda o teste pequeno.

---

## Caminho C — Sem Claude

1. **Python 3.9 ou mais novo.**
   - Linux e Codespace: já vem.
   - Mac: digite `python3 --version` no Terminal. Se o Mac oferecer instalar as ferramentas de
     linha de comando, aceite.
   - Windows: instale pelo python.org/downloads e, na primeira tela do instalador, marque a opção
     de adicionar o Python ao PATH.
2. **Docker:** veja B1.
3. **Baixar o kit:** com Git, `git clone` do endereço do repositório. Sem Git, na página do
   repositório clique em **Code → Download ZIP** e descompacte.
4. **Abrir o terminal dentro da pasta do kit** e rodar, nesta ordem:

```bash
python3 scripts/kit.py verificar
```

```bash
python3 scripts/kit.py preparar
```

```bash
python3 scripts/kit.py testar
```

No Windows, troque `python3` por `py` e `/` por `\` (por exemplo `py scripts\kit.py verificar`).

---

## Prompt de instalação (para colar no Claude)

```text
Quero usar o kit de leads do Google Maps deste repositório:
https://github.com/felipemartins3333-spec/kit-leads-maps-br

Instale e deixe funcionando neste computador, seguindo SÓ o que está no próprio repositório.

1. Baixe o repositório (git clone; se não houver Git, me peça para baixar o ZIP pelo GitHub).
2. Leia o CLAUDE.md e o docs/instalacao.md antes de rodar qualquer comando.
3. Rode "python3 scripts/kit.py verificar" (no Windows: "py scripts\kit.py verificar") e me
   diga, em uma frase, o que falta.
4. Resolva só o que faltar, pelo docs/instalacao.md. Antes de qualquer mudança no sistema
   (instalar programas, usar sudo ou administrador), me mostre o que vai fazer e peça
   confirmação. Se o Docker Desktop precisar ser instalado no Windows ou no Mac, me guie
   passo a passo e espere eu terminar.
5. Rode "kit.py preparar" e depois "kit.py testar".
6. No fim, me diga: o que foi instalado, onde ficou a pasta do kit, como fazer uma busca
   simples e onde abrir o relatório. Mostre só os números do teste, sem nomes, telefones
   ou e-mails de empresas.

Não invente comandos: use só os do repositório e das documentações oficiais citadas nele.
```

Se o Claude Code já estiver aberto dentro da pasta do kit, basta digitar `/leads-instalar`.

---

## Como fazer uma busca

```bash
python3 scripts/kit.py buscar --segmentos "clínicas odontológicas" --cidades "Vitória da Conquista BA"
```

- Vários segmentos ou cidades: `--segmentos "academias" "pilates" --cidades "Salvador BA" "Feira de Santana BA"`.
- Procurar e-mails nos sites (mais lento): acrescente `--email`.
- Mais resultados por consulta: `--profundidade 2` ou `3` (mais tempo e mais risco de bloqueio).

O resultado fica em `resultados/busca-AAAAMMDD-HHMMSS/`:
- `relatorio.html`: abra com duplo clique (busca, filtros e botão de WhatsApp; funciona sem internet);
- `leads-excel.csv`: abre direto no Excel em português;
- `leads-tratados.csv`: o mesmo conteúdo em formato padrão, para importar em CRM.

---

## Problemas comuns

| Mensagem | O que fazer |
|----------|-------------|
| "O Docker não está instalado" | Veja B1. |
| "O Docker Desktop está instalado, mas não está aberto" | Abra o Docker Desktop, espere iniciar e rode de novo. |
| "o serviço não está ligado" (Linux) | `sudo systemctl start docker` |
| "não tem permissão" (Linux) | Passo 4 de `docs/teste-no-chromebook.md` (grupo `docker`), depois feche e abra o terminal. |
| "Falta espaço" | Libere pelo menos 5 GB e rode de novo. |
| "Nenhuma linha coletada" | Veja as causas que o kit mostra: sem internet, rede bloqueando o Google, Google limitando o acesso (mais comum na nuvem) ou pouca memória. Espere um pouco e tente com menos consultas. |
