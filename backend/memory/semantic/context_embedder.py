"""
=============================================================
 KOTHAR v4.0 — Context Embedder (Cofre -> RAG)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Lê os arquivos Markdown do Cofre (Obsidian) e os injeta 
 na coleção `kothar_context` do ChromaDB com chunking inteligente.
"""

import os
import uuid
import re
from pathlib import Path

from backend.core.config import settings
from backend.core.logger import get_logger
from backend.memory.semantic.chroma_client import chroma_memory

log = get_logger("memory.semantic.context_embedder")

# Ignore lists
IGNORE_DIRS = {".obsidian", ".claude", ".git", "rag_backup", "scratch", ".trash"}


def smart_markdown_chunker(text: str, max_chars: int = 1500) -> list[str]:
    """
    Estratégia de chunking eficiente e segura visualmente.
    Respeita blocos de código e tabelas (não quebra ao meio).
    Agrupa parágrafos até o limite de caracteres.
    """
    # Split by double newline (paragraphs/blocks)
    blocks = re.split(r'\n\n+', text)
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    in_code_block = False
    
    for block in blocks:
        block_len = len(block)
        
        # Detecção básica se estamos dentro de um bloco de código (Markdown ``` )
        # Para evitar quebrar o chunk no meio de um bloco de código se ele tiver linhas vazias
        code_fence_count = block.count("```")
        if code_fence_count % 2 != 0:
            in_code_block = not in_code_block

        # Se adicionar o bloco ultrapassar o limite, e não estivermos no meio de um bloco de código, salva o chunk atual
        if current_len + block_len > max_chars and not in_code_block and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [block]
            current_len = block_len
        else:
            current_chunk.append(block)
            current_len += block_len + 2  # +2 para o \n\n
            
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks


class ContextEmbedder:
    """
    Indexa o Cofre (Vault) no ChromaDB (coleção kothar_context).
    """

    def __init__(self):
        # Fallback to hardcoded vault path if not in settings
        self.vault_path = Path(getattr(settings, "vault_path", os.path.expanduser("~/cofre")))

    async def embed_all(self) -> dict[str, int]:
        """Indexa todos os arquivos .md do cofre."""
        if not self.vault_path.exists():
            log.error(f"Cofre não encontrado em {self.vault_path}")
            return {"indexed_files": 0, "indexed_chunks": 0, "errors": 1}

        md_files = []
        for root, dirs, files in os.walk(self.vault_path):
            # Filtra diretórios ignorados
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file.endswith(".md"):
                    md_files.append(Path(root) / file)

        log.info(f"Encontrados {len(md_files)} arquivos Markdown no Cofre para indexação.")

        indexed_files = 0
        indexed_chunks = 0
        errors = 0

        for md_file in md_files:
            try:
                chunks_count = await self.embed_file(md_file)
                indexed_files += 1
                indexed_chunks += chunks_count
            except Exception as e:
                log.error(f"Falha ao indexar arquivo {md_file.name}", error=str(e))
                errors += 1

        log.info("Indexação de Contexto concluída", 
                 files=indexed_files, chunks=indexed_chunks, errors=errors)
        return {"indexed_files": indexed_files, "indexed_chunks": indexed_chunks, "errors": errors}

    async def embed_file(self, md_path: Path) -> int:
        """Indexa um arquivo .md, fazendo chunking inteligente."""
        try:
            content = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            log.warning(f"Ignorando {md_path.name} (não é UTF-8 válido)")
            return 0
            
        if not content.strip():
            return 0
            
        # Nome do arquivo e pasta pai como contexto
        filename = md_path.name
        title = md_path.stem
        parent_dir = md_path.parent.name
        
        tags = [parent_dir] if parent_dir != self.vault_path.name else []
        
        chunks = smart_markdown_chunker(content, max_chars=1500)
        
        for i, chunk in enumerate(chunks):
            # Cria ID único mas determinístico baseado no arquivo e índice do chunk
            chunk_id = f"ctx_{uuid.uuid5(uuid.NAMESPACE_URL, str(md_path) + str(i))}"
            
            # Upsert
            await chroma_memory.upsert_context(
                context_id=chunk_id,
                title=f"{title} (Parte {i+1}/{len(chunks)})",
                content=chunk,
                filename=filename,
                tags=tags
            )
            
        return len(chunks)

# Singleton
context_embedder = ContextEmbedder()
