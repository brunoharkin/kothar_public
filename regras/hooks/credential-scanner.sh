#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Scanner de Credenciais
# Escaneia todos os arquivos de código em busca de credenciais hardcoded
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="credential-scanner"
LOG_FILE="/home/bruno/.claude/hooks/violations.log"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" | tee -a "$LOG_FILE"
}

# Padrões críticos
CRITICAL_PATTERNS=(
    "sk-[a-zA-Z0-9_-]{20,}"           # Anthropic/OpenAI keys
    "AKIA[A-Z0-9]{16}"                 # AWS keys
    "ghp_[a-zA-Z0-9]{36}"             # GitHub tokens
    "glpat-[a-zA-Z0-9_-]{20}"         # GitLab tokens
)

# Padrões de variáveis hardcoded
HARDCODED_PATTERNS=(
    "api_key\s*[=:]\s*['\"][a-zA-Z0-9_-]{20,}"
    "secret_key\s*[=:]\s*['\"][a-zA-Z0-9_-]{20,}"
    "password\s*[=:]\s*['\"][^'\"]{8,}"
    "token\s*[=:]\s*['\"][a-zA-Z0-9_-]{20,}"
)

# Extensões a escanear
EXTENSIONS="py|js|ts|tsx|go|java|rb|php|cpp|c|h"

# Escaneia um diretório
scan_directory() {
    local dir="$1"
    local violations=0

    log "🔍 Escaneando: $dir"

    # Escaneia arquivos de código
    while IFS= read -r -d '' file; do
        # Pula node_modules, .venv, etc
        if [[ "$file" =~ (node_modules|\.venv|__pycache__|\.git|vendor) ]]; then
            continue
        fi

        # Verifica cada padrão crítico
        for pattern in "${CRITICAL_PATTERNS[@]}"; do
            if grep -E "$pattern" "$file" > /dev/null 2>&1; then
                local matched=$(grep -oE "$pattern" "$file" | head -1)
                log "🔴 CRÍTICO: API Key detectada em: $file"
                log "   Valor: ${matched:0:15}... (MASCARADO)"
                ((violations++))
            fi
        done

        # Verifica padrões de hardcoded
        for pattern in "${HARDCODED_PATTERNS[@]}"; do
            if grep -E "$pattern" "$file" 2>/dev/null | grep -vE "https?://|os\.getenv|process\.env" > /dev/null 2>&1; then
                log "🔴 CRÍTICO: Credencial hardcoded em: $file"
                log "   Padrão: $pattern"
                ((violations++))
            fi
        done
    done < <(find "$dir" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.tsx" -o -name "*.go" -o -name "*.java" -o -name "*.rb" \) -print0 2>/dev/null)

    return $violations
}

# Main
main() {
    local target_dir="${1:-$PWD}"

    log "═══════════════════════════════════════════════════════════════"
    log "  CREDENTIAL SCANNER - $(date '+%Y-%m-%d %H:%M:%S')"
    log "  Alvo: $target_dir"
    log "═══════════════════════════════════════════════════════════════"

    local total_violations=0
    scan_directory "$target_dir"
    total_violations=$?

    log ""
    if [[ $total_violations -gt 0 ]]; then
        log "⚠️  TOTAL: $total_violations credenciais hardcoded detectadas!"
        log "   AÇÃO: Remova credenciais → coloque no .env"
        exit 1
    else
        log "✅ Nenhuma credencial hardcoded detectada"
        exit 0
    fi
}

main "$@"
