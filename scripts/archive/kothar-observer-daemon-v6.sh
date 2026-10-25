#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR Observer Daemon v6 - Wrapper robusto para kothar-observer.js
# Mantém o observer rodando persistentemente com auto-restart
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="/home/bruno/kothar"
OBSERVER="$KOTHAR_DIR/scripts/kothar-observer.js"
NODE_PATH="$HOME/.local/bin/node"
PID_FILE="$KOTHAR_DIR/.observer-daemon.pid"
STATE_FILE="$KOTHAR_DIR/.observer-state.json"
LOG_FILE="$KOTHAR_DIR/logs/observer-daemon.log"
LOCK_FILE="$KOTHAR_DIR/.observer-daemon.lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

is_running() {
    [[ -f "$PID_FILE" ]] && kill -0 "$(cat $PID_FILE)" 2>/dev/null
}

wait_for_state() {
    local timeout=10
    while [[ $timeout -gt 0 ]]; do
        if [[ -f "$STATE_FILE" ]] && grep -q '"traceId"' "$STATE_FILE" 2>/dev/null; then
            return 0
        fi
        sleep 1
        ((timeout--))
    done
    return 1
}

start() {
    if is_running; then
        log "Observer daemon já está rodando (PID: $(cat $PID_FILE))"
        return 0
    fi
    
    # Criar lock
    touch "$LOCK_FILE"
    
    # Criar sessão única
    local session_name="kothar-$(date +%Y%m%d-%H%M%S)"
    
    log "🚀 Iniciando Observer Daemon v6..."
    log "   Sessão: $session_name"
    
    # Iniciar com setsid para detached process
    setsid $NODE_PATH "$OBSERVER" start "$session_name" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    
    echo "$pid" > "$PID_FILE"
    
    # Aguardar estado ser criado
    if wait_for_state; then
        log "✅ Observer Daemon iniciado (PID: $pid)"
        log "   Estado salvo em: $STATE_FILE"
        
        # Mostrar estado atual
        if [[ -f "$STATE_FILE" ]]; then
            log "   Session: $(grep -o '"sessionName"[^,]*' "$STATE_FILE" | head -1)"
            log "   Trace: $(grep -o '"traceId"[^,]*' "$STATE_FILE" | head -1)"
        fi
    else
        log "❌ Falha ao iniciar observer (timeout)"
        rm -f "$PID_FILE" "$LOCK_FILE"
        return 1
    fi
}

stop() {
    if ! is_running; then
        log "Observer daemon não está rodando"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    log "Parando observer daemon (PID: $pid)..."
    
    $NODE_PATH "$OBSERVER" end >> "$LOG_FILE" 2>&1
    kill "$pid" 2>/dev/null
    
    sleep 1
    
    rm -f "$PID_FILE" "$LOCK_FILE"
    log "Observer daemon parado"
}

status() {
    if is_running; then
        echo "Observer Daemon v6: RODANDO (PID: $(cat $PID_FILE))"
        $NODE_PATH "$OBSERVER" status 2>/dev/null || echo "Não foi possível obter status"
    else
        echo "Observer Daemon v6: PARADO"
    fi
}

# Auto-restart em loop
auto_restart_loop() {
    log "🔄 Modo auto-restart ativado"
    while true; do
        if is_running; then
            sleep 30
        else
            log "⚠️ Observer parou, reiniciando..."
            start
            sleep 5
        fi
    done
}

case "${1:-start}" in
    start) start ;;
    stop) stop ;;
    status) status ;;
    restart) stop; sleep 2; start ;;
    auto) auto_restart_loop ;;
    *) echo "Uso: $0 {start|stop|status|restart|auto}" ;;
esac
