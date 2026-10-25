#!/bin/bash
# Hook para Git/post-commit: atualiza RAG automaticamente após commits no cofre
#
# Para instalar:
#   cp git-post-commit-kothar.sh "$KOTHAR_VAULT_PATH/.git/hooks/post-commit"
#   chmod +x "$KOTHAR_VAULT_PATH/.git/hooks/post-commit"

set -e

COFRE_DIR="${KOTHAR_VAULT_PATH:-${VAULT_PATH:-$HOME/Cofre}}"
KOTHAR_DIR="${KOTHAR_PROJECT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
RAG_SCRIPT="$KOTHAR_DIR/scripts/rag_watcher.py"
if [ -x "$KOTHAR_DIR/.venv/bin/python" ]; then
    KOTHAR_PYTHON_BIN="$KOTHAR_DIR/.venv/bin/python"
else
    KOTHAR_PYTHON_BIN="$(command -v python3)"
fi

echo "🔄 Kothar RAG Hook: detectando mudanças no cofre..."

# Verifica se houve commit afetando kothar_core/ ou kothar_manuais/ ou sessao/
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || echo "")

if echo "$CHANGED_FILES" | grep -qE "kothar_core|kothar_manuais|sessao"; then
    echo "📝 Mudanças em arquivos do cofre detectadas:"
    echo "$CHANGED_FILES" | grep -E "kothar_core|kothar_manuais|sessao" | head -5
    echo ""
    echo "🔄 Atualizando RAG do Kothar..."
    KOTHAR_VAULT_PATH="$COFRE_DIR" "$KOTHAR_PYTHON_BIN" "$RAG_SCRIPT" --oneshot
    echo ""
    echo "✅ RAG atualizado!"
else
    echo "ℹ️  Nenhuma mudança em arquivos do cofre neste commit"
fi
