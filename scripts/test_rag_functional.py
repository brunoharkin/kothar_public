#!/usr/bin/env python3
"""
Teste de Validação Funcional do RAG do Kothar.
Executado pelo instalador para garantir que o RAG está operacional.
Retorna código 0 se estiver 100% funcional, ou 1 se falhar.
"""
import sys
import os
from pathlib import Path

# Adiciona raiz ao path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from backend.core.config_loader import get_kothar_config
    import chromadb
except ImportError as e:
    print(f"❌ [RAG FALHOU] Dependência ausente: {e}", file=sys.stderr)
    sys.exit(1)

def run_rag_smoke_test():
    cfg = get_kothar_config()
    chroma_path = cfg["caminhos"]["chroma_dir"]
    
    if not os.path.exists(chroma_path):
        print(f"❌ [RAG FALHOU] Diretório do ChromaDB não encontrado: {chroma_path}", file=sys.stderr)
        return False

    try:
        client = chromadb.PersistentClient(path=chroma_path)
        collections = client.list_collections()
        col_names = [c.name for c in collections]
        
        if not col_names:
            print("❌ [RAG FALHOU] Nenhuma coleção encontrada no ChromaDB.", file=sys.stderr)
            return False

        print(f"✅ ChromaDB conectado. Coleções disponíveis: {', '.join(col_names)}")
        
        # Teste de consulta em uma coleção existente
        target_col = None
        for name in ["kothar_cofre", "kothar_core", "skills"]:
            if name in col_names:
                target_col = client.get_collection(name)
                break
        
        if not target_col:
            target_col = client.get_collection(col_names[0])
            
        count = target_col.count()
        print(f"✅ Coleção '{target_col.name}' contém {count} registros indexados.")
        
        if count == 0:
            print("❌ [RAG FALHOU] Coleção está vazia. O RAG precisa de documentos indexados.", file=sys.stderr)
            return False

        # Realizar uma query de teste
        query_text = "regras de segurança e gates do kothar"
        results = target_col.query(query_texts=[query_text], n_results=min(3, count))
        
        if not results or not results.get("documents") or len(results["documents"][0]) == 0:
            print("❌ [RAG FALHOU] Query semântica não retornou resultados.", file=sys.stderr)
            return False

        print(f"✅ Consulta semântica de teste respondida com sucesso! Top match tamanho: {len(results['documents'][0][0])} caracteres.")
        return True

    except Exception as e:
        print(f"❌ [RAG FALHOU] Erro na execução do ChromaDB: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if run_rag_smoke_test():
        print("🎯 RAG KOTHAR: 100% OPERACIONAL E VALIDADO.")
        sys.exit(0)
    else:
        print("🛑 ERRO: O RAG não passou no teste de validação obrigatório.", file=sys.stderr)
        sys.exit(1)
