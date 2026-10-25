"""
=============================================================
 KOTHAR v5.0 — Versionamento de Skills
 Versionamento semântico de skills para controle de mudanças
=============================================================
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import shutil

from backend.core.logger import get_logger

log = get_logger("skills.versioning")

# Diretório de versões
VERSIONS_DIR = Path.home() / ".kothar" / "skill_versions"


class SkillVersion:
    """Representa uma versão de uma skill."""

    def __init__(
        self,
        skill_id: str,
        version: str,
        content_hash: str,
        created_at: datetime,
        created_by: str = "system",
        parent_version: Optional[str] = None,
        changelog: str = "",
    ):
        self.skill_id = skill_id
        self.version = version
        self.content_hash = content_hash
        self.created_at = created_at
        self.created_by = created_by
        self.parent_version = parent_version
        self.changelog = changelog

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_version": self.parent_version,
            "changelog": self.changelog,
        }


class SkillVersioning:
    """
    Gerenciador de versões de skills.
    Usa versionamento semântico: MAJOR.MINOR.PATCH
    - MAJOR: Quebra de compatibilidade
    - MINOR: Nova funcionalidade
    - PATCH: Correções
    """

    def __init__(self, versions_dir: Path = VERSIONS_DIR):
        self.versions_dir = versions_dir
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _get_skill_versions_file(self, skill_id: str) -> Path:
        """Retorna caminho do arquivo de versões de uma skill."""
        safe_id = skill_id.replace("/", "_").replace("\\", "_")
        return self.versions_dir / f"{safe_id}_versions.json"

    def _compute_hash(self, content: str) -> str:
        """Computa hash SHA256 do conteúdo."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _parse_version(self, version: str) -> tuple:
        """Parse versão semântica."""
        parts = version.split(".")
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0,
        )

    def _increment_version(self, version: str, level: str = "patch") -> str:
        """Incrementa versão semântica."""
        major, minor, patch = self._parse_version(version)
        if level == "major":
            return f"{major + 1}.0.0"
        elif level == "minor":
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"

    def get_latest_version(self, skill_id: str) -> Optional[str]:
        """Retorna versão mais recente de uma skill."""
        versions_file = self._get_skill_versions_file(skill_id)
        if not versions_file.exists():
            return None

        with open(versions_file) as f:
            versions = json.load(f)

        if not versions:
            return None

        # Ordena por versão semântica
        sorted_versions = sorted(
            versions, key=lambda v: self._parse_version(v["version"]), reverse=True
        )
        return sorted_versions[0]["version"]

    def get_all_versions(self, skill_id: str) -> list[dict]:
        """Retorna todas as versões de uma skill."""
        versions_file = self._get_skill_versions_file(skill_id)
        if not versions_file.exists():
            return []

        with open(versions_file) as f:
            return json.load(f)

    def save_version(
        self,
        skill_id: str,
        content: str,
        changelog: str = "",
        created_by: str = "system",
        force_version: Optional[str] = None,
    ) -> SkillVersion:
        """
        Salva uma nova versão de skill.
        Detecta automaticamente se houve breaking change.
        """
        content_hash = self._compute_hash(content)
        latest_version = self.get_latest_version(skill_id)

        if latest_version is None:
            # Primeira versão
            new_version = "1.0.0"
            level = "major"
        else:
            # Verifica se conteúdo mudou
            old_versions = self.get_all_versions(skill_id)
            current_hash = old_versions[0]["content_hash"] if old_versions else None

            if content_hash == current_hash:
                log.info(f"Skill {skill_id} sem mudanças, versão não incrementada")
                return SkillVersion(
                    skill_id=skill_id,
                    version=latest_version,
                    content_hash=content_hash,
                    created_at=datetime.now(timezone.utc),
                )

            # Detecta tipo de mudança
            level = self._detect_change_level(content, skill_id)
            new_version = self._increment_version(latest_version, level)

        version = force_version or new_version
        sv = SkillVersion(
            skill_id=skill_id,
            version=version,
            content_hash=content_hash,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            parent_version=latest_version,
            changelog=changelog,
        )

        # Salva versão
        versions_file = self._get_skill_versions_file(skill_id)
        versions = self.get_all_versions(skill_id)
        versions.insert(0, sv.to_dict())

        with open(versions_file, "w") as f:
            json.dump(versions, f, indent=2)

        log.info(
            f"Skill {skill_id} versionada: {version} ({level})",
            skill_id=skill_id,
            version=version,
            level=level,
        )

        return sv

    def _detect_change_level(self, content: str, skill_id: str) -> str:
        """
        Detecta nível de mudança no conteúdo.
        Retorna 'major', 'minor' ou 'patch'.
        """
        # Heurísticas simples:
        # - Mudança de estrutura de campos = major
        # - Adição de novos campos = minor
        # - Correção de texto/bugs = patch

        content_lower = content.lower()

        # Breaking change indicators
        breaking_keywords = [
            "deprecated",
            "removido",
            "removed",
            "breaking",
            "não é mais",
        ]
        if any(kw in content_lower for kw in breaking_keywords):
            return "major"

        # New feature indicators
        feature_keywords = [
            "nova",
            "new",
            "agora suporta",
            "supports",
            "adicionado",
            "added",
        ]
        if any(kw in content_lower for kw in feature_keywords):
            return "minor"

        return "patch"

    def rollback(self, skill_id: str, version: str) -> Optional[str]:
        """
        Faz rollback para uma versão específica.
        Retorna o conteúdo da versão ou None se não existir.
        """
        versions = self.get_all_versions(skill_id)
        for v in versions:
            if v["version"] == version:
                log.info(f"Rollback de {skill_id} para versão {version}")
                return v["content_hash"]
        return None

    def get_version_history(self, skill_id: str, limit: int = 10) -> list[dict]:
        """Retorna histórico de versões."""
        versions = self.get_all_versions(skill_id)
        return versions[:limit]


# Instância global
skill_versioning = SkillVersioning()
