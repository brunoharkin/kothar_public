#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR BACKUP CRON
# Script para execução de backup via cron
# Adicione ao crontab: 0 2 * * * /home/bruno/kothar/scripts/backup/backup-cron.sh
# ═══════════════════════════════════════════════════════════════════════════

set -e

BACKUP_LOG="/home/bruno/kothar/logs/backup.log"
mkdir -p "$(dirname "$BACKUP_LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_LOG"
}

log "🚀 Iniciando backup Kothar..."

# Executa backup Python
cd /home/bruno/kothar
.venv/bin/python scripts/backup/kothar_backup.py backup >> "$BACKUP_LOG" 2>&1

# Verifica resultado
if [ $? -eq 0 ]; then
    log "✅ Backup concluído com sucesso"
else
    log "❌ Backup falhou"
    exit 1
fi

# Limpa backups antigos (> 7 dias)
find /home/bruno/.kothar/backups -name "*.tar.gz" -mtime +7 -delete 2>/dev/null
log "🧹 Backups antigos limpos"

log "🏁 Backup finalizado"
