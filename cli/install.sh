#!/usr/bin/env bash
# =============================================================
#  KOTHAR v4.0 — Instalador do CLI
#  Engenheiro Kothar | Ugarit Digital
# =============================================================
#  Registra o comando `kothar` globalmente no sistema.
#  Uso: bash ~/kothar/cli/install.sh
# =============================================================

set -euo pipefail

KOTHAR_DIR="${HOME}/kothar"
CLI_SCRIPT="${KOTHAR_DIR}/cli/kothar.sh"
INSTALL_LINK="/usr/local/bin/kothar"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}🎵 Instalando Engenheiro Kothar CLI...${RESET}"
echo ""

# 1. Verifica se o script existe
if [ ! -f "${CLI_SCRIPT}" ]; then
    echo "❌ Script não encontrado: ${CLI_SCRIPT}"
    echo "   Certifique-se de que o projeto está em ~/kothar/"
    exit 1
fi

# 2. Torna executável
chmod +x "${CLI_SCRIPT}"

# 3. Cria symlink global
if [ -L "${INSTALL_LINK}" ] || [ -f "${INSTALL_LINK}" ]; then
    sudo rm -f "${INSTALL_LINK}"
fi

sudo ln -s "${CLI_SCRIPT}" "${INSTALL_LINK}"

# 4. Copia .env se não existir
if [ ! -f "${KOTHAR_DIR}/.env" ]; then
    cp "${KOTHAR_DIR}/.env.example" "${KOTHAR_DIR}/.env"
    echo -e "${CYAN}[INFO]${RESET} .env criado — edite as credenciais em ${KOTHAR_DIR}/.env"
fi

# 5. Cria diretório de skills se não existir
mkdir -p "${KOTHAR_DIR}/skills"

echo ""
echo -e "${GREEN}✅ Kothar CLI instalado com sucesso!${RESET}"
echo ""
echo -e "  ${BOLD}Teste agora:${RESET}  kothar --help"
echo -e "  ${BOLD}Inicie stack:${RESET} kothar start"
echo ""
