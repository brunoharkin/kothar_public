"""Health check router."""

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "Engenheiro Kothar API",
            "version": settings.kothar_version,
            "environment": settings.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@router.get("/live")
async def liveness():
    """Kubernetes liveness probe."""
    return {"alive": True}


@router.get("/ready")
async def readiness():
    """Kubernetes readiness probe."""
    return {"ready": True}
