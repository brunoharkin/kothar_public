#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR PRE-ACTIVATION CHECK v3.0
# Roda ANTES de qualquer ação do Kothar
# Se falhar, Kothar não deve se ativar
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

KOTHAR_DIR="$HOME/kothar"
LOG_FILE="$HOME/.claude/projects/-home-bruno-kothar/logs/activation.log"

# Função de log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "══════════════════════════════════════════════════"
log "KOTHAR PRE-ACTIVATION CHECK"
log "══════════════════════════════════════════════════"

# ============================================================
# VERIFICAÇÕES CRÍTICAS
# ============================================================

ERRORS=0

# 1. Diretório principal
if [ ! -d "$KOTHAR_DIR" ]; then
    log "[ERROR] Kothar dir não existe: $KOTHAR_DIR"
    ERRORS=$((ERRORS + 1))
fi

# 2. Arquivos core
for file in "regras/core/core-loop.md" "regras/core/perception.md" "regras/core/gates.md" "regras/core/embedder.py"; do
    if [ ! -f "$KOTHAR_DIR/$file" ]; then
        log "[ERROR] Arquivo core ausente: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# 3. Settings
if [ ! -f "$KOTHAR_DIR/.claude/settings.local.json" ]; then
    log "[ERROR] settings.local.json não existe"
    ERRORS=$((ERRORS + 1))
fi

# 4. Embedder funcional
if ! python3 "$KOTHAR_DIR/regras/core/embedder.py" test >/dev/null 2>&1; then
    log "[ERROR] Embedder não funcional"
    ERRORS=$((ERRORS + 1))
fi

# 5. ChromaDB/SQLite dir
if [ ! -d "$KOTHAR_DIR/chromadb" ]; then
    log "[WARN] ChromaDB dir não existe - criando"
    mkdir -p "$KOTHAR_DIR/chromadb"
fi

# 6. Skill do Kothar
if [ ! -f "$KOTHAR_DIR/.claude/skills/kothar.md" ]; then
    log "[ERROR] Skill /kothar não configurada"
    ERRORS=$((ERRORS + 1))
fi

# ============================================================
# RESULTADO
# ============================================================

log "──────────────────────────────────────────────────"

if [ "$ERRORS" -gt 0 ]; then
    log "[BLOCK] KOTHAR BLOQUEADO - $ERRORS erro(s) crítico(s)"
    log ""
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ KOTHAR BLOQUEADO${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${RED}  $ERRORS erro(s) crítico(s) encontrado(s)${NC}"
    echo ""
    echo -e "  ${YELLOW}Para corrigir, execute:${NC}"
    echo "    ~/kothar/scripts/kothar-health.sh fix"
    echo ""
    exit 1
else
    log "[OK] Todas as verificações passaram"
    log "[OK] Kothar pronto para ativação"
    log "──────────────────────────────────────────────────"
    log ""
    exit 0
fi
