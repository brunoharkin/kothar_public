#!/usr/bin/env python3
"""
Kothar RAG Indexer
Indexa TODO o conteúdo do cofre no ChromaDB para o RAG funcionar de verdade.
"""

import os
import sys
import asyncio
from pathlib import Path
import chromadb
from chromadb.config import Settings
import re


# Configuração - conecta ao ChromaDB do container
CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

COFRE_DIR = Path("/home/bruno-harkin/Cofre")

# Coleções ChromaDB por categoria
COLLECTIONS = {
    "kothar_core": "Núcleo do Kothar (skills, agentes, workflows)",
    "kothar_manuais": "Manuais e documentação técnica do Kothar",
    "kothar_sessoes": "Sessões e histórico de trabalho",
    "kothar_planos": "Planos de implementação",
    "kothar_produtos": "Produtos e documentação comercial (ChronoDesk, Sophia, Orby)",
    "kothar_empresa": "Empresa e cultura Ugarit Digital",
    "kothar_clientes": "Dossiês e histórico de clientes",
}


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list:
    """Divide texto longo em chunks menores."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))

        # Tentar quebrar em parágrafo ou frase
        if end < len(text):
            # Procurar última quebra de parágrafo
            for sep in ["\n\n", "\n", ". ", "? ", "! "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_chars * 0.5:  # Pelo menos metade do chunk
                if last_sep > max_chars * 0.5:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)

    return chunks


def index_directory(client: chromadb.PersistentClient, dir_path: Path, collection_name: str, file_pattern: str = "*.md"):
    """Indexa todos os arquivos .md de um diretório (recursivamente)."""
def index_directory(client, dir_path, collection_name, file_pattern="*.md"):
    if not dir_path.exists():
        print(f"⚠️  Diretório não existe: {dir_path}")
        return 0

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": COLLECTIONS.get(collection_name, "")}
    )

    # Busca arquivos recursivamente
    collection = client.get_or_create_collection(name=collection_name)
    files = list(dir_path.rglob(file_pattern))
    if not files:
        print(f"⚠️  Nenhum arquivo encontrado em {dir_path}")
        return 0

    indexed_count = 0
    for file_path in files:
        # Skip README e CONTEXT nos diretórios raiz (já indexados)
        if file_path.parent == dir_path and file_path.name in ["README.md", "CONTEXT.md"]:
        if file_path.name in ["README.md", "CONTEXT.md"]:
            continue

        relative_path = file_path.relative_to(dir_path)
        print(f"  📄 {relative_path}")

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"     ❌ Erro ao ler: {e}")
            continue

        # Divide em chunks
        chunks = chunk_text(content)
        print(f"     → {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_{i:03d}"
            try:
                collection.add(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "source": str(file_path),
                        "filename": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "category": collection_name,
                        "chunk_index": i
                    }]
                )
                indexed_count += 1
            except Exception as e:
                print(f"     ❌ Erro ao indexar chunk {i}: {e}")

                pass
    return indexed_count


def main():
    print("🔨 Kothar RAG Indexer")
    print("=" * 50)
    print(f"
📡 Conectando ao ChromaDB em {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(allow_reset=True)
        )
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, settings=Settings(allow_reset=True))
        client.heartbeat()
        print("✅ Conectado")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        sys.exit(1)

    total = 0
    collection_name = "kothar_cofre"
    print(f"
📚 Indexando: {collection_name}")
    count = index_directory(client, COFRE_DIR, collection_name)
    total += count
    print(f"✅ {count} chunks indexados em '{collection_name}'")
    print(f"
🎉 Total: {total} chunks indexados")
    try:
        coll = client.get_collection(collection_name)
        print(f"  • {collection_name}: {coll.count()} documentos")
    except Exception as e:
        print(f"  • {collection_name}: erro ao contar - {e}")
    print("✅ Conectado ao ChromaDB")
    count = index_directory(client, COFRE_DIR, "kothar_cofre")
    print(f"✅ {count} chunks indexados em 'kothar_cofre'")

if __name__ == "__main__":
    main()