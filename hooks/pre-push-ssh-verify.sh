#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 - Hook de Verificação SSH e Credenciais
# Executado ANTES de qualquer git push
# Ugarit Digital - Bruno Harkin
# ═══════════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0

echo_info() { echo -e "${BLUE}[CHECK]${NC} $1"; }
echo_success() { echo -e "${GREEN}[✓]${NC} $1"; }
echo_error() { echo -e "${RED}[✗]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# Banner
echo -e "${BLUE}"
echo "══════════════════════════════════════════════════"
echo "  KOTHAR - Verificação de Segurança SSH"
echo "══════════════════════════════════════════════════"
echo -e "${NC}"
echo ""

# 1. Detectar projeto atual
PROJECT_NAME=$(basename "$PWD")
PROJECT_ROOT="$PWD"
echo_info "Projeto: $PROJECT_NAME"
echo_info "Raiz: $PROJECT_ROOT"
echo ""

# 2. Mapear projeto para chave SSH
case "$PROJECT_NAME" in
    "kothar")
        EXPECTED_KEY="id_ed25519_kothar"
        EXPECTED_HOST="github-kothar"
        ;;
    "crm-Sophia"|"crm-sophia")
        EXPECTED_KEY="id_ed25519_crm_sophia"
        EXPECTED_HOST="github.com-crm-sophia"
        ;;
    "chronodesk")
        EXPECTED_KEY="id_ed25519_chronodesk"
        EXPECTED_HOST="github.com-chronodesk"
        ;;
    "Orby.ia"|"orby.ia"|"Orbytwin")
        EXPECTED_KEY="id_ed25519_orby_ia"
        EXPECTED_HOST="github.com-orby-ia"
        ;;
    "Cofre"|"cofre")
        EXPECTED_KEY="id_ed25519_cofre"
        EXPECTED_HOST="github.com-cofre"
        ;;
        ;;
    "Monitor-Admin"|"monitor-admin")
        EXPECTED_KEY="id_ed25519_monitor_admin"
        EXPECTED_HOST="github.com-monitor-admin"
        ;;
    "novo-site-ugarit"|"novo-site-ugarit")
        EXPECTED_KEY="id_ed25519_novo_site_ugarit"
        EXPECTED_HOST="github.com-novo-site-ugarit"
        ;;
    *)
        echo_warn "Projeto não registrado: $PROJECT_NAME"
        echo_warn "Verificação de chave SSH pulada"
        exit 0
        ;;
esac

# 3. Verificar se chave SSH existe
echo_info "Verificando chave SSH para $PROJECT_NAME..."
KEY_PATH="$HOME/.ssh/$EXPECTED_KEY"

if [ -f "$KEY_PATH" ]; then
    echo_success "Chave SSH encontrada: $EXPECTED_KEY"
else
    echo_error "CHAVE SSH NÃO ENCONTRADA: $EXPECTED_KEY"
    echo_error "Crie com: ssh-keygen -t ed25519 -C 'bruno@ugarit.digital' -f ~/.ssh/$EXPECTED_KEY -N ''"
    ERRORS=$((ERRORS + 1))
fi

# 4. Verificar remote do git
echo ""
echo_info "Verificando remote do git..."

if git remote -v | grep -q "$EXPECTED_HOST"; then
    echo_success "Remote usa Host correto: $EXPECTED_HOST"
else
    ACTUAL_REMOTE=$(git remote get-url origin 2>/dev/null || echo "não configurado")
    echo_error "Remote INCORRETO!"
    echo_error "  Esperado: contém '$EXPECTED_HOST'"
    echo_error "  Atual: $ACTUAL_REMOTE"
    echo_warn "Corrija com: git remote set-url origin git@$EXPECTED_HOST:org/repo.git"
    ERRORS=$((ERRORS + 1))
fi

# 5. Verificar .gitignore
echo ""
echo_info "Verificando .gitignore..."

if [ -f ".gitignore" ]; then
    if grep -q "\.env" .gitignore; then
        echo_success ".env está no .gitignore"
    else
        echo_error ".env NÃO está no .gitignore!"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo_warn ".gitignore não encontrado"
fi

# 6. Scan de credenciais
echo ""
echo_info "Scan de credenciais no código..."

CREDENTIAL_PATTERNS="(sk_[a-zA-Z0-9]{20,}|pk_[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9a-zA-Z]+|api[_-]?key|secret|password|passwd)"

FOUND_CREDENTIALS=$(grep -rEn "$CREDENTIAL_PATTERNS" \
    --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" \
    --include="*.py" --include="*.env" --include="*.yml" --include="*.yaml" \
    . 2>/dev/null | grep -v "node_modules" | grep -v ".git" || true)

if [ -n "$FOUND_CREDENTIALS" ]; then
    echo_error "CREDENCIAIS DETECTADAS NO CÓDIGO!"
    echo "$FOUND_CREDENTIALS"
    ERRORS=$((ERRORS + 1))
else
    echo_success "Nenhuma credencial encontrada no código"
fi

# 7. Resumo
echo ""
echo "══════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}  ✅ VERIFICAÇÃO APROVADA${NC}"
    echo "══════════════════════════════════════════════════"
    exit 0
else
    echo -e "${RED}  ❌ $ERRORS ERRO(S) ENCONTRADO(S)${NC}"
    echo "══════════════════════════════════════════════════"
    echo ""
    echo "Corrija os erros antes de fazer push!"
    exit 1
fi
