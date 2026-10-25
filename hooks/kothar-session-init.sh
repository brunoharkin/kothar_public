#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Session Init v3.0
# Inicialização de sessão - prepara ambiente e variáveis
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="kothar-session-init"
KOTHAR_DIR="${KOTHAR_PROJECT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)}"
CLAUDE_DIR="${CLAUDE_PROJECT_DIR:-$HOME/.claude}"
LOG_FILE="${KOTHAR_HOOK_LOG:-$CLAUDE_DIR/hooks/hook.log}"
WELCOME_SCRIPT="$KOTHAR_DIR/scripts/kothar-welcome.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Verifica estrutura Kothar
verify_structure() {
    local missing_dirs=()

    [[ ! -d "$KOTHAR_DIR/core" ]] && missing_dirs+=("core")
    [[ ! -d "$KOTHAR_DIR/hooks" ]] && missing_dirs+=("hooks")
    [[ ! -d "$KOTHAR_DIR/scripts" ]] && missing_dirs+=("scripts")
    [[ ! -d "$KOTHAR_DIR/regras" ]] && missing_dirs+=("regras")

    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        log "⚠️ Diretórios faltando: ${missing_dirs[*]}"
    else
        log "✅ Estrutura Kothar verificada"
    fi
}

# Verifica ChromaDB
verify_chromadb() {
    if [[ -d "$KOTHAR_DIR/.chroma-data" ]]; then
        local db_size=$(du -sh "$KOTHAR_DIR/.chroma-data" 2>/dev/null | cut -f1)
        log "✅ ChromaDB disponível ($db_size)"
    else
        log "ℹ️ ChromaDB não configurado"
    fi
}

# Verifica plugins MCP
check_mcp() {
    if [[ -f "$KOTHAR_DIR/regras/mcp.json" ]]; then
        log "✅ Configuração MCP encontrada"
    fi
}

# Verifica portas em uso
check_ports() {
    local in_use=$(ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | grep -oE ':[0-9]+' | sort -u | wc -l)
    if [[ $in_use -gt 0 ]]; then
        log "📡 Portas em uso: $in_use"
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

# Mostra boas-vindas Kothar
show_welcome() {
    if [[ -x "$WELCOME_SCRIPT" ]]; then
        log "🎯 Executando boas-vindas..."
        # O script de boas-vindas é executado pelo hook de forma silenciosa
        # A mensagem completa é mostrada via skill do Kothar
    fi
}

# Main
main() {
    log "🚀 Kothar v3.0 inicializando..."

    verify_structure
    verify_chromadb
    check_mcp
    check_ports
    record_start
    show_welcome

    log "✅ Inicialização completa - Kothar pronto"
}

main "$@"
