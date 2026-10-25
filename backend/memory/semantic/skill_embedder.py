"""
=============================================================
 KOTHAR v4.0 — Skill Embedder
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Lê arquivos YAML de ~/kothar/skills/ e os indexa no ChromaDB.
 Também persiste no PostgreSQL para auditoria via Git.
"""

import uuid
from pathlib import Path

import yaml

from backend.core.config import settings
from backend.core.database import get_db_session
from backend.core.logger import get_logger
from backend.memory.semantic.chroma_client import chroma_memory
from backend.trace.models import Skill

log = get_logger("memory.semantic.skill_embedder")


class SkillEmbedder:
    """
    Indexa Skills YAML no ChromaDB e PostgreSQL.

    Fluxo:
    1. Lê arquivo YAML de skills/
    2. Valida estrutura mínima
    3. Upsert no PostgreSQL (auditável via Git)
    4. Upsert no ChromaDB (busca semântica)
    """

    def __init__(self):
        self.skills_path: Path = settings.skills_path

    async def embed_all(self) -> dict[str, int]:
        """Indexa todas as skills YAML do diretório skills/."""
        yaml_files = list(self.skills_path.rglob("*.yaml"))
        log.info(f"Indexando {len(yaml_files)} skills encontradas", path=str(self.skills_path))

        indexed = 0
        errors = 0
        for yaml_file in yaml_files:
            if "example" in yaml_file.name:
                continue  # pula exemplos
            try:
                await self.embed_file(yaml_file)
                indexed += 1
            except Exception as e:
                log.error("Falha ao indexar skill", file=str(yaml_file), error=str(e))
                errors += 1

        log.info("Indexação concluída", indexed=indexed, errors=errors)
        return {"indexed": indexed, "errors": errors}

    async def embed_file(self, yaml_path: Path) -> str:
        """Indexa um arquivo YAML de skill. Retorna o skill_id."""
        raw = yaml_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        return await self.embed_dict(data, yaml_content=raw)

    async def embed_dict(self, data: dict, yaml_content: str = "") -> str:
        """Indexa um skill a partir de um dicionário."""
        meta = data.get("metadata", data)  # suporta com ou sem wrapper metadata

        name        = meta.get("name", "")
        description = meta.get("description", "")
        category    = meta.get("category", "general")
        tags        = meta.get("tags", [])
        forged_by   = meta.get("forged_by", "manual")

        if not name:
            raise ValueError("Skill sem nome — campo 'name' obrigatório")

        if not yaml_content:
            yaml_content = yaml.dump(data, allow_unicode=True)

        # Upsert no PostgreSQL
        skill_id = await self._upsert_postgres(
            name=name,
            description=description,
            yaml_content=yaml_content,
            category=category,
            tags=tags,
            forged_by=forged_by,
        )

        # Upsert no ChromaDB
        await chroma_memory.upsert_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            yaml_content=yaml_content,
            category=category,
            tags=tags,
        )

        log.info("Skill indexada", name=name, category=category, skill_id=skill_id[:8])
        return skill_id

    async def _upsert_postgres(
        self,
        name: str,
        description: str,
        yaml_content: str,
        category: str,
        tags: list[str],
        forged_by: str,
    ) -> str:
        """Upsert no PostgreSQL. Retorna skill_id."""
        from sqlalchemy import select

        async with get_db_session() as db:
            result = await db.execute(select(Skill).where(Skill.name == name))
            existing = result.scalar_one_or_none()

            if existing:
                existing.description = description
                existing.yaml_content = yaml_content
                existing.category = category
                existing.tags = tags
                return str(existing.id)

            skill = Skill(
                id=uuid.uuid4(),
                name=name,
                description=description,
                yaml_content=yaml_content,
                category=category,
                tags=tags,
                forged_by=forged_by,
            )
            db.add(skill)
            await db.flush()
            return str(skill.id)

    async def forge_from_session(
        self,
        session_id: str,
        name: str,
        description: str,
        category: str,
        steps: list[dict],
        tags: list[str] | None = None,
        locks: list[str] | None = None,
    ) -> str:
        """
        Forja uma nova skill a partir de uma sessão de sucesso.
        Chamado pelo Skill Trainer ao final do ciclo de aprendizado.
        """
        skill_data = {
            "metadata": {
                "name": name,
                "description": description,
                "category": category,
                "tags": tags or [],
                "forged_by": "engenheiro_kothar",
            },
            "blueprint": {"steps": steps},
            "locks": locks or [],
        }

        import yaml as _yaml
        yaml_content = _yaml.dump(skill_data, allow_unicode=True, default_flow_style=False)

        # Salva arquivo YAML para auditoria Git
        safe_name = name.replace(" ", "_").replace("/", "_").lower()[:60]
        skill_file = self.skills_path / category / f"{safe_name}.yaml"
        skill_file.parent.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(yaml_content, encoding="utf-8")

        skill_id = await self.embed_dict(skill_data, yaml_content=yaml_content)
        log.info("Skill forjada a partir de sessão", name=name, skill_id=skill_id[:8], session_id=session_id[:8])
        return skill_id


# Singleton
skill_embedder = SkillEmbedder()
