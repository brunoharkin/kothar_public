#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Pre-Plan Detection
# Detecta padrões problemáticos antes de Edit/Write
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="pre-plan-detection"
LOG_FILE="/home/bruno/.claude/hooks/hook.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Padrões perigosos
DANGEROUS_PATTERNS=(
    "password\s*=\s*['\"][^'\"]{8,}"
    "api_key\s*=\s*['\"][^'\"]{8,}"
    "secret\s*=\s*['\"][^'\"]{8,}"
    "token\s*=\s*['\"][^'\"]{8,}"
    "DEBUG\s*=\s*True"
    "console\.log"
    "except\s*:"
    "f\".*SELECT.*\{.*\}.*\""
)

# Verifica conteúdo
check_content() {
    local content="$1"
    local file="$2"

    for pattern in "${DANGEROUS_PATTERNS[@]}"; do
        if echo "$content" | grep -qE "$pattern"; then
            log "⚠️ PADRÃO PROBLEMÁTICO ENCONTRADO: $pattern em $file"

            # Verifica se é arquivo de produção
            if [[ "$file" =~ (production|prod|dist|build|main\.py|server\.py) ]]; then
                log "🔴 ERRO CRÍTICO: Padrão perigoso em arquivo de produção"
                echo "ERROR: Padrão perigoso detectado em arquivo de produção"
                exit 1
            fi
        fi
    done

    # Verifica credenciais mock
    if echo "$content" | grep -qE "(sk-[a-zA-Z0-9]{32,}|AKIA[A-Z0-9]{16})"; then
        log "🔴 ERRO: Credencial real parece estar no código"
        echo "ERROR: Possível credencial real detectada"
        exit 1
    fi

    return 0
}

# Main
main() {
    local action="$1"  # Edit ou Write
    local file="$2"
    local content=""

    # Lê do stdin se disponível
    if [[ ! -t 0 ]]; then
        content=$(cat)
    fi

    if [[ -n "$content" ]]; then
        check_content "$content" "$file"
    fi

    log "✅ Verificação concluída para $file"
    exit 0
}

main "$@"
