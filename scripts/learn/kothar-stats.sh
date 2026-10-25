#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR STATS
# Mostra estatísticas de uso do Kothar
# ═══════════════════════════════════════════════════════════════════════════

METRICS_FILE="/home/bruno/kothar/.kothar-metrics.json.sessions"
ERRORS_FILE="/home/bruno/.claude/hooks/errors.log"
LOG_FILE="/home/bruno/.claude/hooks/hook.log"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           KOTHAR v3.0 - ESTATÍSTICAS DE USO              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Sessões
if [[ -f "$METRICS_FILE" ]]; then
    total_sessions=$(wc -l < "$METRICS_FILE")
    echo "📊 SESSÕES"
    echo "   Total de sessões: $total_sessions"
    echo ""
fi

# Erros
if [[ -f "$ERRORS_FILE" ]]; then
    total_errors=$(grep -c "^=== " "$ERRORS_FILE" 2>/dev/null || echo 0)
    echo "🔴 ERROS"
    echo "   Total de erros: $total_errors"
    echo ""

    # Últimos 5 erros
    echo "   Últimos erros:"
    tail -20 "$ERRORS_FILE" | grep "^=== " | tail -5 | while read line; do
        echo "   $line"
    done
    echo ""
fi

# Hooks log
if [[ -f "$LOG_FILE" ]]; then
    total_hooks=$(wc -l < "$LOG_FILE")
    echo "🪝 HOOKS"
    echo "   Total de execuções: $total_hooks"
    echo ""
fi

# Backups
backup_dir="/home/bruno/.kothar/backups"
if [[ -d "$backup_dir" ]]; then
    backup_count=$(ls -1 "$backup_dir"/*.tar.gz 2>/dev/null | wc -l)
    backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1)
    echo "💾 BACKUPS"
    echo "   Backups disponíveis: $backup_count"
    echo "   Tamanho total: $backup_size"
    echo ""
fi

# Projetos ativos
echo "📁 PROJETOS"
ls -1 /home/bruno/.claude/projects/ 2>/dev/null | while read project; do
    echo "   • $project"
done
echo ""

# Portas em uso
echo "🔌 PORTAS EM USO"
ss -tlnp 2>/dev/null | grep -E "(5432|5433|5434|5440|6380|6381|2785|2786|6379)" | while read line; do
    echo "   $line"
done
echo ""

echo "══════════════════════════════════════════════════════════════"
