#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - Aquisição de Conhecimento Data Engineering
# =========================================================================

set -e

TARGET_DIR="/home/bruno/kothar/scratch/awesome-data-engineering"

echo "🧠 Clonando o Cofre de Engenharia de Dados..."

if [ ! -d "$TARGET_DIR" ]; then
    git clone --depth 1 https://github.com/igorbarinov/awesome-data-engineering.git "$TARGET_DIR"
    echo "✅ Engenharia de Dados purificada e absorvida no Cofre."
else
    echo "✅ Cofre já existe em $TARGET_DIR."
fi
