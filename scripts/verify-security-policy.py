#!/usr/bin/env python3
"""Validate the canonical policy and every referenced local skill."""
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator


def verify(root: Path) -> str:
    policy_path = root / "configuracao/kothar-security-policy.json"
    schema_path = root / "configuracao/kothar-security-policy.schema.json"
    policy_bytes = policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    schema = json.loads(schema_path.read_text())
    Draft202012Validator(schema).validate(policy)
    referenced = {name for names in policy["surfaces"].values() for name in names}
    missing = [name for name in sorted(referenced)
               if not (root / ".agents/skills" / name / "SKILL.md").is_file()]
    if missing:
        raise ValueError("skills ausentes: " + ", ".join(missing))
    if not policy["fail_closed"] or policy["default_environment"] != "production":
        raise ValueError("baseline de produção inválida")
    return hashlib.sha256(policy_bytes).hexdigest()


if __name__ == "__main__":
    try:
        digest = verify(Path(__file__).resolve().parents[1])
    except Exception as error:
        print(f"[BLOCKED] política inválida: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1)
    print(f"[OK] política válida sha256={digest}")
