#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Post-Tool Observer v6
# Registra automaticamente cada ferramenta com input/output
# Usa kothar-observer.js v6.2 como backend
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="/home/bruno/kothar"
OBSERVER="$KOTHAR_DIR/scripts/kothar-observer.js"
NODE_PATH="$HOME/.local/bin/node"
STATE_FILE="$KOTHAR_DIR/.observer-state.json"
LOG_FILE="$HOME/.claude/hooks/hook.log"

# Fallback para node
if [[ -x "$NODE_PATH" ]]; then
    NODE="$NODE_PATH"
elif command -v node > /dev/null 2>&1; then
    NODE="node"
else
    NODE="node"  # Tentar PATH padrão
fi

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [kothar-post-tool-observer] $1" >> "$LOG_FILE"
}

# Verifica se há sessão ativa
has_active_session() {
    [[ -f "$STATE_FILE" ]] && grep -q '"traceId"' "$STATE_FILE" 2>/dev/null
}

# Verifica se há arquivo de PID válido
is_observer_running() {
    [[ -f "$KOTHAR_DIR/.observer-daemon.pid" ]] && kill -0 "$(cat "$KOTHAR_DIR/.observer-daemon.pid")" 2>/dev/null
}

# Iniciar observer se necessário
ensure_observer_running() {
    if ! has_active_session || ! is_observer_running; then
        log "Iniciando observer..."
        local session_name="kothar-hook-$(date +%Y%m%d-%H%M%S)"
        
        # Verificar se modo gravação está ativo
        if [[ -f "$KOTHAR_DIR/.recording" ]]; then
            $NODE "$OBSERVER" start "$session_name" >> "$KOTHAR_DIR/logs/observer-daemon.log" 2>&1
            sleep 2
            
            if has_active_session; then
                log "✅ Observer iniciado via hook"
            else
                log "⚠️ Falha ao iniciar observer"
            fi
        else
            log "Modo gravação desativado, ignorando"
            exit 0
        fi
    fi
}

# Sanitizar JSON para linha de comando (evitar problemas com aspas)
sanitize_json() {
    local input="$1"
    # Substituir newlines e tabs, limitar tamanho
    echo "$input" | tr '\n' ' ' | tr '\t' ' ' | sed 's/  */ /g' | cut -c1-10000
}

# Registrar tool no observer
register_tool() {
    local tool="$1"
    local input="$2"
    local output="$3"
    
    $NODE "$OBSERVER" tool "$tool" "$input" "$output" >> "$KOTHAR_DIR/logs/observer.log" 2>&1
    return $?
}

# Main
main() {
    local tool="$1"
    local input="$2"
    local output="$3"
    
    # Verificar modo gravação
    if [[ ! -f "$KOTHAR_DIR/.recording" ]]; then
        exit 0
    fi
    
    # Garantir observer rodando
    ensure_observer_running
    
    # Verificar sessão ativa
    if ! has_active_session; then
        log "⚠️ Sem sessão ativa"
        exit 0
    fi
    
    # Log do tool
    log "Registrando $tool..."
    
    # Sanitizar inputs
    input=$(sanitize_json "$input")
    output=$(sanitize_json "$output")
    
    # Registrar no observer v6
    if register_tool "$tool" "$input" "$output"; then
        log "✅ $tool registrado"
    else
        log "❌ Falha ao registrar $tool"
    fi
}

main "$1" "$2" "$3"
