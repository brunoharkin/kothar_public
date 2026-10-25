#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REGISTRY="$ROOT/configuracao/kothar-agent-registry.json"
OWNERSHIP="$ROOT/configuracao/kothar-ownership.json"
TRANSITIONS="$ROOT/configuracao/kothar-transitions.json"

command -v jq >/dev/null || {
  echo "[ERRO] jq é obrigatório para validar o registro de agents." >&2
  exit 1
}

for file in "$REGISTRY" "$OWNERSHIP" "$TRANSITIONS"; do
  [[ -f "$file" ]] || {
    echo "[ERRO] Manifesto ausente: ${file#$ROOT/}" >&2
    exit 1
  }
  jq empty "$file" || {
    echo "[ERRO] JSON inválido: ${file#$ROOT/}" >&2
    exit 1
  }
done

python3 "$ROOT/scripts/validate-kothar-contracts.py"
python3 "$ROOT/scripts/kothar-agent-security-audit.py" "$ROOT" --json >/dev/null

agent_count=0
while IFS= read -r agent; do
  [[ -n "$agent" ]] || continue
  file="$ROOT/.github/agents/$agent.agent.md"
  [[ -f "$file" ]] || {
    echo "[ERRO] Agent sem manifesto nativo: $agent" >&2
    exit 1
  }
  grep -q '^---$' "$file" || {
    echo "[ERRO] Frontmatter ausente: ${file#$ROOT/}" >&2
    exit 1
  }
  grep -q '^name: ' "$file" || {
    echo "[ERRO] name ausente: ${file#$ROOT/}" >&2
    exit 1
  }
  grep -q '^description: ' "$file" || {
    echo "[ERRO] description ausente: ${file#$ROOT/}" >&2
    exit 1
  }
  agent_count=$((agent_count + 1))
done < <(jq -r '.profiles.full[] | select(type == "string")' "$REGISTRY" | sort -u)

hook_count=$(find "$ROOT/.github/hooks" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
[[ "$hook_count" -gt 0 ]] || {
  echo "[ERRO] Nenhum hook nativo encontrado." >&2
  exit 1
}

echo "[OK] Agents verificados: $agent_count"
echo "[OK] Hooks encontrados: $hook_count"
echo "[OK] Ownership e manifests válidos"
