"""
=============================================================
 Kothar v4.0 — Cofre Router
 Endpoints para salvar arquivos no cofre (~//cofre/).
=============================================================
"""

import os
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.core.logger import get_logger

log = get_logger("api.cofre")
router = APIRouter()

# Diretórios podem ser sobrescritos por ambiente; escrita e leitura continuam separadas.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
configured_write_path = os.environ.get("KOTHAR_VAULT_WRITE_PATH")
if configured_write_path:
    COFRE_RW = Path(configured_write_path).expanduser()
elif os.access("/cofre_rw", os.W_OK):
    COFRE_RW = Path("/cofre_rw")
elif Path("/home/bruno/cofre_rw").exists():
    COFRE_RW = Path("/home/bruno/cofre_rw")
else:
    COFRE_RW = PROJECT_ROOT / ".cofre_rw"
COFRE_REAL = Path(
    os.environ.get("KOTHAR_VAULT_PATH", os.environ.get("VAULT_PATH", "/vault"))
).expanduser()

# Cria pasta base se não existir
COFRE_RW.mkdir(parents=True, exist_ok=True)


class SaveRequest(BaseModel):
    folder: str
    filename: str
    content: str


class SaveResponse(BaseModel):
    success: bool
    path: str
    message: str


@router.post("/save")
async def save_to_cofre(req: SaveRequest) -> SaveResponse:
    """
    Salva conteúdo em uma pasta do cofre.

    Body:
      folder: subpasta dentro de ~/cofre (ex: 'kothar_local_chats')
      filename: nome do arquivo (ex: 'conversa-2026-09-02.md')
      content: conteúdo a ser salvo

    Returns:
      path: caminho completo do arquivo salvo
    """
    # Validação básica
    if not req.folder or not req.filename:
        raise HTTPException(status_code=400, detail="folder e filename são obrigatórios")

    # Segurança: prevenir path traversal
    if ".." in req.folder or ".." in req.filename:
        raise HTTPException(status_code=400, detail="Path traversal detectado")

    # Constrói path final em COFRE_RW (writable)
    target_dir = COFRE_RW / req.folder
    target_path = target_dir / req.filename

    # Valida que o path está dentro do cofre_rw
    try:
        target_path.resolve().relative_to(COFRE_RW.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Path fora do cofre")

    try:
        # Cria diretório se não existir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Salva o arquivo
        target_path.write_text(req.content, encoding="utf-8")

        log.info(
            "Arquivo salvo no cofre",
            path=str(target_path),
            size=len(req.content),
        )

        return SaveResponse(
            success=True,
            path=str(target_path),
            message=f"Arquivo salvo em {target_path}",
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Sem permissão para escrever em {target_path}")
    except OSError:
        log.error("Erro de I/O ao salvar no cofre", path=str(target_path))
        raise HTTPException(status_code=500, detail="Não foi possível salvar o arquivo")


@router.get("/list")
async def list_cofre_folders() -> dict:
    """Lista pastas disponíveis no cofre (read-only + writable)."""
    folders = []

    # Lê do vault (read-only) - lista estrutura original
    if COFRE_REAL.exists():
        for item in COFRE_REAL.iterdir():
            if item.is_dir():
                folders.append({
                    "name": item.name,
                    "path": str(item),
                    "read_only": True,
                })

    # Adiciona pastas writable criadas pelo usuário
    if COFRE_RW.exists():
        for item in COFRE_RW.iterdir():
            if item.is_dir():
                # Só adiciona se não está no vault
                if not any(f["name"] == item.name for f in folders):
                    folders.append({
                        "name": item.name,
                        "path": str(item),
                        "read_only": False,
                    })

    return {"folders": folders, "base_writable": str(COFRE_RW), "base_readonly": str(COFRE_REAL)}
