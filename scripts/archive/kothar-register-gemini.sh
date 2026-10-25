#!/bin/bash
# ============================================
# KOTHAR - Registro no Antigravity (Gemini CLI)
# ============================================

set -e

KOTHAR_DIR="/home/bruno/kothar"
GEMINI_DIR="/home/bruno/.gemini"
ANTIGRAVITY_DIR="$GEMINI_DIR/antigravity"
COMMANDS_DIR="$GEMINI_DIR/commands"

echo "═══════════════════════════════════════════"
echo "🎵 KOTHAR - Registro no Antigravity"
echo "═══════════════════════════════════════════"
echo ""

# 1. Verificar/Criar diretórios
echo "📁 Verificando diretórios..."
mkdir -p "$ANTIGRAVITY_DIR"
mkdir -p "$COMMANDS_DIR"
echo "   ✅ Diretórios OK"

# 2. Copiar definição do Kothar
if [ -f "$KOTHAR_DIR/KOTHAR.md" ]; then
    cp "$KOTHAR_DIR/KOTHAR.md" "$ANTIGRAVITY_DIR/KOTHAR.md"
    echo "   ✅ Definição copiada para $ANTIGRAVITY_DIR/KOTHAR.md"
fi

# 3. Copiar GEMINI.md (instruções do sistema)
if [ -f "$KOTHAR_DIR/GEMINI.md" ]; then
    cp "$KOTHAR_DIR/GEMINI.md" "$GEMINI_DIR/GEMINI.md" 2>/dev/null
    echo "   ✅ GEMINI.md copiado para $GEMINI_DIR/"
fi

# 4. Copiar custom command
if [ -f "$COMMANDS_DIR/kothar.toml" ]; then
    echo "   ✅ Custom command /kothar já instalado"
fi

# 5. Verificar MCP config
echo ""
echo "🔌 Verificando MCP config..."
if [ -s "$ANTIGRAVITY_DIR/mcp_config.json" ]; then
    echo "   ⚠️  mcp_config.json já tem conteúdo (não será modificado)"
else
    cp "$KOTHAR_DIR/regras/mcp.json" "$ANTIGRAVITY_DIR/mcp_config.json" 2>/dev/null
    echo "   ✅ mcp_config.json configurado"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "✅ KOTHAR REGISTRADO NO ANTIGRAVITY!"
echo "═══════════════════════════════════════════"
echo ""
echo "📂 Arquivos criados:"
echo "   - $ANTIGRAVITY_DIR/KOTHAR.md"
echo "   - $COMMANDS_DIR/kothar.toml"
echo ""
echo "🎯 Como usar no Gemini/Antigravity:"
echo ""
echo "   1. Abra o Gemini CLI ou Antigravity"
echo "   2. Digite: /kothar"
echo "   3. Ou: /kothar status"
echo ""
echo "💡 Os seguintes comandos estão disponíveis:"
echo "   - /kothar           → Saudação inicial"
echo "   - /kothar status    → Status completo"
echo "   - /kothar start     → Iniciar gravação"
echo "   - /kothar stop      → Parar gravação"
echo "   - /kothar orquestrar → Iniciar orquestração"
echo "   - /kothar ajuda     → Ver menu completo"
echo ""
echo "💡 Para instalar o Gemini CLI (se ainda não tiver):"
echo "   npm install -g @google/gemini-cli"
echo ""
echo "═══════════════════════════════════════════"
