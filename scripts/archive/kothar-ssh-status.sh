#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# KOTHAR v3.0 - Status SSH de Todos os Projetos
# Mostra o status de isolamento SSH de cada projeto
# Ugarit Digital - Bruno Harkin
# ═══════════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "══════════════════════════════════════════════════════════════════════════════"
echo "  KOTHAR v3.0 - Status de Isolamento SSH por Projeto"
echo "══════════════════════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo ""

# Projetos registrados
declare -A PROJECTS=(
    ["kothar"]="id_ed25519_kothar|github-kothar"
    ["crm-Sophia"]="id_ed25519_crm_sophia|github.com-crm-sophia"
    ["chronodesk"]="id_ed25519_chronodesk|github.com-chronodesk"
    ["Orby.ia"]="id_ed25519_orby_ia|github.com-orby-ia"
    ["Cofre"]="id_ed25519_cofre|github.com-cofre"
    ["Monitor-Admin"]="id_ed25519_monitor_admin|github.com-monitor-admin"
    ["novo-site-ugarit"]="id_ed25519_novo_site_ugarit|github.com-novo-site-ugarit"
)

total=0
ok=0

for project in "${!PROJECTS[@]}"; do
    IFS='|' read -r key_name ssh_host <<< "${PROJECTS[$project]}"
    total=$((total + 1))

    key_path="$HOME/.ssh/$key_name"

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📁 $project${NC}"
    echo "   Chave: $key_name"
    echo "   Host:  $ssh_host"

    # Verificar chave
    if [ -f "$key_path" ]; then
        # Verificar se está no config
        if grep -q "Host $ssh_host" "$HOME/.ssh/config" 2>/dev/null; then
            echo -e "   ${GREEN}✅ Chave SSH: OK${NC}"
            ok=$((ok + 1))
        else
            echo -e "   ${YELLOW}⚠️  Chave existe mas NÃO está no config${NC}"
        fi

        # Mostrar fingerprint
        fingerprint=$(ssh-keygen -lf "$key_path" 2>/dev/null | awk '{print $2}')
        echo "   Fingerprint: $fingerprint"
    else
        echo -e "   ${RED}❌ Chave SSH: NÃO ENCONTRADA${NC}"
    fi

    # Verificar se projeto existe localmente
    project_path="$HOME/$project"
    if [ -d "$project_path/.git" ]; then
        cd "$project_path"
        remote=$(git remote get-url origin 2>/dev/null | head -1)
        if echo "$remote" | grep -q "$ssh_host"; then
            echo -e "   ${GREEN}✅ Remote git: OK${NC}"
        elif echo "$remote" | grep -q "github.com"; then
            echo -e "   ${YELLOW}⚠️  Remote git: OK (sem Host específico)${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Remote: $remote${NC}"
        fi
    else
        echo -e "   ${YELLOW}⚠️  Projeto não encontrado localmente${NC}"
    fi

    echo ""
done

# Resumo
echo -e "${BLUE}══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}RESUMO:${NC} $ok/$total projetos com chave SSH configurada"
echo ""

if [ $ok -eq $total ]; then
    echo -e "${GREEN}✅ Todos os projetos têm chaves SSH configuradas${NC}"
else
    echo -e "${YELLOW}⚠️  $((total - ok)) projeto(s) precisam de configuração SSH${NC}"
    echo ""
    echo "Para configurar um projeto:"
    echo "  ~/.kothar/scripts/kothar-ssh-setup.sh <nome-do-projeto>"
fi

echo ""
echo "───────────────────────────────────────────────────────────────────────────────"
echo "Para adicionar nova chave no GitHub:"
echo "  1. cat ~/.ssh/NOME_DA_CHAVE.pub"
echo "  2. Cole em GitHub → Settings → SSH and GPG keys"
echo "───────────────────────────────────────────────────────────────────────────────"
