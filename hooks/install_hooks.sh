#!/usr/bin/env bash
# =============================================================
#  KOTHAR v4.0 — Instalador de Hooks (Gemini + Claude CLI)
#  Engenheiro Kothar | Ugarit Digital
# =============================================================
#  Registra os hooks do Kothar no Gemini CLI e Claude CLI.
#  Uso: bash ~/kothar/hooks/install_hooks.sh
# =============================================================

set -euo pipefail

KOTHAR_DIR="${HOME}/kothar"
HOOK_GEMINI="${KOTHAR_DIR}/hooks/gemini_hook.py"
HOOK_CLAUDE="${KOTHAR_DIR}/hooks/claude_hook.py"

GEMINI_SETTINGS="${HOME}/.gemini/settings.json"
CLAUDE_SETTINGS="${HOME}/.claude/settings.json"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${BOLD}🔗 Instalando Hooks do Kothar...${RESET}"
echo ""

chmod +x "${HOOK_GEMINI}" "${HOOK_CLAUDE}" 2>/dev/null || true

# =============================================================
# GEMINI CLI — ~/.gemini/settings.json
# =============================================================

install_gemini_hook() {
    mkdir -p "${HOME}/.gemini"

    if [ ! -f "${GEMINI_SETTINGS}" ]; then
        echo "{}" > "${GEMINI_SETTINGS}"
    fi

    # Faz backup
    cp "${GEMINI_SETTINGS}" "${GEMINI_SETTINGS}.bak.$(date +%s)"

    # Injeta hooks via python (evita dep de jq)
    python3 - <<PYEOF
import json, sys

with open("${GEMINI_SETTINGS}") as f:
    cfg = json.load(f)

hook_cmd = "python3 ${HOOK_GEMINI}"

cfg.setdefault("hooks", {})
for event in ["PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit"]:
    hooks = cfg["hooks"].setdefault(event, [])
    if hook_cmd not in hooks:
        hooks.append(hook_cmd)

with open("${GEMINI_SETTINGS}", "w") as f:
    json.dump(cfg, f, indent=2)

print("OK")
PYEOF

    echo -e "${GREEN}✅ Gemini CLI hook instalado${RESET} → ${GEMINI_SETTINGS}"
}

# =============================================================
# CLAUDE CLI — ~/.claude/settings.json
# =============================================================

install_claude_hook() {
    mkdir -p "${HOME}/.claude"

    if [ ! -f "${CLAUDE_SETTINGS}" ]; then
        echo "{}" > "${CLAUDE_SETTINGS}"
    fi

    cp "${CLAUDE_SETTINGS}" "${CLAUDE_SETTINGS}.bak.$(date +%s)"

    python3 - <<PYEOF
import json

with open("${CLAUDE_SETTINGS}") as f:
    cfg = json.load(f)

hook_entry = {"type": "command", "command": "python3 ${HOOK_CLAUDE}"}

cfg.setdefault("hooks", {})
for event in ["PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit"]:
    hooks = cfg["hooks"].setdefault(event, [])
    cmds = [h.get("command","") if isinstance(h,dict) else h for h in hooks]
    if hook_entry["command"] not in cmds:
        hooks.append(hook_entry)

with open("${CLAUDE_SETTINGS}", "w") as f:
    json.dump(cfg, f, indent=2)

print("OK")
PYEOF

    echo -e "${GREEN}✅ Claude CLI hook instalado${RESET} → ${CLAUDE_SETTINGS}"
}

# =============================================================
# Executa instalações
# =============================================================

install_gemini_hook
install_claude_hook

echo ""
echo -e "${BOLD}📡 Hooks instalados! O Kothar agora captura automaticamente:${RESET}"
echo "   • Todas as chamadas de ferramenta do Gemini CLI"
echo "   • Todas as chamadas de ferramenta do Claude CLI"
echo "   • Início e fim de sessão"
echo "   • Erros e tokens usados"
echo ""
echo -e "${CYAN}[INFO]${RESET} Certifique-se de que a API do Kothar está rodando: ${BOLD}kothar start${RESET}"
echo ""
