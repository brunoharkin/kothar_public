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
