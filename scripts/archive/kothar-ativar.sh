#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR WRAPPER v3.0
# Wrapper simples para ativar o Kothar
# Uso: ./kothar-ativar.sh
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTHAR_CLI="$SCRIPT_DIR/kothar-cli.sh"

if [ -x "$KOTHAR_CLI" ]; then
    exec "$KOTHAR_CLI" activate
else
    echo "❌ Kothar CLI não encontrado ou não executável"
    echo "   Execute: chmod +x $KOTHAR_CLI"
    exit 1
fi
