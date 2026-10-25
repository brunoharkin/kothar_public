#!/usr/bin/env python3
"""
KOTHAR — Hook: Credential Scanner (PreToolUse)
Roda ANTES de write_to_file e replace_file_content.
Bloqueia escrita de arquivos com credenciais expostas.
Saída: JSON com decision allow/deny
"""
import re
import json
import sys

from hook_contract import normalize

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
    raw = sys.stdin.read().strip()
    try:
        event = normalize(json.loads(raw))
    except (ValueError, json.JSONDecodeError):
        deny("Evento de hook inválido; a escrita não pode ser verificada")
        return

    if not event.is_write:
        print(json.dumps({"decision": "allow"}))
        return
    conteudo = event.content()
    if conteudo is None:
        deny("Conteúdo de escrita ausente; a operação não pode ser inspecionada")
        return

    violacoes = []
    for padrao, descricao in PADROES_CRITICOS:
        if re.search(padrao, conteudo):
            violacoes.append(descricao)

    if violacoes:
        deny("Conteúdo bloqueado: " + ", ".join(sorted(set(violacoes))))
    else:
        print(json.dumps({"decision": "allow"}))


def deny(reason: str) -> None:
    print(json.dumps({
        "decision": "deny",
        "reason": reason,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()
