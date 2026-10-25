#!/bin/bash
# ============================================
# KOTHAR CLI v3.0 - Interface de Comando
# Sistema de Orquestração de Agentes
# ============================================

set -e

KOTHAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

rag_is_ready() {
    local state_file="${KOTHAR_RAG_STATE_FILE:-$KOTHAR_DIR/.rag-index-state.json}"
    local rag_url="${CHROMA_URL:-http://127.0.0.1:8000}"
    local chunks
    chunks=$(grep -o '"indexed_chunks"[[:space:]]*:[[:space:]]*[0-9]*' "$state_file" 2>/dev/null \
        | grep -o '[0-9]*' | tail -1 || true)
    [ "${chunks:-0}" -gt 0 ] &&
        curl -fsS --max-time 2 "$rag_url/api/v2/heartbeat" >/dev/null 2>&1
}

# ============================================
# VERIFICAÇÃO OBRIGATÓRIA
# ============================================
run_pre_activation_check() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🎵 KOTHAR v3.0 — PRE-ACTIVATION CHECK${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""

    ERRORS=0

    # 1. Diretório
    if [ ! -d "$KOTHAR_DIR" ]; then
        echo -e "${RED}❌ Kothar dir não existe: $KOTHAR_DIR${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✅${NC} Kothar dir: OK"
    fi

    # 2. Core files
    for file in "regras/core/core-loop.md" "regras/core/perception.md" "regras/core/gates.md"; do
        if [ ! -f "$KOTHAR_DIR/$file" ]; then
            echo -e "${RED}❌ Arquivo core ausente: $file${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅${NC} Arquivos core: OK"
    fi

    # 3. Skill
    if [ -f "$HOME/.claude/skills/kothar.md" ] || [ -f "$KOTHAR_DIR/.claude/commands/kothar.md" ]; then
        echo -e "${GREEN}✅${NC} Skill /kothar: OK"
    else
        echo -e "${RED}❌ Skill /kothar: FALHOU${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    # 4. Settings
    if [ -f "$HOME/.claude/settings.local.json" ] || [ -f "$HOME/.claude/settings.json" ]; then
        echo -e "${GREEN}✅${NC} Configuração: OK"
    else
        echo -e "${RED}❌ Configuração: FALHOU${NC}"
        ERRORS=$((ERRORS + 1))
    fi

    # 5. RAG indexado e acessível
    if rag_is_ready; then
        echo -e "${GREEN}✅${NC} RAG: ativo e indexado"
    else
        echo -e "${YELLOW}⚠️${NC} RAG: serviço ou índice indisponível"
    fi

    echo ""
    echo -e "${BLUE}─────────────────────────────────────────────────${NC}"

    if [ "$ERRORS" -gt 0 ]; then
        echo -e "${RED}❌ KOTHAR BLOQUEADO — $ERRORS erro(s)${NC}"
        echo ""
        echo -e "Execute: ${CYAN}~/kothar/scripts/kothar-health.sh fix${NC}"
        echo ""
        return 1
    else
        echo -e "${GREEN}✅ KOTHAR PRONTO — Todas verificações passaram${NC}"
        echo ""
        return 0
    fi
}

# ============================================
# COMANDOS
# ============================================

cmd_activate() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║  ██╗     ██╗ ██████╗ ██╗  ██╗████████╗███████╗ ██████╗██╗  ██╗ ║"
    echo "║  ██║     ██║██╔════╝ ██║  ██║╚══██╔══╝██╔════╝██╔════╝██║  ██║ ║"
    echo "║  ██║     ██║██║  ███╗███████║   ██║   █████╗  ██║     ███████║ ║"
    echo "║  ██║     ██║██║   ██║██╔══██║   ██║   ██╔══╝  ██║     ██╔══██║ ║"
    echo "║  ███████╗██║╚██████╔╝██║  ██║   ██║   ███████╗ ╚██████╔╝╚██████╔╝ ║"
    echo "║  ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝  ╚═════╝  ╚═════╝ ║"
    echo "║                                                                  ║"
    echo "║          v3.0 — Sistema de Orquestração de Agentes             ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    # VERIFICAÇÃO
    if ! run_pre_activation_check; then
        return 1
    fi

    if [ -x "$KOTHAR_DIR/scripts/kothar-rag-start.sh" ]; then
        "$KOTHAR_DIR/scripts/kothar-rag-start.sh" || \
            echo -e "${YELLOW}⚠️ RAG não foi iniciado automaticamente${NC}"
    fi

    # Status atual
    local pwd_now=$(pwd)
    local git_branch=$(git branch --show-current 2>/dev/null || echo "N/A")
    local git_status=$(git status --short 2>/dev/null | wc -l | tr -d ' ')

    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${BOLD}📍 Contexto Atual${NC}"
    echo -e "  • Diretório: ${YELLOW}$pwd_now${NC}"
    echo -e "  • Branch: ${CYAN}$git_branch${NC}"
    if [ "$git_status" -gt 0 ]; then
        echo -e "  • Git: ${YELLOW}$git_status mudança(ões) não commitada(s)${NC}"
    else
        echo -e "  • Git: ${GREEN}limpo${NC}"
    fi
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo -e "${CYAN}🧠 CORE LOOP ATIVO:${NC}"
    echo "   SENTIR → PENSAR → VALIDAR → AGIR → APRENDER → RELATAR"
    echo ""

    echo -e "${YELLOW}🎯 Skills Principais:${NC}"
    echo "   • 5 Sensores (Perception)"
    echo "   • 5 Gates de validação"
    echo "   • 6 Checkpoints de aprovação"
    echo "   • Definition of Done (DoD)"
    echo "   • Auto-Validate"
    echo "   • Fluxo completo de debug"
    echo ""

    echo -e "${YELLOW}📋 Comandos Rápidos:${NC}"
    echo "   /kothar status  — Status do sistema"
    echo "   /kothar health  — Verificação completa"
    echo "   /kothar fix     — Corrigir problemas"
    echo ""

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  ✨ Kothar v3.0 pronto!${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}Como posso orquestrar seu trabalho hoje?${NC}"
    echo ""
}

cmd_health() {
    if [ -x "$KOTHAR_DIR/scripts/kothar-health.sh" ]; then
        "$KOTHAR_DIR/scripts/kothar-health.sh" check
    else
        echo -e "${RED}❌ Script de health não encontrado${NC}"
        exit 1
    fi
}

cmd_fix() {
    if [ -x "$KOTHAR_DIR/scripts/kothar-health.sh" ]; then
        "$KOTHAR_DIR/scripts/kothar-health.sh" fix
    else
        echo -e "${RED}❌ Script de health não encontrado${NC}"
        exit 1
    fi
}

cmd_status() {
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🎵 KOTHAR v3.0 STATUS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
    echo ""

    echo -e "${YELLOW}📡 Portas em Uso:${NC}"
    local ports_found=0
    for port in 2785 2786 3000 5432 5433 5440 6380 6381 9090; do
        if lsof -i :$port >/dev/null 2>&1; then
            echo -e "   ${GREEN}✓ :$port${NC}"
            ports_found=1
        fi
    done
    if [ $ports_found -eq 0 ]; then
        echo "   Nenhuma porta em uso"
    fi
    echo ""

    echo -e "${YELLOW}🧠 RAG:${NC}"
    if rag_is_ready; then
        echo -e "   ${GREEN}✓ Ativo e indexado${NC}"
    else
        echo -e "   ${YELLOW}○ Serviço ou índice indisponível${NC}"
    fi
    echo ""

    echo -e "${YELLOW}🧠 Watchdog:${NC}"
    if pgrep -f "kothar-watchdog" >/dev/null 2>&1; then
        echo -e "   ${GREEN}● RODANDO${NC}"
    else
        echo -e "   ${NC}○ PARADO${NC}"
    fi
    echo ""
}

cmd_help() {
    cat << EOF
${BLUE}═══════════════════════════════════════════════════${NC}
${BLUE}  🎵 KOTHAR v3.0 - Help${NC}
${BLUE}═══════════════════════════════════════════════════${NC}

${GREEN}Comandos:${NC}
  /kothar activate   - Ativar Kothar (com verificação)
  /kothar status     - Status do sistema
  /kothar health     - Verificação completa
  /kothar fix        - Verificar e corrigir

${YELLOW}Core Loop:${NC}
  SENTIR → PENSAR → VALIDAR → AGIR → APRENDER → RELATAR

${YELLOW}Regras de Ouro:${NC}
  1. lsof -i :PORTA antes de subir
  2. Ler docs antes de inventar
  3. Hand-off Arquiteto → Engenheiro
  4. 3x erro → PARAR
  5. Aprendizado dinâmico

${BLUE}═══════════════════════════════════════════════════${NC}
EOF
}

# ============================================
# MAIN
# ============================================
case "${1:-activate}" in
    activate|a) cmd_activate ;;
    status|s) cmd_status ;;
    health|h) cmd_health ;;
    fix|f) cmd_fix ;;
    help|--help|-h) cmd_help ;;
    *) cmd_help ;;
esac
