#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 — Boas-Vindas Automática
# Executado no início de cada sessão do Claude Code
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="/home/bruno/kothar"
MEMORY_DIR="$HOME/.claude/projects/-home-bruno-kothar/memory"

# Cores
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Banner do Kothar
show_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}                                                                  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}██╗     ██╗ ██████╗ ██╗  ██╗████████╗███████╗ ██████╗██╗  ██╗${NC}  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}██║     ██║██╔════╝ ██║  ██║╚══██╔══╝██╔════╝██╔════╝██║  ██║${NC}  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}██║     ██║██║  ███╗███████║   ██║   █████╗  ██║     ███████║${NC}  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}██║     ██║██║   ██║██╔══██║   ██║   ██╔══╝  ██║     ██╔══██║${NC}  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}███████╗██║╚██████╔╝██║  ██║   ██║   ███████╗ ╚██████╔╝╚██████╔╝${NC}  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}${CYAN}╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝  ╚═════╝  ╚═════╝${NC}   ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}          ${BOLD}v3.0 — Sistema de Orquestração de Agentes${NC}              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}          ${YELLOW}Ugarit Digital — Bruno Harkin${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                                  ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Status rápido do sistema
show_status() {
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

    # Verificar se há diário do dia
    local today=$(date +%Y-%m-%d)
    local today_md="$HOME/Cofre/00_Memoria/Diarias/$(date +%Y-%m)/$today.md"
    if [ -f "$today_md" ]; then
        echo -e "  • Diário: ${GREEN}$today existe${NC}"
    else
        echo -e "  • Diário: ${YELLOW}não existe ainda${NC}"
    fi

    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Comandos disponíveis
show_commands() {
    echo ""
    echo -e "  ${BOLD}${CYAN}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "  ${BOLD}${CYAN}│  Comandos Rápidos                                              │${NC}"
    echo -e "  ${BOLD}${CYAN}├─────────────────────────────────────────────────────────────┤${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar${NC}             Ativar Kothar completo                  ${CYAN}│${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar status${NC}       Status do sistema                        ${CYAN}│${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar health${NC}       Verificação de saúde                   ${CYAN}│${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar start${NC}        Iniciar gravação                        ${CYAN}│${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar stop${NC}         Parar gravação                         ${CYAN}│${NC}"
    echo -e "  ${CYAN}│  ${GREEN}/kothar ports${NC}        Verificar portas                        ${CYAN}│${NC}"
    echo -e "  ${BOLD}${CYAN}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Core Loop info
show_core_loop() {
    echo -e "  ${BOLD}🧠 Core Loop Ativo:${NC}"
    echo -e "     SENTIR → PENSAR → VALIDAR → AGIR → APRENDER → RELATAR"
    echo ""
}

# Main
main() {
    show_banner
    show_status
    show_core_loop
    show_commands

    echo -e "  ${BOLD}✨ Kothar v3.0 pronto!${NC}"
    echo -e "  ${CYAN}─────────────────────────────────────────────────────────────────${NC}"
    echo ""
}

main "$@"
