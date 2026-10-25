"""
=============================================================
 KOTHAR v4.0 — Cascade Metrics Router
 API endpoint para métricas do sistema multi-modelo.
=============================================================
"""

from fastapi import APIRouter

from backend.trace.cascade_metrics import get_cascade_metrics, record_cascade_execution

router = APIRouter()


@router.get("/cascade")
async def cascade_metrics():
    """Métricas do sistema multi-modelo (Haiku/Sonnet/Opus)."""
    return get_cascade_metrics()


@router.post("/cascade/record")
async def cascade_record(body: dict):
    """Registra uma execução de cascade (interno)."""
    record_cascade_execution(
        model=body.get("model", "sonnet"),
        tokens=body.get("tokens", 0),
        escalated=body.get("escalated", False),
        from_model=body.get("from_model"),
    )
    return {"ok": True}
