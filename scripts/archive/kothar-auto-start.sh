#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR AUTO-START v3.0
# Este script é executado automaticamente quando o Claude Code inicia
# Mostra a saudação completa do Kothar
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="$HOME/kothar"

# Executar o script de boas-vindas
if [ -x "$KOTHAR_DIR/scripts/kothar-welcome.sh" ]; then
    exec "$KOTHAR_DIR/scripts/kothar-welcome.sh"
fi
