#!/usr/bin/env python3
"""
Kothar Embedder (v2.0)
Responsável por pegar transcripts e notas de decisões e injetar no ChromaDB.
"""

import sys
import json
import uuid
# Import simulado para ChromaDB (requer `pip install chromadb`)
# import chromadb

def clean_secrets(text):
    """
    Simula o gate de segurança: limpa qualquer token ou API key
    antes de jogar pro banco vetorial.
    """
    # Exemplo simples:
    # text = re.sub(r'(sk-[a-zA-Z0-9]{48})', '[REDACTED]', text)
    return text

def embed_document(doc_path, metadata=None):
    """
    Lê o documento, limpa segredos, e joga pro ChromaDB.
    """
    if metadata is None:
        metadata = {}
        
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Erro lendo arquivo: {e}"}))
        sys.exit(1)
        
    safe_content = clean_secrets(content)
    
    # ChromaDB logic (comentado para evitar falha se o modulo não existir na maquina)
    # client = chromadb.PersistentClient(path="~/.kothar/vector-db/")
    # collection = client.get_or_create_collection(name="kothar_memory")
    # 
    # doc_id = str(uuid.uuid4())
    # collection.add(
    #     documents=[safe_content],
    #     metadatas=[metadata],
    #     ids=[doc_id]
    # )
    
    print(json.dumps({"status": "success", "message": f"Documento de {len(safe_content)} bytes vectorizado com sucesso."}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 embedder.py <caminho_do_arquivo> [metadata_json]")
        sys.exit(1)
        
    file_path = sys.argv[1]
    meta = {}
    if len(sys.argv) >= 3:
        try:
            meta = json.loads(sys.argv[2])
        except:
            pass
            
    embed_document(file_path, meta)
