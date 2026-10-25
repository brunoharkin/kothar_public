from pathlib import Path

import pytest

from backend.core.memory import ConversationMemory
from backend.core.project_mode import is_indexable_path

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("session_id", ["../../escape", "a/b", "", "x" * 101])
def test_conversation_memory_rejects_path_traversal(session_id):
    with pytest.raises(ValueError):
        ConversationMemory(session_id)


def test_project_index_rejects_sensitive_files():
    assert not is_indexable_path(ROOT / ".env")
    assert not is_indexable_path(Path("/etc/passwd"))


def test_frontend_does_not_render_model_html_directly():
    source = (ROOT / "frontend/src/paginas/ollama/ollama.page.tsx").read_text()
    assert "dangerouslySetInnerHTML" not in source
    assert "marked.parse" not in source
