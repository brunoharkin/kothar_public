from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.api.routers.workspace_state import StateItem

ROOT = Path(__file__).resolve().parents[2]


def test_state_item_rejects_unsafe_ids_and_oversized_payloads():
    with pytest.raises(ValidationError):
        StateItem(id='../other-tenant', payload={})
    with pytest.raises(ValidationError):
        StateItem(id='valid', payload={'content': 'x' * 256_001})


def test_migration_has_owner_scoped_primary_key_and_size_constraint():
    sql = (ROOT / 'backend/migrations/2026_10_17_workspace_state.sql').read_text()
    assert 'PRIMARY KEY (owner, kind, item_id)' in sql
    assert 'CHECK (octet_length(payload::text) <= 262144)' in sql
    assert 'REVOKE ALL ON workspace_state FROM PUBLIC' in sql


def test_frontend_has_no_web_storage_authority():
    source = '\n'.join(path.read_text(errors='ignore') for path in (ROOT / 'frontend/src').rglob('*')
                       if path.suffix in {'.ts', '.tsx'})
    assert 'localStorage' not in source
    assert 'sessionStorage' not in source
    assert '_ollama_url' not in source
