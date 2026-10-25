"""Skills router."""

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import desc, select

from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.trace.models import Skill

log = get_logger("api.skills")
router = APIRouter()


@router.get("/")
async def list_skills(
    category: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
):
    """Lista skills cristalizadas."""
    async with get_db_session() as db:
        q = select(Skill).order_by(desc(Skill.usage_count))
        if category:
            q = q.where(Skill.category == category)
        q = q.limit(limit).offset(offset)
        result = await db.execute(q)
        return [_skill_to_dict(s) for s in result.scalars().all()]


@router.post("/")
async def create_skill(body: dict):
    """Cristaliza uma nova skill."""
    async with get_db_session() as db:
        skill = Skill(
            name=body["name"],
            description=body.get("description"),
            yaml_content=body["yaml_content"],
            category=body.get("category"),
            tags=body.get("tags", []),
            forged_by=body.get("forged_by"),
        )
        db.add(skill)
        await db.flush()
        log.info("Skill cristalizada", name=skill.name, category=skill.category)
        return _skill_to_dict(skill)


@router.get("/{skill_id}")
async def get_skill(skill_id: uuid.UUID):
    """Retorna uma skill específica."""
    async with get_db_session() as db:
        result = await db.execute(select(Skill).where(Skill.id == skill_id))
        skill = result.scalar_one_or_none()
        if not skill:
            return JSONResponse(status_code=404, content={"error": "Skill não encontrada"})
        return _skill_to_dict(skill)


def _skill_to_dict(s: Skill) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "description": s.description,
        "category": s.category,
        "tags": s.tags or [],
        "usage_count": s.usage_count,
        "success_rate": float(s.success_rate),
        "forged_by": s.forged_by,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }
