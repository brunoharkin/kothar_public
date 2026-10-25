import re

with open("scripts/index_rag.py", "r") as f:
    content = f.read()

new_main = """
def main():
    print("🔨 Kothar RAG Indexer")
    print("=" * 50)
    print(f"\\n📡 Conectando ao ChromaDB em {CHROMA_HOST}:{CHROMA_PORT}...")
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(allow_reset=True)
        )
        client.heartbeat()
        print("✅ Conectado")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        sys.exit(1)

    total = 0
    collection_name = "kothar_cofre"
    print(f"\\n📚 Indexando: {collection_name}")
    count = index_directory(client, COFRE_DIR, collection_name)
    total += count
    print(f"✅ {count} chunks indexados em '{collection_name}'")
    print(f"\\n🎉 Total: {total} chunks indexados")
    try:
        coll = client.get_collection(collection_name)
        print(f"  • {collection_name}: {coll.count()} documentos")
    except Exception as e:
        print(f"  • {collection_name}: erro ao contar - {e}")
"""

content = re.sub(r'def main\(\):.*', new_main.strip(), content, flags=re.DOTALL)

with open("scripts/index_rag.py", "w") as f:
    f.write(content)
