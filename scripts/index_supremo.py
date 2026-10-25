#!/usr/bin/env python3
"""
Kothar RAG Supremo Indexer
Indexa TODO o cofre do Kothar em uma collection unificada (kothar_conhecimento_full)
com chunks otimizados para retrieval granular.

Uso:
    python3 index_supremo.py
"""

import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings


CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

COFRE_DIR = Path("/home/bruno/cofre")

# Collection unificada para o RAG Supremo
SUPREMO_COLLECTION = "kothar_conhecimento_full"

# Pastas do cofre que devem ser indexadas
DIRS_TO_INDEX = [
    "kothar_manuais",
    "kothar_core",
    "sessao",
    "planos",
    "evolucao do agente kothar 1.0",
    "local_ai_sessions",
    "produtos",
    "clientes",
    "empresa",
    "planejamento",
    "kothar_local_chats",
]


def chunk_text_inteligente(text: str, max_chars: int = 1200, overlap: int = 200) -> list:
    """
    Chunking otimizado para retrieval: prefere parágrafos, depois sentenças.
    Chunks menores = retrieval mais granular.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))

        # Tentar quebrar em pontos semânticos fortes
        if end < len(text):
            # Prioridade: \n\n > \n# (títulos) > \n > . ! ?
            for sep in ["\n\n", "\n#", "\n##", "\n", ". ", "? ", "! "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_chars * 0.3:  # mínimo 30% do chunk
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk and len(chunk) > 50:  # descarta chunks muito pequenos
            chunks.append(chunk)

        # Avança com overlap
        start = end - overlap if end < len(text) else len(text)

    return chunks


def indexar_cofre():
    print("=" * 60)
    print("🧠 Kothar RAG Supremo — Indexador do Cofre Completo")
    print("=" * 60)

    print(f"\n📡 Conectando ao ChromaDB em {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(allow_reset=False),
        )
        client.heartbeat()
        print("✅ Conectado")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        sys.exit(1)

    # Pega ou cria a collection suprema
    try:
        # Tenta deletar para reconstruir do zero
        client.delete_collection(SUPREMO_COLLECTION)
        print(f"🗑️  Collection '{SUPREMO_COLLECTION}' anterior removida")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=SUPREMO_COLLECTION,
        metadata={
            "description": "Todo o conhecimento do Kothar indexado para RAG Supremo",
            "chunk_size": 1200,
            "overlap": 200,
        },
    )

    total_files = 0
    total_chunks = 0
    total_chars = 0

    for dir_name in DIRS_TO_INDEX:
        dir_path = COFRE_DIR / dir_name
        if not dir_path.exists():
            print(f"  ⚠️  {dir_name}/ não existe, pulando")
            continue

        md_files = list(dir_path.rglob("*.md"))
        if not md_files:
            print(f"  📁 {dir_name}/ (vazio)")
            continue

        print(f"\n📚 Indexando {dir_name}/ ({len(md_files)} arquivos)...")
        dir_chunks = 0

        for file_path in md_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if len(content) < 100:  # pula arquivos muito pequenos
                    continue

                chunks = chunk_text_inteligente(content, max_chars=1200, overlap=200)
                if not chunks:
                    continue

                for i, chunk in enumerate(chunks):
                    doc_id = f"{file_path.stem}_{i:04d}"
                    try:
                        collection.add(
                            ids=[doc_id],
                            documents=[chunk],
                            metadatas=[{
                                "source": str(file_path),
                                "filename": file_path.name,
                                "category": dir_name,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "char_count": len(chunk),
                                "mtime": file_path.stat().st_mtime,
                            }],
                        )
                        total_chars += len(chunk)
                        dir_chunks += 1
                    except Exception as e:
                        print(f"     ❌ Erro chunk {i}: {e}")

                total_chunks += dir_chunks
                total_files += 1
                print(f"  ✓ {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                print(f"  ❌ Erro em {file_path.name}: {e}")

        print(f"  → {dir_chunks} chunks em {dir_name}/")

    print("\n" + "=" * 60)
    print("🎉 Indexação Concluída")
    print("=" * 60)
    print(f"  📁 Arquivos processados: {total_files}")
    print(f"  📦 Total de chunks: {total_chunks}")
    print(f"  📊 Total de caracteres: {total_chars:,}")
    print(f"  💾 Collection: {SUPREMO_COLLECTION}")

    # Stats
    try:
        count = collection.count()
        print(f"  ✓ Chunks na collection agora: {count}")
    except Exception as e:
        print(f"  ⚠️  Erro ao contar: {e}")


if __name__ == "__main__":
    indexar_cofre()
