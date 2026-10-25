"""
=============================================================
 KOTHAR v4.0 — Configurações Centralizadas
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Todas as configurações do sistema lidas do ambiente.
 Nunca hardcode valores sensíveis — use .env
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centrais do Engenheiro Kothar.
    Lidas automaticamente do .env via pydantic-settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Identidade ----
    kothar_version: str = "4.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # ---- API ----
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_secret_key: str = ""

    # ---- PostgreSQL ----
    postgres_host: str = "kothar_postgres"
    postgres_port: int = 5432
    postgres_user: str = "kothar"
    postgres_password: str = ""
    postgres_db: str = "kothar_trace"

    @property
    def postgres_dsn(self) -> str:
        password = self.require_secret("POSTGRES_PASSWORD", self.postgres_password)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgres_dsn_sync(self) -> str:
        password = self.require_secret("POSTGRES_PASSWORD", self.postgres_password)
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ---- Redis ----
    redis_host: str = "kothar_redis"
    redis_port: int = 6379
    redis_password: str = ""
    session_ttl_seconds: int = 86400

    @property
    def redis_url(self) -> str:
        password = self.require_secret("REDIS_PASSWORD", self.redis_password)
        return f"redis://:{password}@{self.redis_host}:{self.redis_port}/0"

    # ---- Neo4j ----
    neo4j_uri: str = "bolt://kothar_neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # ---- ChromaDB ----
    chroma_host: str = "kothar_chromadb"
    chroma_port: int = 8000
    chroma_token: str = ""

    @property
    def chroma_url(self) -> str:
        return f"http://{self.chroma_host}:{self.chroma_port}"

    # ---- LLM Keys ----
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # ---- Vault (Cofre Obsidian) ----
    vault_path: Path = Path("/home/bruno-harkin/Cofre")

    @property
    def vault_sessions_path(self) -> Path:
        sessions = self.vault_path / "evolucao do agente kothar 1.0" / "sessoes"
        sessions.mkdir(parents=True, exist_ok=True)
        return sessions

    @property
    def skills_path(self) -> Path:
        configured = os.getenv("KOTHAR_SKILLS_PATH")
        skills = Path(configured).expanduser() if configured else Path(__file__).resolve().parents[2] / ".agents" / "skills"
        return skills

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    def require_secret(self, name: str, value: str) -> str:
        """Impede iniciar integrações autenticadas com segredo previsível ou vazio."""
        if not value:
            raise RuntimeError(
                f"Configuração obrigatória ausente: {name}. "
                "Defina a variável correspondente no ambiente."
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna instância singleton das configurações.
    Cached para evitar releitura do .env a cada chamada.
    """
    return Settings()


# Exporta instância padrão
settings = get_settings()
