#!/bin/bash
# ============================================
# KOTHAR - Encerrar Gravação de Sessão
# Para o observer e libera recursos
# ============================================

set -e

KOTHAR_DIR="/home/bruno/kothar"

echo "═══════════════════════════════════════════"
echo "🛑 ENCERRANDO GRAVAÇÃO DE SESSÃO KOTHAR"
echo "═══════════════════════════════════════════"
echo ""

# 1. Verificar se está gravando
if [ ! -f "$KOTHAR_DIR/.recording" ]; then
    echo "⚠️  Não está gravando!"
    exit 1
fi

# 2. Parar observer se existir
if [ -f "$KOTHAR_DIR/.observer-pid" ]; then
    OBSERVER_PID=$(cat "$KOTHAR_DIR/.observer-pid")
    if kill -0 "$OBSERVER_PID" 2>/dev/null; then
        echo "🔍 Parando observer (PID: $OBSERVER_PID)..."
        kill "$OBSERVER_PID" 2>/dev/null || true
        sleep 1
        # Force kill if still running
        kill -9 "$OBSERVER_PID" 2>/dev/null || true
    fi
    rm -f "$KOTHAR_DIR/.observer-pid"
fi

# 3. Calcular duração da sessão
if [ -f "$KOTHAR_DIR/.recording-started" ]; then
    STARTED=$(cat "$KOTHAR_DIR/.recording-started")
    NOW=$(date +%s)
    DURATION=$((NOW - STARTED))
    echo "⏱️  Duração da sessão: $((DURATION / 60))m $((DURATION % 60))s"
fi

# 4. Remover flags
rm -f "$KOTHAR_DIR/.recording"
rm -f "$KOTHAR_DIR/.recording-started"

echo ""
echo "═══════════════════════════════════════════"
echo "✅ GRAVAÇÃO ENCERRADA!"
echo "═══════════════════════════════════════════"
echo ""
echo "📊 Dados preservados em: $KOTHAR_DIR/logs/"
echo ""
echo "💡 Para iniciar nova gravação: kothar-start-recording"
echo ""
