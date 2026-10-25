#!/bin/bash
# =============================================================================
# POST-CODEGEN-VALIDATE — Executa APÓS qualquer Write/Edit
# =============================================================================
# Verifica se o código criado NÃO viola padrões de segurança e consistência
# Violações detectadas bloqueiam a operação para impedir código inseguro.
# =============================================================================

set -euo pipefail

CORES=$(tput colors 2>/dev/null || echo 0)
if [ "$CORES" -ge 8 ]; then
    VERMELHO='\033[0;31m'
    VERDE='\033[0;32m'
    AMARELO='\033[1;33m'
    AZUL='\033[0;34m'
    RESET='\033[0m'
else
    VERMELHO=''
    VERDE=''
    AMARELO=''
    AZUL=''
    RESET=''
fi

# =============================================================================
# FUNÇÕES
# =============================================================================

reportar_erro() {
    echo -e "${AMARELO}⚠️ CODEGEN POST-VALIDATE${RESET}"
    echo -e "${AMARELO}   Arquivo: $1${RESET}"
    echo -e "${AMARELO}   Problema: $2${RESET}"
    echo -e "${VERDE}   Correção sugerida: $3${RESET}"
    echo ""
}

sucesso() {
    echo -e "${VERDE}✅ $1${RESET}"
}

# =============================================================================
# EXTRAIR INFORMAÇÕES
# =============================================================================

ARQUIVO="${KOTHAR_LAST_FILE:-${1:-}}"

if [ -z "$ARQUIVO" ] || [ ! -f "$ARQUIVO" ]; then
    exit 0  # Arquivo não encontrado, não valida
fi

PROJETO_DIR=$(git rev-parse --show-toplevel 2>/dev/null || dirname "$ARQUIVO")

# =============================================================================
# VERIFICAÇÕES DE PÓS-CRIAÇÃO
# =============================================================================

ERROS=0

# -----------------------------------------------------------------------------
# 1. VERIFICAR CONSOLE.LOG EM PRODUÇÃO
# -----------------------------------------------------------------------------
if grep -nE "console\.(log|debug|info)" "$ARQUIVO" 2>/dev/null | grep -v "// DEBUG\|// TODO\|// eslint" > /dev/null; then
    LINHAS=$(grep -nE "console\.(log|debug|info)" "$ARQUIVO" | head -3 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    reportar_erro \
        "$ARQUIVO" \
        "console.log/debug/info encontrado em produção (linhas: $LINHAS)" \
        "Remover ou usar logger configurado (nível debug)"
    ERROS=$((ERROS + 1))
fi

# -----------------------------------------------------------------------------
# 2. VERIFICAR LOGS COM DADOS SENSÍVEIS
# -----------------------------------------------------------------------------
if grep -nE "log.*\$((password|senha|passwd|token|secret|cpf|cartao))" "$ARQUIVO" 2>/dev/null; then
    LINHAS=$(grep -nE "log.*\$((password|senha|passwd|token|secret|cpf|cartao))" "$ARQUIVO" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    reportar_erro \
        "$ARQUIVO" \
        "Possível dado sensível em log (linhas: $LINHAS)" \
        "Logue apenas IDs: logger.info('Login attempt: ' + userId)"
    ERROS=$((ERROS + 1))
fi

# -----------------------------------------------------------------------------
# 3. VERIFICAR CREDENCIAIS HARDCODED
# -----------------------------------------------------------------------------
if grep -nE "(api[_-]?key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9_-]{10,}" "$ARQUIVO" 2>/dev/null | grep -v "os\.getenv\|process\.env\|\.env\|getenv\|env\." > /dev/null; then
    LINHAS=$(grep -nE "(api[_-]?key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9_-]{10,}" "$ARQUIVO" | grep -v "os\.getenv\|process\.env\|\.env\|getenv\|env\." | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    reportar_erro \
        "$ARQUIVO" \
        "Possível credencial hardcoded (linhas: $LINHAS)" \
        "Use: os.getenv('VARIAVEL') ou process.env.VARIAVEL"
    ERROS=$((ERROS + 1))
fi

# -----------------------------------------------------------------------------
# 4. VERIFICAR VARIÁVEIS DE AMBIENTE USADAS
# -----------------------------------------------------------------------------
# Se o arquivo tem conexão com DB ou API externa, DEVE usar .env
if grep -qE "(connect|createClient|new Pool|Connection|connectAsync)" "$ARQUIVO" 2>/dev/null; then
    if ! grep -qE "(getenv|process\.env|os\.environ)" "$ARQUIVO" 2>/dev/null; then
        # Verificar se tem pelo menos placeholders
        if grep -qE "localhost|127\.0\.0\.1|:5432|:3306|:6379" "$ARQUIVO" 2>/dev/null | grep -v "//.*localhost\|#.*localhost"; then
            reportar_erro \
                "$ARQUIVO" \
                "Conexão com DB/Redis sem variável de ambiente" \
                "Use: os.getenv('DATABASE_URL') ou similar"
            ERROS=$((ERROS + 1))
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 5. VERIFICAR ERROS GENÉRICOS CAPTURADOS
# -----------------------------------------------------------------------------
if grep -nE "catch.*\{.*\}" "$ARQUIVO" 2>/dev/null | grep -v "error\|err\|exception" > /dev/null; then
    # Captura vazia
    if grep -nE "catch.*\{\s*\}" "$ARQUIVO" 2>/dev/null; then
        LINHAS=$(grep -nE "catch.*\{\s*\}" "$ARQUIVO" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
        reportar_erro \
            "$ARQUIVO" \
            "catch vazio detectado (linhas: $LINHAS)" \
            "Implemente tratamento de erro adequado"
        ERROS=$((ERROS + 1))
    fi
fi

# -----------------------------------------------------------------------------
# 6. VERIFICAR CSS: OVERFLOW NÃO TRATADO
# -----------------------------------------------------------------------------
if [[ "$ARQUIVO" == *.css ]] || [[ "$ARQUIVO" == *.scss ]]; then
    # Containers sem overflow
    if grep -nE "\.container|\.wrapper|\.card" "$ARQUIVO" 2>/dev/null | grep -v "overflow" > /dev/null; then
        # Verificar se é um container sem overflow definido
        if grep -B2 "\.container\|\.wrapper\|\.card" "$ARQUIVO" | grep -v "overflow" > /dev/null; then
            reportar_erro \
                "$ARQUIVO" \
                "Container sem overflow definido pode causar quebra de layout" \
                "Adicione: overflow: hidden ou overflow-x: auto"
            ERROS=$((ERROS + 1))
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 7. VERIFICAR INJEÇÃO SQL
# -----------------------------------------------------------------------------
if grep -qE "(query|execute|exec|raw)" "$ARQUIVO" 2>/dev/null; then
    # String concatenation em queries SQL
    if grep -nE '(query|execute).*["\`].*\$[a-zA-Z]' "$ARQUIVO" 2>/dev/null | grep -v "param|bind|prepare"; then
        LINHAS=$(grep -nE '(query|execute).*["\`].*\$[a-zA-Z]' "$ARQUIVO" | grep -v "param|bind|prepare" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
        reportar_erro \
            "$ARQUIVO" \
            "Possível injeção SQL (linhas: $LINHAS)" \
            "Use prepared statements: query('SELECT * FROM users WHERE id = $1', [id])"
        ERROS=$((ERROS + 1))
    fi
fi

# -----------------------------------------------------------------------------
# 8. VERIFICAR INPUT SEM SANITIZAÇÃO
# -----------------------------------------------------------------------------
if grep -qE "(innerHTML|dangerouslySetInnerHTML|document\.write)" "$ARQUIVO" 2>/dev/null; then
    LINHAS=$(grep -nE "(innerHTML|dangerouslySetInnerHTML|document\.write)" "$ARQUIVO" | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
    reportar_erro \
        "$ARQUIVO" \
        "Uso de innerHTML/dangerouslySetInnerHTML (linhas: $LINHAS)" \
        "Sanitize o input ou use textContent/innerText"
    ERROS=$((ERROS + 1))
fi

# -----------------------------------------------------------------------------
# 9. VERIFICAR IMPORTS CONSISTENTES (mesmo projeto)
# -----------------------------------------------------------------------------
# Se existir padrão de import, verificar consistência
if [ -d "$PROJETO_DIR/frontend" ] || [ -d "$PROJETO_DIR/backend" ]; then
    # Verificar se está usando @/ para imports absolutos (padrão Kothar)
    if grep -qE "^import.*from ['\"]\.\./" "$ARQUIVO" 2>/dev/null; then
        # Tem import relativo profundo
        if grep -nE "^import.*from ['\"]\.\./\.\./" "$ARQUIVO" > /dev/null; then
            LINHAS=$(grep -nE "^import.*from ['\"]\.\./\.\./" "$ARQUIVO" | head -3 | cut -d: -f1 | tr '\n' ',' | sed 's/,$//')
            reportar_erro \
                "$ARQUIVO" \
                "Imports relativos profundos encontrados (linhas: $LINHAS)" \
                "Use alias @/: import from '@/componentes/botao'"
            ERROS=$((ERROS + 1))
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 10. VERIFICAR CONSISTÊNCIA DE AUTENTICAÇÃO (Frontend)
# -----------------------------------------------------------------------------
if [[ "$ARQUIVO" == *.tsx ]] || [[ "$ARQUIVO" == *.jsx ]]; then
    # Se parece com página mas não tem auth
    if echo "$ARQUIVO" | grep -qE "pagina-|page-" 2>/dev/null; then
        if ! grep -qE "(useAutenticacao|verificarToken|useAuth|isAuthenticated)" "$ARQUIVO" 2>/dev/null; then
            # Verificar se é rota pública intencional
            if ! grep -qE "(login|cadastro|public|esqueci|recover)" "$ARQUIVO" 2>/dev/null; then
                reportar_erro \
                    "$ARQUIVO" \
                    "Página sem verificação de autenticação" \
                    "Adicione: const { verificarToken } = useAutenticacao(); useEffect(() => { if (!verificarToken()) router.push('/login'); }, []);"
                ERROS=$((ERROS + 1))
            fi
        fi
    fi
fi

# =============================================================================
# RESULTADO
# =============================================================================

echo ""
echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${AZUL}  CODEGEN POST-VALIDATE${RESET}"

if [ "$ERROS" -eq 0 ]; then
    echo -e "${VERDE}  ✅ Nenhum problema encontrado${RESET}"
    echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
    exit 0
else
    echo -e "${VERMELHO}  ❌ $ERROS problema(s) encontrado(s)${RESET}"
    echo -e "${AZUL}═══════════════════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "${VERMELHO}  Operação bloqueada. Corrija os problemas acima antes de continuar.${RESET}"
    echo ""
    echo -e "${AZUL}  Dica: Use a skill 'codegen' para mais orientações${RESET}"
    echo ""
    exit 1
fi
