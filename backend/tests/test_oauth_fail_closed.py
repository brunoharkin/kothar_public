from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_legacy_file_oauth_callbacks_are_not_exposed():
    source = (ROOT / 'backend/api/main.py').read_text()
    assert 'autenticacao_google' not in source
    assert 'autenticacao_linkedin' not in source
    assert 'autenticacao_meta' not in source
