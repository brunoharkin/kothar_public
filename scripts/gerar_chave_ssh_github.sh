#!/usr/bin/env bash
set -euo pipefail

SSH_DIR="$HOME/.ssh"
KEY_PATH="$SSH_DIR/id_ed25519_kothar_public"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ ! -f "$KEY_PATH" ]; then
    echo "🔑 Gerando nova chave SSH Ed25519 para o repositório público..."
    ssh-keygen -t ed25519 -C "bruno@kothar.public" -f "$KEY_PATH" -N ""
else
    echo "ℹ️ Chave SSH já existente em $KEY_PATH."
fi

echo ""
echo "========================================================================="
echo "📋 CHAVE PÚBLICA SSH GERADA (Copie e adicione ao GitHub):"
echo "========================================================================="
cat "${KEY_PATH}.pub"
echo "========================================================================="
echo ""
echo "👉 Acesse: https://github.com/settings/ssh/new"
echo "   Título: Kothar Public"
echo "   Cole a chave acima e clique em 'Add SSH key'."
echo ""
