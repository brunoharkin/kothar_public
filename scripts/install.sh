#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
MODE="workspace"

case "${1:-}" in
  ""|--workspace) MODE="workspace" ;;
  --user) MODE="user" ;;
  --check) exec "$ROOT/scripts/sync-ides.sh" --workspace --check ;;
  -h|--help)
    echo "Uso: ./install.sh [--workspace|--user|--check]"
    exit 0
    ;;
  *) echo "Opção desconhecida: $1" >&2; exit 2 ;;
esac

command -v python3 >/dev/null || {
  echo "[ERRO] Python 3 é obrigatório para validar as configurações." >&2
  exit 1
}

chmod +x "$ROOT/scripts/sync-ides.sh"
"$ROOT/scripts/sync-ides.sh" "--$MODE"

echo
echo "Kothar sincronizado."
echo "Workspace: $ROOT"
echo "Credenciais: use variáveis de ambiente (HF_TOKEN, ANTHROPIC_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY)."
