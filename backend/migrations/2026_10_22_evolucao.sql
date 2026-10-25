-- Aplicação explícita pelo operador; nenhuma migração automática no startup.
BEGIN;
CREATE TABLE IF NOT EXISTS evolution_records (
    owner VARCHAR(128) NOT NULL,
    project VARCHAR(128) NOT NULL,
    kind VARCHAR(32) NOT NULL CHECK (kind IN ('fact','task','budget','reservation','action','feedback','prospect','profile','feedback_proposal','evaluation','selection','skill_receipt','business','rate_limit')),
    item_id VARCHAR(100) NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
    updated_at BIGINT NOT NULL,
    PRIMARY KEY (owner, project, kind, item_id),
    CHECK (octet_length(payload::text) <= 262144)
);
CREATE INDEX IF NOT EXISTS evolution_scope_recent ON evolution_records(owner, project, kind, updated_at DESC);
REVOKE ALL ON evolution_records FROM PUBLIC;
COMMIT;
