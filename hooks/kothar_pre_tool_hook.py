#!/usr/bin/env python3
"""
=============================================================
 KOTHAR HOOK: Pre-Tool-Use
 Engenheiro Kothar | Ugarit Digital
=============================================================

 Hook executado ANTES de cada ferramenta ser chamada.
 Verifica se a ação é segura e alerta sobre problemas.
"""

import os
import re
import sys
import json
from pathlib import Path


def check_security_issues(tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """
    Verifica problemas de segurança no input da ferramenta.
    Retorna (is_safe, message).
    """
    input_str = json.dumps(tool_input, ensure_ascii=False).lower()

    # Padrões críticos
    critical_patterns = [
        (r'api[_-]?key["\s]*[:=]', "Tentativa de definir API Key"),
        (r'secret[_-]?key', "Tentativa de definir Secret Key"),
        (r'password["\s]*[:=]\s*["\'][^"\']{6,}', "Tentativa de definir Password"),
        (r'token["\s]*[:=]\s*["\'][a-z0-9_-]{20,}', "Tentativa de definir Token"),
        (r'sk-[a-z0-9]{20,}', "OpenAI Key exposta"),
    ]

    for pattern, description in critical_patterns:
        if re.search(pattern, input_str):
            return False, f"⚠️ {description}: REJEITADO pelo hook"

    # Padrões altos
    high_patterns = [
        (r'localstorage.*setitem.*(?:token|key|secret|password)',
         "localStorage para dados sensíveis"),
        (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,5}',
         "IP:Porta internos"),
    ]

    for pattern, description in high_patterns:
        if re.search(pattern, input_str):
            return False, f"⚠️ {description}: BLOQUEADO"

    # Verificar se está tentando escrever em arquivos seguros
    if tool_name in ['Write', 'Edit']:
        file_path = tool_input.get('file_path', '')
        if file_path:
            # Arquivos protegidos
            protected_paths = [
                '.env',
                'credentials',
                'secrets',
                'passwords',
            ]
            for protected in protected_paths:
                if protected in file_path.lower():
                    # Allow if it's an example file
                    if 'example' not in file_path.lower():
                        return False, f"⚠️ Arquivo protegido: {file_path}"

    return True, ""


def check_frontend_modifications(tool_name: str, tool_input: dict) -> str:
    """
    Verifica modificações no frontend e alerta sobre segurança.
    """
    if tool_name not in ['Write', 'Edit', 'Bash']:
        return ""

    file_path = tool_input.get('file_path', '')

    # Se está modificando frontend
    if 'frontend' in file_path or file_path.endswith(('.tsx', '.ts')):
        input_str = json.dumps(tool_input, ensure_ascii=False).lower()

        # Verificar localStorage
        if 'localstorage' in input_str:
            return "⚠️ FRONTEND: localStorage detectado - use backend para dados sensíveis"

        # Verificar tokens
        if 'token' in input_str and ('setitem' in input_str or 'getitem' in input_str):
            return "⚠️ FRONTEND: Token em localStorage - backend deve gerenciar"

    return ""


def main():
    """Função principal do hook."""
    # Ler input do hook
    input_data = json.loads(sys.stdin.read())

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Verificar segurança
    is_safe, message = check_security_issues(tool_name, tool_input)
    if not is_safe:
        print(json.dumps({
            'approved': False,
            'reason': message,
            'severity': 'critical'
        }))
        return

    # Verificar modificações frontend
    warning = check_frontend_modifications(tool_name, tool_input)
    if warning:
        print(json.dumps({
            'approved': True,
            'warning': warning
        }))
        return

    # Aprovado
    print(json.dumps({'approved': True}))


if __name__ == '__main__':
    main()
