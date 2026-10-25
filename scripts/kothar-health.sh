#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HEALTH CHECK v3.0
# Verificação completa e auto-correção do sistema
# ═══════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

KOTHAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -n "${KOTHAR_PYTHON:-}" ] && [ -x "${KOTHAR_PYTHON}" ]; then
    KOTHAR_PYTHON_BIN="${KOTHAR_PYTHON}"
elif [ -x "$KOTHAR_DIR/.venv/bin/python" ]; then
    KOTHAR_PYTHON_BIN="$KOTHAR_DIR/.venv/bin/python"
else
    KOTHAR_PYTHON_BIN="$(command -v python3 || true)"
fi
CLAUDE_SETTINGS="$KOTHAR_DIR/.claude/settings.local.json"
if [ ! -f "$CLAUDE_SETTINGS" ] && [ -f "$HOME/.claude/settings.json" ]; then
    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
fi
FIX_MODE="${1:-check}"  # check, fix, force-fix

# Contadores
PASSED=0
FAILED=0
WARNINGS=0
FIXED=0
SKIPPED=0

# ============================================================
# FUNÇÕES DE OUTPUT
# ============================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
    PASSED=$((PASSED + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED=$((FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_fix() {
    echo -e "${CYAN}[FIX]${NC} $1"
    FIXED=$((FIXED + 1))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    SKIPPED=$((SKIPPED + 1))
}

separator() {
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================
# VERIFICAÇÕES
# ============================================================

check_dir() {
    local dir="$1"
    local name="$2"

    if [ -d "$dir" ]; then
        log_ok "$name: $dir"
        return 0
    else
        if [ "$FIX_MODE" = "fix" ] || [ "$FIX_MODE" = "force-fix" ]; then
            log_fix "Criando $name: $dir"
            mkdir -p "$dir"
            return 0
        else
            log_fail "$name: $dir (não existe)"
            return 1
        fi
    fi
}

check_file() {
    local file="$1"
    local name="$2"

    if [ -f "$file" ]; then
        log_ok "$name"
        return 0
    else
        if [ "$FIX_MODE" = "fix" ] || [ "$FIX_MODE" = "force-fix" ]; then
            log_warn "$name: $file (não existe)"
        else
            log_fail "$name: $file (não existe)"
        fi
        return 1
    fi
}

check_permission() {
    local permission="$1"
    local name="$2"

    if grep -q "\"$permission\"" "$CLAUDE_SETTINGS" 2>/dev/null; then
        log_ok "Permission: $name"
        return 0
    else
        log_fail "Permission: $name (ausente)"
        return 1
    fi
}

# ============================================================
# VERIFICAÇÃO COMPLETA
# ============================================================

run_health_check() {
    separator
    echo -e "${BOLD}  🎵 KOTHAR v3.0 — HEALTH CHECK${NC}"
    separator
    echo ""
    echo -e "Mode: ${CYAN}$FIX_MODE${NC}"
    echo ""

    # ============================================================
    # 1. ESTRUTURA DE DIRETÓRIOS
    # ============================================================
    echo -e "${BOLD}📁 Estrutura de Diretórios${NC}"
    echo "─────────────────────────────────────────────────────────"

    check_dir "$KOTHAR_DIR" "Kothar Dir"
    check_dir "$KOTHAR_DIR/scripts" "Scripts"
    check_dir "$KOTHAR_DIR/hooks" "Hooks"
    check_dir "$KOTHAR_DIR/.agents/skills" "Skills"
    check_dir "$KOTHAR_DIR/.claude" ".claude"
    check_dir "$KOTHAR_DIR/.chroma-data" "ChromaDB"
    if [ -d "$HOME/.envs" ]; then
        log_ok ".envs: $HOME/.envs"
    else
        log_info ".envs: opcional e não configurado"
    fi
    if [ -d "$HOME/.claude/projects/-home-bruno-harkin-kothar/memory" ]; then
        log_ok "Memory: disponível"
    else
        log_info "Memory: opcional e não configurada"
    fi

    echo ""

    # ============================================================
    # 2. ARQUIVOS CORE (CRÍTICOS)
    # ============================================================
    echo -e "${BOLD}🧠 Arquivos Core (Críticos)${NC}"
    echo "─────────────────────────────────────────────────────────"

    check_file "$KOTHAR_DIR/.agents/skills/kothar/SKILL.md" "Skill Kothar"
    check_file "$KOTHAR_DIR/.agents/skills/kothar-rag/SKILL.md" "Skill RAG"
    check_file "$KOTHAR_DIR/.agents/skills/kothar-seguranca/SKILL.md" "Skill Segurança"
    check_file "$KOTHAR_DIR/.agents/skills/kothar-workflow/SKILL.md" "Skill Workflow"
    check_file "$KOTHAR_DIR/backend/memory/semantic/context_embedder.py" "Embedder"
    check_file "$KOTHAR_DIR/README.md" "Definição"

    echo ""

    # ============================================================
    # 3. SKILLS (MÍNIMO 20)
    # ============================================================
    echo -e "${BOLD}📚 Skills${NC}"
    echo "─────────────────────────────────────────────────────────"

    SKILL_COUNT=$(find "$KOTHAR_DIR/.agents/skills" -name "SKILL.md" 2>/dev/null | wc -l)

    if [ "$SKILL_COUNT" -ge 20 ]; then
        log_ok "Skills: $SKILL_COUNT encontradas"
    elif [ "$SKILL_COUNT" -gt 0 ]; then
        log_warn "Skills: $SKILL_COUNT (mínimo recomendado: 20)"
    else
        log_fail "Skills: nenhuma encontrada"
    fi

    # Skills críticas
    for skill in rag-engine swarm-router memory-nudge context-handoff-automatico; do
        if [ -f "$KOTHAR_DIR/.agents/skills/$skill/SKILL.md" ]; then
            log_ok "Skill: $skill"
        else
            log_warn "Skill: $skill (ausente)"
        fi
    done

    echo ""

    # ============================================================
    # 4. CONFIGURAÇÃO DO CLAUDE CODE
    # ============================================================
    echo -e "${BOLD}⚙️ Configuração Claude Code${NC}"
    echo "─────────────────────────────────────────────────────────"

    if [ -f "$CLAUDE_SETTINGS" ]; then
        log_ok "Configuração Claude existe: $CLAUDE_SETTINGS"

        # Verificar hooks
        HOOK_COUNT=$(grep -c '"name"' "$CLAUDE_SETTINGS" 2>/dev/null || true)
        HOOK_COUNT="${HOOK_COUNT:-0}"
        if [ "$HOOK_COUNT" -gt 0 ]; then
            log_ok "Hooks configurados: $HOOK_COUNT"
        else
            log_info "Hooks: nenhum configurado no perfil selecionado"
        fi

        # Verificar permissões essenciais
        for perm in "Bash(python3" "Bash(git" "Read(/home/bruno" "Write(/home/bruno"; do
            if grep -q "$perm" "$CLAUDE_SETTINGS" 2>/dev/null; then
                : # Já logado acima
            else
                log_info "Permission base não declarada: $perm"
            fi
        done
    else
        log_fail "settings.local.json não existe"
    fi

    # Verificar skill do Kothar
    if [ -f "$KOTHAR_DIR/.claude/skills/kothar.md" ]; then
        log_ok "Skill /kothar configurada"
    else
        log_fail "Skill /kothar não configurada"
    fi

    # Verificar comandos
    if [ -f "$HOME/.claude/commands/kothar.toml" ]; then
        log_ok "Comandos customizados"
    else
        log_info "Comandos customizados não existem no perfil do usuário"
    fi

    echo ""

    # ============================================================
    # 5. MEMÓRIA VETORIAL (RAG)
    # ============================================================
    echo -e "${BOLD}🧠 Memória Vetorial (RAG)${NC}"
    echo "─────────────────────────────────────────────────────────"

    # Testar embedder
    EMBEDDER_ERROR=""
    if [ -z "$KOTHAR_PYTHON_BIN" ]; then
        EMBEDDER_ERROR="Python 3 não encontrado"
    elif ! EMBEDDER_ERROR=$("$KOTHAR_PYTHON_BIN" -c "from backend.memory.semantic.context_embedder import context_embedder" 2>&1 >/dev/null); then
        EMBEDDER_ERROR="${EMBEDDER_ERROR:-falha desconhecida}"
    fi
    if [ -z "$EMBEDDER_ERROR" ]; then
        ENGINE="context_embedder"
        log_ok "Embedder funcional (Engine: $ENGINE)"

        DOC_COUNT=0
        if [ -f "$KOTHAR_DIR/.rag-index-state.json" ]; then
            DOC_COUNT=$(grep -o '"indexed_chunks"[[:space:]]*:[[:space:]]*[0-9]*' \
                "$KOTHAR_DIR/.rag-index-state.json" | grep -o '[0-9]*' | tail -1 || true)
        fi
        DOC_COUNT="${DOC_COUNT:-0}"
        if [ "$DOC_COUNT" -gt 0 ]; then
            log_ok "Documentos vectorizados: $DOC_COUNT"
        else
            log_fail "Vector DB vazio - execute a indexação do Cofre antes de usar o RAG"
        fi
    else
        log_fail "Embedder não funcional: ${EMBEDDER_ERROR//$'\n'/ }"
    fi

    echo ""

    # ============================================================
    # 6. SCRIPTS ESSENCIAIS
    # ============================================================
    echo -e "${BOLD}📜 Scripts${NC}"
    echo "─────────────────────────────────────────────────────────"

    for script in kothar-cli.sh kothar-diagnostic.sh kothar_start.sh; do
        if [ -f "$KOTHAR_DIR/scripts/$script" ]; then
            if [ -x "$KOTHAR_DIR/scripts/$script" ]; then
                log_ok "Script: $script (executável)"
            else
                if [ "$FIX_MODE" = "fix" ] || [ "$FIX_MODE" = "force-fix" ]; then
                    chmod +x "$KOTHAR_DIR/scripts/$script"
                    log_fix "Script: $script (tornado executável)"
                else
                    log_warn "Script: $script (não executável)"
                fi
            fi
        else
            log_fail "Script: $script (não existe)"
        fi
    done

    echo ""

    # ============================================================
    # 7. HOOKS
    # ============================================================
    echo -e "${BOLD}🪝 Hooks${NC}"
    echo "─────────────────────────────────────────────────────────"

    for hook in kothar-session-init.sh credential-scanner.sh; do
        if [ -f "$KOTHAR_DIR/hooks/$hook" ]; then
            if [ -x "$KOTHAR_DIR/hooks/$hook" ]; then
                log_ok "Hook: $hook"
            else
                if [ "$FIX_MODE" = "fix" ] || [ "$FIX_MODE" = "force-fix" ]; then
                    chmod +x "$KOTHAR_DIR/hooks/$hook"
                    log_fix "Hook: $hook (tornado executável)"
                else
                    log_warn "Hook: $hook (não executável)"
                fi
            fi
        else
            log_fail "Hook: $hook (não existe)"
        fi
    done

    echo ""

    # ============================================================
    # 8. SEGURANÇA
    # ============================================================
    echo -e "${BOLD}🔐 Segurança${NC}"
    echo "─────────────────────────────────────────────────────────"

    # SSH
    if [ -f "$HOME/.ssh/config" ] || [ -d "$HOME/.ssh" ]; then
        log_ok "SSH disponível"
    else
        log_fail "SSH config/diretório (crítico)"
    fi

    # ChromaDB path
    if [ -d "$KOTHAR_DIR/.chroma-data" ]; then
        log_ok "ChromaDB dir existe"
    else
        if [ "$FIX_MODE" = "fix" ] || [ "$FIX_MODE" = "force-fix" ]; then
            mkdir -p "$KOTHAR_DIR/.chroma-data"
            log_fix "ChromaDB dir criado"
        fi
    fi

    # Verificar credenciais expostas
    CRED_COUNT=$(grep -rE "(password|secret|token|api[_-]?key)\s*=\s*['\"][^'\"]{8,}" "$KOTHAR_DIR" \
        --exclude-dir=".git" --exclude-dir=".venv" --exclude-dir=".chroma-data" \
        --exclude-dir="node_modules" --exclude-dir="infra" --exclude-dir="ambiente-voz" \
        --include="*.py" --include="*.js" --include="*.ts" 2>/dev/null \
        | grep -vE "\.git|/tests/|os\.getenv|os\.environ|process\.env|getenv\(|https?://" | wc -l)
    if [ "$CRED_COUNT" -eq 0 ]; then
        log_ok "Sem credenciais hardcoded"
    else
        log_fail "Credenciais hardcoded encontradas: $CRED_COUNT"
    fi

    echo ""

    # ============================================================
    # 9. PROJETOS (APRENDIZADO DINÂMICO)
    # ============================================================
    echo -e "${BOLD}📦 Projetos${NC}"
    echo "─────────────────────────────────────────────────────────"

    # Verifica se há projetos registrados na memória
    MEMORY_PROJECTS="$HOME/.claude/projects/-home-bruno-kothar/memory/projetos-ativos.md"
    if [ -f "$MEMORY_PROJECTS" ]; then
        PROJECT_COUNT=$(grep -c "^## " "$MEMORY_PROJECTS" 2>/dev/null || echo "0")
        if [ "$PROJECT_COUNT" -gt 0 ]; then
            log_ok "Projetos registrados na memória: $PROJECT_COUNT"
        else
            log_ok "Sistema pronto para aprendizado dinâmico de projetos"
        fi
    else
        log_ok "Sistema pronto para aprendizado dinâmico de projetos"
    fi

    echo ""

    # ============================================================
    # 10. LANGFUSE (DEVE ESTAR REMOVIDO)
    # ============================================================
    echo -e "${BOLD}❌ Langfuse (deve estar removido)${NC}"
    echo "─────────────────────────────────────────────────────────"

    LANGFUSE_REF=$(grep -r "langfuse" "$KOTHAR_DIR" --include="*.env" 2>/dev/null | grep -v ".git" | wc -l)
    if [ "$LANGFUSE_REF" -eq 0 ]; then
        log_ok "Langfuse: REMOVIDO"
    else
        log_fail "Langfuse: ainda referenciado ($LANGFUSE_REF)"
    fi

    echo ""
}

# ============================================================
# RESULTADO
# ============================================================

show_result() {
    separator
    echo -e "${BOLD}  📊 RESULTADO${NC}"
    separator
    echo ""

    TOTAL=$((PASSED + FAILED))

    TOTAL=$((PASSED + FAILED))
    if [ "$FAILED" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
        echo -e "${GREEN}${BOLD}  ✅ KOTHAR 100% FUNCIONAL${NC}"
        echo ""
        echo -e "  Verificações: ${PASSED}/${TOTAL} aprovadas"
        if [ "$FIXED" -gt 0 ]; then
            echo -e "  Corrigidos: $FIXED"
        fi
        echo ""
        return 0
    else
        PERCENT=$((PASSED * 100 / TOTAL))
        echo -e "${RED}${BOLD}  ❌ KOTHAR NÃO VALIDADO${NC}"
        echo ""
        echo -e "  Verificações: ${PASSED}/${TOTAL} aprovadas (${PERCENT}%)"
        echo -e "  Falhas: $FAILED"
        echo -e "  Avisos: $WARNINGS"

        if [ "$FIXED" -gt 0 ]; then
            echo -e "  Corrigidos automaticamente: $FIXED"
        fi

        echo ""
        echo -e "  ${YELLOW}Para corrigir automaticamente:${NC}"
        echo "    ~/kothar/scripts/kothar-health.sh fix"
        echo ""
        return 1
    fi
}

# ============================================================
# EXECUÇÃO
# ============================================================

run_health_check
show_result
exit $?
