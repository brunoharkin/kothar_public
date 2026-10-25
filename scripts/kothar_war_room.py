#!/usr/bin/env python3
"""
Módulo de Sincronização Canônica do Kothar com o War Room Auditivo
Uso: kothar_war_room.py enviar-plano "Título" "Conteudo Markdown" "Resumo em Voz"
"""

import sys
import os
import json
import urllib.request
import urllib.error

PLANO_FILE = "/home/bruno-harkin/kothar/ferramentas/leitor-voz-ptbr/plano-ativo.json"
WAR_ROOM_URL = "http://127.0.0.1:3344/api/plano"

def enviar_plano_para_war_room(titulo, markdown, resumo_voz=None):
    if not resumo_voz:
        # Gera um resumo limpo removendo caracteres markdown para locução
        resumo_voz = markdown.replace("#", "").replace("*", "").replace("-", "")[:350]

    payload = {
        "id": f"plano_{int(os.times().elapsed * 1000)}",
        "titulo": titulo,
        "data": "2026-10-23T19:15:00-03:00",
        "status": "PENDENTE_DEBATE",
        "resumoVoz": resumo_voz,
        "conteudoMarkdown": markdown,
        "historicoDebate": [
            {
                "autor": "Kothar",
                "mensagem": f"Plano '{titulo}' recebido e carregado na mesa de debate. Use o microfone para discutir alterações ou aprove diretamente.",
                "timestamp": "2026-10-23T19:15:00-03:00"
            }
        ]
    }

    # 1. Salvar no arquivo persistente
    os.makedirs(os.path.dirname(PLANO_FILE), exist_ok=True)
    with open(PLANO_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"✅ [Kothar War Room] Plano '{titulo}' gravado com sucesso em {PLANO_FILE}!")
    print(f"🌐 Acesse http://localhost:3344 para debater por voz com o Alex.")
    return True

def verificar_status_aprovacao():
    if not os.path.exists(PLANO_FILE):
        return None
    try:
        with open(PLANO_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("status")
    except Exception as e:
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "enviar-plano":
        titulo = sys.argv[2] if len(sys.argv) > 2 else "Plano de Ação Kothar"
        conteudo = sys.argv[3] if len(sys.argv) > 3 else "Conteúdo do plano a ser executado."
        resumo = sys.argv[4] if len(sys.argv) > 4 else None
        enviar_plano_para_war_room(titulo, conteudo, resumo)
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print(verificar_status_aprovacao())

