#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR SESSION INITIALIZER v3.0
# Este script é executado automaticamente ao ativar /kothar
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Cores
VERDE='\033[0;32m'
AMARELO='\033[1;33m'
VERMELHO='\033[0;31m'
AZUL='\033[0;34m'
CINZA='\033[0;90m'
RESET='\033[0m'
BOLD='\033[1m'

KOTHAR_DIR="$HOME/kothar"
LOG_FILE="$HOME/.claude/hooks/hook.log"
ERROR_TRACKER="$KOTHAR_DIR/scripts/error-tracker.py"
PROMPT_ENRICHER="$KOTHAR_DIR/scripts/prompt-enricher.py"
CONTEXT_PLANNER="$KOTHAR_DIR/scripts/context-planner.py"
MEMORY_DIR="$HOME/.claude/projects/-home-bruno-kothar/memory"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SESSION-INIT] $1" | tee -a "$LOG_FILE" 2>/dev/null || true
}

echo ""
echo -e "${BOLD}${AZUL}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${AZUL}║         🚀 KOTHAR v3.0 - INICIALIZANDO SESSÃO              ║${RESET}"
echo -e "${BOLD}${AZUL}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# 1. Verificar estrutura Kothar
log "Verificando estrutura Kothar..."
if [[ ! -d "$KOTHAR_DIR" ]]; then
    echo -e "${VERMELHO}❌ Kothar não encontrado em $KOTHAR_DIR${RESET}"
    exit 1
fi
echo -e "${VERDE}✅${RESET} Estrutura Kothar verificada"

# 2. Inicializar Error Tracker
echo ""
echo -e "${BOLD}🔍 Inicializando Error Tracker...${RESET}"
log "Inicializando Error Tracker..."

ERROR_LOG="$MEMORY_DIR/erros/error-tracker.json"
if [[ -f "$ERROR_TRACKER" ]]; then
    chmod +x "$ERROR_TRACKER" 2>/dev/null || true

    # Criar sessão nova
    SESSION_ID=$(date +%Y%m%d-%H%M%S)
    echo -e "${VERDE}✅${RESET} Error Tracker inicializado (Sessão: $SESSION_ID)"
    echo -e "${CINZA}   Erros e acertos serão rastreados automaticamente${RESET}"
    log "Error Tracker pronto - Sessão: $SESSION_ID"
else
    echo -e "${VERMELHO}❌${RESET} Error Tracker não encontrado"
    log "ERRO: Error Tracker não encontrado"
fi

# 4. Verificar ChromaDB
echo ""
echo -e "${BOLD}💾 Verificando RAG (ChromaDB)...${RESET}"
if [[ -d "$KOTHAR_DIR/chromadb" ]]; then
    CHROMADB_SIZE=$(du -sh "$KOTHAR_DIR/chromadb" 2>/dev/null | cut -f1)
    CHROMADB_COLS=$(find "$KOTHAR_DIR/chromadb" -type d -name "*.parquet" 2>/dev/null | wc -l)
    echo -e "${VERDE}✅${RESET} ChromaDB disponível ($CHROMADB_SIZE)"
    echo -e "${CINZA}   Coleções: $CHROMADB_COLS${RESET}"
    log "ChromaDB: $CHROMADB_SIZE, $CHROMADB_COLS coleções"
else
    echo -e "${AMARELO}⚠️${RESET} ChromaDB não encontrado"
    log "AVISO: ChromaDB não encontrado"
fi

# 5. Verificar Hooks
echo ""
echo -e "${BOLD}🪝 Verificando hooks...${RESET}"
chmod +x "$KOTHAR_DIR/hooks"/*.sh 2>/dev/null || true
chmod +x "$KOTHAR_DIR/regras/hooks"/*.sh 2>/dev/null || true
echo -e "${VERDE}✅${RESET} Hooks configurados e executáveis"
log "Hooks verificados"

# 6. Verificar Prompt Enricher
echo ""
echo -e "${BOLD}📝 Verificando Prompt Enricher...${RESET}"
if [[ -f "$PROMPT_ENRICHER" ]]; then
    chmod +x "$PROMPT_ENRICHER" 2>/dev/null || true
    echo -e "${VERDE}✅${RESET} Prompt Enricher disponível"
    log "Prompt Enricher pronto"
else
    echo -e "${AMARELO}⚠️${RESET} Prompt Enricher não encontrado"
fi

# 7. Verificar Context Planner
echo ""
echo -e "${BOLD}📋 Verificando Context Planner...${RESET}"
if [[ -f "$CONTEXT_PLANNER" ]]; then
    chmod +x "$CONTEXT_PLANNER" 2>/dev/null || true
    echo -e "${VERDE}✅${RESET} Context Planner disponível"
    log "Context Planner pronto"
else
    echo -e "${AMARELO}⚠️${RESET} Context Planner não encontrado"
fi

# 8. Carregar diário do dia
echo ""
echo -e "${BOLD}📅 Verificando diário...${RESET}"
DIARIO="$HOME/Cofre/00_Memoria/Diarias/$(date +%Y-%m)/$(date +%Y-%m-%d).md"
if [[ -f "$DIARIO" ]]; then
    echo -e "${VERDE}✅${RESET} Diário do dia encontrado"
    log "Diário: $(basename $DIARIO)"
else
    echo -e "${AMARELO}📝${RESET} Diário do dia não existe (será criado)"
    log "Diário não existe"
fi

# 9. Verificar git status
echo ""
echo -e "${BOLD}📦 Verificando git...${RESET}"
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "detached")
    STATUS=$(git status --short 2>/dev/null | wc -l)
    LAST_COMMIT=$(git log -1 --format='%h - %s' 2>/dev/null || echo "N/A")
    echo -e "${VERDE}✅${RESET} Git: branch=${AZUL}$BRANCH${RESET}, changes=$STATUS"
    echo -e "${CINZA}   Último: $LAST_COMMIT${RESET}"
    log "Git: $BRANCH, $STATUS mudanças"
else
    echo -e "${CINZA}⚠️${RESET} Não é repositório git"
fi

# 10. Verificar portas
echo ""
echo -e "${BOLD}📡 Portas reservadas:${RESET}"
for port in 2785 2786 5432 5433 5440 6380 6381 3000 8000; do
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo -e "   • $port: ${VERMELHO}🔴 EM USO${RESET}"
    else
        echo -e "   • $port: ${VERDE}🟢 LIVRE${RESET}"
    fi
done

# 11. Load Error Tracker Status
echo ""
echo -e "${BOLD}📊 Status Error Tracker:${RESET}"
if [[ -f "$ERROR_TRACKER" ]]; then
    python3 "$ERROR_TRACKER" status 2>/dev/null || echo -e "${CINZA}   Execute 'python3 $ERROR_TRACKER status' para ver detalhes${RESET}"
fi

# Resumo Final
echo ""
echo -e "${BOLD}${AZUL}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${AZUL}║                    SESSÃO INICIALIZADA                     ║${RESET}"
echo -e "${BOLD}${AZUL}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo -e "${BOLD}${AZUL}║                                                              ║${RESET}"
echo -e "${BOLD}${AZUL}║  ${RESET}📍 Local: $(pwd)${AZUL}                            ║${RESET}"
echo -e "${BOLD}${AZUL}║  ${RESET}🕐 Hora: $(date '+%H:%M:%S')${AZUL}                                    ║${RESET}"
echo -e "${BOLD}${AZUL}║  ${RESET}🔍 Error Tracker: ${VERDE}PRONTO${AZUL}                                 ║${RESET}"
echo -e "${BOLD}${AZUL}║  ${RESET}💾 RAG: $([[ -d "$KOTHAR_DIR/chromadb" ]] && echo -e "${VERDE}DISPONÍVEL${AZUL}" || echo -e "${AMARELO}N/A${AZUL}")${AZUL}                                    ║${RESET}"
echo -e "${BOLD}${AZUL}║                                                              ║${RESET}"
echo -e "${BOLD}${AZUL}╠══════════════════════════════════════════════════════════════╣${RESET}"
echo -e "${BOLD}${VERDE}║  ✅ PRONTO PARA TRABALHAR!                                ║${RESET}"
echo -e "${BOLD}${AZUL}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

log "✅ Sessão Kothar inicializada completamente"
exit 0
