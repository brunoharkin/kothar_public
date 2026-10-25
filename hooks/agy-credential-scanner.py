#!/usr/bin/env python3
"""
KOTHAR — Hook: Credential Scanner (PreToolUse)
Roda ANTES de write_to_file e replace_file_content.
Bloqueia escrita de arquivos com credenciais expostas.
Saída: JSON com decision allow/deny
"""
import json
import sys
import re

PADROES_CRITICOS = [
    (r'sk-[a-zA-Z0-9_-]{20,}', 'Anthropic/OpenAI API Key'),
    (r'AKIA[A-Z0-9]{16}', 'AWS Access Key'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Token'),
    (r'glpat-[a-zA-Z0-9_-]{20}', 'GitLab Token'),
    (r'(?i)api[_-]?key\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', 'API Key hardcoded'),
    (r'(?i)password\s*=\s*["\'][^"\']{8,}["\']', 'Password hardcoded'),
    (r'(?i)secret\s*=\s*["\'][^"\']{8,}["\']', 'Secret hardcoded'),
    (r'localStorage\.setItem\(["\']token', 'Token em localStorage'),
]

def main():
    payload = {}
    raw = sys.stdin.read().strip()
    if raw:
        try:
            payload = json.loads(raw)
        except:
            pass

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # Só verifica ferramentas de escrita
    escrita_tools = {"write_to_file", "replace_file_content", "create_file"}
    if tool_name not in escrita_tools:
        print(json.dumps({"decision": "allow"}))
        return

    # Extrai conteúdo dos contratos usados pelos diferentes runtimes.
    conteudo = (
        args.get("CodeContent", "")
        or args.get("ReplacementContent", "")
        or args.get("content", "")
        or args.get("newContent", "")
        or args.get("text", "")
    )
    if not isinstance(conteudo, str):
        conteudo = json.dumps(conteudo, ensure_ascii=False)

    violacoes = []
    for padrao, descricao in PADROES_CRITICOS:
        if re.search(padrao, conteudo):
            violacoes.append(descricao)

    if violacoes:
        motivo = (
            "🔴 KOTHAR GATE G3 — CREDENCIAL DETECTADA:\n"
            + "\n".join(f"  • {v}" for v in violacoes)
            + "\n\nREGRA INEGOCIÁVEL: Credenciais SEMPRE em variáveis de ambiente (.env). "
            + "Nunca no código. Remova e use os.getenv() ou process.env."
        )
        print(json.dumps({
            "decision": "deny",
            "reason": motivo
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
