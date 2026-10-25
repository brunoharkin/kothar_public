"""
=============================================================
 KOTHAR v4.0 — Migration: Add FlowExecution Table
 Executar: python -m backend.migrations.add_flow_execution
=============================================================
"""

import asyncio
from sqlalchemy import text

from backend.core.database import get_pg_engine
from backend.core.logger import get_logger

log = get_logger("migrations.add_flow_execution")


MIGRATION_SQL = """
-- Cria tabela flow_executions se não existir
CREATE TABLE IF NOT EXISTS flow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'running',
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    failed_steps INTEGER DEFAULT 0,
    skipped_steps INTEGER DEFAULT 0,
    total_duration_ms INTEGER DEFAULT 0,
    checkpoint_recovered BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Cria índice para consultas por sessão
CREATE INDEX IF NOT EXISTS idx_flow_executions_session ON flow_executions(session_id);

-- Cria índice para consultas por status
CREATE INDEX IF NOT EXISTS idx_flow_executions_status ON flow_executions(status);
"""


async def run_migration():
    """Executa a migração."""
    engine = get_pg_engine()

    log.info("Iniciando migração: add_flow_execution")

    async with engine.begin() as conn:
        try:
            await conn.execute(text(MIGRATION_SQL))
            log.info("✅ Tabela flow_executions criada com sucesso")
        except Exception as e:
            log.error(f"❌ Erro na migração: {e}")
            raise

    await engine.dispose()
    log.info("Migração concluída")


if __name__ == "__main__":
    asyncio.run(run_migration())
