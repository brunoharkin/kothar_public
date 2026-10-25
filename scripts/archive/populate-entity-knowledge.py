#!/usr/bin/env python3
"""
KOTHAR ENTITY KNOWLEDGE POPULATOR v3.0
Popula o ChromaDB com conhecimento sobre o usuário e sistema.
Usa ChromaDB se disponível, caso contrário usa SQLite.
"""

import os
import sys
import json
from pathlib import Path

# Adicionar path do embedder
sys.path.insert(0, str(Path(__file__).parent.parent / "regras" / "core"))
from embedder import embed_document, CHROMADB_AVAILABLE, VECTOR_DB_PATH

# Entidades do sistema Kothar
SYSTEM_ENTITIES = [
    {
        "id": "kothar_system",
        "text": """Kothar v3.0 é um sistema Multi-LLM de orquestração de agentes criado pela Ugarit Digital.
        Desenvolvido por Bruno Harkin. Arquitetura ECC (Event-Driven Computing) com agentes especializados:
        Maestro (Kothar), Architect, Engineer, DevOps, DBA, Desktop Assistant, Red Team.
        Sistema Core Loop: Sentir → Pensar → Validar → Agir → Aprender → Relatar.
        Usa RAG (vector search) para memória e SQLite/ChromaDB para persistência.""",
        "metadata": {"type": "system", "category": "architecture"}
    },
    {
        "id": "bruno_harkin",
        "text": """Bruno Harkin é o criador do sistema Kothar e fundador da Ugarit Digital.
        Desenvolvedor full-stack com foco em sistemas de IA, automação e integrações WhatsApp.
        Projetos conhecidos: disparo-em-massa, crm-sophia, orby-ia, bioleads, linkdabio, chronodesk.
        Localização: Brasil. Preferências: Claude Code como IDE, automação web com Playwright.
        Empresa: Ugarit Digital.""",
        "metadata": {"type": "user", "category": "identity"}
    },
    {
        "id": "projects_portfolio",
        "text": """Portfólio de projetos ativos:
        - cofre: Vault Obsidian para notas e memória
        - disparo-em-massa: Sistema de disparo WhatsApp em massa (portas: 2786, 5432)
        - crm-sophia: CRM com integração WhatsApp (portas: 2785, 5433, 6380)
        - chronodesk: Gerenciamento de tarefas (porta: 3000)
        - orby-ia: Sistema de IA (portas: 5440, 6381)
        - bioleads: Geração de leads biológicos
        - linkdabio: Links para biologia
        - kothar: Sistema de orquestração (é o próprio sistema)""",
        "metadata": {"type": "user", "category": "projects"}
    },
    {
        "id": "stack_tecnologica",
        "text": """Stack tecnológica do Kothar:
        - LLM: Claude Opus via API customizada
        - RAG: Vector database (ChromaDB ou SQLite fallback)
        - Automação: Playwright MCP
        - Banco: PostgreSQL (portas 5432, 5433)
        - Cache: Redis (portas 6380, 6381)
        - Mensagens: Evolution API (portas 2785, 2786)
        - Container: Docker com docker-compose""",
        "metadata": {"type": "system", "category": "stack"}
    },
    {
        "id": "ugart_digital",
        "text": """Ugarit Digital é a empresa/marca por trás do Kothar.
        Criada por Bruno Harkin. Foco em soluções de IA para automação empresarial.
        Produtos: sistemas de disparo em massa, CRMs integrados com WhatsApp,
        ferramentas de produtividade com IA.""",
        "metadata": {"type": "organization", "category": "brand"}
    },
    {
        "id": "kothar_rules",
        "text": """Regras de Ouro do Kothar:
        1. Verificar porta ANTES de subir servidor (lsof -i :PORTA)
        2. Sistema RAG: NUNCA alucinar parâmetros de APIs
        3. Hand-off: Arquiteto cria Blueprint → Engenheiro implementa
        4. Limite de Loops: 3x erro = parar e pedir instrução humana
        5. Prompt Caching: Contexto base NUNCA modificado""",
        "metadata": {"type": "system", "category": "rules"}
    },
    {
        "id": "kothar_architecture",
        "text": """Arquitetura Kothar:
        Core Loop: perception → reasoning → gates → tool_calls → instinct → auto-relatabilidade
        5 Gates: Projeto, Escopo, Credenciais, Viabilidade, Nomenclatura
        6 Checkpoints: Projeto, Nomenclatura, Commit, Push, Delete, Feature
        5 Sensores: pwd, git, ssh, diario, modo
        Isolamento: cada projeto = chave SSH única + .env isolado""",
        "metadata": {"type": "system", "category": "architecture"}
    }
]

def populate_entities():
    """Popula o banco vetorial com entidades de conhecimento."""
    print(f"📚 Populando entity_knowledge...")
    print(f"   Engine: {'ChromaDB' if CHROMADB_AVAILABLE else 'SQLite'}")
    print(f"   Path: {VECTOR_DB_PATH}")
    print()

    for entity in SYSTEM_ENTITIES:
        try:
            # Criar arquivo temporário com o texto
            temp_file = f"/tmp/entity_{entity['id']}.txt"
            with open(temp_file, 'w') as f:
                f.write(entity['text'])

            # Vectorizar
            success = embed_document(temp_file, entity['metadata'])

            if success:
                print(f"   ✅ {entity['id']}")
            else:
                print(f"   ❌ {entity['id']}: erro")

            # Limpar
            os.remove(temp_file)

        except Exception as e:
            print(f"   ❌ {entity['id']}: {e}")

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       KOTHAR ENTITY KNOWLEDGE POPULATOR v3.0            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    populate_entities()

    print()
    print("✅ entity_knowledge populado com sucesso!")

if __name__ == "__main__":
    main()
