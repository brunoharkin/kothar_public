#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Session Init
# Inicialização de sessão - prepara ambiente e variáveis
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="kothar-session-init"
PROJECT_DIR="${KOTHAR_PROJECT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
CLAUDE_DIR="${CLAUDE_PROJECT_DIR:-$HOME/.claude}"
LOG_FILE="${KOTHAR_HOOK_LOG:-$CLAUDE_DIR/hooks/hook.log}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Verifica estrutura Kothar
verify_structure() {
    local missing_dirs=()

    [[ ! -d "$PROJECT_DIR/core" ]] && missing_dirs+=("core")
    [[ ! -d "$PROJECT_DIR/hooks" ]] && missing_dirs+=("hooks")
    [[ ! -d "$PROJECT_DIR/scripts" ]] && missing_dirs+=("scripts")

    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log "⚠️ Diretórios faltando: ${missing_dirs[*]}"
    else
        log "✅ Estrutura Kothar verificada"
    fi
}

# Verifica ChromaDB
verify_chromadb() {
    if [[ -d "$PROJECT_DIR/chromadb" ]]; then
        local db_size=$(du -sh "$PROJECT_DIR/chromadb" 2>/dev/null | cut -f1)
        log "✅ ChromaDB disponível ($db_size)"
    else
        log "⚠️ ChromaDB não encontrado"
    fi
}

# Verifica portas em uso
check_ports() {
    local ports=(2785 2786 5432 5433 5440 6380 6381)
    local in_use=()

    for port in "${ports[@]}"; do
        if ss -tlnp 2>/dev/null | grep -q ":$port "; then
            in_use+=("$port")
        fi
    done

    if [[ ${#in_use[@]} -gt 0 ]]; then
        log "📡 Portas em uso: ${in_use[*]}"
    fi
}

# Cria arquivo de início de sessão
record_start() {
    local session_dir="${CLAUDE_SESSION_DIR:-~/.claude/sessions}"
    session_dir="${session_dir/#\~/$HOME}"

    mkdir -p "$session_dir"
    date +%s > "$session_dir/start_time"
    log "📝 Sessão iniciada em $(date '+%Y-%m-%d %H:%M:%S')"
}

# Main
main() {
    log "🚀 Kothar v3.0 inicializando..."

    verify_structure
    verify_chromadb
    check_ports
    record_start

    log "✅ Inicialização completa - Kothar pronto"
}

main "$@"
