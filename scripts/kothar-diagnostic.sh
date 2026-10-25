#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR DIAGNOSTIC v3.0
# Diagnóstico completo do sistema Kothar
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

KOTHAR_DIR="$HOME/kothar"
SCORE=0
MAX_SCORE=100

print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  🎵 KOTHAR v3.0 DIAGNOSTIC${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

check() {
    local name="$1"
    local status="$2"
    local points="$3"

    if [ "$status" = "OK" ]; then
        echo -e "   ${GREEN}✅${NC} $name"
        SCORE=$((SCORE + points))
    elif [ "$status" = "WARN" ]; then
        echo -e "   ${YELLOW}⚠️${NC} $name"
        SCORE=$((SCORE + points/2))
    else
        echo -e "   ${RED}❌${NC} $name"
    fi
}

# ============================================================
# 1. ESTRUTURA DE DIRETÓRIOS
# ============================================================
echo -e "${CYAN}📁 Estrutura de Diretórios${NC}"
echo "───────────────────────────────────────────────────────"

[ -d "$KOTHAR_DIR" ] && check "Kothar dir" "OK" 5 || check "Kothar dir" "FAIL" 5
[ -d "$KOTHAR_DIR/scripts" ] && check "Scripts dir" "OK" 5 || check "Scripts dir" "FAIL" 5
[ -d "$KOTHAR_DIR/hooks" ] && check "Hooks dir" "OK" 5 || check "Hooks dir" "FAIL" 5
[ -d "$KOTHAR_DIR/regras" ] && check "Regras dir" "OK" 5 || check "Regras dir" "FAIL" 5
[ -d "$KOTHAR_DIR/.claude" ] && check ".claude dir" "OK" 5 || check ".claude dir" "FAIL" 5
[ -d "$HOME/.envs" ] && check ".envs dir" "OK" 5 || check ".envs dir" "WARN" 5
[ -d "$HOME/kothar/.chroma-data" ] && check "ChromaDB dir" "OK" 5 || check "ChromaDB dir" "WARN" 5

echo ""

# ============================================================
# 2. ARQUIVOS CORE
# ============================================================
echo -e "${CYAN}🧠 Arquivos Core${NC}"
echo "───────────────────────────────────────────────────────"

[ -f "$KOTHAR_DIR/regras/core/core-loop.md" ] && check "Core Loop" "OK" 5 || check "Core Loop" "FAIL" 5
[ -f "$KOTHAR_DIR/regras/core/perception.md" ] && check "Perception" "OK" 5 || check "Perception" "FAIL" 5
[ -f "$KOTHAR_DIR/regras/core/gates.md" ] && check "Gates" "OK" 5 || check "Gates" "FAIL" 5
[ -f "$KOTHAR_DIR/regras/core/reasoning.md" ] && check "Reasoning" "OK" 5 || check "Reasoning" "FAIL" 5
[ -f "$KOTHAR_DIR/regras/core/embedder.py" ] && check "Embedder" "OK" 5 || check "Embedder" "FAIL" 5

echo ""

# ============================================================
# 3. SKILLS
# ============================================================
echo -e "${CYAN}📚 Skills${NC}"
echo "───────────────────────────────────────────────────────"

SKILL_COUNT=$(find "$KOTHAR_DIR/regras/habilidades" -name "*.md" 2>/dev/null | wc -l)
if [ "$SKILL_COUNT" -gt 50 ]; then
    check "Skills ($SKILL_COUNT)" "OK" 10
elif [ "$SKILL_COUNT" -gt 0 ]; then
    check "Skills ($SKILL_COUNT)" "WARN" 5
else
    check "Skills" "FAIL" 10
fi

[ -f "$KOTHAR_DIR/docs/KOTHAR-DEFINITION.md" ] && check "Definição Consolidada" "OK" 5 || check "Definição" "FAIL" 5

echo ""

# ============================================================
# 4. CONFIGURAÇÃO
# ============================================================
echo -e "${CYAN}⚙️ Configuração${NC}"
echo "───────────────────────────────────────────────────────"

if grep -q '"hooks"' "$KOTHAR_DIR/.claude/settings.local.json" 2>/dev/null; then
    HOOK_COUNT=$(grep -c '"name"' "$KOTHAR_DIR/.claude/settings.local.json" 2>/dev/null || echo "0")
    if [ "$HOOK_COUNT" -gt 0 ]; then
        check "Hooks configurados ($HOOK_COUNT)" "OK" 5
    else
        check "Hooks configurados" "WARN" 3
    fi
else
    check "Hooks configurados" "WARN" 3
fi

[ -f "$HOME/.claude/commands/kothar.toml" ] && check "Comandos customizados" "OK" 5 || check "Comandos customizados" "WARN" 5
[ -f "$KOTHAR_DIR/.claude/skills/kothar.md" ] && check "Skill Kothar" "OK" 5 || check "Skill Kothar" "FAIL" 5

echo ""

# ============================================================
# 5. SSH E SEGURANÇA
# ============================================================
echo -e "${CYAN}🔐 Segurança${NC}"
echo "───────────────────────────────────────────────────────"

[ -f "$HOME/.ssh/config" ] && check "SSH config" "OK" 5 || check "SSH config" "FAIL" 5
[ -f "$HOME/.ssh/id_ed25519_kothar" ] && check "Chave SSH Kothar" "OK" 5 || check "Chave SSH Kothar" "FAIL" 5
[ -f "$HOME/.ssh/id_ed25519_crm_sophia" ] && check "Chave SSH CRM" "OK" 5 || check "Chave SSH CRM" "WARN" 3

# Verificar credenciais expostas
CRED_COUNT=$(grep -r "password\s*=\s*['\"][^'\"]{8,}" "$KOTHAR_DIR" --include="*.py" --include="*.js" 2>/dev/null | grep -v ".git" | wc -l)
if [ "$CRED_COUNT" -eq 0 ]; then
    check "Sem credenciais expostas" "OK" 5
else
    check "Credenciais expostas ($CRED_COUNT)" "FAIL" 5
fi

echo ""

# ============================================================
# 6. RAG / MEMÓRIA VETORIAL
# ============================================================
echo -e "${CYAN}🧠 Memória Vetorial${NC}"
echo "───────────────────────────────────────────────────────"

# Verificar se ChromaDB ou SQLite funcionam
if python3 -c "from embedder import list_documents; list_documents()" 2>/dev/null || python3 "$KOTHAR_DIR/regras/core/embedder.py" list >/dev/null 2>&1; then
    DOC_COUNT=$(python3 "$KOTHAR_DIR/regras/core/embedder.py" list 2>/dev/null | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")
    if [ "$DOC_COUNT" -gt 0 ]; then
        check "Vector DB ($DOC_COUNT docs)" "OK" 10
    else
        check "Vector DB (vazio)" "WARN" 5
    fi
else
    check "Vector DB" "WARN" 5
fi

echo ""

# ============================================================
# 7. SCRIPTS
# ============================================================
echo -e "${CYAN}📜 Scripts${NC}"
echo "───────────────────────────────────────────────────────"

[ -f "$KOTHAR_DIR/scripts/kothar-cli.sh" ] && check "Kothar CLI" "OK" 3 || check "Kothar CLI" "FAIL" 3
[ -f "$KOTHAR_DIR/scripts/kothar-watchdog.py" ] && check "Watchdog" "OK" 3 || check "Watchdog" "FAIL" 3
[ -f "$KOTHAR_DIR/scripts/kothar-ssh-verify.sh" ] && check "SSH Verify" "OK" 3 || check "SSH Verify" "FAIL" 3

echo ""

# ============================================================
# 8. PROJETOS
# ============================================================
echo -e "${CYAN}📦 Projetos${NC}"
echo "───────────────────────────────────────────────────────"

[ -d "$HOME/crm-Sophia" ] && check "CRM Sophia" "OK" 5 || check "CRM Sophia" "WARN" 3
[ -d "$HOME/chronodesk" ] && check "ChronoDesk" "OK" 5 || check "ChronoDesk" "WARN" 3
[ -d "$HOME/Orby.ia" ] && check "Orby.ia" "OK" 5 || check "Orby.ia" "WARN" 3
[ -d "$HOME/disparo-em-massa" ] && check "Disparo em Massa" "OK" 5 || check "Disparo em Massa" "WARN" 3

echo ""

# ============================================================
# RESUMO
# ============================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📊 RESULTADO${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

PERCENT=$((SCORE * 100 / MAX_SCORE))

if [ "$PERCENT" -ge 90 ]; then
    STATUS="${GREEN}EXCELENTE${NC}"
elif [ "$PERCENT" -ge 70 ]; then
    STATUS="${GREEN}FUNCIONAL${NC}"
elif [ "$PERCENT" -ge 50 ]; then
    STATUS="${YELLOW}PARCIAL${NC}"
else
    STATUS="${RED}CRÍTICO${NC}"
fi

echo -e "   Score: ${SCORE}/${MAX_SCORE} (${PERCENT}%)"
echo -e "   Status: $STATUS"
echo ""

if [ "$PERCENT" -lt 90 ]; then
    echo -e "${YELLOW}⚠️  Ações recomendadas:${NC}"
    echo ""

    if [ ! -d "$HOME/.envs" ]; then
        echo "   • Criar diretório ~/.envs para credenciais"
    fi

    if [ ! -f "$HOME/.ssh/id_ed25519_orby_ia" ]; then
        echo "   • Criar chave SSH para Orby.ia"
    fi

    if [ ! -f "$HOME/.ssh/id_ed25519_cofre" ]; then
        echo "   • Criar chave SSH para Cofre"
    fi

    DOC_COUNT=$(python3 "$KOTHAR_DIR/regras/core/embedder.py" list 2>/dev/null | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")
    if [ "$DOC_COUNT" -lt 5 ]; then
        echo "   • Popular entity knowledge: python3 scripts/populate-entity-knowledge.py"
    fi

    echo ""
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
