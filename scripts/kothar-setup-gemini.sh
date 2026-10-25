#!/bin/bash
# ============================================
# KOTHAR - Setup do Gemini CLI
# ============================================

echo "═══════════════════════════════════════════"
echo "🎵 KOTHAR - Setup do Gemini CLI"
echo "═══════════════════════════════════════════"
echo ""

# Verificar versão do Node.js
echo "📋 Verificando pré-requisitos..."
NODE_VERSION=$(node -v 2>/dev/null)
echo "   Node.js: $NODE_VERSION"

if [[ "$NODE_VERSION" < "v20" ]]; then
    echo "   ⚠️  Node.js < v20 detectado - necessário >= v20"
    echo ""
    echo "   Para atualizar Node.js, execute:"
    echo "   sudo npm install -g n"
    echo "   sudo n latest"
fi

# Opção 1: Instalar localmente (sem sudo)
echo ""
echo "═══════════════════════════════════════════"
echo "📦 Opção 1: Instalação LOCAL (sem root)"
echo "═══════════════════════════════════════════"
echo ""
echo "   Execute:"
echo "   mkdir -p ~/.local/npm-global"
echo "   npm config set prefix ~/.local/npm-global"
echo "   npm install -g @google/gemini-cli"
echo "   export PATH=\$HOME/.local/npm-global/bin:\$PATH"
echo ""

# Opção 2: Instalar com sudo
echo "═══════════════════════════════════════════"
echo "🔐 Opção 2: Instalação GLOBAL (com sudo)"
echo "═══════════════════════════════════════════"
echo ""
echo "   Execute:"
echo "   sudo npm install -g @google/gemini-cli"
echo ""

# Opção 3: Usar Kothar CLI local (já funciona)
echo "═══════════════════════════════════════════"
echo "✅ Opção 3: Usar KOTHAR CLI LOCAL (já disponível!)"
echo "═══════════════════════════════════════════"
echo ""
echo "   O Kothar CLI já está instalado em:"
echo "   ~/kothar/scripts/kothar-cli.sh"
echo ""
echo "   Para criar um alias, adicione ao ~/.bashrc:"
echo "   alias kothar='/home/bruno/kothar/scripts/kothar-cli.sh'"
echo "   alias /kothar='/home/bruno/kothar/scripts/kothar-cli.sh'"
echo ""
echo "   Depois execute: source ~/.bashrc"
echo ""

echo "═══════════════════════════════════════════"
echo "📌 Verificação: O Kothar CLI já funciona AGORA!"
echo "═══════════════════════════════════════════"
echo ""
echo "   Testando..."
~/kothar/scripts/kothar-cli.sh status | head -10
