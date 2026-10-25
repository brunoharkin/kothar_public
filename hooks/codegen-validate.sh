#!/bin/bash
# =============================================================================
# CODEGEN-VALIDATE — Validação completa de projeto
# =============================================================================
# Usage: codegen-validate.sh [--all|--quick|--security|--consistency]
# =============================================================================

set -euo pipefail

CORES=$(tput colors 2>/dev/null || echo 0)
if [ "$CORES" -ge 8 ]; then
    VERMELHO='\033[0;31m'
    VERDE='\033[0;32m'
    AMARELO='\033[1;33m'
    AZUL='\033[0;34m'
    CIANO='\033[0;36m'
    RESET='\033[0m'
else
    VERMELHO=''
    VERDE=''
    AMARELO=''
    AZUL=''
    CIANO=''
    RESET=''
fi

MODO="${1:---all}"
PROJETO_DIR="${2:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${AZUL}  🔍 CODEGEN VALIDATE v3.0${RESET}"
echo -e "${AZUL}  Modo: $MODO${RESET}"
echo -e "${AZUL}  Projeto: $PROJETO_DIR${RESET}"
echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
echo ""

TOTAL_ERROS=0
TOTAL_AVISOS=0

# =============================================================================
# FUNÇÕES
# =============================================================================

erro() {
    echo -e "${VERMELHO}❌ ERRO: $1${RESET}"
    [ -n "${2:-}" ] && echo -e "${VERMELHO}   Em: $2${RESET}"
    TOTAL_ERROS=$((TOTAL_ERROS + 1))
}

aviso() {
    echo -e "${AMARELO}⚠️ AVISO: $1${RESET}"
    [ -n "${2:-}" ] && echo -e "${AMARELO}   Em: $2${RESET}"
    TOTAL_AVISOS=$((TOTAL_AVISOS + 1))
}

sucesso() {
    echo -e "${VERDE}✅ $1${RESET}"
}

info() {
    echo -e "${CIANO}ℹ️  $1${RESET}"
}

# =============================================================================
# VALIDAÇÃO COMPLETA (--all)
# =============================================================================

validar_seguranca() {
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo -e "${AZUL}  🔒 VALIDAÇÃO DE SEGURANÇA${RESET}"
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo ""

    # 1. Credenciais hardcoded
    info "Verificando credenciais hardcoded..."
    CREDENCIAIS=$(grep -rEn "(api[_-]?key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9_-]{10,}" \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" \
        --include="*.java" --include="*.go" 2>/dev/null | grep -v "getenv\|process.env\|\.env\|os.environ" | head -20)

    if [ -n "$CREDENCIAIS" ]; then
        while IFS= read -r linha; do
            erro "Credencial hardcoded detectada" "$linha"
        done <<< "$CREDENCIAIS"
    else
        sucesso "Nenhuma credencial hardcoded encontrada"
    fi
    echo ""

    # 2. Logs com dados sensíveis
    info "Verificando logs seguros..."
    LOGS_SENSIVEIS=$(grep -rEn "log.*\$((password|senha|passwd|token|secret|cpf|cartao))" \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" 2>/dev/null | head -10)

    if [ -n "$LOGS_SENSIVEIS" ]; then
        while IFS= read -r linha; do
            erro "Log pode expor dado sensível" "$linha"
        done <<< "$LOGS_SENSIVEIS"
    else
        sucesso "Nenhum log sensivel encontrado"
    fi
    echo ""

    # 3. Console.log em produção
    info "Verificando console.log em produção..."
    CONSOLE_LOGS=$(grep -rEn "console\.(log|debug|info)\(" \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | grep -v "//.*console\|/\\*.*console\|eslint-disable" | head -20)

    if [ -n "$CONSOLE_LOGS" ]; then
        while IFS= read -r linha; do
            aviso "console.log em produção" "$linha"
        done <<< "$CONSOLE_LOGS"
    else
        sucesso "Nenhum console.log em produção encontrado"
    fi
    echo ""

    # 4. Injeção SQL
    info "Verificando proteção contra injeção SQL..."
    SQL_VULNERAVEL=$(grep -rEn '(query|execute|exec|raw).*["\`].*\$[a-zA-Z]' \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" 2>/dev/null | grep -v "param|bind|prepare|placeholder" | head -10)

    if [ -n "$SQL_VULNERAVEL" ]; then
        while IFS= read -r linha; do
            erro "Possivel vulnerabilidade de injeção SQL" "$linha"
        done <<< "$SQL_VULNERAVEL"
    else
        sucesso "Nenhuma vulnerabilidade SQL óbvia encontrada"
    fi
    echo ""

    # 5. XSS
    info "Verificando proteção contra XSS..."
    XSS_RISCO=$(grep -rEn "(innerHTML|dangerouslySetInnerHTML|document\.write)" \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" 2>/dev/null | grep -v "sanitize\|DOMPurify\|xss" | head -10)

    if [ -n "$XSS_RISCO" ]; then
        while IFS= read -r linha; do
            aviso "Possível risco de XSS (verifique sanitização)" "$linha"
        done <<< "$XSS_RISCO"
    else
        sucesso "Nenhum uso perigoso de innerHTML encontrado"
    fi
    echo ""
}

validar_consistencia() {
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo -e "${AZUL}  🔄 VALIDAÇÃO DE CONSISTÊNCIA${RESET}"
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo ""

    # 1. Verificar estrutura de pastas
    info "Verificando estrutura de pastas..."
    ANTIPADRÕES=0

    if find "$PROJETO_DIR" -maxdepth 2 -type d -name "src" 2>/dev/null | grep -v node_modules > /dev/null; then
        aviso "Pasta 'src/' encontrada (proibida nos padrões Kothar)"
        ANTIPADRÕES=$((ANTIPADRÕES + 1))
    fi

    if find "$PROJETO_DIR" -maxdepth 2 -type d -name "lib" 2>/dev/null | grep -v node_modules > /dev/null; then
        aviso "Pasta 'lib/' encontrada (proibida nos padrões Kothar)"
        ANTIPADRÕES=$((ANTIPADRÕES + 1))
    fi

    if [ "$ANTIPADRÕES" -eq 0 ]; then
        sucesso "Nenhuma pasta genérica proibida encontrada"
    fi
    echo ""

    # 2. Verificar arquivos duplicados
    info "Verificando arquivos duplicados..."
    DUPLICADOS=$(find "$PROJETO_DIR" \( -name "*_v2*" -o -name "*_v3*" -o -name "*_new*" -o -name "*_old*" -o -name "*_backup*" \) -type f 2>/dev/null | grep -v node_modules | head -10)

    if [ -n "$DUPLICADOS" ]; then
        while IFS= read -r arquivo; do
            aviso "Arquivo duplicado/backup encontrado" "$arquivo"
        done <<< "$DUPLICADOS"
    else
        sucesso "Nenhum arquivo duplicado encontrado"
    fi
    echo ""

    # 3. Verificar consistência de imports
    info "Verificando consistência de imports..."

    # Frontend: deve ter @/ alias ou imports consistentes
    if [ -d "$PROJETO_DIR/frontend" ]; then
        DEEP_RELATIVE=$(grep -rEn "from ['\"]\.\./\.\./" "$PROJETO_DIR/frontend" --include="*.ts" --include="*.tsx" 2>/dev/null | head -10)

        if [ -n "$DEEP_RELATIVE" ]; then
            while IFS= read -r linha; do
                aviso "Import relativo profundo (considere usar @/)" "$linha"
            done <<< "$DEEP_RELATIVE"
        else
            sucesso "Imports relativos estão adequados"
        fi
    fi
    echo ""

    # 4. Verificar consistência de autenticação (frontend)
    info "Verificando consistência de autenticação em páginas..."
    if [ -d "$PROJETO_DIR/frontend/paginas" ] || [ -d "$PROJETO_DIR/frontend/pages" ]; then
        PAGINAS_DIR=$(find "$PROJETO_DIR/frontend" -type d \( -name "paginas" -o -name "pages" \) 2>/dev/null | head -1)

        if [ -n "$PAGINAS_DIR" ]; then
            # Páginas que parecem precisar de auth mas não têm
            TODAS_PAGINAS=$(find "$PAGINAS_DIR" -name "*.tsx" -o -name "*.jsx" 2>/dev/null)
            PAGINAS_COM_AUTH=$(grep -l "useAutenticacao\|verificarToken\|useAuth\|isAuthenticated" $TODAS_PAGINAS 2>/dev/null || true)

            for pagina in $TODAS_PAGINAS; do
                BASENAME=$(basename "$pagina" .tsx | basename -s .jsx)

                # Páginas públicas intencionalmente
                if echo "$BASENAME" | grep -qiE "(login|cadastro|esqueci|recover|public)"; then
                    continue
                fi

                # Verificar se esta página tem auth
                if ! echo "$PAGINAS_COM_AUTH" | grep -q "$pagina" 2>/dev/null; then
                    aviso "Página sem verificação de autenticação" "$pagina"
                fi
            done
        fi
    fi
    echo ""

    # 5. Verificar consistência de logging
    info "Verificando consistência de logging..."
    if [ -d "$PROJETO_DIR/backend" ]; then
        ARQUIVOS_COM_LOG=$(grep -rl "logger\|console\." "$PROJETO_DIR/backend" --include="*.ts" --include="*.js" --include="*.py" 2>/dev/null | head -5)
        ARQUIVOS_SEM_LOG=$(find "$PROJETO_DIR/backend/servicos" -name "*.ts" -o -name "*.js" -o -name "*.py" 2>/dev/null | while read f; do
            if ! grep -q "logger\|console\." "$f" 2>/dev/null; then
                echo "$f"
            fi
        done | head -10)

        if [ -n "$ARQUIVOS_SEM_LOG" ]; then
            while IFS= read -r arquivo; do
                aviso "Servico sem log configurado" "$arquivo"
            done <<< "$ARQUIVOS_SEM_LOG"
        else
            sucesso "Todos os servicos têm logging configurado"
        fi
    fi
    echo ""
}

validar_versoes() {
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo -e "${AZUL}  📦 VALIDAÇÃO DE VERSÕES${RESET}"
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo ""

    # 1. package.json - versões não bloqueadas
    if [ -f "$PROJETO_DIR/package.json" ]; then
        info "Verificando package.json..."

        if grep -q "@latest\|@\*" "$PROJETO_DIR/package.json" 2>/dev/null; then
            erro "Dependência usando @latest ou @*" "$PROJETO_DIR/package.json"
        else
            sucesso "Dependencies bloqueadas corretamente"
        fi

        # Verificar se há audit de segurança
        if [ -f "$PROJETO_DIR/package-lock.json" ]; then
            if command -v npm &> /dev/null; then
                info "Rodando npm audit..."
                AUDIT=$(npm audit --omit=dev 2>/dev/null || true)
                if echo "$AUDIT" | grep -q "vulnerabilities"; then
                    VULNS=$(echo "$AUDIT" | grep -oE "[0-9]+ vulnerabilities" | head -1)
                    aviso "Vulnerabilidades encontradas no npm audit" "$VULNS"
                else
                    sucesso "Nenhuma vulnerabilidade crítica encontrada"
                fi
            fi
        fi
    fi

    # 2. requirements.txt - Python
    if [ -f "$PROJETO_DIR/requirements.txt" ]; then
        info "Verificando requirements.txt..."

        if grep -q "==" "$PROJETO_DIR/requirements.txt" 2>/dev/null; then
            sucesso "Dependencies Python bloqueadas com versões específicas"
        else
            if grep -qE "^[a-zA-Z0-9-]+$" "$PROJETO_DIR/requirements.txt" 2>/dev/null; then
                erro "Dependencies Python SEM versão especificada" "$PROJETO_DIR/requirements.txt"
            fi
        fi

        if command -v pip-audit &> /dev/null; then
            info "Rodando pip-audit..."
            PIP_AUDIT=$(pip-audit 2>/dev/null || true)
            if echo "$PIP_AUDIT" | grep -q "vulnerable"; then
                aviso "Possiveis vulnerabilidades em packages Python"
            else
                sucesso "Nenhuma vulnerabilidade crítica encontrada em Python packages"
            fi
        fi
    fi
    echo ""
}

validar_quick() {
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo -e "${AZUL}  ⚡ VALIDAÇÃO RÁPIDA${RESET}"
    echo -e "${AZUL}─────────────────────────────────────────────────────────────${RESET}"
    echo ""

    # Só o essencial
    info "Verificando credenciais hardcoded..."
    CREDENCIAIS=$(grep -rEn "(api[_-]?key|secret|password)\s*=\s*['\"][a-zA-Z0-9_-]{10,}" \
        "$PROJETO_DIR" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" 2>/dev/null | grep -v "getenv\|process.env\|\.env\|os.environ" | head -5)

    if [ -n "$CREDENCIAIS" ]; then
        erro "Credenciais hardcoded encontradas (use /codegen para detalhes)"
    else
        sucesso "Sem credenciais expostas"
    fi
    echo ""

    info "Verificando antipadrões..."
    ANTIPADROES=$(find "$PROJETO_DIR" \( -name "index.ts" -o -name "utils.ts" -o -name "*_v2*" \) -type f 2>/dev/null | grep -v node_modules | head -5)

    if [ -n "$ANTIPADROES" ]; then
        aviso "Antipadrões encontrados (use /codegen para detalhes)"
    else
        sucesso "Sem antipadrões óbvios"
    fi
    echo ""
}

# =============================================================================
# EXECUTAR VALIDAÇÃO
# =============================================================================

case "$MODO" in
    --all)
        validar_seguranca
        validar_consistencia
        validar_versoes
        ;;
    --security)
        validar_seguranca
        ;;
    --consistency)
        validar_consistencia
        ;;
    --versions)
        validar_versoes
        ;;
    --quick)
        validar_quick
        ;;
    *)
        echo "Uso: codegen-validate.sh [--all|--quick|--security|--consistency|--versions]"
        exit 1
        ;;
esac

# =============================================================================
# RESULTADO FINAL
# =============================================================================

echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${AZUL}  RESULTADO${RESET}"
echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"

if [ "$TOTAL_ERROS" -eq 0 ] && [ "$TOTAL_AVISOS" -eq 0 ]; then
    echo -e "${VERDE}  ✅ PROJETO APROVADO${RESET}"
    echo -e "${VERDE}  Sem erros ou avisos críticos${RESET}"
    exit 0
elif [ "$TOTAL_ERROS" -eq 0 ]; then
    echo -e "${AMARELO}  ⚠️ $TOTAL_AVISOS aviso(s)${RESET}"
    echo -e "${AMARELO}  Corrija para seguir padrões Kothar${RESET}"
    exit 0
else
    echo -e "${VERMELHO}  ❌ $TOTAL_ERROS erro(s)${RESET}"
    [ "$TOTAL_AVISOS" -gt 0 ] && echo -e "${AMARELO}  ⚠️ $TOTAL_AVISOS aviso(s)${RESET}"
    echo -e "${VERMELHO}  Ações necessárias antes de continuar${RESET}"
    exit 1
fi
