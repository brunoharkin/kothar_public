"""
=============================================================
 KOTHAR v6.0 — Project Mode
 Indexa uma pasta como projeto e dá contexto de código real.
 Coleção ChromaDB dedicada: kothar_project_<hash>
=============================================================
"""
import os
import re
import hashlib
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger("kothar.project")

# Coleção de projetos (cada um tem sua collection)
PROJECT_COLLECTIONS = {}
PROJECT_ROOTS = [
    Path(value).expanduser().resolve()
    for value in os.environ.get("KOTHAR_PROJECT_ROOTS", str(Path(__file__).resolve().parents[2])).split(":")
    if value
]
SENSITIVE_PARTS = {".git", ".ssh", ".aws", "node_modules", "secrets", "credentials", ".venv", "venv"}
SENSITIVE_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "token.json"}


def is_indexable_path(path: Path) -> bool:
    try:
        resolved = path.resolve(strict=True)
        if not any(resolved == root or resolved.is_relative_to(root) for root in PROJECT_ROOTS):
            return False
        if {part.lower() for part in resolved.parts} & SENSITIVE_PARTS:
            return False
        if resolved.name.lower() in SENSITIVE_NAMES or resolved.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
            return False
        return resolved.is_file()
    except (OSError, RuntimeError):
        return False


def get_project_id(path: str) -> str:
    """Gera ID determinístico do projeto baseado no path."""
    return "proj_" + hashlib.md5(path.encode("utf-8")).hexdigest()[:10]


def detect_language(path: str) -> str:
    """Detecta linguagem do arquivo pela extensão."""
    ext = Path(path).suffix.lower()
    return {
        ".py": "python",
        ".ts": "typescript", ".tsx": "tsx",
        ".js": "javascript", ".jsx": "jsx",
        ".md": "markdown",
        ".go": "go", ".rs": "rust",
        ".java": "java", ".kt": "kotlin",
        ".rb": "ruby", ".php": "php",
        ".c": "c", ".cpp": "cpp", ".h": "c_header",
        ".sh": "bash", ".yaml": "yaml", ".yml": "yaml",
        ".json": "json", ".toml": "toml",
    }.get(ext, "text")


def chunk_code(content: str, max_lines: int = 50, max_chars: int = 2000) -> List[str]:
    """
    Chunks inteligentes para código:
    - Funções/classes preferidas quando possível
    - Fallback: chunks por linhas
    """
    if len(content) <= max_chars:
        return [content]

    chunks = []
    lines = content.split("\n")

    # Tenta split por funções/classes primeiro (Python/JS/Go)
    boundaries = []
    for i, line in enumerate(lines):
        # Python: def/class
        if re.match(r"^(def |class |async def )", line):
            boundaries.append(i)
        # JS/TS: function/class
        elif re.match(r"^(function |class |const \w+ = .*=>|export )", line):
            boundaries.append(i)
        # Go: func/type
        elif re.match(r"^func |^type \w+ ", line):
            boundaries.append(i)

    if len(boundaries) >= 3:
        # Chunk por boundary
        boundaries.append(len(lines))
        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = min(boundaries[i + 1], start + max_lines)
            chunk = "\n".join(lines[start:end])
            if chunk.strip():
                chunks.append(chunk)
    else:
        # Fallback: chunks por tamanho
        start = 0
        while start < len(lines):
            end = min(start + max_lines, len(lines))
            chunk = "\n".join(lines[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start = end - 5 if end < len(lines) else len(lines)  # 5 linhas overlap

    return chunks


async def index_project(
    project_path: str,
    collection_name: Optional[str] = None,
    file_patterns: Optional[List[str]] = None,
    max_files: int = 500,
) -> Dict:
    """
    Indexa um projeto (pasta) no ChromaDB.
    Retorna stats.
    """
    project = Path(project_path).expanduser().resolve()
    if not any(project == root or project.is_relative_to(root) for root in PROJECT_ROOTS):
        return {"ok": False, "error": "Diretório fora das raízes permitidas"}
    project_path = str(project)
    if not os.path.isdir(project_path):
        return {"ok": False, "error": f"Não é diretório: {project_path}"}

    # Collection name
    proj_id = get_project_id(project_path)
    coll_name = collection_name or f"kothar_{proj_id}"

    # Padrões default
    if not file_patterns:
        file_patterns = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.go", "*.rs",
                         "*.md", "*.yaml", "*.yml", "*.json", "*.toml"]

    try:
        import chromadb
        client = chromadb.HttpClient(host="kothar_chromadb", port=8000)

        # Limpa collection anterior
        try:
            client.delete_collection(coll_name)
        except Exception:
            pass

        collection = client.get_or_create_collection(
            name=coll_name,
            metadata={"project_path": project_path, "project_id": proj_id},
        )

        # Encontra arquivos
        all_files = []
        for pattern in file_patterns:
            all_files.extend(Path(project_path).rglob(pattern))

        # Filtra node_modules, .git, __pycache__, etc
        all_files = [
            f for f in all_files
            if is_indexable_path(f)
            and f.stat().st_size < 500_000  # 500KB max
        ]
        all_files = all_files[:max_files]

        # Indexa cada arquivo
        indexed = 0
        for file_path in all_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if len(content) < 30:
                    continue

                chunks = chunk_code(content, max_lines=50, max_chars=2000)
                lang = detect_language(str(file_path))

                for i, chunk in enumerate(chunks):
                    doc_id = f"{file_path.stem}_{i:03d}"
                    try:
                        collection.add(
                            ids=[doc_id],
                            documents=[chunk],
                            metadatas=[{
                                "source": str(file_path),
                                "filename": file_path.name,
                                "category": "project",
                                "project_id": proj_id,
                                "language": lang,
                                "chunk_index": i,
                                "rel_path": str(file_path.relative_to(project_path)),
                            }],
                        )
                        indexed += 1
                    except Exception as e:
                        logger.debug(f"Erro chunk {file_path}:{i}: {e}")

            except Exception as e:
                logger.debug(f"Erro arquivo {file_path}: {e}")

        PROJECT_COLLECTIONS[project_path] = coll_name

        logger.info(f"Projeto {project_path}: {len(all_files)} arquivos, {indexed} chunks em {coll_name}")
        return {
            "ok": True,
            "project_id": proj_id,
            "collection": coll_name,
            "files_indexed": len(all_files),
            "chunks_indexed": indexed,
        }

    except Exception as e:
        logger.error(f"Falha ao indexar projeto: {e}")
        return {"ok": False, "error": str(e)}


def get_project_collection(project_path: str) -> Optional[str]:
    """Retorna o nome da collection de um projeto indexado."""
    if project_path in PROJECT_COLLECTIONS:
        return PROJECT_COLLECTIONS[project_path]
    proj_id = get_project_id(project_path)
    return f"kothar_{proj_id}"


def list_indexed_projects() -> List[Dict]:
    """Lista projetos indexados."""
    return [
        {"path": p, "collection": c}
        for p, c in PROJECT_COLLECTIONS.items()
    ]
