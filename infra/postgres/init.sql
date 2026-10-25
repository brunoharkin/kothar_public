-- =============================================================
--  KOTHAR v4.0 — Schema Inicial PostgreSQL
--  Engenheiro Kothar | Ugarit Digital
-- =============================================================
--  Data Lake de Traces, Sessões, Skills e Travamentos.
-- =============================================================

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- busca textual eficiente

-- =============================================================
-- SESSÕES — Registro de cada sessão de trabalho
-- =============================================================
CREATE TABLE IF NOT EXISTS sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    agent_name      VARCHAR(100) NOT NULL,           -- ex: "maestro", "engineer"
    llm_model       VARCHAR(100),                    -- ex: "claude-3-5-sonnet"
    task_summary    TEXT,
    status          VARCHAR(50) DEFAULT 'active',    -- active | completed | failed
    tokens_input    INTEGER DEFAULT 0,
    tokens_output   INTEGER DEFAULT 0,
    total_cost_usd  NUMERIC(10, 6) DEFAULT 0,
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_name);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at DESC);

-- =============================================================
-- TRACES — Registro granular de cada ação do agente
-- =============================================================
CREATE TABLE IF NOT EXISTS traces (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    sequence        INTEGER NOT NULL,                -- ordem dentro da sessão
    event_type      VARCHAR(100) NOT NULL,           -- tool_call | llm_response | error | decision
    agent_name      VARCHAR(100) NOT NULL,
    content         TEXT,
    tool_name       VARCHAR(200),                    -- nome da ferramenta usada
    tool_input      JSONB,
    tool_output     JSONB,
    duration_ms     INTEGER,
    tokens_used     INTEGER DEFAULT 0,
    is_error        BOOLEAN DEFAULT FALSE,
    error_message   TEXT,
    metadata        JSONB DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_type ON traces(event_type);
CREATE INDEX IF NOT EXISTS idx_traces_error ON traces(is_error) WHERE is_error = TRUE;
CREATE INDEX IF NOT EXISTS idx_traces_created ON traces(created_at DESC);

-- =============================================================
-- SKILLS — Registro das skills cristalizadas pelo Maestro
-- =============================================================
CREATE TABLE IF NOT EXISTS skills (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL UNIQUE,
    description     TEXT,
    yaml_content    TEXT NOT NULL,                   -- conteúdo YAML da skill
    chroma_doc_id   VARCHAR(200),                    -- ID no ChromaDB
    category        VARCHAR(100),                    -- ex: "frontend", "devops"
    tags            TEXT[] DEFAULT '{}',
    usage_count     INTEGER DEFAULT 0,
    success_rate    NUMERIC(5, 2) DEFAULT 100.0,
    forged_by       VARCHAR(100),                    -- agente que criou
    source_session  UUID REFERENCES sessions(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
CREATE INDEX IF NOT EXISTS idx_skills_tags ON skills USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_skills_name_trgm ON skills USING GIN(name gin_trgm_ops);

-- =============================================================
-- LOCKS (TRAVAS) — Erros que o Trace Analyser cristalizou
-- =============================================================
CREATE TABLE IF NOT EXISTS locks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern         VARCHAR(500) NOT NULL,           -- padrão de erro detectado
    description     TEXT NOT NULL,                   -- o que NÃO fazer
    alternative     TEXT,                            -- o que fazer em vez disso
    chroma_doc_id   VARCHAR(200),                    -- embedding no ChromaDB
    trigger_count   INTEGER DEFAULT 1,               -- quantas vezes disparou
    category        VARCHAR(100),
    source_session  UUID REFERENCES sessions(id),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locks_active ON locks(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_locks_pattern_trgm ON locks USING GIN(pattern gin_trgm_ops);

-- =============================================================
-- BLUEPRINTS — Planos de tarefas gerenciados pelo Redis/Maestro
-- =============================================================
CREATE TABLE IF NOT EXISTS blueprints (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID REFERENCES sessions(id),
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    steps           JSONB NOT NULL DEFAULT '[]'::jsonb,  -- lista de passos
    status          VARCHAR(50) DEFAULT 'pending',   -- pending | active | done | failed
    assigned_agent  VARCHAR(100),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_blueprints_session ON blueprints(session_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_status ON blueprints(status);

-- Estado durável das ferramentas do frontend; nunca usar Web Storage como autoridade.
CREATE TABLE IF NOT EXISTS workspace_state (
    owner VARCHAR(128) NOT NULL,
    kind VARCHAR(32) NOT NULL CHECK (kind IN ('prompt_variant', 'ab_test', 'marked_error')),
    item_id VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (owner, kind, item_id),
    CHECK (octet_length(payload::text) <= 262144)
);

REVOKE ALL ON workspace_state FROM PUBLIC;

-- =============================================================
-- FUNÇÃO: atualiza updated_at automaticamente
-- =============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_skills_updated_at
    BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
