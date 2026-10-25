#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR: Iniciar Observer em Background
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="/home/bruno/kothar"
OBSERVER="$KOTHAR_DIR/scripts/kothar-event-observer.js"
NODE_PATH="$HOME/.local/bin/node"

# Verificar se já está rodando
if pgrep -f "kothar-event-observer" > /dev/null; then
    echo "Observer já está rodando"
    exit 0
fi

# Verificar modo gravação
touch "$KOTHAR_DIR/.recording"

# Iniciar
nohup $NODE_PATH "$OBSERVER" start "kothar-$(date +%Y%m%d-%H%M%S)" > "$KOTHAR_DIR/logs/observer.log" 2>&1 &

echo "Observer iniciado em background"
