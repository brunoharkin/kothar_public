#!/usr/bin/env python3
"""
Hook de Contabilização de Tokens
=================================

Inspirado no sistema do Codenotch.

Este hook registra o uso de tokens após cada resposta do Claude.
Pode ser integrado como PostToolUse hook no settings.json.

Uso:
    # No settings.json:
    {
        "hooks": {
            "PostToolUse": {
                "*": "python3 ~/.kothar/hooks/token-counter-hook.py"
            }
        }
    }

O hook extrai informações de token das respostas e salva no ledger.
"""

from __future__ import annotations

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Adiciona o backend ao path
KOTHAR_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(KOTHAR_ROOT / "backend"))


# =============================================================================
# Configuração
# =============================================================================

TOKEN_USAGE_DIR = Path(os.path.expanduser("~/.kothar/token-usage"))
TOKEN_USAGE_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_FILE = TOKEN_USAGE_DIR / "ledger.json"

# Regex para extrair tokens de diferentes formatos
TOKENS_PATTERNS = {
    # Anthropic API format
    "anthropic": re.compile(
        r'input_tokens["\']?\s*[:=]\s*(\d+)',
        re.IGNORECASE,
    ),
    "anthropic_output": re.compile(
        r'output_tokens["\']?\s*[:=]\s*(\d+)',
        re.IGNORECASE,
    ),
    # OpenAI format
    "openai": re.compile(
        r'"usage"\s*:\s*\{[^}]*"prompt_tokens"\s*:\s*(\d+)',
        re.DOTALL,
    ),
    # Generic patterns
    "generic_input": re.compile(
        r'(?:input|prompt)[_\s]?tokens["\']?\s*[:=]\s*(\d+)',
        re.IGNORECASE,
    ),
    "generic_output": re.compile(
        r'(?:output|completion)[_\s]?tokens["\']?\s*[:=]\s*(\d+)',
        re.IGNORECASE,
    ),
    # Reasoning tokens (Anthropic extended)
    "reasoning": re.compile(
        r'reasoning_tokens["\']?\s*[:=]\s*(\d+)',
        re.IGNORECASE,
    ),
}


# =============================================================================
# Ledger
# =============================================================================

def load_ledger() -> dict:
    """Carrega o ledger do disco."""
    if LEDGER_FILE.exists():
        try:
            with open(LEDGER_FILE) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {}


def save_ledger(ledger: dict) -> None:
    """Salva o ledger no disco."""
    with open(LEDGER_FILE, "w") as f:
        json.dump(ledger, f, indent=2)


def get_date_key() -> str:
    """Retorna a chave de data atual."""
    return datetime.now().strftime("%Y-%m-%d")


def record_tokens(
    input_tokens: int = 0,
    output_tokens: int = 0,
    reasoning_tokens: int = 0,
    instance: str = "claude-code",
) -> dict:
    """
    Registra tokens no ledger.

    Args:
        input_tokens: Tokens de entrada
        output_tokens: Tokens de saída
        reasoning_tokens: Tokens de raciocínio
        instance: Nome da instância

    Returns:
        Totais atualizados do dia
    """
    ledger = load_ledger()
    date_key = get_date_key()

    if date_key not in ledger:
        ledger[date_key] = {}

    if instance not in ledger[date_key]:
        ledger[date_key][instance] = {
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "reasoning_tokens": 0,
            "total_tokens": 0,
        }

    entry = ledger[date_key][instance]
    entry["requests"] += 1
    entry["input_tokens"] += input_tokens
    entry["output_tokens"] += output_tokens
    entry["reasoning_tokens"] += reasoning_tokens
    entry["total_tokens"] = entry["input_tokens"] + entry["output_tokens"]

    save_ledger(ledger)

    return entry


# =============================================================================
# Extração de Tokens
# =============================================================================

def extract_tokens_from_tool_result(tool_name: str, result: str) -> dict:
    """
    Extrai contagem de tokens do resultado de uma ferramenta.

    Args:
        tool_name: Nome da ferramenta
        result: Resultado (stdout/stderr)

    Returns:
        Dict com input_tokens, output_tokens, reasoning_tokens
    """
    tokens = {
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
    }

    if not result:
        return tokens

    # Procura por diferentes padrões
    for pattern_name, pattern in TOKENS_PATTERNS.items():
        match = pattern.search(result)
        if match:
            value = int(match.group(1))

            if "input" in pattern_name:
                tokens["input_tokens"] = value
            elif "output" in pattern_name or "completion" in pattern_name:
                tokens["output_tokens"] = value
            elif "reasoning" in pattern_name:
                tokens["reasoning_tokens"] = value

    return tokens


def extract_from_message_content(content: str) -> dict:
    """
    Tenta extrair tokens do conteúdo de uma mensagem.

    Pode ser útil quando o Claude inclui metadados de tokens.
    """
    tokens = {
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
    }

    if not content:
        return tokens

    # Procura por Usage blocks
    usage_match = re.search(
        r'```json\s*\{[^}]*"usage"[^}]*\}[^}]*```',
        content,
        re.IGNORECASE | re.DOTALL,
    )

    if usage_match:
        try:
            usage_json = json.loads(usage_match.group(0).strip("```json").strip("```"))
            if "usage" in usage_json:
                u = usage_json["usage"]
                tokens["input_tokens"] = u.get("input_tokens", 0)
                tokens["output_tokens"] = u.get("output_tokens", 0)
                tokens["reasoning_tokens"] = u.get("reasoning_tokens", 0)
        except json.JSONDecodeError:
            pass

    return tokens


# =============================================================================
# Hook Principal
# =============================================================================

def main():
    """
    Entry point do hook.

    Lê variáveis de ambiente do Claude Code e registra tokens.
    """
    # Verifica se deve executar
    if os.environ.get("KOTHAR_TOKEN_COUNTER_ENABLED", "true").lower() != "true":
        return 0

    # Lê contexto da sessão
    tool_name = os.environ.get("TOOL_NAME", "")
    tool_result = os.environ.get("TOOL_RESULT", "")
    instance = os.environ.get("CLAUDE_SESSION_ID", "claude-code")

    # Se não há resultado, tenta ler do stdin
    if not tool_result:
        try:
            tool_result = sys.stdin.read()
        except Exception:
            pass

    # Extrai tokens
    tokens = extract_tokens_from_tool_result(tool_name, tool_result)

    # Também tenta extrair de message content se tool_name indica resposta
    if not any(tokens.values()):
        if tool_name in ["claude", "assistant", "claude-code"]:
            tokens = extract_from_message_content(tool_result)

    # Registra se encontrou tokens
    if any(tokens.values()):
        result = record_tokens(
            input_tokens=tokens["input_tokens"],
            output_tokens=tokens["output_tokens"],
            reasoning_tokens=tokens["reasoning_tokens"],
            instance=instance,
        )

        # Log para debug
        print(
            f"[token-counter] Recorded: "
            f"{tokens['input_tokens']} in / "
            f"{tokens['output_tokens']} out / "
            f"{tokens['reasoning_tokens']} reasoning | "
            f"Total today: {result['total_tokens']}",
            file=sys.stderr,
        )

    return 0


# =============================================================================
# CLI para consulta
# =============================================================================

def cmd_summary():
    """Mostra resumo do uso de tokens."""
    ledger = load_ledger()
    date_key = get_date_key()

    print(f"=== Token Usage Summary ===")
    print(f"Date: {date_key}")
    print()

    if date_key not in ledger or not ledger[date_key]:
        print("No usage recorded today.")
        return

    for instance, data in ledger[date_key].items():
        print(f"Instance: {instance}")
        print(f"  Requests:  {data['requests']}")
        print(f"  Input:    {data['input_tokens']:,}")
        print(f"  Output:   {data['output_tokens']:,}")
        print(f"  Reasoning:{data['reasoning_tokens']:,}")
        print(f"  Total:    {data['total_tokens']:,}")
        print()


def cmd_today():
    """Mostra totais de hoje."""
    ledger = load_ledger()
    date_key = get_date_key()

    total_input = 0
    total_output = 0
    total_requests = 0

    if date_key in ledger:
        for instance, data in ledger[date_key].items():
            total_input += data.get("input_tokens", 0)
            total_output += data.get("output_tokens", 0)
            total_requests += data.get("requests", 0)

    print(json.dumps({
        "date": date_key,
        "requests": total_requests,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_input + total_output,
    }, indent=2))


def cmd_record(input_tokens: int, output_tokens: int, reasoning_tokens: int = 0):
    """Registra tokens manualmente."""
    result = record_tokens(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "summary":
            cmd_summary()
        elif cmd == "today":
            cmd_today()
        elif cmd == "record" and len(sys.argv) >= 5:
            cmd_record(
                int(sys.argv[2]),
                int(sys.argv[3]),
                int(sys.argv[4]) if len(sys.argv) > 4 else 0,
            )
        else:
            print(f"Usage: {sys.argv[0]} [summary|today|record <in> <out> [reasoning]]")
            sys.exit(1)
    else:
        sys.exit(main())
