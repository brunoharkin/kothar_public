#!/usr/bin/env python3
"""Propaga uma referência verificável à política canônica de segurança."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

START = "<!-- kothar-security-policy:start -->"
END = "<!-- kothar-security-policy:end -->"


def policy_block(root: Path) -> str:
    policy_path = root / "configuracao/kothar-security-policy.json"
    raw = policy_path.read_bytes()
    policy = json.loads(raw)
    digest = hashlib.sha256(raw).hexdigest()
    return f"""{START}
## Política canônica de segurança

Antes de implementar, revisar ou liberar código que toque autenticação, entrada de usuário, persistência, APIs externas, logs, agentes conversacionais ou implantação:

1. leia `configuracao/kothar-security-policy.json`;
2. aplique todas as skills declaradas para a superfície afetada;
3. trate ambiente de produção e falha fechada como padrão;
4. bloqueie a entrega até haver evidência dos requisitos de release aplicáveis.

Versão esperada: `{policy['policy_version']}`. SHA-256 esperado: `{digest}`.
{END}"""


def replace_block(text: str, block: str) -> str:
    if START in text and END in text:
        prefix, rest = text.split(START, 1)
        _, suffix = rest.split(END, 1)
        return prefix.rstrip() + "\n\n" + block + suffix
    return text.rstrip() + "\n\n" + block + "\n"


def targets(root: Path) -> list[Path]:
    files = [root / name for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md")]
    files += [
        root / ".claude/agents/kothar.md",
        root / ".claude/commands/kothar.md",
        root / ".agents/plugins/kothar/rules/AGENTS.md",
    ]
    files.extend(sorted((root / ".github/agents").glob("*.agent.md")))
    return files


def sync(root: Path, apply: bool) -> list[str]:
    block = policy_block(root)
    drift: list[str] = []
    for path in targets(root):
        if not path.is_file():
            drift.append(str(path.relative_to(root)) + " (ausente)")
            continue
        current = path.read_text(encoding="utf-8")
        expected = replace_block(current, block)
        if current != expected:
            drift.append(str(path.relative_to(root)))
            if apply:
                path.write_text(expected, encoding="utf-8")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--apply", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    drift = sync(root, args.apply)
    if drift and args.check:
        print("[BLOCKED] política não sincronizada: " + ", ".join(drift))
        return 1
    print(f"[OK] política sincronizada em {len(drift)} arquivo(s)" if drift else "[OK] política já sincronizada")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
