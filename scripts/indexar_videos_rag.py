#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Indexador Cirúrgico da Base de Conhecimento de Vídeos do Cofre
Indexa apenas os arquivos novos de transcrições em /home/bruno-harkin/Cofre/base-de-conhecimento/videos/
"""

import os
import sys
from pathlib import Path
import chromadb

DIRETORIO_VIDEOS = Path("/home/bruno-harkin/Cofre/base-de-conhecimento/videos")
CHROMA_PATH = os.environ.get("KOTHAR_CHROMA_DATA_PATH", "/home/bruno-harkin/kothar/.chroma-data")

def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list:
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", "? ", "! "]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_chars * 0.5:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)
    return chunks

def indexar_videos():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="kothar_cofre",
        metadata={"description": "Memória permanente do Cofre / Obsidian"}
    )

    arquivos = list(DIRETORIO_VIDEOS.glob("*.md"))
    print(f"[*] Total de arquivos de transcrição encontrados: {len(arquivos)}")

    total_chunks = 0
    for idx, f in enumerate(arquivos, start=1):
        try:
            conteudo = f.read_text(encoding="utf-8", errors="ignore")
            chunks = chunk_text(conteudo)
            
            ids = [f"{f.stem}_{i:03d}" for i in range(len(chunks))]
            metadatas = [{
                "source": str(f),
                "filename": f.name,
                "categoria": "base-de-conhecimento",
                "tipo": "video-transcricao",
                "chunk_index": i,
                "total_chunks": len(chunks)
            } for i in range(len(chunks))]

            collection.upsert(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            total_chunks += len(chunks)
            print(f"[{idx}/{len(arquivos)}] [OK] {f.name} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"[{idx}/{len(arquivos)}] [ERRO] {f.name}: {e}")

    print("=" * 60)
    print(f"✅ Concluído! {len(arquivos)} vídeos indexados cirurgicamente ({total_chunks} chunks no ChromaDB).")
    print("=" * 60)

if __name__ == "__main__":
    indexar_videos()

