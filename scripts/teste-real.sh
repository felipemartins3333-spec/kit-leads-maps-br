#!/usr/bin/env bash
# Atalho antigo, mantido para quem seguiu o guia do Chromebook.
# O teste agora é feito pelo scripts/kit.py (funciona também no Windows e no Mac).
#   bash scripts/teste-real.sh --so-checar   ==  python3 scripts/kit.py verificar
#   bash scripts/teste-real.sh               ==  python3 scripts/kit.py testar
cd "$(dirname "$0")/.." || exit 1
if [ "${1:-}" = "--so-checar" ]; then
  exec python3 -I scripts/kit.py verificar
fi
exec python3 -I scripts/kit.py testar "$@"
