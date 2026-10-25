#!/usr/bin/env python3
"""Sincroniza o contrato de entrega sem afirmar que um runtime o executou."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

START = "<!-- kothar-delivery-contract:start -->"
END = "<!-- kothar-delivery-contract:end -->"
SOURCE = ".agents/skills/auto-relatabilidade/SKILL.md"
MARKDOWN_TARGETS = (
    "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".claude/agents/kothar.md",
    ".claude/commands/kothar.md", ".agents/plugins/kothar/rules/AGENTS.md",
)
CODEX = ".codex/agents/kothar.toml"
MANIFEST = ".agents/agents/kothar.json"


def contract_from(root: Path) -> str:
    source = (root / SOURCE).read_text(encoding="utf-8")
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("A skill deve conter exatamente um contrato de entrega.")
    start, end = source.index(START), source.index(END)
    if end <= start:
        raise ValueError("Marcadores do contrato fora de ordem.")
    return source[start:end + len(END)]


def replace_contract(text: str, contract: str) -> str:
    if START not in text and END not in text:
        return text.rstrip() + "\n\n" + contract + "\n"
    if text.count(START) != 1 or text.count(END) != 1 or text.index(END) < text.index(START):
        raise ValueError("Contrato duplicado ou incompleto.")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    return before + contract + after


def expected_content(path: Path, content: str, contract: str) -> str:
    if path.suffix == ".toml":
        match = re.search(r'(developer_instructions\s*=\s*""")(.*?)(""")', content, re.S)
        if match is None:
            raise ValueError("developer_instructions multilinha ausente.")
        updated = replace_contract(match.group(2), contract)
        return content[:match.start(2)] + updated + content[match.end(2):]
    if path.suffix == ".json":
        data = json.loads(content)
        prompt = data.get("systemPrompt")
        if not isinstance(prompt, str):
            raise ValueError("systemPrompt ausente.")
        updated = replace_contract(prompt, contract)
        if updated == prompt:
            return content
        data["systemPrompt"] = updated
        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    return replace_contract(content, contract)


def synchronize(root: Path, apply: bool = False) -> list[str]:
    root = root.resolve()
    contract = contract_from(root)
    agents = sorted((root / ".github/agents").glob("*.agent.md"))
    if not agents:
        raise ValueError("Nenhum manifesto de subagente encontrado.")
    targets = [root / p for p in (*MARKDOWN_TARGETS, CODEX, MANIFEST)] + agents
    pending = []
    # Validar tudo antes de escrever: um arquivo inválido não causa sincronização parcial.
    for target in targets:
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ValueError("Destino fora da raiz ou symlink.")
        content = target.read_text(encoding="utf-8")
        expected = expected_content(target, content, contract)
        if content != expected:
            pending.append((target, expected))
    if apply:
        for target, expected in pending:
            target.write_text(expected, encoding="utf-8")
    return [str(path.relative_to(root)) for path, _ in pending]


def synchronize_user(root: Path, profile_home: Path, apply: bool = False) -> list[str]:
    """Atualiza só o contrato em arquivos Kothar já instalados, sem copiar/deletar perfis."""
    profile_home = profile_home.resolve()
    contract = contract_from(root)
    relative_targets = [
        ".codex/AGENTS.md", ".codex/agents/kothar.toml",
        ".claude/agents/kothar.md", ".gemini/GEMINI.md", ".gemini/agents/kothar.json",
    ]
    relative_targets.extend(
        ".copilot/agents/" + path.name
        for path in sorted((root / ".github/agents").glob("*.agent.md"))
    )
    pending = []
    found = 0
    for relative in relative_targets:
        target = profile_home / relative
        if not target.exists():
            continue
        if target.is_symlink() or not target.resolve().is_relative_to(profile_home):
            raise ValueError("Perfil instalado fora da raiz ou symlink.")
        content = target.read_text(encoding="utf-8")
        if "kothar" not in content[:1500].lower():
            continue
        found += 1
        expected = expected_content(target, content, contract)
        if content != expected:
            pending.append((target, expected))
    if not found:
        raise ValueError("Nenhum perfil Kothar instalado encontrado.")
    if apply:
        for target, expected in pending:
            target.write_text(expected, encoding="utf-8")
    return [str(path.relative_to(profile_home)) for path, _ in pending]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--user", action="store_true", help="somente perfis Kothar já instalados")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        pending = (
            synchronize_user(args.root, Path.home(), apply=args.apply) if args.user
            else synchronize(args.root, apply=args.apply)
        )
    except (OSError, ValueError) as error:
        print(f"[ERRO] Contrato de entrega: {type(error).__name__}", file=sys.stderr)
        return 2
    for path in pending:
        print(f"[{'ATUALIZADO' if args.apply else 'DIVERGENTE'}] {path}")
    if pending and args.check:
        return 1
    print("[OK] Contratos de instrução sincronizados; execução nativa não é comprovada por este check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

