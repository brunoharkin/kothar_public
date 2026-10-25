#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Pre-Execution Memory Check
# Verifica uso de memória antes de executar comandos Bash
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="pre-execution-memory-check"
LOG_FILE="/home/bruno/.claude/hooks/hook.log"
MEMORY_THRESHOLD_MB=500

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Verifica memória disponível
check_memory() {
    local mem_available=$(free -m | awk 'NR==2 {print $7}')
    echo "$mem_available"
}

# Verifica se é um comando pesado
is_heavy_command() {
    local cmd="$1"
    [[ "$cmd" =~ (docker\s+build|docker\s+run|terraform|ansible|pip\s+install|npm\s+install|yarn|make.*build) ]]
}

# Verifica se é um comando de limpeza
is_cleanup_command() {
    local cmd="$1"
    [[ "$cmd" =~ (rm\s+-rf|dd|shred|format|mkfs) ]]
}

# Verifica se é um comando de rede
is_network_command() {
    local cmd="$1"
    [[ "$cmd" =~ (curl|wget|nc|netcat|ssh\s+root|ssh\s+admin|scp\s+.*:/) ]]
}

# Main
main() {
    local args="$*"

    # Verifica memória
    local mem_available=$(check_memory)

    if [[ "$mem_available" -lt "$MEMORY_THRESHOLD_MB" ]]; then
        log "⚠️ MEMÓRIA BAIXA: ${mem_available}MB disponível (threshold: ${MEMORY_THRESHOLD_MB}MB)"
    fi

    # Verifica comandos perigosos
    if is_cleanup_command "$args"; then
        log "⚠️ COMANDO DE LIMPEZA DETECTADO: $args"
    fi

    if is_network_command "$args"; then
        log "🔍 COMANDO DE REDE DETECTADO: $args"
    fi

    # Verifica comandos pesados
    if is_heavy_command "$args"; then
        log "⏳ COMANDO PESADO DETECTADO: $args"
    fi

    log "✅ Verificação concluída - memória: ${mem_available}MB"
    exit 0
}

main "$@"
