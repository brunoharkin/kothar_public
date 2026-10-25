#!/usr/bin/env python3
"""
Kothar Embedder v3.0
Sistema de vectorização com fallback para SQLite.
Usa ChromaDB se disponível, caso contrário usa busca por texto.
"""

import sys
import os
import json
import uuid
import re
import sqlite3
from pathlib import Path

# Config
VECTOR_DB_PATH = os.path.expanduser("~/kothar/chromadb")
SQLITE_DB = os.path.join(VECTOR_DB_PATH, "kothar_memory.db")

# Tentar importar ChromaDB
CHROMADB_AVAILABLE = False
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    pass

def clean_secrets(text):
    """Limpa segredos antes de vectorizar."""
    # Redact API keys
    text = re.sub(r'(sk-[a-zA-Z0-9]{32,})', '[API_KEY]', text)
    text = re.sub(r'(pk-[a-zA-Z0-9]{32,})', '[PUB_KEY]', text)
    text = re.sub(r'(AKIA[0-9A-Z]{16})', '[AWS_KEY]', text)
    # Redact passwords
    text = re.sub(r'(password\s*[:=]\s*["\'][^"\']{8,})', 'password=[REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'(senha\s*[:=]\s*["\'][^"\']{4,})', 'senha=[REDACTED]', text, flags=re.IGNORECASE)
    # Redact tokens
    text = re.sub(r'(token\s*[:=]\s*["\'][^"\']{20,})', 'token=[REDACTED]', text, flags=re.IGNORECASE)
    return text

def init_sqlite():
    """Inicializa banco SQLite."""
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    conn = sqlite3.connect(SQLITE_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            content TEXT,
            metadata TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_content ON documents(content)
    ''')
    conn.commit()
    return conn

def embed_document_sqlite(doc_path, metadata=None):
    """Vectoriza usando SQLite (fallback)."""
    if metadata is None:
        metadata = {}

    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Erro lendo arquivo: {e}"}))
        return False

    safe_content = clean_secrets(content)
    doc_id = str(uuid.uuid4())

    meta_json = json.dumps(metadata)
    source = str(doc_path)

    conn = init_sqlite()
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO documents (id, content, metadata, source) VALUES (?, ?, ?, ?)',
        (doc_id, safe_content, meta_json, source)
    )
    conn.commit()
    conn.close()

    return True

def search_sqlite(query, n_results=3):
    """Busca usando SQLite (fallback - busca por palavras-chave)."""
    conn = init_sqlite()
    c = conn.cursor()

    # Extrair palavras da query
    words = query.lower().split()
    query_pattern = '%' + '%'.join(words) + '%'

    c.execute(
        'SELECT id, content, metadata, source FROM documents WHERE content LIKE ? LIMIT ?',
        (query_pattern, n_results)
    )

    results = []
    for row in c.fetchall():
        results.append({
            "ids": [row[0]],
            "documents": [row[1]],
            "metadatas": [json.loads(row[2])],
            "distances": [0.5]  # Placeholder
        })

    conn.close()
    return results

def embed_chromadb(doc_path, metadata=None):
    """Vectoriza usando ChromaDB."""
    if metadata is None:
        metadata = {}

    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False

    safe_content = clean_secrets(content)

    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    collection = client.get_or_create_collection(name="kothar_memory")

    doc_id = str(uuid.uuid4())
    metadata['source'] = str(doc_path)

    collection.add(
        documents=[safe_content],
        metadatas=[metadata],
        ids=[doc_id]
    )

    return True

def embed_document(doc_path, metadata=None):
    """Vectoriza documento (usa ChromaDB ou SQLite)."""
    if CHROMADB_AVAILABLE:
        success = embed_chromadb(doc_path, metadata)
    else:
        success = embed_document_sqlite(doc_path, metadata)

    if success:
        print(json.dumps({
            "status": "success",
            "engine": "chromadb" if CHROMADB_AVAILABLE else "sqlite",
            "path": VECTOR_DB_PATH,
            "doc": doc_path
        }))
    return success

def search_documents(query, n_results=3):
    """Busca documentos."""
    if CHROMADB_AVAILABLE:
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        collection = client.get_or_create_collection(name="kothar_memory")
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
    else:
        results = search_sqlite(query, n_results)

    return results

def list_documents():
    """Lista documentos."""
    conn = init_sqlite()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM documents')
    count = c.fetchone()[0]
    conn.close()

    print(json.dumps({
        "status": "success",
        "engine": "chromadb" if CHROMADB_AVAILABLE else "sqlite",
        "count": count,
        "path": VECTOR_DB_PATH
    }))
    return count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  embedder.py embed <arquivo> [metadata_json]")
        print("  embedder.py search <query> [n_resultados]")
        print("  embedder.py list")
        print(f"\nEngine: {'ChromaDB' if CHROMADB_AVAILABLE else 'SQLite (fallback)'}")
        sys.exit(1)

    command = sys.argv[1]

    if command == "embed":
        if len(sys.argv) < 3:
            print("Erro: arquivo não especificado")
            sys.exit(1)

        file_path = sys.argv[2]
        meta = {"type": "document"}
        if len(sys.argv) >= 4:
            try:
                meta = {**meta, **json.loads(sys.argv[3])}
            except:
                pass

        embed_document(file_path, meta)

    elif command == "search":
        query = sys.argv[2] if len(sys.argv) >= 3 else ""
        n = int(sys.argv[3]) if len(sys.argv) >= 4 else 3

        if not query:
            print("Erro: query não especificada")
            sys.exit(1)

        results = search_documents(query, n)
        if results:
            print(json.dumps(results, indent=2, default=str))

    elif command == "list":
        list_documents()

    elif command == "test":
        print(f"ChromaDB disponível: {CHROMADB_AVAILABLE}")
        print(f"Path: {VECTOR_DB_PATH}")
        print(f"SQLite DB: {SQLITE_DB}")

    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)
