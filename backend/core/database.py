"""
=============================================================
 KOTHAR v4.0 — Conexões de Banco de Dados
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Gerencia conexões com PostgreSQL, Redis, Neo4j e ChromaDB.
 Padrão: context managers para garantir fechamento correto.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import chromadb
import redis.asyncio as aioredis
from neo4j import AsyncGraphDatabase
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings
from backend.core.logger import get_logger

log = get_logger("core.database")

# =============================================================
# PostgreSQL (SQLAlchemy Async)
# =============================================================

class Base(DeclarativeBase):
    """Base para todos os modelos SQLAlchemy do Kothar."""
    pass


_pg_engine: AsyncEngine | None = None
_pg_session_factory: async_sessionmaker | None = None


def get_pg_engine() -> AsyncEngine:
    global _pg_engine
    if _pg_engine is None:
        _pg_engine = create_async_engine(
            settings.postgres_dsn,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            echo=settings.is_development,
        )
        log.info("PostgreSQL engine criado", dsn_host=settings.postgres_host)
    return _pg_engine


def get_session_factory() -> async_sessionmaker:
    global _pg_session_factory
    if _pg_session_factory is None:
        _pg_session_factory = async_sessionmaker(
            bind=get_pg_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _pg_session_factory


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para sessão do banco.
    Garante commit em sucesso e rollback em erro.

    Uso:
        async with get_db_session() as session:
            await session.execute(...)
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# =============================================================
# Redis (Cache de Curto Prazo)
# =============================================================

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        log.info("Redis conectado", host=settings.redis_host)
    return _redis_client


# =============================================================
# Neo4j (GraphRAG)
# =============================================================

_neo4j_driver = None


def get_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=20,
        )
        log.info("Neo4j driver criado", uri=settings.neo4j_uri)
    return _neo4j_driver


@asynccontextmanager
async def get_neo4j_session():
    """
    Context manager para sessão Neo4j.

    Uso:
        async with get_neo4j_session() as session:
            await session.run("MATCH (n) RETURN n LIMIT 1")
    """
    driver = get_neo4j_driver()
    async with driver.session() as session:
        yield session


# =============================================================
# ChromaDB (Memória Semântica RAG)
# =============================================================

_chroma_client = None


async def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = await chromadb.AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            headers={"Authorization": f"Bearer {settings.chroma_token}"},
        )
        log.info("ChromaDB client criado", host=settings.chroma_host)
    return _chroma_client


# =============================================================
# Lifecycle — Inicialização e Fechamento
# =============================================================

async def init_databases() -> None:
    """Inicializa todas as conexões ao subir a API."""
    log.info("Inicializando conexões de banco de dados...")
    await get_redis()
    get_neo4j_driver()
    await get_chroma_client()
    log.info("✅ Todas as conexões inicializadas")


async def close_databases() -> None:
    """Fecha todas as conexões ao encerrar a API."""
    global _pg_engine, _redis_client, _neo4j_driver

    if _pg_engine:
        await _pg_engine.dispose()
        log.info("PostgreSQL engine fechado")

    if _redis_client:
        await _redis_client.aclose()
        log.info("Redis conexão fechada")

    if _neo4j_driver:
        await _neo4j_driver.close()
        log.info("Neo4j driver fechado")

    log.info("✅ Todas as conexões encerradas")
