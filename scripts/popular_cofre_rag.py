import os
from pathlib import Path
import chromadb

COFRE_DIR = Path("/home/bruno-harkin/Cofre")
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

def index_cofre():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    
    collection = client.get_or_create_collection(
        name="kothar_cofre", 
        metadata={"description": "Memória permanente do Cofre / Obsidian"}
    )
    
    files = list(COFRE_DIR.rglob("*.md"))
    indexed = 0
    for file_path in files:
        if file_path.name in ["README.md", "CLAUDE.md", "GEMINI.md"] and file_path.parent == COFRE_DIR:
            continue
            
        print(f"📄 Indexando: {file_path.relative_to(COFRE_DIR)}")
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_{i:03d}"
            try:
                collection.upsert(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "source": str(file_path),
                        "filename": file_path.name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }]
                )
                indexed += 1
            except Exception as e:
                print(f"❌ Erro no chunk {i} de {file_path.name}: {e}")
                
    print(f"✅ Total de chunks indexados: {indexed}")

if __name__ == "__main__":
    index_cofre()
