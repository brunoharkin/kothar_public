#!/bin/bash
#=============================================================
# KOTHAR v5.0 — Full Start Script
# Inicia todos os serviços necessários
#=============================================================

set -e

echo "🎵 Kothar v5.0 — Iniciando sistema..."
echo ""

# 1. Inicia o CBM daemon se não estiver rodando
echo "🔍 Verificando Codebase Memory MCP..."
if ! curl -s http://localhost:9749 > /dev/null 2>&1; then
    echo "   Iniciando CBM daemon..."
    codebase-memory-mcp daemon start 2>/dev/null || true 2>/dev/null || true
    sleep 2
else
    echo "   ✅ CBM daemon já está rodando"
fi

# 2. Inicia containers Docker
echo ""
echo "🐳 Iniciando containers Docker..."
cd ~/kothar
docker compose up -d

# 3. Aguarda API ficar pronta
echo ""
echo "⏳ Aguardando API ficar pronta..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health/ > /dev/null 2>&1; then
        echo "   ✅ API pronta!"
        break
    fi
    sleep 1
done

# 4. Verifica serviços
echo ""
echo "📊 Status dos serviços:"
echo "   - API Kothar:     $(curl -s http://localhost:8080/health/ | grep -o 'ok' || echo 'offline')"
echo "   - CBM Daemon:     $(curl -s http://localhost:9749 | head -1 | grep -o 'Codebase' || echo 'offline')"
echo "   - Neo4j:          $(curl -s http://localhost:7474 | head -1 | grep -o 'neo4j' || echo 'offline')"
echo "   - ChromaDB:       $(curl -s http://localhost:8000 | head -1 | grep -o 'chromadb' || echo 'offline')"

echo ""
echo "🚀 Kothar v5.0 pronto!"
echo ""
echo "📍 URLs de acesso:"
echo "   - Frontend Kothar:  http://localhost:3030/observatory.html"
echo "   - Frontend Novo:    http://localhost:3031/frontend/index.html"
echo "   - CBM 3D Graph:    http://localhost:9749"
echo "   - API Docs:         http://localhost:8080/docs"
