#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 - Script de Restauração do Sistema
# Restaura todos os projetos e configurações
# Ugarit Digital - Bruno Harkin
# ═══════════════════════════════════════════════════════════════════════════════

set -e

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
echo -e "${RED}"
cat << 'EOF'
    _  __     _           __          __
   / |/ /__ _(_))__)___   / /  ___    / /_
  /    // _ `/ / __/ -_) / /__/ -_)  / __/
 /_/|_|\_, / /_/ \__/\__/ /____/\__/  \__/
      /___/
EOF
echo -e "${NC}"
echo -e "${RED}══════════════════════════════════════════════════${NC}"
echo -e "  RESTAURAÇÃO DO SISTEMA KOTHAR"
echo -e "${RED}══════════════════════════════════════════════════${NC}"
echo ""

# Listar backups disponíveis
BACKUP_DIR="$HOME/kothar_backups"
echo_info "Backups disponíveis:"
echo ""
if [ -d "$BACKUP_DIR" ]; then
    ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
else
    echo_warn "Nenhum backup encontrado em $BACKUP_DIR"
fi
echo ""

# Perguntar qual backup restaurar
echo_info "Digite o caminho do backup (ex: ~/kothar_backups/backup_20260825_120000.tar.gz)"
echo -n "Backup: "
read -r BACKUP_FILE

# Expandir caminho
BACKUP_FILE="${BACKUP_FILE/#\~/$HOME}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo_error "Arquivo de backup não encontrado!"
    exit 1
fi

echo_info "Extraindo backup..."
mkdir -p /tmp/kothar_restore
tar -xzf "$BACKUP_FILE" -C /tmp/kothar_restore

# Encontrar o diretório extraído
EXTRACTED_DIR=$(ls /tmp/kothar_restore/ | head -1)
RESTORE_PATH="/tmp/kothar_restore/$EXTRACTED_DIR"

echo_success "Backup extraído"
echo ""

# Listar o que será restaurado
echo_info "Itens no backup:"
echo ""
echo "  📁 Repositórios:"
ls -d "$RESTORE_PATH/repos"/*/ 2>/dev/null | xargs -I {} basename {} | sed 's/^/     - /'
echo ""
echo "  📁 Claude config:"
ls "$RESTORE_PATH/claude/.claude" 2>/dev/null | head -5 | sed 's/^/     - /'
echo ""
echo "  📁 Tema:"
ls "$RESTORE_PATH/theme/.themes" 2>/dev/null | sed 's/^/     - /'
echo ""

# Confirmar restauração
echo_warn "Isso substituirá os arquivos existentes!"
echo_info "Continuar? (yes/nao)"
read -r response

if [ "$response" != "yes" ]; then
    echo_info "Restauração cancelada."
    rm -rf /tmp/kothar_restore
    exit 0
fi

# Restaurar repositórios
echo_info "Restaurando repositórios..."
for repo_dir in "$RESTORE_PATH/repos"/*/; do
    repo_name=$(basename "$repo_dir")
    echo -n "   📦 $repo_name... "

    # Se já existe, fazer backup primeiro
    if [ -d "$HOME/$repo_name" ]; then
        mv "$HOME/$repo_name" "$HOME/${repo_name}.bak.$(date +%s)"
    fi

    cp -r "$repo_dir" "$HOME/$repo_name"
    echo_success "OK"
done

# Restaurar configurações Claude
echo_info "Restaurando configurações Claude..."
if [ -d "$RESTORE_PATH/claude/.claude" ]; then
    cp -r "$RESTORE_PATH/claude/.claude"/* "$HOME/.claude/" 2>/dev/null || true
    echo_success "OK"
fi

# Restaurar tema
echo_info "Restaurando tema..."
if [ -d "$RESTORE_PATH/theme/.themes" ]; then
    cp -r "$RESTORE_PATH/theme/.themes"/* "$HOME/.themes/" 2>/dev/null || true
    echo_success "OK"
fi

# Restaurar SSH config
echo_info "Restaurando configuração SSH..."
if [ -f "$RESTORE_PATH/ssh/config" ]; then
    cp "$RESTORE_PATH/ssh/config" "$HOME/.ssh/config"
    echo_success "OK"
fi

# Restaurar bashrc
echo_info "Restaurando bashrc..."
if [ -f "$RESTORE_PATH/bashrc" ]; then
    cp "$RESTORE_PATH/bashrc" "$HOME/.bashrc"
    echo_success "OK"
fi

# Limpar
rm -rf /tmp/kothar_restore

# Finalização
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ RESTAURAÇÃO CONCLUÍDA!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════${NC}"
echo ""
echo_info "Ações recomendadas:"
echo "  1. Reinicie o terminal"
echo "  2. Execute git pull em cada repositório"
echo "  3. Verifique se as chaves SSH estão configuradas"
echo "  4. Teste com: cd ~/.kothar && git status"
echo ""
