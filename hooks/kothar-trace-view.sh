#!/bin/bash
TRACE_DIR="${HOME}/.claude/kothar-trace"
EVENTS_FILE="$TRACE_DIR/events.jsonl"

if [ ! -f "$EVENTS_FILE" ]; then
    echo "Nenhum trace encontrado."
    exit 1
fi

show_stats() {
    echo ""
    echo "📊 ESTATÍSTICAS DA SESSÃO"
    echo "========================="
    python3 "$HOME/kothar/hooks/kothar-trace-recorder.py" stats
}

show_events() {
    local limit=${1:-50}
    echo ""
    echo "📋 ÚLTIMOS $limit EVENTOS"
    echo "========================="
    python3 "$HOME/kothar/hooks/kothar-trace-recorder.py" events "$limit"
}

case "${1:-stats}" in
    stats) show_stats ;;
    events) show_events "${2:-50}" ;;
    *) show_stats; show_events 20 ;;
esac
