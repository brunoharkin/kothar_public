#!/usr/bin/env python3
"""Fail-closed final-file validation after a write tool completes."""
import json
import os
from pathlib import Path
import re
import sys

from hook_contract import normalize

BLOCKED = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[A-Z0-9]{16}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"localStorage\.(?:setItem|getItem)\s*\([^)]*(?:token|auth|session|password|secret)", re.I),
    re.compile(r"sessionStorage\.(?:setItem|getItem)\s*\([^)]*(?:token|auth|session|password|secret)", re.I),
]


def main() -> int:
    try:
        event = normalize(json.load(sys.stdin))
    except (ValueError, json.JSONDecodeError):
        print("BLOQUEADO: evento pós-escrita inválido", file=sys.stderr)
        return 2
    if not event.is_write:
        return 0
    raw_path = event.path()
    if not raw_path:
        print("BLOQUEADO: caminho escrito ausente", file=sys.stderr)
        return 2
    root = Path(os.environ.get("KOTHAR_PROJECT_DIR", os.getcwd())).resolve()
    path = Path(raw_path)
    path = (root / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        path.relative_to(root)
        if path.is_symlink() or not path.is_file():
            raise OSError
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        print("BLOQUEADO: arquivo final não pôde ser verificado", file=sys.stderr)
        return 2
    if any(pattern.search(content) for pattern in BLOCKED):
        print("BLOQUEADO: padrão sensível no arquivo final; conteúdo omitido", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
