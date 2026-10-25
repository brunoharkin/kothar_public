#!/usr/bin/env python3
"""
Kothar Fine-Tuning Dataset Builder
Extrai conversas do cofre e sessions para gerar dataset de fine-tuning.

Usage:
  python3 build_finetune_dataset.py --output kothar-dataset.jsonl

Output format (JSONL, cada linha = 1 exemplo):
  {
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ],
    "source": "cofre|traces|manual",
    "quality": "high/medium/low"
  }
"""

import json
import sqlite3
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import argparse

# System prompt base para todos os exemplos
BASE_SYSTEM_PROMPT = """Você é Kothar v3.0, o Maestro do Orquestro Digital da plataforma Kothar. Você é um assistente técnico especializado em desenvolvimento de software, análise de código, arquitetura e planejamento. Sempre responda em português brasileiro, de forma técnica e direta. Use markdown quando útil. Termine com próximos passos quando relevante."""


def extract_from_cofre(cofre_path: str = "/home/bruno/cofre") -> List[Dict[str, Any]]:
    """
    Extrai conhecimento do cofre.
    - Manuais Kothar (documentação técnica)
    - Planos (exemplos de planejamento)
    - Sessões registradas (exemplos de raciocínio)
    """
    examples = []

    cofre = Path(cofre_path)
    if not cofre.exists():
        print(f"⚠️  Cofre não encontrado em {cofre_path}")
        return examples

    # 1. Manuais Kothar — usar como contexto técnico
    manuals_dir = cofre / "kothar_manuais"
    if manuals_dir.exists():
        for md_file in manuals_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                # Criar exemplo "manual lookup"
                if "ARQUITETURA" in md_file.name.upper() or "README" in md_file.name.upper():
                    examples.append({
                        "messages": [
                            {"role": "system", "content": BASE_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Resuma a arquitetura do Kothar baseado em {md_file.name}."},
                            {"role": "assistant", "content": content[:2000]}  # Limitar tamanho
                        ],
                        "source": f"cofre:manuais/{md_file.name}",
                        "quality": "high"
                    })
            except Exception as e:
                print(f"   Erro ao ler {md_file}: {e}")

    # 2. Planos — exemplos de planejamento estruturado
    plans_dir = cofre / "planos"
    if plans_dir.exists():
        for plan_file in plans_dir.glob("*.md"):
            try:
                content = plan_file.read_text(encoding="utf-8", errors="ignore")
                examples.append({
                    "messages": [
                        {"role": "system", "content": BASE_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Qual o plano descrito em {plan_file.name}?"},
                        {"role": "assistant", "content": content[:2000]}
                    ],
                    "source": f"cofre:planos/{plan_file.name}",
                    "quality": "medium"
                })
            except Exception as e:
                print(f"   Erro ao ler {plan_file}: {e}")

    # 3. Sessões — exemplos de diálogo Kothar
    sessao_dir = cofre / "sessao"
    if sessao_dir.exists():
        for sess_file in sessao_dir.glob("*.md"):
            try:
                content = sess_file.read_text(encoding="utf-8", errors="ignore")
                # Sessões têm formato: objetivo → raciocínio → resultado
                examples.append({
                    "messages": [
                        {"role": "system", "content": BASE_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Descreva o que foi feito na sessão {sess_file.stem}."},
                        {"role": "assistant", "content": content[:2000]}
                    ],
                    "source": f"cofre:sessao/{sess_file.name}",
                    "quality": "high"
                })
            except Exception as e:
                print(f"   Erro ao ler {sess_file}: {e}")

    return examples


def extract_from_traces(db_path: str = "/home/bruno/tracing/backend/banco/traces.db") -> List[Dict[str, Any]]:
    """
    Extrai conversas reais do banco SQLite local do backend tracing.
    NOTA: O backend principal está em :8080 (PostgreSQL), este SQLite é cache local.
    """
    examples = []
    if not os.path.exists(db_path):
        print(f"   SQLite local não encontrado em {db_path} (normal se backend usa Postgres)")
        return examples

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    try:
        # Verificar schema primeiro
        cur.execute("PRAGMA table_info(sessions)")
        cols = [row[1] for row in cur.fetchall()]

        if 'agent' not in cols and 'agent_name' not in cols:
            print(f"   Schema do SQLite local diferente, pulando")
            return examples

        agent_col = 'agent_name' if 'agent_name' in cols else 'agent'
        name_col = 'name' if 'name' in cols else 'task_summary'

        cur.execute(f"""
            SELECT s.id, s.{name_col}, s.{agent_col}
            FROM sessions s
            WHERE s.{agent_col} = 'kothar-local-ai'
            ORDER BY s.started_at DESC
            LIMIT 200
        """)
        sessions = cur.fetchall()

        for sess_id, sess_name, agent in sessions:
            cur.execute("""
                SELECT tool_input, tool_output, tool_name, tokens_input, tokens_output
                FROM traces
                WHERE session_id = ? AND event_type = 'chat'
                ORDER BY sequence ASC, created_at ASC
            """, (sess_id,))

            rows = cur.fetchall()

            # Construir mensagens em pares (user, assistant)
            messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]
            for tool_inp, tool_out, tool_name, tinp, tout in rows:
                inp_str = tool_inp if isinstance(tool_inp, str) else json.dumps(tool_inp, ensure_ascii=False)
                out_str = tool_out if isinstance(tool_out, str) else json.dumps(tool_out, ensure_ascii=False)

                if inp_str:
                    messages.append({"role": "user", "content": inp_str[:1500]})
                if out_str:
                    messages.append({"role": "assistant", "content": out_str[:1500]})

            if len(messages) >= 3:
                examples.append({
                    "messages": messages,
                    "source": f"sqlite:{sess_name[:30] if sess_name else 'chat'}",
                    "quality": "high" if len(messages) > 5 else "medium"
                })

    except sqlite3.OperationalError as e:
        print(f"   Banco SQLite local vazio ou inacessível: {e}")
    finally:
        conn.close()

    return examples


def extract_from_api(base_url: str = "http://localhost:8080") -> List[Dict[str, Any]]:
    """
    Extrai conversas reais via API REST do backend de traces.
    Fallback caso o SQLite local não esteja disponível.
    """
    examples = []
    try:
        import urllib.request
        import urllib.parse

        # Listar sessões kothar-local-ai
        url = f"{base_url}/api/sessions/"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = data if isinstance(data, list) else data.get('items', [])

            for sess in items:
                if sess.get('agent_name') != 'kothar-local-ai':
                    continue

                sess_id = sess.get('id')
                # Buscar traces dessa sessão
                traces_url = f"{base_url}/api/traces/?session_id={sess_id}&limit=100"
                with urllib.request.urlopen(traces_url, timeout=10) as traces_resp:
                    traces_data = json.loads(traces_resp.read().decode('utf-8'))
                    traces = traces_data if isinstance(traces_data, list) else traces_data.get('items', [])

                    messages = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]
                    for t in traces:
                        # Backend usa tool_input/tool_output
                        user_msg = t.get('tool_input') or t.get('input')
                        asst_msg = t.get('tool_output') or t.get('output')
                        if user_msg:
                            messages.append({"role": "user", "content": str(user_msg)[:1500]})
                        if asst_msg:
                            messages.append({"role": "assistant", "content": str(asst_msg)[:1500]})

                    if len(messages) >= 3:
                        examples.append({
                            "messages": messages,
                            "source": f"api:session/{sess_id[:8]}",
                            "quality": "high" if len(messages) > 5 else "medium"
                        })
    except Exception as e:
        print(f"   API backend não acessível: {e}")

    return examples


def extract_from_chromadb() -> List[Dict[str, Any]]:
    """
    Extrai knowledge base do ChromaDB (RAG).
    Documentos lá representam o conhecimento técnico do projeto.
    """
    examples = []
    chroma_path = Path("/home/bruno/tracing/backend/banco/chroma-data")
    if not chroma_path.exists():
        return examples

    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(chroma_path))
        # Listar collections
        collections = client.list_collections()
        for coll in collections:
            try:
                results = coll.get(limit=50)
                for doc in results.get('documents', []):
                    if doc and len(doc) > 100:
                        examples.append({
                            "messages": [
                                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                                {"role": "user", "content": "O que você sabe sobre o Kothar?"},
                                {"role": "assistant", "content": doc[:1500]}
                            ],
                            "source": f"chroma:{coll.name}",
                            "quality": "medium"
                        })
            except Exception as e:
                print(f"   Erro ao ler collection {coll.name}: {e}")
    except ImportError:
        print("   chromadb não instalado, pulando")
    except Exception as e:
        print(f"   Erro no chromadb: {e}")

    return examples


def generate_synthetic_examples() -> List[Dict[str, Any]]:
    """
    Exemplos sintéticos hand-crafted para cobrir casos onde o modelo local
    costuma falhar (identidade, capacidade, raciocínio básico).
    """
    return [
        {
            "messages": [
                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                {"role": "user", "content": "Olá, qual o seu nome?"},
                {"role": "assistant", "content": "Olá! Sou Kothar v3.0, o Maestro do Orquestro Digital. Estou aqui para orquestrar seu trabalho técnico — desde análise de código até planejamento de arquitetura de sistemas. Como posso ajudar hoje?"}
            ],
            "source": "synthetic:identity",
            "quality": "high"
        },
        {
            "messages": [
                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                {"role": "user", "content": "Quais são suas habilidades?"},
                {"role": "assistant", "content": "Minhas capacidades principais:\n\n1. **Análise de código** — revisão, refactoring, debugging em Python, TypeScript, Go, Rust\n2. **Arquitetura** — design de sistemas distribuídos, escolha de stack tecnológica\n3. **Planejamento** — estruturação de projetos em etapas com deliverables claros\n4. **Otimização** — performance, escalabilidade, redução de custos\n5. **Documentação** — READMEs, ADRs (Architecture Decision Records), specs técnicas\n\nTrabalho melhor quando tenho contexto claro do objetivo. Qual seu projeto?"}
            ],
            "source": "synthetic:capabilities",
            "quality": "high"
        },
        {
            "messages": [
                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                {"role": "user", "content": "Como organizar 3 projetos em paralelo?"},
                {"role": "assistant", "content": "Para 3 projetos paralelos, recomendo esta estrutura:\n\n## 1. Priorização por dependências\n- **Projeto A**: bloqueia B e C → fazer primeiro\n- **Projeto B**: depende de A\n- **Projeto C**: independente, pode rodar junto com B\n\n## 2. Delegação por contexto\n- Use **workspaces separados** (git worktree)\n- Sessões Ollama distintas para cada projeto\n- Cada projeto com seu próprio prompt de contexto\n\n## 3. Sincronização\n- Compartilhe apenas o que está **estável** (APIs, contratos)\n- Documente decisões em **ADRs** compartilhados\n- Use feature flags para deploys parciais\n\nQuer que eu detalhe algum desses pontos?"}
            ],
            "source": "synthetic:reasoning",
            "quality": "high"
        },
        {
            "messages": [
                {"role": "system", "content": BASE_SYSTEM_PROMPT},
                {"role": "user", "content": "Crie um plano para deployar uma API FastAPI com Docker"},
                {"role": "assistant", "content": "## Plano: Deploy FastAPI + Docker\n\n### Etapa 1: Estrutura do projeto\n```\nprojeto/\n├── app/\n│   ├── main.py\n│   └── requirements.txt\n├── Dockerfile\n├── docker-compose.yml\n└── .dockerignore\n```\n\n### Etapa 2: Dockerfile multi-stage\n```dockerfile\nFROM python:3.11-slim AS builder\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n\nFROM python:3.11-slim\nWORKDIR /app\nCOPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages\nCOPY ./app ./app\nCMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n```\n\n### Etapa 3: docker-compose.yml\n```yaml\nversion: '3.8'\nservices:\n  api:\n    build: .\n    ports:\n      - \"8000:8000\"\n    environment:\n      - DATABASE_URL=postgresql://...\n```\n\n### Etapa 4: Verificação\n- [ ] `docker build` sem erros\n- [ ] `docker-compose up` sobe a API\n- [ ] `curl localhost:8000/health` retorna 200\n- [ ] Logs limpos (sem stack traces)\n\n**Próximo passo:** Adicionar CI/CD no GitHub Actions?"}
            ],
            "source": "synthetic:planning",
            "quality": "high"
        },
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="kothar-dataset.jsonl")
    parser.add_argument("--min-quality", default="low", choices=["low", "medium", "high"])
    args = parser.parse_args()

    print("🔨 Construindo dataset de fine-tuning Kothar...\n")

    all_examples = []

    print("📚 1/5 Extraindo do cofre...")
    cofre_examples = extract_from_cofre()
    all_examples.extend(cofre_examples)
    print(f"   ✅ {len(cofre_examples)} exemplos")

    print("🗃️  2/5 Extraindo traces do SQLite local...")
    trace_examples = extract_from_traces()
    all_examples.extend(trace_examples)
    print(f"   ✅ {len(trace_examples)} exemplos")

    print("🌐 3/5 Extraindo via API REST (backend :8080)...")
    api_examples = extract_from_api()
    all_examples.extend(api_examples)
    print(f"   ✅ {len(api_examples)} exemplos")

    print("🧠 4/5 Extraindo ChromaDB...")
    chroma_examples = extract_from_chromadb()
    all_examples.extend(chroma_examples)
    print(f"   ✅ {len(chroma_examples)} exemplos")

    print("✨ 5/5 Adicionando exemplos sintéticos...")
    synth_examples = generate_synthetic_examples()
    all_examples.extend(synth_examples)
    print(f"   ✅ {len(synth_examples)} exemplos")

    # Filtrar por qualidade
    quality_order = {"low": 0, "medium": 1, "high": 2}
    min_q = quality_order[args.min_quality]
    filtered = [
        ex for ex in all_examples
        if quality_order.get(ex.get("quality", "low"), 0) >= min_q
    ]

    # Deduplicar por hash do conteúdo
    seen = set()
    deduped = []
    for ex in filtered:
        key = hash(json.dumps(ex["messages"], sort_keys=True))
        if key not in seen:
            seen.add(key)
            deduped.append(ex)

    # Salvar
    output_path = Path(args.output)
    with output_path.open("w", encoding="utf-8") as f:
        for ex in deduped:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n🎉 Dataset salvo em: {output_path}")
    print(f"   Total de exemplos: {len(deduped)}")
    print(f"   Fontes: {dict([(s, len([e for e in deduped if e['source'].startswith(s)])) for s in ['cofre', 'traces', 'chroma', 'synthetic']])}")

    # Stats por qualidade
    by_quality = {}
    for ex in deduped:
        q = ex.get("quality", "low")
        by_quality[q] = by_quality.get(q, 0) + 1
    print(f"   Qualidade: {by_quality}")


if __name__ == "__main__":
    main()