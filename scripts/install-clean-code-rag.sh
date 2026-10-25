#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - Aquisição de Conhecimento: Clean Code
# =========================================================================

set -e

TARGET_DIR="/home/bruno/kothar/scratch/clean-code"

echo "🧠 Clonando o Cofre de Clean Code e Boas Práticas..."

if [ ! -d "$TARGET_DIR" ]; then
    git clone --depth 1 https://github.com/ryanmcdermott/clean-code-javascript.git "$TARGET_DIR"
    echo "✅ Conhecimento de Código Limpo e Revisão absorvido."
else
    echo "✅ Cofre já existe em $TARGET_DIR."
fi
