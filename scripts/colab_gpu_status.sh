#!/bin/bash
# =========================================================================
# Kothar - GPU Status Check
# Verifica o status do túnel e do modelo Ollama
# =========================================================================

SESSION_NAME="kothar-gpu-worker"

echo "🔍 Verificando status da sessão GPU: $SESSION_NAME"
echo ""

# Verifica se a sessão existe
echo "📡 Status da sessão:"
colab status -s "$SESSION_NAME" 2>&1 | head -20
echo ""

# Verifica Ollama
echo "🤖 Status do Ollama:"
colab exec -s "$SESSION_NAME" 'curl -s http://localhost:11434/api/tags 2>&1 | head -20' --timeout 30 2>&1
echo ""

# Verifica modelos instalados
echo "📦 Modelos instalados:"
colab exec -s "$SESSION_NAME" '/usr/local/bin/ollama list 2>&1' --timeout 30 2>&1
echo ""

# Verifica processos do Ollama
echo "⚙️ Processos:"
colab exec -s "$SESSION_NAME" 'ps aux | grep -E "ollama|ngrok" | grep -v grep' --timeout 30 2>&1
