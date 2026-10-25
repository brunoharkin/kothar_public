#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v5.0 — Skill Indexer (ChromaDB v2 API)
 Indexa skills no ChromaDB para RAG
=============================================================
"""

import os
import sys
import json
import uuid
import hashlib
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# ============================================================
# CONFIGURAÇÃO
# ============================================================
SKILLS_DIR = Path(__file__).parent.parent / "skills"
CHROMA_URL = "http://localhost:8000"
TENANT = "default_tenant"
DATABASE = "default_database"
BASE_URL = f"{CHROMA_URL}/api/v2/tenants/{TENANT}/databases/{DATABASE}"

COLLECTION_SKILLS = "kothar_skills"
COLLECTION_LOCKS = "kothar_locks"

# ============================================================
# UTILITÁRIOS
# ============================================================

def log(msg: str):
    print(f"[SKILL-INDEXER] {msg}", file=sys.stderr)

def api_request(method: str, path: str, data: dict = None) -> dict:
    """Faz requisição à API do ChromaDB."""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}

    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=15) as resp:
            content = resp.read().decode()
            if content:
                return json.loads(content)
            return {"success": True}
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        try:
            return {"error": json.loads(body), "status": e.code}
        except:
            return {"error": body, "status": e.code}
    except Exception as e:
        return {"error": str(e)}

def create_collection(name: str) -> str:
    """Cria ou obtém collection. Retorna o ID."""
    result = api_request("POST", "/collections", {
        "name": name,
        "get_or_create": True
    })

    if "error" in result:
        # Pode já existir, tenta obter
        existing = api_request("GET", f"/collections/{name}")
        if "id" in existing:
            return existing["id"]
        log(f"Erro ao criar collection: {result}")
        return None

    return result.get("id")

def add_documents(collection_name: str, documents: list, ids: list, metadatas: list) -> bool:
    """Adiciona documentos à collection."""
    result = api_request("POST", f"/collections/{collection_name}/add", {
        "documents": documents,
        "ids": ids,
        "metadatas": metadatas
    })

    if "error" in result:
        log(f"Erro ao adicionar: {result}")
        return False
    return True

def load_yaml_text(filepath: Path) -> str:
    """Lê arquivo YAML como texto."""
    try:
        return filepath.read_text(encoding="utf-8")
    except:
        return ""

def parse_yaml_simple(content: str) -> dict:
    """Parse simples de YAML."""
    result = {}
    lines = content.split('\n')

    for line in lines:
        line = line.rstrip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key = line.split(':', 1)[0].strip()
            value = line.split(':', 1)[1].strip()
            if not value:
                result[key] = True
            else:
                result[key] = value

    return result

# ============================================================
# INDEXAÇÃO DE SKILLS
# ============================================================

def index_skills():
    """Indexa todas as skills."""

    log("Criando collection de skills...")
    create_collection(COLLECTION_SKILLS)

    skills_files = list(SKILLS_DIR.glob("**/*.yaml"))
    log(f"Encontradas {len(skills_files)} skills")

    documents = []
    ids = []
    metadatas = []

    for skill_file in skills_files:
        try:
            relative = skill_file.relative_to(SKILLS_DIR)
            category = str(relative.parent).replace('/', '.')
            skill_name = skill_file.stem

            content = load_yaml_text(skill_file)
            parsed = parse_yaml_simple(content)

            name = parsed.get('name', skill_name)
            description = parsed.get('description', parsed.get('overview', ''))
            instructions = parsed.get('instructions', parsed.get('when_to_use', ''))

            document = f"""SKILL: {name}
CATEGORIA: {category}
DESCRIÇÃO: {description}
INSTRUÇÕES: {instructions}
CONTEÚDO YAML:
{content}""".strip()

            skill_id = f"skill_{category.replace('.', '_')}_{skill_name}"

            documents.append(document)
            ids.append(skill_id)
            metadatas.append({
                "name": name,
                "category": category,
                "file": str(skill_file),
                "type": "skill"
            })

            log(f"  ✅ {category}/{skill_name}")

        except Exception as e:
            log(f"  ❌ {skill_file.name}: {e}")

    # Adiciona em batch
    if documents:
        log(f"Indexando {len(documents)} documentos...")
        add_documents(COLLECTION_SKILLS, documents, ids, metadatas)

    log(f"✅ Skills indexadas com sucesso!")

# ============================================================
# INDEXAÇÃO DE LOCKS
# ============================================================

def index_locks():
    """Indexa locks/vetos."""
    log("Criando collection de locks...")
    create_collection(COLLECTION_LOCKS)

    locks = [
        {
            "id": "lock_debug_write",
            "pattern": "Debug write ativo vazando dados no claude_hook.py",
            "description": "Debug write em /tmp/claude_raw_events.jsonl causa vazamento",
            "alternative": "Usar KOTHAR_DEBUG=1 para ativar debug apenas quando necessário"
        },
        {
            "id": "lock_no_rag",
            "pattern": "Claude não respeita RAG e alucina informações externas",
            "description": "Agente não consulta ChromaDB antes de agir",
            "alternative": "Sempre buscar skills relevantes antes de executar tarefa"
        },
        {
            "id": "lock_no_qa",
            "pattern": "Código criado não é testado automaticamente",
            "description": "Frontend/backend criado mas QA não é invocado",
            "alternative": "Sempre executar QA Agent após criar/modificar código"
        },
        {
            "id": "lock_no_browser_test",
            "pattern": "Não testa se o código funciona no navegador",
            "description": "Código pode compilar mas não funcionar em produção",
            "alternative": "Executar Playwright E2E após cada entrega de código"
        },
        {
            "id": "lock_spaghetti_code",
            "pattern": "Código sem estrutura clara, imports não usados",
            "description": "Code reviewer deve inspecionar antes de entregar",
            "alternative": "Executar code_reviewer após cada entrega"
        }
    ]

    documents = []
    ids = []
    metadatas = []

    for lock in locks:
        doc = f"ERRO: {lock['pattern']}\n\nEvitar porque: {lock['description']}\n\nAlternativa: {lock['alternative']}"
        documents.append(doc)
        ids.append(lock["id"])
        metadatas.append({
            "type": "lock",
            "pattern": lock['pattern'][:100]
        })
        log(f"  🔒 {lock['id']}")

    add_documents(COLLECTION_LOCKS, documents, ids, metadatas)
    log(f"✅ {len(locks)} locks indexados!")

# ============================================================
# TESTE DE BUSCA
# ============================================================

def test_search(query: str, n: int = 3):
    """Testa busca."""
    result = api_request("POST", f"/collections/{COLLECTION_SKILLS}/query", {
        "query_texts": [query],
        "n_results": n
    })

    if "error" in result:
        print(f"Erro: {result['error']}")
        return

    print(f"\n🔍 Busca: '{query}'")
    print("=" * 60)

    if result.get("ids") and result["ids"][0]:
        for i, doc_id in enumerate(result["ids"][0]):
            dist = result["distances"][0][i]
            sim = 1 - dist if dist is not None else 0
            meta = result.get("metadatas", [[{}]])[0][i]

            print(f"\n{i+1}. {meta.get('name', doc_id)} ({meta.get('category', '')})")
            print(f"   Similaridade: {sim:.2%}")
            doc = result["documents"][0][i]
            print(f"   {doc[:150]}...")
    else:
        print("Nenhuma skill encontrada.")

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    log("🚀 KOTHAR Skill Indexer v5.0")
    log("=" * 50)

    if len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "frontend interface"
        test_search(query)
    else:
        index_locks()
        log("")
        index_skills()
        log("")
        log("✅ Indexação completa!")
