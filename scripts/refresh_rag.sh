#!/bin/bash
# Kothar RAG Refresh (versão completa)
# Re-indexa TODO o conteúdo, atualiza state, e reinicia backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KOTHAR_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COFRE_DIR="${KOTHAR_VAULT_PATH:-${VAULT_PATH:-$HOME/Cofre}}"
BACKEND_DIR="$KOTHAR_DIR"
STATE_FILE="$SCRIPT_DIR/../.rag_state.json"
if [ -n "${KOTHAR_PYTHON:-}" ] && [ -x "${KOTHAR_PYTHON}" ]; then
  KOTHAR_PYTHON_BIN="$KOTHAR_PYTHON"
elif [ -x "$KOTHAR_DIR/.venv/bin/python" ]; then
  KOTHAR_PYTHON_BIN="$KOTHAR_DIR/.venv/bin/python"
else
  KOTHAR_PYTHON_BIN="$(command -v python3)"
fi

echo "🔄 Kothar RAG Refresh (Full)"
echo "============================"

# 1. Re-indexar tudo (limpa e recria)
echo ""
echo "📚 [1/4] Indexando conteúdo do cofre..."
KOTHAR_VAULT_PATH="$COFRE_DIR" "$KOTHAR_PYTHON_BIN" "$SCRIPT_DIR/index_rag.py" 2>&1 | tail -20

# 2. Atualizar state com novos hashes
echo ""
echo "📝 [2/4] Atualizando state file..."
KOTHAR_VAULT_PATH="$COFRE_DIR" "$KOTHAR_PYTHON_BIN" "$SCRIPT_DIR/rag_watcher.py" --oneshot 2>&1 | tail -5

# 3. Reiniciar backend para recarregar cache
echo ""
echo "🔄 [3/4] Reiniciando backend..."
cd "$BACKEND_DIR"
docker compose restart kothar_api
sleep 5

# 4. Verificar saúde + RAG
echo ""
echo "🏥 [4/4] Verificando saúde e RAG..."
HEALTH=$(curl -s http://localhost:8080/health/detailed)
echo "$HEALTH" | "$KOTHAR_PYTHON_BIN" -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Status geral: {d.get(\"status\")}')
for c, info in d.get('components', {}).items():
    icon = '✅' if info.get('status') == 'healthy' else '❌'
    print(f'  {icon} {c:10}: {info.get(\"status\")}')
"

echo ""
echo "🧪 Testando RAG com pergunta sobre kothar_core..."
RESP=$(curl -s -m 30 -X POST http://localhost:8080/api/ollama/proxy/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kothar-gemma:latest",
    "stream": false,
    "messages": [{"role": "user", "content": "O que é o sistema de Locks do Kothar?"}]
  }' | "$KOTHAR_PYTHON_BIN" -c "
import sys, json
d = json.load(sys.stdin)
r = d.get('message',{}).get('content','')
print(f'  ({d.get(\"eval_count\",0)} tok out, {d.get(\"prompt_eval_count\",0)} in)')
print(f'  {r[:200]}')
" 2>/dev/null)
echo "$RESP"

echo ""
echo "✅ RAG Refresh completo!"
echo ""
echo "💡 Para manter atualizado automaticamente:"
echo "   - Modo daemon:  python3 $SCRIPT_DIR/rag_watcher.py --watch"
echo "   - Git hook:     cp $SCRIPT_DIR/git-post-commit-kothar.sh /home/bruno/cofre/.git/hooks/post-commit"
echo "   - Manual:       bash $SCRIPT_DIR/refresh_rag.sh"
