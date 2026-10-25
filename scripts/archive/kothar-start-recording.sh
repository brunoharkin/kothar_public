#!/bin/bash
# ============================================
# KOTHAR - Iniciar Gravação de Sessão
# Inicia o observer para registrar a sessão
# ============================================

set -e

KOTHAR_DIR="/home/bruno/kothar"
OBSERVER_SCRIPT="$KOTHAR_DIR/scripts/kothar-observer.js"

echo "═══════════════════════════════════════════"
echo "🎬 INICIANDO GRAVAÇÃO DE SESSÃO KOTHAR"
echo "═══════════════════════════════════════════"
echo ""

# 1. Verificar se já está gravando
if [ -f "$KOTHAR_DIR/.recording" ]; then
    echo "⚠️  Já está gravando! Use kothar-stop-recording primeiro."
    exit 1
fi

# 2. Criar flag de gravação com timestamp
echo "$(date +%s)" > "$KOTHAR_DIR/.recording"
date +%s > "$KOTHAR_DIR/.recording-started"

# 3. Iniciar observer em background
echo "🔍 Iniciando observer..."
SESSION_ID="sessao-$(date +%Y%m%d-%H%M%S)"

# Verificar se node está disponível
if command -v node > /dev/null 2>&1; then
    nohup node "$OBSERVER_SCRIPT" start "$SESSION_ID" > "$KOTHAR_DIR/logs/observer-$(date +%Y%m%d).log" 2>&1 &
    OBSERVER_PID=$!
    echo "$OBSERVER_PID" > "$KOTHAR_DIR/.observer-pid"

    # Aguardar observer iniciar
    sleep 2

    # Verificar se está rodando
    if kill -0 "$OBSERVER_PID" 2>/dev/null; then
        echo "   ✅ Observer ativo (PID: $OBSERVER_PID)"
    else
        echo "   ⚠️  Observer não conseguiu iniciar"
    fi
else
    echo "   ⚠️  Node.js não encontrado"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "✅ GRAVAÇÃO ATIVA!"
echo "═══════════════════════════════════════════"
echo ""
echo "📝 Sessão ID:    $SESSION_ID"
echo "🔍 Observer PID: ${OBSERVER_PID:-N/A}"
echo ""
echo "📊 Logs:        $KOTHAR_DIR/logs/"
echo ""
echo "Para ENCERRAR:    kothar-stop-recording"
echo ""
