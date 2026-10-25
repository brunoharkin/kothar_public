from pathlib import Path

from backend.core.tools import _is_path_allowed


def test_tool_access_rejects_secret_files_and_directories(tmp_path: Path):
    assert not _is_path_allowed(str(Path.home() / ".ssh" / "id_rsa"))
    assert not _is_path_allowed(str(Path(__file__).parents[2] / ".env"))
    assert not _is_path_allowed(str(Path(__file__).parents[2] / "private.key"))


def test_tool_access_accepts_regular_project_source():
    path = Path(__file__).parents[1] / "core" / "tools.py"
    assert _is_path_allowed(str(path))
