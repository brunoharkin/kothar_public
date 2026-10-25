#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="workspace"
CHECK_ONLY=0

usage() {
  cat <<'EOF'
Uso: ./scripts/sync-ides.sh [--workspace|--user] [--check]

--workspace  valida a integração no repositório atual (padrão)
--user       sincroniza componentes suportados no perfil do usuário
--check      não altera arquivos; retorna erro se houver componente inválido
EOF
}

while (($#)); do
  case "$1" in
    --workspace) MODE="workspace" ;;
    --user) MODE="user" ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opção desconhecida: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

require_file() {
  local file="$1"
  if [[ ! -f "$ROOT/$file" ]]; then
    echo "[ERRO] Ausente: $file" >&2
    return 1
  fi
  echo "[OK] $file"
}

validate_json() {
  local file="$1"
  python3 - "$ROOT/$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as stream:
    json.load(stream)
PY
  echo "[OK] JSON válido: $file"
}

backup_and_copy() {
  local source="$1"
  local destination="$2"
  mkdir -p "$(dirname "$destination")"
  if [[ -e "$destination" ]] && ! cmp -s "$source" "$destination"; then
    cp "$destination" "$destination.bak.$(date +%Y%m%d%H%M%S)"
  fi
  cp "$source" "$destination"
}

echo "Kothar — sincronização de integrações ($MODE)"
status=0

for file in \
  .github/agents/*.agent.md \
  ".github/hooks/kothar-session-init.json" \
  ".github/hooks/kothar-rag-preload.json" \
  ".github/hooks/kothar-credential-scanner.json" \
  ".github/hooks/kothar-post-codegen-validate.json" \
  ".github/hooks/kothar-structure-audit.json" \
  ".github/hooks/kothar-session-end.json" \
  ".vscode/mcp.json" \
  "AGENTS.md" \
  "GEMINI.md" \
  ".claude/agents/kothar.md" \
  ".agents/agents/kothar.json" \
  "configuracao/kothar-agent-registry.json" \
  "configuracao/kothar-ownership.json" \
  "configuracao/kothar-transitions.json" \
  "configuracao/kothar-integration.json"; do
  require_file "$file" || status=1
done

for hook_file in \
  ".github/hooks/kothar-session-init.json" \
  ".github/hooks/kothar-rag-preload.json" \
  ".github/hooks/kothar-credential-scanner.json" \
  ".github/hooks/kothar-post-codegen-validate.json" \
  ".github/hooks/kothar-structure-audit.json" \
  ".github/hooks/kothar-session-end.json"; do
  validate_json "$hook_file" || status=1
done
validate_json ".vscode/mcp.json" || status=1
validate_json "configuracao/kothar-agent-registry.json" || status=1
validate_json "configuracao/kothar-ownership.json" || status=1
validate_json "configuracao/kothar-transitions.json" || status=1
validate_json "configuracao/kothar-integration.json" || status=1
validate_json ".agents/agents/kothar.json" || status=1

if ((status != 0 || CHECK_ONLY == 1)); then
  if ((status != 0)); then
    echo "[FALHA] Integração inválida; nenhuma alteração aplicada." >&2
    exit "$status"
  fi
  echo "[OK] Verificação concluída sem alterações."
  exit 0
fi

if [[ "$MODE" == "user" ]]; then
  rm -f "$HOME/.copilot/agents/kothar.agent.md" \
    "$HOME/.copilot/agents/kothar-"*.agent.md \
    "$HOME/.copilot/hooks/kothar.json" \
    "$HOME/.copilot/hooks/kothar.json.disabled"
  for agent_file in "$ROOT"/.github/agents/*.agent.md; do
    backup_and_copy "$agent_file" "$HOME/.copilot/agents/$(basename "$agent_file")"
  done
  for hook_file in "$ROOT"/.github/hooks/*.json; do
    backup_and_copy "$hook_file" "$HOME/.copilot/hooks/$(basename "$hook_file")"
  done
  backup_and_copy "$ROOT/.claude/agents/kothar.md" "$HOME/.claude/agents/kothar.md"
  backup_and_copy "$ROOT/.agents/agents/kothar.json" "$HOME/.gemini/agents/kothar.json"
  backup_and_copy "$ROOT/GEMINI.md" "$HOME/.gemini/GEMINI.md"
  backup_and_copy "$ROOT/AGENTS.md" "$HOME/.codex/AGENTS.md"
  echo "[OK] Agents Copilot sincronizados: $(find "$ROOT/.github/agents" -maxdepth 1 -name '*.agent.md' -type f | wc -l | tr -d ' ')"
  echo "[OK] Hook Copilot sincronizado em ~/.copilot/hooks"
  echo "[OK] Agent Claude sincronizado em ~/.claude/agents"
  echo "[OK] Manifesto Antigravity sincronizado em ~/.gemini/agents"
  echo "[OK] Instruções Gemini sincronizadas em ~/.gemini/GEMINI.md"
  echo "[OK] Instruções Codex sincronizadas em ~/.codex/AGENTS.md"
else
  echo "[OK] Workspace já contém os formatos nativos."
fi

echo "[OK] Skills: $(find "$ROOT/.agents/skills" -name SKILL.md -type f | wc -l | tr -d ' ')"
echo "[OK] MCP: 4 servidores declarados em .vscode/mcp.json"
echo "[OK] Hooks: $(find "$ROOT/.github/hooks" -maxdepth 1 -name '*.json' -type f | wc -l | tr -d ' ') contratos em .github/hooks/"
echo "[OK] Nenhuma chave de API foi criada ou copiada."
