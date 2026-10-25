#!/bin/bash
# ============================================
# KOTHAR - Wrapper de Comandos
# Executa comando com logging
# ============================================

KOTHAR_DIR="/home/bruno/kothar"
LOG_FILE="$KOTHAR_DIR/logs/commands.log"

# Criar diretório de logs se não existir
mkdir -p "$KOTHAR_DIR/logs"

# Executar comando
"$@"
exit_code=$?

# Registrar resultado
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Finalizado: $* (exit: $exit_code)" >> "$LOG_FILE"

exit $exit_code
