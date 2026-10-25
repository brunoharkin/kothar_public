#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR SECURITY CHECK
# Verifica configurações de segurança do .env
# ═══════════════════════════════════════════════════════════════════════════

VERDE='\033[0;32m'
VERMELHO='\033[0;31m'
AMARELO='\033[1;33m'
AZUL='\033[0;34m'
RESET='\033[0m'
BOLD='\033[1m'

KOTHAR_DIR="$HOME/kothar"
ENV_FILE="$KOTHAR_DIR/.env"

echo ""
echo -e "${BOLD}${AZUL}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${AZUL}║          🔒 KOTHAR SECURITY CHECK                          ║${RESET}"
echo -e "${BOLD}${AZUL}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""

# 1. Verificar se .env existe
echo -e "${BOLD}1. Verificando .env...${RESET}"
if [[ -f "$ENV_FILE" ]]; then
    echo -e "   ✅ $ENV_FILE existe"

    # Verificar se está no gitignore
    if grep -q "^\.env$" "$KOTHAR_DIR/.gitignore" 2>/dev/null; then
        echo -e "   ✅ Protegido no .gitignore"
    else
        echo -e "   ❌ NÃO está no .gitignore!"
    fi
else
    echo -e "   ❌ $ENV_FILE não existe!"
    echo -e "   💡 Execute: cp $KOTHAR_DIR/config/model-router.env.example $ENV_FILE"
    exit 1
fi

echo ""

# 2. Verificar API Keys
echo -e "${BOLD}2. Verificando API Keys...${RESET}"

check_key() {
    local name=$1
    local var=$2

    value=$(grep "^${var}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

    if [[ -z "$value" ]]; then
        echo -e "   ❌ $name: ${AMARELO}NÃO CONFIGURADO${RESET}"
        return 1
    else
        local masked="${value:0:8}...${value: -4}"
        echo -e "   ✅ $name: ${VERDE}$masked${RESET}"
        return 0
    fi
}

keys_ok=0
keys_missing=0

if check_key "Claude (Anthropic)" "ANTHROPIC_API_KEY"; then ((keys_ok++)); else ((keys_missing++)); fi
if check_key "GPT (OpenAI)" "OPENAI_API_KEY"; then ((keys_ok++)); else ((keys_missing++)); fi
if check_key "Gemini (Google)" "GOOGLE_API_KEY"; then ((keys_ok++)); else ((keys_missing++)); fi

echo ""

# 3. Verificar Model Router
echo -e "${BOLD}3. Verificando Model Router...${RESET}"

provider=$(grep "^PREFERRED_PROVIDER=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
if [[ -n "$provider" ]]; then
    echo -e "   ✅ Provider preferido: ${VERDE}$provider${RESET}"
else
    echo -e "   ⚠️ Provider preferido: ${AMARELO}não definido (usará anthropic)${RESET}"
fi

tier1=$(grep "^MODEL_TIER1=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
tier2=$(grep "^MODEL_TIER2=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
tier3=$(grep "^MODEL_TIER3=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

echo -e "   🟢 Tier 1: ${VERDE}${tier1:-claude-haiku}${RESET}"
echo -e "   🟡 Tier 2: ${VERDE}${tier2:-claude-sonnet}${RESET}"
echo -e "   🔴 Tier 3: ${VERDE}${tier3:-claude-opus}${RESET}"

echo ""

# 4. Verificar Gates
echo -e "${BOLD}4. Verificando Gates de Segurança...${RESET}"

check_gate() {
    local name=$1
    local var=$2

    value=$(grep "^${var}=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

    if [[ "$value" == "true" ]]; then
        echo -e "   ✅ $name"
    else
        echo -e "   ❌ $name: ${AMARELO}desabilitado${RESET}"
    fi
}

check_gate "G3 - Validação de Credenciais" "GATE_G3_ENABLED"
check_gate "Scan antes de commit" "GATE_SCAN_ENABLED"
check_gate "Auto-Validate" "AUTO_VALIDATE_ENABLED"
check_gate "Error Tracker" "ERROR_TRACKER_ENABLED"
check_gate "Model Router" "MODEL_ROUTER_ENABLED"

echo ""

# 5. Verificar Database
echo -e "${BOLD}5. Verificando Banco de Dados...${RESET}"

db_host=$(grep "^DB_HOST=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
db_port=$(grep "^DB_PORT=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
db_name=$(grep "^DB_NAME=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)
db_user=$(grep "^DB_USER=" "$ENV_FILE" 2>/dev/null | cut -d'=' -f2-)

if [[ -n "$db_host" ]]; then
    echo -e "   ✅ Host: $db_host:$db_port"
    echo -e "   ✅ Database: $db_name"
    echo -e "   ✅ User: $db_user"
else
    echo -e "   ⚠️ Banco de dados: ${AMARELO}não configurado${RESET}"
fi

echo ""

# 6. Resumo
echo -e "${BOLD}${AZUL}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${AZUL}║                      RESUMO                                 ║${RESET}"
echo -e "${BOLD}${AZUL}╠══════════════════════════════════════════════════════════════╣${RESET}"

if [[ $keys_missing -eq 0 ]]; then
    echo -e "${BOLD}${AZUL}║  🔑 API Keys: ${VERDE}TODAS CONFIGURADAS${AZUL}                           ║${RESET}"
else
    echo -e "${BOLD}${AZUL}║  🔑 API Keys: ${VERMELHO}$keys_missing FALTANDO${AZUL}                          ║${RESET}"
fi

if [[ $keys_ok -eq 3 ]]; then
    echo -e "${BOLD}${AZUL}║  🚀 Model Router: ${VERDE}PRONTO${AZUL}                                   ║${RESET}"
else
    echo -e "${BOLD}${AZUL}║  🚀 Model Router: ${AMARELO}PRECISA CONFIGURAR${AZUL}                        ║${RESET}"
fi

echo -e "${BOLD}${AZUL}╚══════════════════════════════════════════════════════════════╝${RESET}"

echo ""

# Próximos passos
if [[ $keys_missing -gt 0 ]]; then
    echo -e "${AMARELO}⚠️  PRÓXIMOS PASSOS:${RESET}"
    echo ""
    echo -e "   1. Edite o arquivo: ${BOLD}nano $ENV_FILE${RESET}"
    echo -e "   2. Adicione suas API Keys:"
    echo -e "      • ANTHROPIC_API_KEY (Claude)"
    echo -e "      • OPENAI_API_KEY (GPT)"
    echo -e "      • GOOGLE_API_KEY (Gemini)"
    echo -e "   3. Salve o arquivo (Ctrl+O, Enter, Ctrl+X)"
    echo ""
fi

exit 0
