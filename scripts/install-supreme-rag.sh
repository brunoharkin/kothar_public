#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - Aquisição de Conhecimento: System Design Primer
# =========================================================================

set -e

TARGET_DIR="/home/bruno/kothar/scratch/system-design-primer"

echo "🧠 Clonando o Cofre de Arquitetura de Sistemas (260k+ Stars)..."

if [ ! -d "$TARGET_DIR" ]; then
    git clone --depth 1 https://github.com/donnemartin/system-design-primer.git "$TARGET_DIR"
    echo "✅ Conhecimento Arquitetural (Escala e Segurança) absorvido."
else
    echo "✅ Cofre já existe em $TARGET_DIR."
fi
