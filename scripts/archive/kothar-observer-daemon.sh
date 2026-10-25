#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR: Daemon Observer
# Mantém o observer rodando persistentemente
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="/home/bruno/kothar"
OBSERVER="$KOTHAR_DIR/scripts/kothar-event-observer.js"
NODE_PATH="$HOME/.local/bin/node"
PID_FILE="$KOTHAR_DIR/.observer-daemon.pid"
STATE_FILE="$KOTHAR_DIR/.observer-state.json"
LOG_FILE="$KOTHAR_DIR/logs/observer-daemon.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Verifica se já está rodando
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
        rm -f "$PID_FILE"
    fi
    return 1
}

# Iniciar daemon
start() {
    if is_running; then
        echo "Observer daemon já está rodando (PID: $(cat $PID_FILE))"
        return 0
    fi

    echo "Iniciando observer daemon..."

    # Verificar se modo gravação está ativo
    touch "$KOTHAR_DIR/.recording" 2>/dev/null || true

    # Criar sessão única
    local session_name="kothar-daemon-$(date +%Y%m%d-%H%M%S)"

    # Iniciar em background
    $NODE_PATH "$OBSERVER" start "$session_name" >> "$LOG_FILE" 2>&1 &
    local pid=$!

    echo "$pid" > "$PID_FILE"

    sleep 2

    if is_running; then
        log "Daemon started: PID=$pid, Session=$session_name"
        echo "Observer daemon iniciado (PID: $pid)"
        echo "Sessão: $session_name"
    else
        log "Failed to start daemon"
        echo "Erro ao iniciar daemon"
        return 1
    fi
}

# Parar daemon
stop() {
    if ! is_running; then
        echo "Observer daemon não está rodando"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    echo "Parando observer daemon (PID: $pid)..."

    kill "$pid" 2>/dev/null
    sleep 1

    if ! is_running; then
        rm -f "$PID_FILE"
        log "Daemon stopped"
        echo "Observer daemon parado"
    else
        kill -9 "$pid" 2>/dev/null
        rm -f "$PID_FILE"
        echo "Observer daemon forçado a parar"
    fi
}

# Status
status() {
    if is_running; then
        echo "Observer daemon: RODANDO (PID: $(cat $PID_FILE))"
        if [[ -f "$STATE_FILE" ]]; then
            echo ""
            echo "Estado atual:"
            cat "$STATE_FILE" | python3 -m json.tool 2>/dev/null || cat "$STATE_FILE"
        fi
    else
        echo "Observer daemon: PARADO"
    fi
}

# Restart
restart() {
    stop
    sleep 1
    start
}

# Auto-start se não estiver rodando
auto_start() {
    if ! is_running; then
        if [[ -f "$KOTHAR_DIR/.recording" ]]; then
            start
        fi
    fi
}

# Main
case "${1:-start}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    auto)
        auto_start
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|auto}"
        exit 1
        ;;
esac
