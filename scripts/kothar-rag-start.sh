#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${CHROMA_HOST:-127.0.0.1}"
PORT="${CHROMA_PORT:-8000}"
URL="${CHROMA_URL:-http://${HOST}:${PORT}}"
STATE_FILE="${KOTHAR_RAG_STATE_FILE:-$ROOT/.rag-index-state.json}"
DATA_PATH="${KOTHAR_CHROMA_DATA_PATH:-$ROOT/.chroma-data}"
PID_FILE="${KOTHAR_RAG_PID_FILE:-$ROOT/.kothar-rag.pid}"
LOG_FILE="${KOTHAR_RAG_LOG_FILE:-$ROOT/.kothar-rag.log}"

chunks=$(grep -o '"indexed_chunks"[[:space:]]*:[[:space:]]*[0-9]*' "$STATE_FILE" 2>/dev/null \
    | grep -o '[0-9]*' | tail -1 || true)
if [ "${chunks:-0}" -le 0 ]; then
    echo "[ERRO] Índice RAG vazio ou ausente: $STATE_FILE" >&2
    exit 1
fi

if curl -fsS --max-time 2 "$URL/api/v2/heartbeat" >/dev/null 2>&1; then
    echo "[OK] RAG já ativo em $URL (${chunks} chunks)"
    exit 0
fi

CHROMA_BIN="$ROOT/.venv/bin/chroma"
if [ ! -x "$CHROMA_BIN" ]; then
    echo "[ERRO] Serviço Chroma não disponível em $CHROMA_BIN" >&2
    exit 1
fi

mkdir -p "$DATA_PATH"
nohup "$CHROMA_BIN" run --path "$DATA_PATH" --host "$HOST" --port "$PORT" \
    >"$LOG_FILE" 2>&1 &
echo "$!" >"$PID_FILE"

for _ in $(seq 1 15); do
    if curl -fsS --max-time 2 "$URL/api/v2/heartbeat" >/dev/null 2>&1; then
        echo "[OK] RAG iniciado em $URL (${chunks} chunks)"
        exit 0
    fi
    sleep 1
done

echo "[ERRO] Chroma não respondeu; consulte $LOG_FILE" >&2
exit 1
