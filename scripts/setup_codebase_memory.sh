#!/bin/bash
#=============================================================
# KOTHAR v5.0 — Setup Codebase Memory MCP
# Instala e configura CBM para integração com Kothar
#=============================================================

set -e

echo "🎯 Kothar Codebase Memory MCP Setup"
echo "=================================="

# 1. Verificar se CBM já está instalado
if command -v codebase-memory-mcp &> /dev/null; then
    echo "✅ Codebase Memory MCP já instalado"
    codebase-memory-mcp --version
else
    echo "📦 Instalando Codebase Memory MCP..."
    curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash

    # Verificar instalação
    if command -v codebase-memory-mcp &> /dev/null; then
        echo "✅ CBM instalado com sucesso"
    else
        echo "❌ Falha ao instalar CBM"
        exit 1
    fi
fi

# 2. Configurar auto-index
echo ""
echo "⚙️  Configurando auto-index..."
codebase-memory-mcp config set auto_index true
codebase-memory-mcp config set auto_watch true
echo "✅ Auto-index habilitado"

# 3. Configurar variáveis de ambiente
echo ""
echo "📝 Adicionando variáveis ao ~/.bashrc..."
CBM_EXPORT='
# Codebase Memory MCP (Kothar Code Intelligence)
export CBM_CACHE_DIR="$HOME/.cache/codebase-memory-mcp"
export CBM_LOG_LEVEL="info"
'

if ! grep -q "CBM_CACHE_DIR" ~/.bashrc 2>/dev/null; then
    echo "$CBM_EXPORT" >> ~/.bashrc
    echo "✅ Variáveis configuradas"
else
    echo "ℹ️  Variáveis já existem no ~/.bashrc"
fi

# 4. Criar diretório de projetos
mkdir -p ~/projects
echo "✅ Diretório de projetos criado"

# 5. Indexar projetos existentes
echo ""
echo "🔍 Indexando projetos existentes..."
PROJECTS_DIR="$HOME/projects"
if [ -d "$PROJECTS_DIR" ] && [ "$(ls -A $PROJECTS_DIR 2>/dev/null)" ]; then
    for dir in "$PROJECTS_DIR"/*; do
        if [ -d "$dir" ] && [ -d "$dir/.git" ]; then
            echo "  Indexando $(basename $dir)..."
            codebase-memory-mcp cli index_repository --repo-path "$dir" 2>/dev/null || true
        fi
    done
    echo "✅ Projetos indexados"
else
    echo "ℹ️  Nenhum projeto encontrado em ~/projects"
fi

# 6. Testar CBM
echo ""
echo "🧪 Testando CBM..."
codebase-memory-mcp cli list_projects

# 7. Resumo
echo ""
echo "=================================="
echo "🎉 Setup completo!"
echo ""
echo "Ferramentas disponíveis:"
echo "  • index_repository  - Indexa repositório"
echo "  • list_projects    - Lista projetos"
echo "  • search_graph     - Busca símbolos"
echo "  • trace_path       - Rastreia dependências"
echo "  • query_graph      - Query Cypher"
echo "  • get_architecture - Resumo da arquitetura"
echo "  • detect_changes   - Detecta mudanças git"
echo "  • find_dead_code   - Encontra código morto"
echo ""
echo "Executar no Kothar:"
echo "  python3 ~/kothar/hooks/cbm_preload.py preload <tarefa>"
echo "  python3 ~/kothar/hooks/cbm_preload.py arch"
echo ""
echo "Visualização 3D do grafo:"
echo "  codebase-memory-mcp --ui=true --port=9749"
echo "=================================="
