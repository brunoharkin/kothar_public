#!/usr/bin/env python3
"""Auditoria local de superfícies agentic sem rede, execução ou envio de conteúdo."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SECRETS = (
    (r"sk-[A-Za-z0-9_-]{20,}", "credencial de provedor"),
    (r"ghp_[A-Za-z0-9]{36}", "token GitHub"),
    (r"AKIA[A-Z0-9]{16}", "chave AWS"),
    (r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*[\"'][^\"']{8,}[\"']", "segredo literal"),
)
DANGEROUS = (
    (r"(?i)\beval\s*\(", "execução dinâmica"),
    (r"(?i)innerHTML\s*=", "injeção HTML"),
    (r"(?i)localStorage\.(setItem|getItem)\s*\([^)]*(token|secret|password)", "token em storage"),
    (r"(?i)(curl|wget)\s+[^|\n]+\|\s*(sh|bash)", "download e execução encadeados"),
    (r"(?i)0\.0\.0\.0", "bind público"),
)
IGNORED_PARTS = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}


def finding(severity: str, rule: str, path: Path) -> dict[str, str]:
    return {"severity": severity, "rule": rule, "path": path.as_posix()}


def iter_surface(root: Path) -> list[Path]:
    paths: list[Path] = []
    for folder in (root / ".github", root / ".agents", root / ".vscode"):
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts):
                paths.append(path)
    return paths


def audit(root: Path) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    files = iter_surface(root)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(finding("REVIEW", "arquivo não legível", path.relative_to(root)))
            continue
        relative = path.relative_to(root)
        for pattern, rule in SECRETS:
            # Markdown pode conter exemplos de padrões proibidos; tokens reais
            # continuam sendo bloqueados em qualquer extensão.
            is_documentation = path.suffix.lower() in {".md", ".txt"}
            is_strong_token = rule in {"credencial de provedor", "token GitHub", "chave AWS"}
            is_literal_secret = rule == "segredo literal"
            if re.search(pattern, text) and (
                not is_documentation or is_strong_token or is_literal_secret
            ):
                findings.append(finding("BLOCK", rule, relative))
        if path.suffix.lower() not in {".md", ".txt"}:
            for pattern, rule in DANGEROUS:
                if re.search(pattern, text):
                    findings.append(finding("REVIEW", rule, relative))
        if path.suffix == ".json":
            try:
                json.loads(text)
            except json.JSONDecodeError:
                findings.append(finding("BLOCK", "JSON inválido", relative))

    mcp = root / ".vscode" / "mcp.json"
    if mcp.exists():
        try:
            config = json.loads(mcp.read_text(encoding="utf-8"))
            for name, server in config.get("servers", {}).items():
                if server.get("type") == "http" and server.get("url", "").startswith(("http://", "https://")):
                    findings.append(finding("REVIEW", f"MCP externo requer aprovação: {name}", mcp.relative_to(root)))
                command = str(server.get("command", ""))
                if command in {"bash", "sh", "powershell", "cmd"}:
                    findings.append(finding("REVIEW", f"MCP executa shell: {name}", mcp.relative_to(root)))
        except json.JSONDecodeError:
            pass

    counts = {severity: sum(item["severity"] == severity for item in findings) for severity in ("BLOCK", "REVIEW", "INFO")}
    return {"version": 1, "root": str(root), "filesAudited": len(files), "counts": counts, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--strict", action="store_true", help="falha também em REVIEW")
    parser.add_argument("--json", action="store_true", help="emite somente JSON")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"[BLOCK] raiz inexistente: {root}", file=sys.stderr)
        return 2
    report = audit(root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"[OK] Superfície auditada: {report['filesAudited']} arquivos")
        for item in report["findings"]:
            print(f"[{item['severity']}] {item['rule']} — {item['path']}")
        print(f"[RESUMO] BLOCK={report['counts']['BLOCK']} REVIEW={report['counts']['REVIEW']}")
    if report["counts"]["BLOCK"] or (args.strict and report["counts"]["REVIEW"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
