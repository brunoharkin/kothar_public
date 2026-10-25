#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 - Script de Backup Completo
# Faz backup de todos os projetos e configurações
# Ugarit Digital - Bruno Harkin
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Configurações
BACKUP_DIR="$HOME/kothar_backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DATE}"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Repositórios
REPOS=(
    "kothar"
    "crm-Sophia"
    "novo-site-ugarit"
    "Monitor-Admin"
    "Orby.ia"
    "Cofre"
    "chronodesk"
)

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[✓]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
echo -e "${BLUE}"
cat << 'EOF'
    _  __     _           __          __
   / |/ /__ _(_))__)___   / /  ___    / /_
  /    // _ `/ / __/ -_) / /__/ -_)  / __/
 /_/|_|\_, / /_/ \__/\__/ /____/\__/  \__/
      /___/
EOF
echo -e "${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "  BACKUP COMPLETO DO KOTHAR"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""

# Criar diretório de backup
mkdir -p "$BACKUP_PATH"

echo_info "Backup será salvo em: $BACKUP_PATH"
echo ""

# 1. Backup dos repositórios git
echo_info "1. Fazendo backup dos repositórios git..."
mkdir -p "$BACKUP_PATH/repos"

for repo in "${REPOS[@]}"; do
    REPO_PATH="$HOME/$repo"
    if [ -d "$REPO_PATH/.git" ]; then
        echo -n "   📦 $repo... "
        cp -r "$REPO_PATH" "$BACKUP_PATH/repos/$repo"
        echo_success "OK"
    else
        echo_warn "   ⚠️  $repo não encontrado"
    fi
done

# 2. Backup das configurações Claude
echo_info "2. Fazendo backup das configurações Claude..."
mkdir -p "$BACKUP_PATH/claude"
if [ -d "$HOME/.claude" ]; then
    cp -r "$HOME/.claude" "$BACKUP_PATH/claude/"
    echo_success "Configurações Claude salvas"
else
    echo_warn "Diretório .claude não encontrado"
fi

# 3. Backup do tema
echo_info "3. Fazendo backup do tema..."
mkdir -p "$BACKUP_PATH/theme"
if [ -d "$HOME/.themes" ]; then
    cp -r "$HOME/.themes" "$BACKUP_PATH/theme/"
    echo_success "Tema salvo"
else
    echo_warn "Diretório .themes não encontrado"
fi

# 4. Backup SSH config
echo_info "4. Fazendo backup das configurações SSH..."
mkdir -p "$BACKUP_PATH/ssh"
if [ -f "$HOME/.ssh/config" ]; then
    cp "$HOME/.ssh/config" "$BACKUP_PATH/ssh/config"
    echo_success "Configuração SSH salva"
fi

# 5. Backup bashrc
echo_info "5. Fazendo backup das configurações shell..."
if [ -f "$HOME/.bashrc" ]; then
    cp "$HOME/.bashrc" "$BACKUP_PATH/bashrc"
    echo_success "bashrc salvo"
fi

# 6. Backup docker configs
echo_info "6. Fazendo backup das configurações Docker..."
mkdir -p "$BACKUP_PATH/docker"
if [ -d "$HOME/.docker" ]; then
    cp -r "$HOME/.docker" "$BACKUP_PATH/docker/"
    echo_success "Configurações Docker salvas"
fi

# 7. Compactar backup
echo_info "7. Compactando backup..."
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# 8. Criar log
cat > "$BACKUP_DIR/${BACKUP_NAME}_log.txt" << EOF
KOTHAR BACKUP LOG
=================
Data: $(date)
Host: $(hostname)
Usuário: $(whoami)

REPOSITÓRIOS BACKUP:
$(ls -la "$BACKUP_PATH/repos" 2>/dev/null || echo "Nenhum")

ARQUIVO COMPACTADO: ${BACKUP_NAME}.tar.gz
TAMANHO: $(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)

BACKUP COMPLETO: $BACKUP_DIR/${BACKUP_NAME}.tar.gz
EOF

# Resumo
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ BACKUP CONCLUÍDO!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo_info "Arquivo: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo_info "Tamanho: $(du -h "$BACKUP_DIR/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo_info "Log: $BACKUP_DIR/${BACKUP_NAME}_log.txt"
echo ""
echo_warn "Lista de backups:"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -5
echo ""

# Perguntar se quer restaurar algo
echo_info "Deseja restaurar o backup agora? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo_info "Restauração não implementada neste script."
    echo_info "Para restaurar manualmente:"
    echo "  tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C ~"
fi
