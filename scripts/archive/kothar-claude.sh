#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# KOTHAR WRAPPER v3.0
# Wrapper que inicia o Claude Code já com o Kothar ativado
# ═══════════════════════════════════════════════════════════════════════════

KOTHAR_DIR="$HOME/kothar"
CLAUDE_BIN="claude"

# Verificar se o Claude Code está instalado
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code não encontrado. Instale com: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

# Verificar se Kothar está instalado
if [ ! -d "$KOTHAR_DIR" ]; then
    echo "❌ Kothar não encontrado em: $KOTHAR_DIR"
    exit 1
fi

# Executar Claude Code
echo ""
echo "🎵 Iniciando Claude Code com Kothar v3.0..."
echo ""

# Passar argumentos para o Claude Code
exec claude "$@"
