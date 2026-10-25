#!/usr/bin/env bash
# ==============================================================================
# KOTHAR v4.0 — One-Click Universal Installer & Onboarding Bootstrap
# Compatível com: Copilot, Claude Code, Gemini CLI, Cursor e Codex
# ==============================================================================
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC=""

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║             ⚡ KOTHAR v4.0 — INSTALADOR UNIVERSAL                ║"
echo "║          Orquestrador Disciplinado de IA Multi-IDE               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Verificar pré-requisitos de sistema
echo "🔍 [1/6] Verificando ambiente de sistema..."
command -v python3 >/dev/null || {
  echo "❌ [ERRO] Python 3 é obrigatório para rodar o Kothar." >&2
  exit 1
}

command -v git >/dev/null || {
  echo "❌ [ERRO] Git é obrigatório para versionamento do Kothar." >&2
  exit 1
}

# 2. Configurar Virtualenv e Dependências Core
echo "📦 [2/6] Preparando ambiente isolado (.venv)..."
if [ ! -d "$ROOT/.venv" ]; then
  python3 -m venv "$ROOT/.venv"
fi
PYTHON_EXEC="$ROOT/.venv/bin/python"

# Instalar dependências essenciais de RAG e infraestrutura
"$ROOT/.venv/bin/pip" install --quiet --upgrade pip
"$ROOT/.venv/bin/pip" install --quiet chromadb fastapi uvicorn pydantic python-dotenv || {
  echo "⚠️ Falha ao instalar pacotes via pip. Verifique sua conexão." >&2
}

# 3. Onboarding & Configuração de Identidade
echo "👤 [3/6] Configuração de Operador e Identidade..."
CONFIG_FILE="$ROOT/configuracao/kothar-config.json"
USER_CONFIG_DIR="$HOME/.kothar"
USER_CONFIG_FILE="$USER_CONFIG_DIR/config.json"

if [ ! -f "$CONFIG_FILE" ] && [ ! -f "$USER_CONFIG_FILE" ]; then
  INPUT_NAME=""
  INPUT_ORG=""
  INPUT_VAULT=""

  if [ -t 0 ]; then
    read -p "👉 Nome do Operador [$(whoami)]: " INPUT_NAME || true
    read -p "👉 Empresa / Organização [Workspace]: " INPUT_ORG || true
    read -p "👉 Caminho do Cofre de Memória [$HOME/Cofre]: " INPUT_VAULT || true
  fi

  OP_NAME="${INPUT_NAME:-$(whoami)}"
  OP_ORG="${INPUT_ORG:-Workspace}"
  OP_VAULT="${INPUT_VAULT:-$HOME/Cofre}"

  mkdir -p "$ROOT/configuracao"
  mkdir -p "$OP_VAULT"
  mkdir -p "$ROOT/.chroma-data"

  cat <<CFG_EOF > "$CONFIG_FILE"
{
  "versao": "4.0.0",
  "operador": {
    "nome": "$OP_NAME",
    "empresa": "$OP_ORG",
    "cargo": "Desenvolvedor / Operador"
  },
  "caminhos": {
    "kothar_dir": "$ROOT",
    "vault_dir": "$OP_VAULT",
    "chroma_dir": "$ROOT/.chroma-data"
  },
  "rag": {
    "ativo": true,
    "modo": "persistente_local"
  }
}
CFG_EOF
  echo "✅ Configuração salva em configuracao/kothar-config.json"
else
  echo "✅ Configuração existente detectada e preservada."
fi

# 4. Auditoria e Alerta de Chaves de API
echo "🔑 [4/6] Verificando chaves de API e capacidades dos modelos..."
"$PYTHON_EXEC" "$ROOT/scripts/verificar_chaves_api.py" || true

# 5. Validação Funcional do RAG (GATE OBRIGATÓRIO)
echo "🧠 [5/6] Verificação Funcional do RAG (ChromaDB)..."
if ! "$PYTHON_EXEC" "$ROOT/scripts/test_rag_functional.py"; then
  echo ""
  echo "❌ [BLOQUEIO TOTAL] O motor de RAG falhou no teste funcional." >&2
  echo "   O Kothar exige RAG ativo para operar em produção." >&2
  echo "   Corrija o erro acima e tente novamente." >&2
  exit 1
fi

# 6. Sincronização com IDEs (VS Code, Copilot, Claude, Gemini, Codex)
echo "🔄 [6/6] Sincronizando integrações nativas com IDEs..."
chmod +x "$ROOT/scripts/sync-ides.sh"
"$ROOT/scripts/sync-ides.sh" --workspace

echo ""
echo "🎉 [SUCESSO] KOTHAR v4.0 INSTALADO E PRONTO PARA ORQUESTRAR!"
echo "   Operador e RAG validados com 100% de integridade."
echo "   Para iniciar uma sessão em qualquer IDE suportada, digite: /kothar"
echo ""
