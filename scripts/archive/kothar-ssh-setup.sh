#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 - Setup SSH para Projeto
# Configura chave SSH isolada para um projeto
# Ugarit Digital - Bruno Harkin
# ═══════════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[✓]${NC} $1"; }
echo_error() { echo -e "${RED}[✗]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[!]${NC} $1"; }

PROJECT_NAME="$1"

if [ -z "$PROJECT_NAME" ]; then
    echo "Uso: kothar-ssh-setup <nome-do-projeto>"
    echo ""
    echo "Projetos disponíveis:"
    echo "  - kothar"
    echo "  - crm-Sophia"
    echo "  - chronodesk"
    echo "  - Orby.ia"
    echo "  - Cofre"
    echo "  - Monitor-Admin"
    echo "  - novo-site-ugarit"
    exit 1
fi

# Mapear projeto para configurações
case "$PROJECT_NAME" in
    "kothar")
        KEY_NAME="id_ed25519_kothar"
        SSH_HOST="github-kothar"
        ;;
    "crm-Sophia"|"crm-sophia")
        KEY_NAME="id_ed25519_crm_sophia"
        SSH_HOST="github.com-crm-sophia"
        ;;
    "chronodesk")
        KEY_NAME="id_ed25519_chronodesk"
        SSH_HOST="github.com-chronodesk"
        ;;
    "Orby.ia"|"orby.ia"|"Orbytwin")
        KEY_NAME="id_ed25519_orby_ia"
        SSH_HOST="github.com-orby-ia"
        ;;
    "Cofre"|"cofre")
        KEY_NAME="id_ed25519_cofre"
        SSH_HOST="github.com-cofre"
        ;;
        ;;
    "Monitor-Admin"|"monitor-admin")
        KEY_NAME="id_ed25519_monitor_admin"
        SSH_HOST="github.com-monitor-admin"
        ;;
    "novo-site-ugarit")
        KEY_NAME="id_ed25519_novo_site_ugarit"
        SSH_HOST="github.com-novo-site-ugarit"
        ;;
    *)
        echo_error "Projeto desconhecido: $PROJECT_NAME"
        exit 1
        ;;
esac

KEY_PATH="$HOME/.ssh/$KEY_NAME"
KEY_PUB="$KEY_PATH.pub"
CONFIG_PATH="$HOME/.ssh/config"

echo -e "${BLUE}"
echo "══════════════════════════════════════════════════"
echo "  Setup SSH para: $PROJECT_NAME"
echo "══════════════════════════════════════════════════"
echo -e "${NC}"
echo ""

# 1. Verificar se chave já existe
if [ -f "$KEY_PATH" ]; then
    echo_info "Chave já existe: $KEY_NAME"
else
    echo_info "Criando chave SSH: $KEY_NAME"
    ssh-keygen -t ed25519 \
        -C "bruno@ugarit.digital" \
        -f "$KEY_PATH" \
        -N ""
    echo_success "Chave criada!"
fi

# 2. Mostrar chave pública
echo ""
echo_info "Chave pública (adicione no GitHub):"
echo "──────────────────────────────────────────"
cat "$KEY_PUB"
echo "──────────────────────────────────────────"
echo ""
echo_warn "Copie a chave acima e adicione em:"
echo "   GitHub → Settings → SSH and GPG keys → New SSH key"
echo ""

# 3. Atualizar ~/.ssh/config
echo_info "Atualizando ~/.ssh/config..."

SSH_CONFIG_ENTRY="
# $PROJECT_NAME
Host $SSH_HOST
    HostName github.com
    User git
    IdentityFile ~/$KEY_NAME
    IdentitiesOnly yes"

# Verificar se entrada já existe
if grep -q "Host $SSH_HOST" "$CONFIG_PATH" 2>/dev/null; then
    echo_success "Entrada já existe no config"
else
    echo "$SSH_CONFIG_ENTRY" >> "$CONFIG_PATH"
    echo_success "Entrada adicionada ao config"
fi

# 4. Testar conexão
echo ""
echo_info "Testando conexão SSH..."
if ssh -T "git@$SSH_HOST" 2>&1 | grep -q "successfully authenticated"; then
    echo_success "Conexão SSH OK!"
elif ssh -T "git@$SSH_HOST" 2>&1 | grep -q "does not provide shell access"; then
    echo_success "Conexão SSH OK (GitHub não fornece shell)"
else
    echo_warn "Não foi possível testar (adicione a chave no GitHub primeiro)"
fi

# 5. Mostrar comandos úteis
echo ""
echo_success "Setup concluído!"
echo ""
echo_info "Próximos passos:"
echo "  1. Adicione a chave pública no GitHub"
echo "  2. Configure o remote do git:"
echo "     git remote set-url origin git@$SSH_HOST:org/repo.git"
echo "  3. Teste: git push"
