#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR HOOK: Auditoria Estrutural Automática
# REGRA SUPREMA: Nada é criado em estrutura suja
# Executa ao iniciar sessão em um projeto
# ═══════════════════════════════════════════════════════════════════════════

HOOK_NAME="kothar-structure-audit"
CLAUDE_HOOKS_DIR="${CLAUDE_HOOKS_DIR:-${HOME}/.claude/hooks}"
if ! mkdir -p "$CLAUDE_HOOKS_DIR" 2>/dev/null; then
    CLAUDE_HOOKS_DIR="${PROJECT_DIR:-$(pwd)}/logs"
    mkdir -p "$CLAUDE_HOOKS_DIR" 2>/dev/null || CLAUDE_HOOKS_DIR="/tmp"
fi
LOG_FILE="${CLAUDE_HOOKS_DIR}/hook.log"
AUDIT_REPORT="${CLAUDE_HOOKS_DIR}/structure-audit.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$HOOK_NAME] $1" >> "$LOG_FILE"
}

# Detecta diretório do projeto atual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTHAR_BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$KOTHAR_BASE_DIR}"

log "🔍 Iniciando auditoria estrutural em $PROJECT_DIR"

# Se não existe, aborta silenciosamente
if [[ ! -d "$PROJECT_DIR" ]]; then
    log "ℹ️ Diretório não existe, pulando auditoria"
    exit 0
fi

# Inicia relatório
echo "═══════════════════════════════════════════════════════════════" > "$AUDIT_REPORT"
echo "  AUDITORIA ESTRUTURAL KOTHAR - $(date '+%Y-%m-%d %H:%M:%S')" >> "$AUDIT_REPORT"
echo "  Projeto: $PROJECT_DIR" >> "$AUDIT_REPORT"
echo "═══════════════════════════════════════════════════════════════" >> "$AUDIT_REPORT"
echo "" >> "$AUDIT_REPORT"

VIOLATIONS=0

# 1. Arquivos genéricos proibidos
echo "🔴 ARQUIVOS GENÉRICOS (proibidos):" >> "$AUDIT_REPORT"
GENERIC_FILES=$(find "$PROJECT_DIR" \
    -type f \
    \( -name "index.ts" -o -name "index.js" -o -name "index.py" \
       -o -name "utils.ts" -o -name "utils.js" -o -name "utils.py" \
       -o -name "helpers.ts" -o -name "helpers.js" -o -name "helpers.py" \
       -o -name "app.ts" -o -name "app.js" -o -name "app.py" \
       -o -name "main_old.*" -o -name "main_new.*" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.venv/*" \
    -not -path "*/skills/*" \
    -not -path "*/infra/*" \
    -not -path "*/__pycache__/*" \
    2>/dev/null)

if [[ -n "$GENERIC_FILES" ]]; then
    echo "$GENERIC_FILES" | while read f; do
        echo "   ❌ $f" >> "$AUDIT_REPORT"
        ((VIOLATIONS++))
    done
else
    echo "   ✅ Nenhum encontrado" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 2. Arquivos com sufixos duplicados (_v2, _new, _copia, etc)
echo "🔴 ARQUIVOS DUPLICADOS/SUPLANTES:" >> "$AUDIT_REPORT"
DUPLICATE_FILES=$(find "$PROJECT_DIR" \
    -type f \
    \( -name "*_v2.*" -o -name "*_v3.*" -o -name "*_v4.*" \
       -o -name "*_new.*" -o -name "*_novo.*" \
       -o -name "*_old.*" -o -name "*_antigo.*" \
       -o -name "*_backup.*" -o -name "*_copia.*" -o -name "*_copy.*" \
       -o -name "*_test.*" -o -name "*_temp.*" -o -name "*_tmp.*" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.venv/*" \
    -not -path "*/kothar/*" \
    2>/dev/null)

if [[ -n "$DUPLICATE_FILES" ]]; then
    echo "$DUPLICATE_FILES" | while read f; do
        echo "   ❌ $f" >> "$AUDIT_REPORT"
        ((VIOLATIONS++))
    done
else
    echo "   ✅ Nenhum encontrado" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 3. Pastas genéricas proibidas
echo "🔴 PASTAS GENÉRICAS (proibidas):" >> "$AUDIT_REPORT"
GENERIC_DIRS=$(find "$PROJECT_DIR" \
    -type d \
    \( -name "src" -o -name "lib" -o -name "app" \
       -o -name "components" -o -name "modules" -o -name "controllers" \
       -o -name "models" -o -name "views" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.venv/*" \
    -not -path "*/kothar/*" \
    2>/dev/null)

if [[ -n "$GENERIC_DIRS" ]]; then
    echo "$GENERIC_DIRS" | while read d; do
        echo "   ❌ $d" >> "$AUDIT_REPORT"
        ((VIOLATIONS++))
    done
else
    echo "   ✅ Nenhuma encontrada" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 4. Mistura de idiomas (heurística simples)
echo "🟡 POSSÍVEL MISTURA DE IDIOMAS:" >> "$AUDIT_REPORT"
ENGLISH_FILES=$(find "$PROJECT_DIR" \
    -type f \( -name "*.ts" -o -name "*.py" -o -name "*.js" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.venv/*" \
    -regex ".*/(user|login|auth|service|controller|helper|manager|handler|util|model|view|router|middleware|repository)\..*" \
    2>/dev/null | head -20)

if [[ -n "$ENGLISH_FILES" ]]; then
    echo "$ENGLISH_FILES" | while read f; do
        echo "   ⚠️  $f (nome em inglês)" >> "$AUDIT_REPORT"
    done
else
    echo "   ✅ Nenhum padrão inglês detectado" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 5. Backend/frontend não separados
echo "🔴 SEPARAÇÃO BACKEND/FRONTEND:" >> "$AUDIT_REPORT"
if [[ -d "$PROJECT_DIR/backend" && -d "$PROJECT_DIR/frontend" ]]; then
    echo "   ✅ Estrutura separada corretamente" >> "$AUDIT_REPORT"
elif [[ -d "$PROJECT_DIR/src" ]]; then
    echo "   ❌ Estrutura monolítica em src/ - DEVE ser separado em backend/ e frontend/" >> "$AUDIT_REPORT"
    ((VIOLATIONS++))
else
    echo "   ⚠️  Não foi possível detectar padrão (pode ser projeto simples)" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 6. Arquivos de configuração na raiz
echo "🔴 CONFIGURAÇÕES NA RAIZ:" >> "$AUDIT_REPORT"
if [[ -f "$PROJECT_DIR/.env" && ! -f "$PROJECT_DIR/.gitignore" ]]; then
    echo "   ❌ .env existe mas .gitignore ausente (risco de commitar secrets)" >> "$AUDIT_REPORT"
    ((VIOLATIONS++))
fi

if [[ -f "$PROJECT_DIR/.env" && ! -f "$PROJECT_DIR/.env.exemplo" ]]; then
    echo "   ⚠️  .env existe mas .env.exemplo ausente" >> "$AUDIT_REPORT"
fi

if [[ ! -f "$PROJECT_DIR/README.md" ]]; then
    echo "   ❌ README.md ausente na raiz" >> "$AUDIT_REPORT"
    ((VIOLATIONS++))
else
    echo "   ✅ README.md presente" >> "$AUDIT_REPORT"
fi
echo "" >> "$AUDIT_REPORT"

# 7. Estatísticas
echo "═══════════════════════════════════════════════════════════════" >> "$AUDIT_REPORT"
echo "  TOTAL DE VIOLAÇÕES: $VIOLATIONS" >> "$AUDIT_REPORT"

if [[ "$VIOLATIONS" -gt 0 ]]; then
    echo "" >> "$AUDIT_REPORT"
    echo "  ⚠️  AÇÃO NECESSÁRIA:" >> "$AUDIT_REPORT"
    echo "  O Engenheiro DEVE:" >> "$AUDIT_REPORT"
    echo "  1. Listar cada violação ao usuário" >> "$AUDIT_REPORT"
    echo "  2. Propor plano de correção" >> "$AUDIT_REPORT"
    echo "  3. AGUARDAR aprovação do usuário" >> "$AUDIT_REPORT"
    echo "  4. SÓ ENTÃO começar a corrigir" >> "$AUDIT_REPORT"
    echo "" >> "$AUDIT_REPORT"
    echo "  🚫 BLOQUEADO: Criação de novos arquivos até estrutura estar limpa" >> "$AUDIT_REPORT"
fi
echo "═══════════════════════════════════════════════════════════════" >> "$AUDIT_REPORT"

log "📊 Auditoria concluída: $VIOLATIONS violações encontradas"
log "📄 Relatório salvo em $AUDIT_REPORT"

# Saída resumida para o console
if [[ "$VIOLATIONS" -gt 0 ]]; then
    echo ""
    echo "⚠️  AUDITORIA ESTRUTURAL DETECTOU $VIOLATIONS VIOLAÇÕES" >&2
    echo "   Veja: $AUDIT_REPORT" >&2
    echo "   AÇÃO: Organize a estrutura ANTES de criar novos arquivos" >&2
    exit 1
fi

exit 0