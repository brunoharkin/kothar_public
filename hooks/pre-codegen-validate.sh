#!/bin/bash
# =============================================================================
# PRE-CODEGEN-VALIDATE — Executa ANTES de qualquer Write/Edit
# =============================================================================
# Verifica se o código a ser criado NÃO viola padrões Kothar
# Se detectar problema, BLOQUEIA a criação e avisa o agente
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
# FUNÇÕES DE ALERTA
# =============================================================================

alerta_bloqueio() {
    echo -e "${VERMELHO}🛑 BLOQUEADO - $1${RESET}"
    echo -e "${AMARELO}   Motivo: $2${RESET}"
    echo -e "${AZUL}   Ação: $3${RESET}"
    echo ""
}

alerta_aviso() {
    echo -e "${AMARELO}⚠️ AVISO - $1${RESET}"
    echo -e "${AMARELO}   $2${RESET}"
}

sucesso() {
    echo -e "${VERDE}✅ $1${RESET}"
}

# =============================================================================
# EXTRAIR INFORMAÇÕES DO CALL
# =============================================================================

# Pega o tool call que está prestes a executar
TOOL_CALL="${KOTHAR_TOOL_CALL:-}"
ARQUIVO_ALVO="${KOTHAR_FILE_PATH:-}"
CONTEUDO="${KOTHAR_CONTENT:-}"

# Se não houver variáveis de ambiente, tenta extrair do argumento
if [ -z "$TOOL_CALL" ] && [ -n "${1:-}" ]; then
    ARQUIVO_ALVO="$1"
    shift
fi

if [ -z "$ARQUIVO_ALVO" ]; then
    echo -e "${AMARELO}⚠️ AVISO: Arquivo alvo não identificado${RESET}"
    exit 0  # Não bloqueia, só avisa
fi

# =============================================================================
# VERIFICAÇÕES DE BLOQUEIO
# =============================================================================

BLOQUEADO=0

# -----------------------------------------------------------------------------
# 1. VERIFICAR SE É ARQUIVO DUPLICADO
# -----------------------------------------------------------------------------
NOME_BASE=$(basename "$ARQUIVO_ALVO" | sed 's/\.[^.]*$//')
EXTENSAO=$(basename "$ARQUIVO_ALVO" | sed 's/.*\.//')

# Buscar arquivos com nome similar
DIRETORIO=$(dirname "$ARQUIVO_ALVO")
PROJETO_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Padrões duplicados conhecidos
if echo "$NOME_BASE" | grep -qE "(v2|v3|v4|_v2|_v3|_new|_old|_backup|_copia)$"; then
    # Buscar versão sem sufixo
    NOME_SEM_SUFIXO=$(echo "$NOME_BASE" | sed -E 's/(v2|v3|v4|_v2|_v3|_new|_old|_backup|_copia)$//')
    ACHADO=$(find "$PROJETO_DIR" -name "${NOME_SEM_SUFIXO}.*" -type f 2>/dev/null | head -5)

    if [ -n "$ACHADO" ]; then
        alerta_bloqueio \
            "ARQUIVO DUPLICADO DETECTADO" \
            "Já existe: $ACHADO" \
            "Edite o arquivo existente ao invés de criar duplicata"
        BLOQUEADO=1
    fi
fi

# -----------------------------------------------------------------------------
# 2. VERIFICAR NOMES GENÉRICOS PROIBIDOS
# -----------------------------------------------------------------------------
if echo "$NOME_BASE" | grep -qE "^(index|utils|helpers|app|main|test|config|settings)$"; then
    alerta_bloqueio \
        "NOME GENÉRICO PROIBIDO" \
        "'$NOME_BASE' não descreve a função do arquivo" \
        "Use nome descritivo em português: servico-login.ts, pagina-cadastro.tsx"
    BLOQUEADO=1
fi

# -----------------------------------------------------------------------------
# 3. VERIFICAR SE ESTÁ NO LOCAL CORRETO
# -----------------------------------------------------------------------------
if [[ "$ARQUIVO_ALVO" == *"/src/"* ]] || [[ "$ARQUIVO_ALVO" == *"/lib/"* ]]; then
    alerta_bloqueio \
        "PASTA GENÉRICA PROIBIDA" \
        "Pastas 'src/' e 'lib/' são proibidas nos padrões Kothar" \
        "Use organização por feature: backend/servicos/, frontend/paginas/"
    BLOQUEADO=1
fi

# -----------------------------------------------------------------------------
# 4. VERIFICAR MISTURA DE IDIOMAS
# -----------------------------------------------------------------------------
# Mistura real = prefixo PT + suffix EN (ex: pagina-login-page.tsx)
# NÃO é mistura = prefixo PT + termo técnico universal (login, dashboard, config)
PARALAVRAS_PT="(pagina|servico|componente|utilitario|banco|modelo|rotas|configuracao|usuario|cadastro)"
PARALAVRAS_EN="(page|service|component|util|db|model|routes|config|user|signup)"

# Verificar se tem palavra PT E palavra EN (não universais)
if echo "$NOME_BASE" | grep -qE "$PARALAVRAS_PT"; then
    if echo "$NOME_BASE" | grep -qE "$PARALAVRAS_EN"; then
        alerta_bloqueio \
            "MISTURA DE IDIOMAS" \
            "Nome mistura português e inglês" \
            "Use apenas um idioma: 'pagina-login.tsx' ou 'page-login.tsx'"
        BLOQUEADO=1
    fi
fi

# -----------------------------------------------------------------------------
# 5. VERIFICAR CONTEÚDO SENSÍVEL NO CÓDIGO
# -----------------------------------------------------------------------------
if [ -n "$CONTEUDO" ]; then
    # Credenciais hardcoded
    if echo "$CONTEUDO" | grep -qE "(sk-|api[_-]?key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9]"; then
        alerta_bloqueio \
            "CREDENCIAL HARDCODED DETECTADA" \
            "API key ou senha no código" \
            "Use: os.getenv('VARIAVEL') e configure no .env"
        BLOQUEADO=1
    fi

    # Senha em texto puro em logs
    if echo "$CONTEUDO" | grep -qiE "log.*(password|senha|passwd)"; then
        if echo "$CONTEUDO" | grep -qiE "log.*['\"].*\$"; then
            alerta_bloqueio \
                "DADOS SENSÍVEIS EM LOG" \
                "Variável potencialmente exposta em log" \
                "Logue apenas IDs, não valores: logger.info('Login: ' + userId)"
            BLOQUEADO=1
        fi
    fi
fi

# -----------------------------------------------------------------------------
# 6. VERIFICAR VERSÕES INSECURAS
# -----------------------------------------------------------------------------
if [ -n "$CONTEUDO" ] && echo "$CONTEUDO" | grep -qE "(npm install|pip install|requirements\.txt|package\.json)"; then
    # Versão latest ou *
    if echo "$CONTEUDO" | grep -qE "@latest|@\*|==\*"; then
        alerta_bloqueio \
            "VERSÃO NÃO BLOQUEADA" \
            "Usando 'latest' ou '*' que pode instalar versão insegura" \
            "Bloqueie versão específica: express@4.18.2"
        BLOQUEADO=1
    fi
fi

# -----------------------------------------------------------------------------
# 7. VERIFICAR SEPARAÇÃO BACKEND/FRONTEND
# -----------------------------------------------------------------------------
# Se é código frontend, verificar se está em pasta frontend
if echo "$CONTEUDO" | grep -qE "(import.*react|export.*function|const.*use)"; then
    if [[ "$ARQUIVO_ALVO" != *"/frontend/"* ]] && [[ "$ARQUIVO_ALVO" != *"/paginas/"* ]]; then
        # Também aceita componentes-compartilhados
        if [[ "$ARQUIVO_ALVO" != *"/componentes-compartilhados/"* ]]; then
            alerta_aviso \
                "POSSÍVEL FRONTEND FORA DA PASTA" \
                "Código React/Vue fora de /frontend ou /paginas"
        fi
    fi
fi

# Se é código backend Python/Node, verificar se está em pasta backend
if echo "$CONTEUDO" | grep -qE "(def |async def |import os|import sys|const express|import http)"; then
    if [[ "$ARQUIVO_ALVO" != *"/backend/"* ]] && [[ "$ARQUIVO_ALVO" != *"/servicos/"* ]]; then
        alerta_aviso \
            "POSSÍVEL BACKEND FORA DA PASTA" \
            "Código servidor fora de /backend ou /servicos"
    fi
fi

# =============================================================================
# RESULTADO
# =============================================================================

if [ "$BLOQUEADO" -eq 1 ]; then
    echo ""
    echo -e "${VERMELHO}═══════════════════════════════════════════════════════════════${RESET}"
    echo -e "${VERMELHO}  ❌ CRIAÇÃO BLOQUEADA PELO CODEGEN${RESET}"
    echo -e "${VERMELHO}═══════════════════════════════════════════════════════════════${RESET}"
    echo ""
    echo -e "${AZUL}  O arquivo '$ARQUIVO_ALVO' viola padrões Kothar.${RESET}"
    echo -e "${AZUL}  Corrija os problemas acima e tente novamente.${RESET}"
    echo ""
    echo -e "${AMARELO}  Dica: Use a skill 'codegen' para orientação: /skill codegen${RESET}"
    echo ""
    exit 1  # Bloqueia o tool call
fi

# Se chegou aqui, está liberado
sucesso "Pré-validação CODEGEN aprovada para: $ARQUIVO_ALVO"
exit 0
