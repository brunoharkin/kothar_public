#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR SSH VERIFY v3.0
# Verifica isolamento de chaves SSH por projeto
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  🔐 KOTHAR SSH VERIFY v3.0${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Projetos esperados
PROJECTS=(
    "kothar"
    "crm_sophia"
    "chronodesk"
    "orby_ia"
    "cofre"
)

# Contadores
total=0
ok=0

echo -e "${YELLOW}Verificando chaves SSH por projeto...${NC}"
echo ""

for project in "${PROJECTS[@]}"; do
    total=$((total + 1))
    key_file="$HOME/.ssh/id_ed25519_$project"

    if [ -f "$key_file" ]; then
        echo -e "${GREEN}✅ $project${NC}: $(basename $key_file) existe"
        ok=$((ok + 1))
    else
        echo -e "${RED}❌ $project${NC}: chave não encontrada"
    fi
done

echo ""
echo -e "${YELLOW}Resultado: $ok/$total projetos com chave SSH${NC}"
echo ""

# Verificar ~/.ssh/config
echo -e "${YELLOW}Verificando ~/.ssh/config...${NC}"
if [ -f "$HOME/.ssh/config" ]; then
    host_count=$(grep -c "^Host " "$HOME/.ssh/config" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ ~/.ssh/config existe ($host_count hosts)${NC}"

    for project in "${PROJECTS[@]}"; do
        host_name="github-$project"
        if grep -q "Host $host_name" "$HOME/.ssh/config" 2>/dev/null; then
            echo -e "   ${GREEN}✓${NC} Host: $host_name"
        fi
    done
else
    echo -e "${RED}❌ ~/.ssh/config não existe${NC}"
fi

echo ""

# Verificar .envs
echo -e "${YELLOW}Verificando ~/.envs/...${NC}"
if [ -d "$HOME/.envs" ]; then
    env_count=$(ls -1 "$HOME/.envs"/*.env 2>/dev/null | wc -l)
    echo -e "${GREEN}✅ Diretório ~/.envs existe ($env_count arquivos)${NC}"
else
    echo -e "${RED}❌ Diretório ~/.envs não existe${NC}"
    echo -e "   ${YELLOW}→ Criar com: mkdir -p ~/.envs && chmod 700 ~/.envs${NC}"
fi

echo ""

# Verificar ChromaDB
echo -e "${YELLOW}Verificando ChromaDB...${NC}"
CHROMADB_PATH="$HOME/kothar/chromadb"
if [ -d "$CHROMADB_PATH" ]; then
    db_size=$(du -sh "$CHROMADB_PATH" 2>/dev/null | cut -f1)
    echo -e "${GREEN}✅ ChromaDB: $CHROMADB_PATH ($db_size)${NC}"
else
    echo -e "${RED}❌ ChromaDB não existe${NC}"
fi

echo ""

# Resumo
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📊 RESUMO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  🔑 Chaves SSH:    $ok/$total"
echo -e "  📁 ~/.ssh/config: $([ -f $HOME/.ssh/config ] && echo '✅' || echo '❌')"
echo -e "  🔐 ~/.envs/:      $([ -d $HOME/.envs ] && echo '✅' || echo '❌')"
echo -e "  🧠 ChromaDB:      $([ -d $CHROMADB_PATH ] && echo '✅' || echo '❌')"
echo ""

# Verificar credenciais expostas
echo -e "${YELLOW}Verificando credenciais expostas...${NC}"
cred_count=0
if [ -d "$HOME/kothar" ]; then
    cred_count=$(grep -r "password\s*=\s*['\"][^'\"]{8,}" "$HOME/kothar" --include="*.py" --include="*.js" --include="*.ts" 2>/dev/null | grep -v ".git" | wc -l)
fi

if [ "$cred_count" -gt 0 ]; then
    echo -e "   ${RED}⚠️  $cred_count possíveis credenciais encontradas${NC}"
else
    echo -e "   ${GREEN}✓ Nenhuma credencial hardcoded encontrada${NC}"
fi

echo ""
