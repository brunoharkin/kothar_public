#!/bin/bash
# =========================================================================
# Kothar - Integração PersonaLive (Avatar Specialist)
# =========================================================================

set -euo pipefail

log() { echo -e "\033[0;35m[KOTHAR]\033[0m $1"; }

COFRE_DIR="$HOME/cofre/planejamento"
AVATAR_DIR="$HOME/cofre/marketing/avatares"

log "Criando infraestrutura estrita do PersonaLive..."

# 1. Pastas do Cofre para isolar os rostos (Anti-Alucinação)
mkdir -p "$AVATAR_DIR"
log "Pasta de Avatares autorizados criada em: $AVATAR_DIR"

# 2. Criando o Manual de Especificação da API no Cofre para o RAG
cat << 'EOF' > "$COFRE_DIR/personalive_api_spec.md"
# PersonaLive REST API Spec - Kothar Guidelines

Este documento define como o Agente de Avatares deve interagir com o backend do PersonaLive.

## Fluxo Resiliente (Fila de Renderização)
Como a inferência do PersonaLive consome VRAM (12GB+ GPU), é estritamente proibido disparar requisições pesadas cegas.
1. O Agente **DEVE** fazer um `GET http://kothar_gpu_cluster:8188/api/system/status`.
2. Se `executing > 0`, a GPU está OCUPADA.
3. Se ocupada, o Agente **NÃO** deve falhar a tarefa, mas reportar o status `"GPU_BUSY_QUEUED"` ao Redis/Orquestrador.

## Payload de Renderização (ComfyUI Workflow API)
Quando a GPU estiver livre (`executing == 0`), faça o `POST` para `http://kothar_gpu_cluster:8188/api/prompt` com o seguinte formato básico:
```json
{
  "prompt": {
    "3": {
      "class_type": "LoadImage",
      "inputs": { "image": "/vault/marketing/avatares/bruno_harkin.jpg" }
    },
    "4": {
      "class_type": "LoadAudio",
      "inputs": { "audio": "/tmp/tts_generated_voice.wav" }
    },
    "5": {
      "class_type": "PersonaLiveNode",
      "inputs": {
        "image": ["3", 0],
        "audio": ["4", 0]
      }
    }
  }
}
```
*Sempre respeite as referências oficiais presentes na pasta de avatares.*
EOF

log "Diretrizes e especificações do PersonaLive integradas ao RAG!"
log "Agente Avatar Specialist pronto para operar."
