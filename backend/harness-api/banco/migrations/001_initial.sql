-- ============================================
-- Kothar Trace Backend — Migration 001
-- Schema consolidado PostgreSQL
-- ============================================

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    name TEXT,
    agent TEXT,
    sub_agent TEXT DEFAULT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'active',
    agent_name TEXT,
    llm_model TEXT,
    task_summary TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent);
CREATE INDEX IF NOT EXISTS idx_sessions_sub_agent ON sessions(sub_agent);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tool TEXT,
    input TEXT,
    output TEXT,
    reasoning TEXT,
    duration INTEGER,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    context_tokens INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    sequence INTEGER,
    event_type TEXT,
    agent_name TEXT,
    content TEXT,
    tool_name TEXT,
    tool_input JSONB,
    tool_output JSONB,
    duration_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,
    is_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_traces_session ON traces(session_id);
CREATE INDEX IF NOT EXISTS idx_traces_timestamp ON traces(timestamp);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_has_reasoning ON traces(session_id) WHERE reasoning IS NOT NULL;
