"""
=============================================================
 KOTHAR v4.0 — Cascade Metrics Router
 API endpoint para métricas do sistema multi-modelo.
=============================================================
"""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.trace.cascade_metrics import get_cascade_metrics, record_cascade_execution

router = APIRouter()


class CascadeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(default="sonnet", min_length=1, max_length=100)
    tokens: int = Field(default=0, ge=0, le=100_000_000)
    escalated: bool = False
    from_model: str | None = Field(default=None, max_length=100)


@router.get("/cascade")
async def cascade_metrics():
    """Métricas do sistema multi-modelo (Haiku/Sonnet/Opus)."""
    return get_cascade_metrics()


@router.post("/cascade/record")
async def cascade_record(body: CascadeRecord):
    """Registra uma execução de cascade (interno)."""
    record_cascade_execution(
        model=body.model, tokens=body.tokens, escalated=body.escalated, from_model=body.from_model,
    )
    return {"ok": True}
