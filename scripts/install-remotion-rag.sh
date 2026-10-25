#!/bin/bash
# =========================================================================
# Kothar - Integração RAG Remotion (Boilerplate & Docs)
# =========================================================================

set -euo pipefail

log() { echo -e "\033[0;32m[KOTHAR]\033[0m $1"; }

COFRE_DIR="$HOME/cofre/planejamento"
BOILERPLATE_DIR="$HOME/kothar/scratch/Kothar-Remotion-Boilerplate"

log "Iniciando a integração do framework Remotion no Kothar..."

# 1. Configurando a "Fonte da Verdade" no RAG
log "Criando documento mestre de guidelines do Remotion no Cofre..."
mkdir -p "$COFRE_DIR"
cat << 'EOF' > "$COFRE_DIR/remotion_guidelines.md"
# Remotion Framework - Kothar Guidelines
O Kothar usa Remotion para criação programática de vídeos.
Todo criativo deve ser implementado via React.

## Regras de Ouro
1. **Nunca use setInterval/setTimeout**. O tempo no Remotion é ditado por `useCurrentFrame()`.
2. As cenas devem ser modulares, usando o componente `<Sequence>`.
3. Animações devem usar funções matemáticas de interpolação:
```tsx
const frame = useCurrentFrame();
const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
```
4. Valores e textos devem ser recebidos via Props, para automação em massa.
EOF

# 2. Setup do Boilerplate
log "Clonando/Criando o Kothar-Remotion-Boilerplate inicial..."
if [ ! -d "$BOILERPLATE_DIR" ]; then
    # Por padrão, vamos gerar um projeto remotion simples no modo headless
    mkdir -p "$HOME/kothar/scratch"
    cd "$HOME/kothar/scratch"
    npx create-video@latest Kothar-Remotion-Boilerplate --template tailwind --packageManager npm
    log "Boilerplate gerado em $BOILERPLATE_DIR!"
else
    log "Boilerplate já existe."
fi

log "Integração do Remotion concluída. O Agente de Redes Sociais já pode ser orquestrado!"
