#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware de Guardrails em Três Frentes (Entrada, Ferramentas, Saída)
Aplica validações determinísticas de baixo custo antes e depois das chamadas ao modelo.
"""

import re
from typing import Dict, Any, Tuple

# Padrões determinísticos de PII (Personally Identifiable Information)
PADRAO_CPF = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
PADRAO_CARTAO = r'\b(?:\d{4}[ -]?){3}\d{4}\b'
PADRAO_EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

# Tentativas conhecidas de Jailbreak / Prompt Injection
PADROES_INJECTION = [
    r'ignore (all|previous|above) instructions',
    r'system prompt override',
    r'você agora é um modelo sem regras',
    r'desconsidere as regras anteriores'
]

class GuardrailsMiddleware:

    @staticmethod
    def validar_entrada(texto: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Intercepta a entrada do usuário antes do modelo.
        Retorna (autorizado, texto_sanitizado, metadados_de_bloqueio).
        """
        texto_lower = texto.lower()

        # 1. Detecção de Prompt Injection
        for padrao in PADROES_INJECTION:
            if re.search(padrao, texto_lower):
                return False, "Sua solicitação viola as diretrizes de segurança do sistema.", {
                    "motivo": "prompt_injection_detectado",
                    "padrao": padrao
                }

        # 2. Sanitização/Mascaração de PII
        texto_sanitizado = re.sub(PADRAO_CARTAO, '[CARTAO_REMOVIDO]', texto)
        texto_sanitizado = re.sub(PADRAO_CPF, '[CPF_MASCARADO]', texto_sanitizado)

        return True, texto_sanitizado, {"pii_sanitizado": texto != texto_sanitizado}

    @staticmethod
    def validar_ferramenta(nome_ferramenta: str, parametros: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Intercepta a chamada da ferramenta. Aplica Human-In-The-Loop para ações irreversíveis.
        """
        ferramentas_irreversiveis = ['deletar_banco', 'executar_sql_raw', 'apagar_usuario', 'deletar_arquivo']
        if nome_ferramenta in ferramentas_irreversiveis:
            return False, f"Ação '{nome_ferramenta}' é irreversível e exige aprovação humana (Checkpoints CP5)."

        return True, "Aprovado para execução."

    @staticmethod
    def validar_saida(texto_resposta: str) -> Tuple[bool, str]:
        """
        Intercepta a saída gerada antes de entregar ao usuário.
        Garante que credenciais, chaves de API ou dados sensíveis não vazem.
        """
        # Checa por chaves de API comuns
        padrao_api_key = r'(sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})'
        if re.search(padrao_api_key, texto_resposta):
            return False, "A resposta gerada continha credenciais sensíveis e foi bloqueada pelo guardrail de saída."

        return True, texto_resposta

