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

O Claude consegue instalar o Docker **sozinho**, usando a instalação por linha de comando da
documentação oficial do Docker (comandos abaixo). Ele mostra o que vai rodar e pede **uma**
confirmação. No Mac, o computador pede a sua senha uma vez; no Windows, só o WSL (se faltar) pede
administrador.

> **Licença do Docker Desktop (Windows e Mac).** Pelo resumo oficial do Docker, o Docker Desktop é
> gratuito para uso pessoal, educação, projetos de código aberto sem fins comerciais e **empresas com
> menos de 250 funcionários e menos de US$ 10 milhões de faturamento por ano**. Empresas maiores
> precisam de assinatura paga. A instalação aceita esse contrato
> (docker.com/legal/docker-subscription-service-agreement): o Claude mostra este resumo e só segue com
> o seu "sim".

**Windows** (fonte: docs.docker.com/desktop/setup/install/windows-install/)

1. Requisitos oficiais: Windows 10 ou 11 de 64 bits ainda com suporte da Microsoft, 8 GB de RAM,
   virtualização ligada no computador e **WSL 2** versão 2.1.5 ou mais nova. Para conferir: `wsl --version`.
2. Se o WSL faltar ou for antigo: num terminal **aberto como administrador**, `wsl --install`
   (ou `wsl --update`). Pode pedir para reiniciar o computador.
3. Baixar o instalador oficial: desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
   (computador com chip Arm: troque `amd64` por `arm64`).
4. Instalar no modo "por usuário", que **não precisa de administrador** (PowerShell, na pasta do arquivo):

```powershell
Start-Process 'Docker Desktop Installer.exe' -Wait -ArgumentList 'install', '--user', '--accept-license'
```

5. Abrir o **Docker Desktop** pelo menu Iniciar e esperar terminar de iniciar.

**Mac** (fonte: docs.docker.com/desktop/setup/install/mac-install/)

1. Requisitos oficiais: uma das três versões mais recentes do macOS e 4 GB de RAM.
2. Baixar o `Docker.dmg` do chip certo (`uname -m` mostra `arm64` ou `x86_64`):
   chip Apple (M1, M2...): desktop.docker.com/mac/main/arm64/Docker.dmg ·
   chip Intel: desktop.docker.com/mac/main/amd64/Docker.dmg
3. Instalar (pede a senha do Mac; a primeira vez pode levar alguns minutos por causa das checagens de
   segurança do macOS):

```bash
sudo hdiutil attach Docker.dmg
sudo /Volumes/Docker/Docker.app/Contents/MacOS/install --accept-license
sudo hdiutil detach /Volumes/Docker
```

4. Abrir o **Docker** em Aplicativos e esperar terminar de iniciar.

**Linux (Debian):** siga o Passo 3 e o Passo 4 de `docs/teste-no-chromebook.md` (comandos da
documentação oficial). **Ubuntu:** página oficial *Install Docker Engine on Ubuntu*
(docs.docker.com/engine/install/ubuntu/). No Linux não há licença do Docker Desktop: é o Docker Engine,
de código aberto.

Se preferir instalar com o mouse, as mesmas páginas oficiais têm o instalador com janelas.

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
- duas formas de usar: pelo terminal (um comando de busca pronto para copiar) e pedindo
  para você em português (o comando /leads-buscar);
- onde abrir o resultado de uma busca: o relatório HTML (duplo clique) e a planilha para Excel;
- os números do teste, sem nomes, telefones, e-mails ou sites de empresas.

Se algo der errado, explique em português simples e pare antes de tentar alternativas
que mexam no sistema.
```

Se o Claude Code já estiver aberto dentro da pasta do kit, basta digitar `/leads-instalar`.

---

## Como fazer uma busca

```bash
python3 scripts/kit.py buscar --segmentos "clínicas odontológicas" --cidades "Vitória da Conquista BA"
```

- Vários segmentos ou cidades: `--segmentos "academias" "pilates" --cidades "Salvador BA" "Feira de Santana BA"`.
- Procurar e-mails nos sites (mais lento): acrescente `--email`.
- Quer um número certo? `--quantidade 60` entrega as 60 com contato mais completo (WhatsApp, telefone,
  site, e-mail, nota); a lista inteira fica em `todas-excel.csv`.
- Veio categoria que não é do segmento? Refaça a lista **sem coletar de novo**:
  `python3 scripts/kit.py refinar --pasta resultados/busca-... --excluir-categorias "Academia" "Personal trainer"`.
- Mais resultados por consulta: `--profundidade 2` ou `3` (mais tempo e mais risco de bloqueio).
- **Cidade grande?** O Google Maps mostra um número limitado de empresas por busca. Em vez de aumentar
  muito a profundidade, divida por bairros: `--cidades "Pituba, Salvador BA" "Barra, Salvador BA"`.

O resultado fica em `resultados/busca-AAAAMMDD-HHMMSS/`:
- `relatorio.html`: abra com duplo clique (busca, filtros e botão de WhatsApp; funciona sem internet);
- `leads-excel.csv`: abre direto no Excel em português;
- `leads-tratados.csv`: o mesmo conteúdo em formato padrão, para importar em CRM.

E o **painel** `resultados/painel.html` reúne todas as suas buscas, cada uma num cartão com os números
e atalhos para o relatório e a planilha (duplo clique; funciona sem internet). Para gerá-lo de novo:
`python3 scripts/kit.py painel`.

---

## Atualizar

```bash
python3 scripts/kit.py atualizar
```

Baixa a versão nova do kit (se a pasta veio pelo `git clone`) e a versão do motor que ela usa. O kit
usa sempre uma **versão fixa e testada** do motor; ele só muda quando o kit é atualizado. Se você
baixou pelo ZIP, baixe o ZIP de novo e copie a sua pasta `resultados/` para a pasta nova.

## Liberar espaço ou desinstalar

```bash
python3 scripts/kit.py limpar
```

Mostra o que vai remover (o motor, ~2 GB, e o cache dele) e só remove depois que você digitar `sim`.
A pasta `resultados/` (as suas listas) **não** é apagada. Para remover só versões antigas do motor
depois de atualizar: `python3 scripts/kit.py limpar --antigas`.

---

## Problemas comuns

| Mensagem | O que fazer |
|----------|-------------|
| "O Docker não está instalado" | Veja B1. |
| "O Docker Desktop está instalado, mas não está aberto" | Abra o Docker Desktop, espere iniciar e rode de novo. |
| "o serviço não está ligado" (Linux) | `sudo systemctl start docker` |
| "não tem permissão" (Linux) | Passo 4 de `docs/teste-no-chromebook.md` (grupo `docker`), depois feche e abra o terminal. |
| "Falta espaço" | Libere pelo menos 5 GB e rode de novo (`kit.py limpar --antigas` remove versões velhas do motor). |
| Parece travado durante a busca | O kit mostra o andamento a cada 20 s. Se quiser parar, aperte Ctrl+C: o motor é parado e o que já foi coletado fica em `resultados/`. |
| "Nenhuma linha coletada" | Veja as causas que o kit mostra: sem internet, rede bloqueando o Google, Google limitando o acesso (mais comum na nuvem) ou pouca memória. Espere um pouco e tente com menos consultas. |
