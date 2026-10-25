#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Post-Tool Error Capture
# Captura e registra erros após execução de ferramentas
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="post-tool-error-capture"
LOG_FILE="/home/bruno/.claude/hooks/hook.log"
ERROR_LOG="/home/bruno/.claude/hooks/errors.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Padrões de erro comuns
ERROR_PATTERNS=(
    "Error:"
    "error:"
    "Exception:"
    "exception:"
    "Traceback"
    "FAILED"
    "Failed:"
    "Permission denied"
    "Connection refused"
    "Timeout"
    "not found"
    "No such file"
)

# Extrai e registra erro
capture_error() {
    local tool="$1"
    local status="$2"
    local output="$3"

    if [[ "$status" -ne 0 ]]; then
        log "🔴 ERRO em $tool (exit: $status)"

        # Registra no log de erros
        echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$ERROR_LOG"
        echo "Tool: $tool" >> "$ERROR_LOG"
        echo "Exit: $status" >> "$ERROR_LOG"
        echo "--- Output ---" >> "$ERROR_LOG"
        echo "$output" >> "$ERROR_LOG"
        echo "" >> "$ERROR_LOG"

        # Analisa tipo de erro
        for pattern in "${ERROR_PATTERNS[@]}"; do
            if echo "$output" | grep -qi "$pattern"; then
                local error_type=$(echo "$pattern" | tr '[:upper:]' '[:lower:]' | sed 's/://')
                log "📊 Tipo de erro detectado: $error_type"
            fi
        done
    else
        log "✅ $tool completado com sucesso"
    fi
}

# Main
main() {
    local tool="$1"
    local status="$2"
    local output=""

    # Lê output do stdin se disponível
    if [[ ! -t 0 ]]; then
        output=$(cat)
    fi

    capture_error "$tool" "$status" "$output"
    exit 0
}

main "$@"
