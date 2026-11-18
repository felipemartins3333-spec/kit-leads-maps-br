#!/usr/bin/env bash
# Instala o Claude Desktop (beta para Linux) dentro do Codespace de GRAVAÇÃO DE VÍDEOS.
# Segue exatamente a documentação oficial: https://code.claude.com/docs/en/desktop-linux
# Roda sozinho na criação do Codespace (postCreateCommand). Pode ser rodado de novo à mão:
#   bash .devcontainer/video/instalar-claude-desktop.sh
set -euo pipefail

CHAVE=/usr/share/keyrings/claude-desktop-archive-keyring.asc
DIGITAL_OFICIAL=31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE   # impressão digital publicada na documentação

if command -v claude-desktop >/dev/null 2>&1; then
  echo "[ok] Claude Desktop já está instalado."
  exit 0
fi

echo "== Instalando o Claude Desktop (documentação oficial, beta para Linux) =="

# 1. Repositório oficial da Anthropic
sudo apt-get update
sudo apt-get install -y curl gnupg
sudo curl -fsSLo "$CHAVE" https://downloads.claude.ai/claude-desktop/key.asc

# A documentação manda conferir a impressão digital da chave antes de seguir.
# Só a impressão digital da chave PRINCIPAL (as subchaves também aparecem no --with-colons).
DIGITAIS="$(gpg --show-keys --with-colons "$CHAVE" | awk -F: '$1=="pub"{p=1; next} p && $1=="fpr"{print $10; p=0}')"
if [ "$DIGITAIS" != "$DIGITAL_OFICIAL" ]; then
  echo "[PAROU] A chave baixada não confere com a impressão digital oficial. Nada foi instalado."
  sudo rm -f "$CHAVE"
  exit 1
fi
echo "[ok] Chave conferida: $DIGITAL_OFICIAL"

echo "deb [arch=amd64,arm64 signed-by=$CHAVE] https://downloads.claude.ai/claude-desktop/apt/stable stable main" \
  | sudo tee /etc/apt/sources.list.d/claude-desktop.list >/dev/null

# 2. Instalar o pacote
sudo apt-get update
sudo apt-get install -y claude-desktop

echo
echo "[ok] Claude Desktop instalado."
echo "Para abrir: conecte na área de trabalho (porta 6080, veja docs/gravacao-videos.md)"
echo "e rode no terminal:  claude-desktop &"
