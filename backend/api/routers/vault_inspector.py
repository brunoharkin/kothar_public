"""
=============================================================
 KOTHAR v6.0 — Vault/Cofre Inspector
 Mapeia TODO o cofre: estrutura, stats, collections ChromaDB
=============================================================
"""
import os
import json
import logging
import httpx
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Query

logger = logging.getLogger("kothar.vault_inspector")
router = APIRouter()

COFRE_DIR = Path(
    os.environ.get("KOTHAR_VAULT_PATH", str(Path.home() / "Cofre"))
)


def _scan_directory(dir_path: Path, recursive: bool = True) -> Dict:
    """Escaneia um diretório e retorna stats."""
    if not dir_path.exists():
        return {"exists": False, "path": str(dir_path), "files": 0, "size_bytes": 0}

    total_size = 0
    total_files = 0
    md_files = 0
    md_size = 0
    other_files = 0
    other_size = 0
    subdirs = []

    try:
        if recursive:
            # Scan recursivo
            for item in dir_path.rglob("*"):
                if item.is_file():
                    size = item.stat().st_size
                    total_size += size
                    total_files += 1
                    if item.suffix.lower() in (".md", ".markdown"):
                        md_files += 1
                        md_size += size
                    else:
                        other_files += 1
                        other_size += size
                elif item.is_dir() and not item.name.startswith("."):
                    if item != dir_path:
                        subdirs.append(str(item.relative_to(dir_path)))
            subdirs = sorted(set(subdirs))
        else:
            # Scan só do primeiro nível
            for item in dir_path.iterdir():
                if item.is_dir():
                    if not item.name.startswith("."):
                        subdirs.append(item.name)
                elif item.is_file():
                    size = item.stat().st_size
                    total_size += size
                    total_files += 1
                    if item.suffix.lower() in (".md", ".markdown"):
                        md_files += 1
                        md_size += size
                    else:
                        other_files += 1
                        other_size += size
    except PermissionError:
        pass

    return {
        "exists": True,
        "path": str(dir_path),
        "files": total_files,
        "md_files": md_files,
        "other_files": other_files,
        "size_bytes": total_size,
        "md_size_bytes": md_size,
        "other_size_bytes": other_size,
        "subdirs": sorted(subdirs),
    }


def _scan_recursive(dir_path: Path, max_depth: int = 4, current_depth: int = 0) -> Dict:
    """Scan recursivo com profundidade limitada."""
    base = _scan_directory(dir_path)
    if current_depth >= max_depth:
        base["children"] = {}
        return base

    children = {}
    for sub in base.get("subdirs", []):
        sub_path = dir_path / sub
        children[sub] = _scan_recursive(sub_path, max_depth, current_depth + 1)

    base["children"] = children
    return base


@router.get("/vault/tree")
async def vault_tree(max_depth: int = Query(default=3, le=5)):
    """Retorna árvore completa do cofre."""
    if not COFRE_DIR.exists():
        return {"error": f"Cofre não existe: {COFRE_DIR}", "tree": {}}

    tree = _scan_recursive(COFRE_DIR, max_depth=max_depth)
    return {
        "root": str(COFRE_DIR),
        "tree": tree,
        "total_files": tree.get("files", 0),
        "total_size_bytes": tree.get("size_bytes", 0),
    }


@router.get("/vault/stats")
async def vault_stats():
    """Stats agregadas do cofre por categoria."""
    categories = [
        "kothar_manuais", "kothar_core", "sessao", "planos",
        "evolucao do agente kothar 1.0", "local_ai_sessions",
        "produtos", "clientes", "empresa", "planejamento",
        "kothar_local_chats", "rag_backup",
    ]

    stats = []
    total_size = 0
    total_files = 0
    total_md = 0

    for cat in categories:
        cat_path = COFRE_DIR / cat
        s = _scan_directory(cat_path)
        if s["exists"] and s["files"] > 0:
            stats.append({
                "category": cat,
                "path": str(cat_path),
                "files": s["files"],
                "md_files": s["md_files"],
                "size_bytes": s["size_bytes"],
                "size_kb": round(s["size_bytes"] / 1024, 1),
            })
            total_size += s["size_bytes"]
            total_files += s["files"]
            total_md += s["md_files"]

    # Top arquivos por tamanho
    top_files = []
    for cat in categories:
        cat_path = COFRE_DIR / cat
        if not cat_path.exists():
            continue
        try:
            for f in cat_path.rglob("*.md"):
                top_files.append({
                    "name": f.name,
                    "path": str(f),
                    "category": cat,
                    "size_bytes": f.stat().st_size,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                })
        except Exception:
            pass

    top_files.sort(key=lambda x: x["size_bytes"], reverse=True)
    top_files = top_files[:20]

    return {
        "categories": stats,
        "total_files": total_files,
        "total_md": total_md,
        "total_size_bytes": total_size,
        "total_size_kb": round(total_size / 1024, 1),
        "top_files": top_files,
    }


@router.get("/vault/file")
async def read_file(path: str, max_lines: int = Query(default=200, le=2000)):
    """Lê conteúdo de um arquivo do cofre."""
    p = Path(path)
    if not p.exists():
        return {"error": f"Arquivo não existe: {path}"}
    if not p.is_file():
        return {"error": f"Não é arquivo: {path}"}

    # Whitelist: só cofre
    try:
        p_resolved = p.resolve()
        cofre_resolved = COFRE_DIR.resolve()
        if not str(p_resolved).startswith(str(cofre_resolved)):
            return {"error": f"Fora do cofre: {path}"}
    except Exception:
        return {"error": "Path inválido"}

    try:
        content = p.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        truncated = len(lines) > max_lines
        shown = "\n".join(lines[:max_lines])
        return {
            "path": path,
            "name": p.name,
            "size_bytes": p.stat().st_size,
            "total_lines": len(lines),
            "shown_lines": min(len(lines), max_lines),
            "truncated": truncated,
            "content": shown,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/chromadb/collections")
async def chromadb_collections():
    """Mapa de todas as collections do ChromaDB com contagem."""
    try:
        import chromadb
        client = chromadb.HttpClient(host="kothar_chromadb", port=8000)
        collections = client.list_collections()

        result = []
        total_docs = 0
        for col in collections:
            try:
                count = col.count()
                total_docs += count
                # Pega sample de metadata
                sample = col.peek(limit=3)
                metadatas = sample.get("metadatas", [])
                categories = set()
                for m in metadatas:
                    if isinstance(m, dict) and "category" in m:
                        categories.add(m["category"])

                result.append({
                    "name": col.name,
                    "count": count,
                    "categories": sorted(categories),
                    "sample_metadata": metadatas[0] if metadatas else None,
                })
            except Exception as e:
                result.append({
                    "name": col.name,
                    "error": str(e),
                    "count": 0,
                })

        return {
            "collections": result,
            "total_collections": len(result),
            "total_documents": total_docs,
        }
    except Exception as e:
        return {"error": f"ChromaDB indisponível: {e}", "collections": []}


@router.get("/chromadb/collection/{name}/sample")
async def chromadb_collection_sample(name: str, limit: int = Query(default=5, le=20)):
    """Pega sample de documentos de uma collection."""
    try:
        import chromadb
        client = chromadb.HttpClient(host="kothar_chromadb", port=8000)
        col = client.get_collection(name)
        sample = col.peek(limit=limit)

        docs = []
        for i, (doc, meta, doc_id) in enumerate(zip(
            sample.get("documents", []),
            sample.get("metadatas", []),
            sample.get("ids", []),
        )):
            docs.append({
                "id": doc_id,
                "metadata": meta,
                "content_preview": doc[:300] + ("..." if len(doc) > 300 else ""),
                "content_length": len(doc),
            })

        return {
            "collection": name,
            "total": col.count(),
            "sample": docs,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/rag/analysis")
async def rag_analysis():
    """Análise agregada do RAG: top sources, top queries, distribuição."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "http://localhost:8080/api/rag-tracker/recent?limit=200"
            )
            data = resp.json()
            queries = data.get("queries", [])

        # Top sources
        source_count: Dict[str, int] = {}
        # Top palavras nas queries
        from collections import Counter
        import re
        word_count: Counter = Counter()
        chunk_dist: list = []
        time_buckets: Dict[str, int] = {}

        for q in queries:
            for s in q.get("sources", []):
                source_count[s] = source_count.get(s, 0) + 1
            for word in re.findall(r"\b[a-zà-ú]{4,}\b", q.get("query", "").lower()):
                if word not in {"como", "qual", "quais", "sobre", "para", "isso", "esse"}:
                    word_count[word] += 1
            chunks = q.get("chunks_count", 0)
            chunk_dist.append(chunks)
            # Bucket por hora
            import time
            hour = time.strftime("%H:00", time.localtime(q.get("timestamp", 0)))
            time_buckets[hour] = time_buckets.get(hour, 0) + 1

        # Top 10 sources
        top_sources = sorted(source_count.items(), key=lambda x: x[1], reverse=True)[:15]
        # Top 20 words
        top_words = word_count.most_common(20)
        # Distribuição de chunks
        avg_chunks = sum(chunk_dist) / max(len(chunk_dist), 1) if chunk_dist else 0
        max_chunks = max(chunk_dist) if chunk_dist else 0
        chunks_histogram = {}
        for c in chunk_dist:
            bucket = f"{(c // 5) * 5}-{(c // 5) * 5 + 4}"
            chunks_histogram[bucket] = chunks_histogram.get(bucket, 0) + 1

        return {
            "total_queries_analyzed": len(queries),
            "top_sources": [{"name": s, "count": c} for s, c in top_sources],
            "top_keywords": [{"word": w, "count": c} for w, c in top_words],
            "chunks_stats": {
                "avg": round(avg_chunks, 1),
                "max": max_chunks,
                "min": min(chunk_dist) if chunk_dist else 0,
                "histogram": dict(sorted(chunks_histogram.items())),
            },
            "time_distribution": dict(sorted(time_buckets.items())),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/sessions/active")
async def active_sessions():
    """Sessões ativas com RAG, com queries por sessão."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("http://localhost:8080/api/rag-tracker/sessions")
            data = resp.json()
            sessions = data.get("sessions", [])

            # Enriquece cada sessão com últimas queries
            for s in sessions[:10]:
                sid = s["session_id"]
                try:
                    detail_resp = await client.get(
                        f"http://localhost:8080/api/rag-tracker/sessions/{sid}"
                    )
                    detail = detail_resp.json()
                    s["recent_queries"] = detail.get("queries", [])[-5:]
                except Exception:
                    s["recent_queries"] = []

            return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        return {"error": str(e)}
