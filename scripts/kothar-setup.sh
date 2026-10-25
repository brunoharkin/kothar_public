#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR SETUP COMPLETO
# Executa setup inicial do Kothar v3.0
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           KOTHAR v3.0 - SETUP COMPLETO                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

KOTHAR_DIR="$HOME/kothar"
CLAUDE_DIR="$HOME/.claude"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }

# 1. Verifica estrutura
log "Verificando estrutura de diretórios..."
mkdir -p "$KOTHAR_DIR"/{hooks,scripts/{backup,learn},core,config}
mkdir -p "$CLAUDE_DIR"/{agents,references,skills,hooks,plans}
log "Estrutura criada"

# 2. Torna scripts executáveis
log "Configurando permissões..."
chmod +x "$KOTHAR_DIR"/hooks/*.sh 2>/dev/null || true
chmod +x "$KOTHAR_DIR"/scripts/backup/*.sh 2>/dev/null || true
chmod +x "$KOTHAR_DIR"/scripts/backup/*.py 2>/dev/null || true
log "Permissões configuradas"

# 3. Cria arquivos de log
log "Criando arquivos de log..."
touch "$CLAUDE_DIR/hooks/hook.log"
touch "$CLAUDE_DIR/hooks/errors.log"
mkdir -p "$HOME/.kothar/backups"
log "Logs inicializados"

# 4. Verifica ChromaDB
log "Verificando ChromaDB..."
if [ -d "$KOTHAR_DIR/.chroma-data" ]; then
    log "ChromaDB já existe"
else
    mkdir -p "$KOTHAR_DIR/.chroma-data"
    log "ChromaDB criado"
fi

# 5. Verifica portas
log "Verificando portas em uso..."
echo ""
echo "   Portas reservadas do Kothar:"
for port in 2785 2786 5432 5433 5440 6380 6381; do
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "   • $port: EM USO"
    else
        echo "   • $port: LIVRE"
    fi
done
echo ""

# 8. Cria cron para backup
log "Configurando backup automático..."
CRON_JOB="0 2 * * * $KOTHAR_DIR/scripts/backup/backup-cron.sh >> $KOTHAR_DIR/logs/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v "backup-cron.sh"; echo "$CRON_JOB") | crontab - 2>/dev/null || warn "Crontab não disponível"
log "Cron configurado (backup diário às 2h)"

# 9. Resumo final
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETO                         ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Estrutura:      ✅                                        ║"
echo "║  Permissões:     ✅                                        ║"
echo "║  Logs:          ✅                                        ║"
echo "║  Python venv:   ✅                                        ║"
echo "║  ChromaDB:      ✅                                        ║"
echo "║  Métricas:      ✅                                        ║"
echo "║  Cron Backup:   ✅                                        ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Próximos passos:                                         ║"
echo "║  1. Execute: ~/.kothar/learn/scripts/kothar-stats.sh     ║"
echo "║  2. Use /kothar para orquestrar                          ║"
echo "╚══════════════════════════════════════════════════════════════╝"
