#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Post-Session Learner
# Aprendizado pós-sessão - registra métricas e insights
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="post-session-learner"
PROJECT_DIR="${KOTHAR_PROJECT_DIR:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)}"
CLAUDE_DIR="${CLAUDE_PROJECT_DIR:-$HOME/.claude}"
LOG_FILE="${KOTHAR_HOOK_LOG:-$CLAUDE_DIR/hooks/hook.log}"
METRICS_FILE="${KOTHAR_METRICS_FILE:-$PROJECT_DIR/core/observabilidade/metrics.json}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Captura métricas da sessão
collect_metrics() {
    local session_id="$1"
    local session_dir="$2"

    log "📊 Coletando métricas da sessão $session_id"

    # Conta mensagens
    local message_count=0
    if [[ -f "$session_dir/messages.jsonl" ]]; then
        message_count=$(wc -l < "$session_dir/messages.jsonl" 2>/dev/null || echo 0)
    fi

    # Conta erros
    local error_count=0
    if [[ -f "$CLAUDE_DIR/hooks/errors.log" ]]; then
        error_count=$(grep -c "^=== " "$CLAUDE_DIR/hooks/errors.log" 2>/dev/null || echo 0)
    fi

    # Tempo de sessão
    local session_duration=""
    if [[ -f "$session_dir/start_time" ]]; then
        local start_time=$(cat "$session_dir/start_time")
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        session_duration="$((duration / 60))m ${duration % 60}s"
    fi

    # Atualiza metrics.json
    local timestamp=$(date -Iseconds)
    local metrics=$(cat "$METRICS_FILE" 2>/dev/null || echo "{}")

    # Adiciona nova entrada
    local new_entry=$(cat <<EOF
{
    "session_id": "$session_id",
    "timestamp": "$timestamp",
    "message_count": $message_count,
    "error_count": $error_count,
    "duration": "$session_duration",
    "agents_used": []
}
EOF
)

    # Simpler approach: append to metrics log
    echo "$new_entry" >> "${METRICS_FILE}.sessions"
    log "✅ Métricas coletadas: $message_count msgs, $error_count erros, duração: $session_duration"
}

# Gera insights
generate_insights() {
    local metrics_file="${METRICS_FILE}.sessions"

    if [[ ! -f "$metrics_file" ]]; then
        return
    fi

    # Calcula estatísticas
    local total_sessions=$(wc -l < "$metrics_file")
    local total_errors=$(grep -o '"error_count":[0-9]*' "$metrics_file" | grep -o '[0-9]*' | awk '{s+=$1} END {print s}')
    local avg_messages=$(grep -o '"message_count":[0-9]*' "$metrics_file" | grep -o '[0-9]*' | awk '{s+=$1; n++} END {print int(s/n)}')

    log "📈 Insights: $total_sessions sessões, $total_errors erros totais, ~$avg_messages msgs/sessão"

    # Alertas
    if [[ "$total_errors" -gt 10 ]]; then
        log "⚠️ ALERTA: Alto número de erros detectados"
    fi
}

# Main
main() {
    local session_id="${CLAUDE_SESSION_ID:-unknown}"
    local session_dir="${CLAUDE_SESSION_DIR:-~/.claude/sessions}"

    session_dir="${session_dir/#\~/$HOME}"

    log "🎓 Iniciando aprendizado pós-sessão"

    collect_metrics "$session_id" "$session_dir"
    generate_insights

    log "✅ Aprendizado concluído"
}

main "$@"
