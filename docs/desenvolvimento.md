# Regras de desenvolvimento do kit

> Para quem ALTERA o código ou a documentação deste kit (inclusive o Claude em sessões de
> desenvolvimento). Quem só instala e usa o kit segue o `CLAUDE.md` da raiz.

Kit brasileiro de geração de leads com Google Maps. Tudo em português do Brasil, simples e
à prova de erro, para quem não é técnico. Licença MIT (Felipe Martins Muniz).

## Regras invioláveis

1. **Originalidade.** Não copiar texto, código, nomes, banners ou visual de nenhum
   repositório de referência (gosom, Mahanaicoach, vzbaggio). Pode aprender a ideia e
   reescrever do zero. O motor entra só como imagem Docker publicada, sem o código-fonte.
2. **Nada de flag inventada.** Confirmar toda flag com `docker run --rm gosom/google-maps-scraper -h`
   ou com o README oficial antes de usar. Registrar a versão do motor nas medições.
3. **Testes pequenos.** No máximo 3 consultas, `-depth 1`, sem proxy. Nada de varredura grande.
4. **Rede.** Nunca expor porta além de `127.0.0.1`. O único servidor é a tela (`kit.py abrir`): só `127.0.0.1`, chave no link, cabeçalho próprio no POST, checagem de Host e arquivos só de `resultados/`. Qualquer mudança nela precisa manter essas proteções e os testes de `tests/test_interface.py`.
5. **Dados reais nunca vão para o git.** Resultados ficam em `resultados/` (ignorada). O único
   CSV versionado é `examples/demo-*.csv`, 100% fictício, com `fonte = DEMO`.
6. **Honestidade.** Dizer sempre que o scraping do Google Maps pode contrariar os termos do
   Google e que dados de contato envolvem LGPD. Nada de promessa de volume ou de resultado.
7. **Telemetria.** Todo `docker run` do motor leva `-e DISABLE_TELEMETRY=1`.
8. **Validar o CSV, não o código de saída.** O motor sai com código 0 mesmo sem coletar nada.
   Sempre contar as linhas com o módulo `csv` (campos podem ter quebra de linha; `wc -l` erra).
9. **Por fase.** Trabalhar por fase, parar ao terminar, resumir e esperar aprovação.
10. **Fatos, não impressões.** Registrar em `NOTES.md` só o que foi medido ou lido na fonte,
    marcando claramente o que é suposição.
11. **Sessões de desenvolvimento na nuvem (Claude Code na web).** Essa nuvem não alcança o
    Google Maps. A coleta real é feita pelo Felipe (máquina própria ou Codespace). Nessas
    sessões: não tentar acessar o Google, não subir `dockerd`, não instalar nada com
    privilégio elevado. Arquivos com blocos de shell dentro são gravados com a ferramenta de
    escrita de arquivos, nunca por heredoc (ver incidente em NOTES.md).
12. **Git.** Autor dos commits: o e-mail noreply do GitHub configurado neste repositório.
    Antes de cada commit/push: procurar segredos (chaves, tokens, `.env`) e conferir o autor.
    Nunca `push --force` sem nova autorização explícita do Felipe.

## Convenções

- Ponto de entrada único: `scripts/kit.py` (Windows, Mac, Linux, Codespace). Não criar
  caminhos paralelos em Bash; `scripts/teste-real.sh` é só um atalho antigo.
- Scripts Python: só biblioteca padrão. Rodar com `python3 -I` quando lerem arquivos baixados.
- Dados privados nunca em relatórios para colar no chat: só números, tempos e versões.
- Dados de demonstração: nomes claramente inventados, e-mails `@example.com`, `fonte = DEMO`.
