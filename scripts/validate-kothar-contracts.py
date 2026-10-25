#!/usr/bin/env python3
"""Valida contratos e transições sem depender de serviços externos."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSITIONS = ROOT / "configuracao" / "kothar-transitions.json"
REGISTRY = ROOT / "configuracao" / "kothar-agent-registry.json"


def main() -> int:
    transitions = json.loads(TRANSITIONS.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    agents = set(registry["profiles"]["full"])
    terminal_states = {"blueprint", "execution", "review", "security", "qa", "evaluator", "checkpoint", "done"}
    errors: list[str] = []

    if transitions.get("maxReviewAttempts") != 3:
        errors.append("maxReviewAttempts deve permanecer 3")
    for index, transition in enumerate(transitions.get("transitions", []), start=1):
        for key in ("from", "on", "conditions", "next", "owner"):
            if key not in transition:
                errors.append(f"transição {index}: campo ausente {key}")
        if transition.get("owner") not in agents:
            errors.append(f"transição {index}: owner desconhecido {transition.get('owner')}")
        unknown = [
            target for target in transition.get("next", [])
            if target not in agents and target not in terminal_states
        ]
        if unknown:
            errors.append(f"transição {index}: destino desconhecido {unknown}")

    if errors:
        for error in errors:
            print(f"[ERRO] {error}", file=sys.stderr)
        return 1

    contract = ROOT / "backend" / "contracts" / "execution.py"
    if not contract.is_file():
        print("[ERRO] contrato de execução ausente", file=sys.stderr)
        return 1
    contract_text = contract.read_text(encoding="utf-8")
    for symbol in ("class Handoff", "class ReviewResult", "class ExecutionState"):
        if symbol not in contract_text:
            print(f"[ERRO] contrato sem símbolo obrigatório: {symbol}", file=sys.stderr)
            return 1

    print("[OK] Contratos tipados e transições válidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
