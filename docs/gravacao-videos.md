# Gravar vídeos com o Claude Desktop (sem precisar de Mac ou Windows)

Um Codespace especial, só para gravação: abre uma **área de trabalho no navegador** com o
**Claude Desktop** (versão Linux, beta), o Docker e o kit. Serve para gravar, de qualquer
computador (inclusive Chromebook), o Claude Desktop instalando e usando o kit.

> **Ainda não testado de ponta a ponta.** A configuração usa só recursos oficiais (veja as
> fontes no fim), mas o primeiro teste real é o seu. Se algo falhar, me mande a mensagem exata.

**Custo:** o GitHub dá 120 horas-núcleo por mês na conta gratuita (cerca de 60 horas na máquina
padrão de 2 núcleos). **Pare o Codespace quando terminar de gravar** (fim deste guia).

---

## 1. Criar o Codespace de gravação

1. Abra a página do repositório no GitHub.
2. Clique em **Code → Codespaces**, depois nos três pontinhos **`...`** e em **New with options**.
3. Em **Dev container configuration**, escolha **"Gravação de vídeos (área de trabalho + Claude Desktop)"**.
4. Clique em **Create codespace** e espere. A primeira vez demora mais: ele instala a área de
   trabalho, o Docker e o Claude Desktop.

## 2. Abrir a área de trabalho no navegador

1. No VS Code do Codespace, abra a aba **Portas** (ou **Ports**), ao lado do Terminal.
2. Na linha **6080 – "Área de trabalho (abra no navegador)"**, clique no ícone de **globo**.
3. Na página que abrir, clique em **Connect** e digite a senha **`vscode`**.

Essa porta é **privada**: só abre com o seu login do GitHub. Não mude para "Public".

## 3. Abrir o Claude Desktop

No **Terminal** do VS Code do Codespace, rode:

```bash
claude-desktop &
```

A janela aparece na área de trabalho (aba do navegador). Faça login com a sua conta Claude.

Se aparecer `command not found`, a instalação automática falhou. Rode de novo, e me mande o erro
se falhar outra vez:

```bash
bash .devcontainer/video/instalar-claude-desktop.sh
```

O instalador segue a documentação oficial e só continua se a chave de segurança da Anthropic
conferir com a impressão digital publicada.

## 4. Gravar

- Use o gravador de tela do próprio Chromebook (atalho **Ctrl + Shift + tecla de mostrar
  janelas**, depois escolha **vídeo**) e grave só a aba da área de trabalho.
- Deixe a aba em tela cheia (tecla **F11** ou a tecla de tela cheia do Chromebook).

### Roteiro sugerido para o vídeo de instalação

1. Mostrar o Claude Desktop aberto.
2. Abrir uma sessão de código apontando para a pasta `/workspaces/kit-leads-maps-br`.
3. Colar o prompt de instalação (está em `docs/instalacao.md`) ou digitar `/leads-instalar`.
4. Mostrar o Claude conferindo a máquina, preparando o motor e rodando o teste.
5. Abrir o relatório de demonstração: `examples/demo-relatorio.html`.

## Cuidados com o que aparece no vídeo

- **Dados de empresas reais são dados de terceiros (LGPD).** Para mostrar o relatório, prefira a
  **demonstração fictícia** (`examples/demo-relatorio.html`). Se mostrar uma busca real, borre
  nomes, telefones, e-mails e sites na edição.
- Não mostre a tela de login, e-mails de conta, nem chaves ou senhas.
- Este Codespace roda na nuvem: a coleta pode vir menor do que viria da internet de casa.
  Não apresente esses números como regra.

## Problemas comuns

| O que acontece | O que fazer |
|---|---|
| A aba da porta 6080 não abre | Confira na aba **Portas** se a 6080 aparece; se não, espere a criação terminar e recarregue. |
| Pede senha e não aceita | A senha padrão é `vscode`. |
| O Claude Desktop não abre ou fecha sozinho | Rode `claude-desktop` (sem o `&`) no terminal e me mande a mensagem que aparecer. |
| O login não fica salvo | Normal em alguns ambientes (a documentação oficial explica que o login fica no "keyring"). Faça login de novo. |
| Ficou lento | Feche o que não estiver usando; se continuar, crie o Codespace com uma máquina maior (gasta mais cota). |

## Ao terminar: parar o Codespace

Abra github.com/codespaces, clique nos três pontinhos do Codespace de gravação e escolha
**Stop codespace**. Parado, ele não gasta horas (o armazenamento continua contando um pouco).
Quando não for mais usar, escolha **Delete**.

---

Fontes oficiais: Claude Desktop no Linux (code.claude.com/docs/en/desktop-linux); área de
trabalho para Codespace `desktop-lite` (github.com/devcontainers/features, `src/desktop-lite`);
cota do Codespaces (docs.github.com, "How use of GitHub Codespaces is measured").
