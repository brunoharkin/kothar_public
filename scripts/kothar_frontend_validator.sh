#!/usr/bin/env bash
#=============================================================
# KOTHAR v4.0 - VALIDADOR DE FRONTEND
# Engenheiro Kothar | Ugarit Digital
#=============================================================
# Valida o frontend após cada alteração
#=============================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FRONTEND_DIR="/home/bruno/Orby.ia/frontend"

echo "=============================================="
echo "🧪 KOTHAR FRONTEND VALIDATOR v4.0"
echo "=============================================="
echo ""

# Verificar se diretório existe
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Diretório frontend não encontrado: $FRONTEND_DIR${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

FAILED=0

# 1. Verificar dependências
echo -e "${CYAN}1. Verificando dependências...${NC}"
if [ -d "node_modules" ]; then
    echo -e "${GREEN}   ✅ Dependências instaladas${NC}"
else
    echo -e "${YELLOW}   ⚠️ node_modules não encontrado, executando npm install...${NC}"
    npm install > /dev/null 2>&1
    echo -e "${GREEN}   ✅ Dependências instaladas${NC}"
fi

# 2. TypeScript
echo ""
echo -e "${CYAN}2. Verificando TypeScript...${NC}"
npx tsc --noEmit > /tmp/ts_check.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ TypeScript OK${NC}"
else
    echo -e "${RED}   ❌ TypeScript com erros:${NC}"
    cat /tmp/ts_check.txt | head -20
    FAILED=1
fi

# 3. Lint
echo ""
echo -e "${CYAN}3. Verificando Lint...${NC}"
npm run lint > /tmp/lint_check.txt 2>&1 || true
if grep -q "error" /tmp/lint_check.txt 2>/dev/null; then
    echo -e "${RED}   ❌ Lint com erros:${NC}"
    grep "error" /tmp/lint_check.txt | head -10
    FAILED=1
else
    echo -e "${GREEN}   ✅ Lint OK${NC}"
fi

# 4. Build
echo ""
echo -e "${CYAN}4. Verificando Build...${NC}"
npm run build > /tmp/build_check.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ Build OK${NC}"
else
    echo -e "${RED}   ❌ Build falhou:${NC}"
    cat /tmp/build_check.txt | tail -30
    FAILED=1
fi

# 5. Segurança
echo ""
echo -e "${CYAN}5. Verificando segurança...${NC}"

# Verificar credenciais expostas
CREDENTIAL_ISSUES=$(grep -r "api[_-]key\|password\|token" \
    --include="*.ts" --include="*.tsx" \
    --exclude-dir=node_modules \
    -l 2>/dev/null | grep -v ".test." | wc -l)

if [ "$CREDENTIAL_ISSUES" -gt 0 ]; then
    echo -e "${RED}   ❌ Possíveis credenciais expostas em $CREDENTIAL_ISSUES arquivo(s)${NC}"
    grep -r "api[_-]key\|password\|token" \
        --include="*.ts" --include="*.tsx" \
        --exclude-dir=node_modules \
        -l 2>/dev/null | grep -v ".test." | head -5
    FAILED=1
else
    echo -e "${GREEN}   ✅ Nenhuma credencial exposta${NC}"
fi

# Verificar localStorage com dados sensíveis
LOCALSTORAGE_ISSUES=$(grep -r "localStorage\.\(set\|get\)Item" \
    --include="*.ts" --include="*.tsx" \
    --exclude-dir=node_modules \
    -l 2>/dev/null | wc -l)

if [ "$LOCALSTORAGE_ISSUES" -gt 0 ]; then
    echo -e "${YELLOW}   ⚠️ $LOCALSTORAGE_ISSUES arquivo(s) usa(m) localStorage${NC}"
    echo -e "${YELLOW}      Verifique se não são dados sensíveis${NC}"
fi

# 6. Verificar importações quebradas
echo ""
echo -e "${CYAN}6. Verificando imports...${NC}"
BROKEN_IMPORTS=$(grep -r "from \"@/" \
    --include="*.ts" --include="*.tsx" \
    --exclude-dir=node_modules \
    -h 2>/dev/null | sed 's/.*from "//;s/".*//' | while read -r imp; do
    # Verificar se o arquivo existe
    if [ ! -f "src/$imp.ts" ] && [ ! -f "src/$imp.tsx" ]; then
        echo "$imp"
    fi
done | wc -l)

if [ "$BROKEN_IMPORTS" -gt 0 ]; then
    echo -e "${RED}   ❌ $BROKEN_IMPORTS import(s) quebrado(s)${NC}"
    FAILED=1
else
    echo -e "${GREEN}   ✅ Imports OK${NC}"
fi

# Resultado final
echo ""
echo "=============================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ FRONTEND VALIDADO COM SUCESSO${NC}"
    echo "=============================================="
    exit 0
else
    echo -e "${RED}❌ FRONTEND COM PROBLEMAS${NC}"
    echo "=============================================="
    echo ""
    echo "Corrija os problemas antes de continuar."
    exit 1
fi
