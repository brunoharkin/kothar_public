#!/bin/bash
# =========================================================================
# Kothar - GPU Quick Test (testa conexão sem baixar modelo pesado)
# =========================================================================

SESSION_NAME="kothar-gpu-worker"

echo "🧪 Teste rápido de GPU Colab"
echo ""

# Verifica se sessão existe
echo "[1/4] Verificando sessão..."
colab status -s "$SESSION_NAME" 2>&1 | head -5
echo ""

# Testa se GPU está disponível
echo "[2/4] Verificando GPU..."
colab exec -s "$SESSION_NAME" 'nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv' --timeout 30 2>&1
echo ""

# Testa se Ollama está rodando
echo "[3/4] Verificando Ollama..."
colab exec -s "$SESSION_NAME" 'curl -s http://localhost:11434/api/version 2>&1 || echo "Ollama não está rodando"' --timeout 30 2>&1
echo ""

# Testa modelo mínimo
echo "[4/4] Testando modelo leve (llama3.2:1b)..."
colab exec -s "$SESSION_NAME" 'echo "Ola" | /usr/local/bin/ollama run llama3.2:1b --verbose 2>&1 | tail -10' --timeout 120 2>&1
echo ""

echo "✅ Teste completo!"
echo ""
echo "Se Ollama não está rodando, execute:"
echo "  ~/kothar/scripts/colab_gpu_spinup.sh llama3.2:3b <ngrok_token>"
