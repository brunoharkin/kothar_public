#!/usr/bin/env python3
"""
=============================================================
 KOTHAR v4.0 — Setup Inicial (Migrations + Indexação)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Roda na primeira inicialização para:
 1. Criar tabelas no PostgreSQL
 2. Criar coleções no ChromaDB
 3. Criar constraints no Neo4j
 4. Indexar todas as skills YAML existentes
 5. Verificar saúde de todos os serviços

 Uso: python3 ~/kothar/scripts/setup.py
=============================================================
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from backend.core.config import settings
from backend.core.database import close_databases, get_chroma_client, get_neo4j_driver, get_pg_engine, get_redis, init_databases
from backend.core.logger import get_logger, setup_logging
from backend.core.database import Base

setup_logging()
log = get_logger("scripts.setup")


async def create_postgres_tables():
    """Cria todas as tabelas SQLAlchemy."""
    log.info("Criando tabelas PostgreSQL...")
    engine = get_pg_engine()
    # Importa todos os modelos para registrar no metadata
    from backend.trace import models  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("✅ Tabelas criadas")


async def setup_chromadb():
    """Cria coleções ChromaDB."""
    log.info("Configurando ChromaDB...")
    client = await get_chroma_client()
    collections = ["kothar_skills", "kothar_locks", "kothar_context"]
    for name in collections:
        await client.get_or_create_collection(name=name)
        log.info(f"  Coleção: {name}")
    log.info("✅ ChromaDB configurado")


async def setup_neo4j():
    """Aplica constraints do Neo4j."""
    log.info("Configurando Neo4j...")
    constraints_file = ROOT / "infra" / "neo4j" / "constraints.cypher"
    if not constraints_file.exists():
        log.warn("Arquivo de constraints não encontrado", path=str(constraints_file))
        return

    cypher = constraints_file.read_text()
    driver = get_neo4j_driver()
    # Executa cada statement separadamente
    statements = [s.strip() for s in cypher.split(";") if s.strip() and not s.strip().startswith("//")]
    async with driver.session() as session:
        for stmt in statements:
            try:
                await session.run(stmt)
            except Exception as e:
                log.warn("Constraint ignorada (pode já existir)", stmt=stmt[:60], error=str(e)[:100])
    log.info("✅ Neo4j configurado")


async def index_existing_skills():
    """Indexa skills YAML existentes no ChromaDB."""
    log.info("Indexando skills existentes...")
    from backend.memory.semantic.skill_embedder import skill_embedder
    result = await skill_embedder.embed_all()
    log.info("✅ Skills indexadas", indexed=result["indexed"], errors=result["errors"])


async def health_check():
    """Verifica saúde de todos os serviços."""
    log.info("Verificando saúde dos serviços...")
    services = {}

    # PostgreSQL
    try:
        from sqlalchemy import text
        engine = get_pg_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        services["postgres"] = "✅ OK"
    except Exception as e:
        services["postgres"] = f"❌ {e}"

    # Redis
    try:
        r = await get_redis()
        await r.ping()
        services["redis"] = "✅ OK"
    except Exception as e:
        services["redis"] = f"❌ {e}"

    # Neo4j
    try:
        driver = get_neo4j_driver()
        async with driver.session() as s:
            await s.run("RETURN 1")
        services["neo4j"] = "✅ OK"
    except Exception as e:
        services["neo4j"] = f"❌ {e}"

    # ChromaDB
    try:
        client = await get_chroma_client()
        await client.heartbeat()
        services["chromadb"] = "✅ OK"
    except Exception as e:
        services["chromadb"] = f"❌ {e}"

    print("\n" + "="*50)
    print("  KOTHAR v4.0 — Health Check")
    print("="*50)
    for svc, status in services.items():
        print(f"  {svc:12} {status}")
    print("="*50 + "\n")

    return all("✅" in s for s in services.values())


async def main():
    print("\n🎵 KOTHAR v4.0 — Setup Inicial\n")

    try:
        await init_databases()
        await create_postgres_tables()
        await setup_chromadb()
        await setup_neo4j()
        await index_existing_skills()
        all_healthy = await health_check()

        if all_healthy:
            print("✅ Setup concluído! Kothar está pronto.\n")
            print("   kothar start   → inicia a stack Docker")
            print("   bash ~/kothar/hooks/install_hooks.sh → instala hooks CLI\n")
        else:
            print("⚠️  Setup concluído com avisos. Verifique os serviços acima.\n")
            sys.exit(1)
    finally:
        await close_databases()


if __name__ == "__main__":
    asyncio.run(main())
