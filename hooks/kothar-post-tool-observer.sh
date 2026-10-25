#!/bin/bash
# =============================================================
# KOTHAR v5.0 — Post Tool Observer (TRACE COMPLETO)
# Engenheiro Kothar | Ugarit Digital
# =============================================================
# Captura TODOS os eventos pós-ferramenta
# =============================================================

# Este script é chamado via hook do Claude CLI após cada ferramenta
# O hook de Python (kothar-trace-recorder.py) é quem faz o trabalho real

TRACE_DIR="${HOME}/.claude/kothar-trace"
RECORDER="$HOME/kothar/hooks/kothar-trace-recorder.py"

# Passar o evento JSON para o recorder Python
if [ -p /dev/stdin ]; then
    # Hook chamado com dados stdin
    python3 "$RECORDER"
else
    # Inicializar se necessário
    python3 "$RECORDER" session 2>/dev/null || python3 "$RECORDER" init
fi

exit 0
