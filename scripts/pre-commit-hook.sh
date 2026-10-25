#!/usr/bin/env bash
#=============================================================
# KOTHAR v4.0 - HOOK DE PRE-COMMIT
# Engenheiro Kothar | Ugarit Digital
#=============================================================
# Este hook executa auditoria de segurança antes de cada commit
#=============================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "🔒 KOTHAR PRE-COMMIT HOOK"
echo "=============================================="

# Diretório do projeto
PROJECT_DIR="$(git rev-parse --show-toplevel)"

# 1. Executar auditor de segurança
echo ""
echo "📋 Executando auditoria de segurança..."
echo ""

cd "$PROJECT_DIR"

if ! python3 scripts/kothar_security_audit.py; then
    echo "COMMIT BLOQUEADO: scanner reprovado ou indisponível."
    exit 1
fi

# 2. Verificar TypeScript (se existir)
if [ -f "frontend/package.json" ]; then
    echo ""
    echo "📝 Verificando TypeScript..."
    cd frontend
    npx tsc --noEmit > /dev/null 2>&1 && {
        echo -e "${GREEN}✅ TypeScript OK${NC}"
    } || {
        echo -e "${RED}❌ TypeScript com erros${NC}"
        echo "Corrija os erros antes de commitar."
        exit 1
    }
    cd "$PROJECT_DIR"
fi

# 3. Verificar lint (se existir)
if [ -f "frontend/package.json" ]; then
    echo ""
    echo "📝 Verificando lint..."
    cd frontend
    npm run lint > /dev/null 2>&1 && {
        echo -e "${GREEN}✅ Lint OK${NC}"
    } || {
        echo -e "${YELLOW}⚠️ Lint com warnings${NC}"
    }
    cd "$PROJECT_DIR"
fi

# 4. Verificar .env (não deve estar commitado)
echo ""
echo "📝 Verificando arquivos sensíveis..."
if git diff --cached --name-only | grep -q "\.env$"; then
    echo -e "${RED}❌ ARQUIVO .env NÃO PODE SER COMMITADO${NC}"
    echo "Remova o .env do staging e use .env.example"
    exit 1
fi

echo ""
echo "=============================================="
echo -e "${GREEN}✅ PRÉ-COMMIT APROVADO${NC}"
echo "=============================================="
echo ""
echo "Arquivos prontos para commit."
echo ""

exit 0
