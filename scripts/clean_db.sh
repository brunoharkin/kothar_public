#!/bin/bash
# KOTHAR SCRIPT: Clean DB (Purge Sessions)

echo "🔥 INICIANDO EXPURGO TOTAL DE SESSÕES (HARD RESET)..."

API_URL="http://localhost:8080"

echo "📡 Conectando ao backend em $API_URL..."

RESPONSE=$(curl -s -X DELETE "${API_URL}/api/sessions/action/purge_all")

if echo "$RESPONSE" | grep -q '"deleted":true' || echo "$RESPONSE" | grep -q '"deleted": true'; then
    echo "✅ Banco de Dados limpo com sucesso! Nenhuma sessão antiga restante."
    # Apagar caches locais que seguram IDs de sessões mortas
    rm -f /tmp/kothar_session_*.json /tmp/kothar_cursor_*.txt 2>/dev/null
    echo "✅ Cache temporário limpo."
else
    echo "❌ Falha ao expurgar o banco. Resposta: $RESPONSE"
    exit 1
fi

echo "🧹 Você também deve garantir que Neo4j e ChromaDB foram limpos se aplicável."
exit 0
