"""As operações não ultrapassam o workspace nem substituem arquivos sem revisão."""

import hashlib

import pytest

from backend.core.workspace_files import (
    WorkspaceError,
    create_workspace_file,
    read_workspace_file,
    replace_workspace_text,
)


def test_create_never_overwrites_existing_file(tmp_path):
    target = tmp_path / "source.py"
    target.write_text("VALUE = 1\n")
    with pytest.raises(WorkspaceError):
        create_workspace_file(tmp_path, "source.py", "VALUE = 2\n")
    assert target.read_text() == "VALUE = 1\n"


def test_patch_requires_unique_original_and_preserves_file_on_failure(tmp_path):
    original = "VALUE = 1\nOTHER = 1\n"
    target = tmp_path / "source.py"
    target.write_text(original)
    with pytest.raises(WorkspaceError):
        replace_workspace_text(tmp_path, "source.py", "1", "2", hashlib.sha256(original.encode()).hexdigest())
    assert target.read_text() == original
    assert not list(tmp_path.glob(".kothar-edit-*"))


def test_hard_link_cannot_change_other_file(tmp_path):
    original = "VALUE = 1\n"
    target = tmp_path / "original.py"
    target.write_text(original)
    (tmp_path / "linked.py").hardlink_to(target)
    with pytest.raises(WorkspaceError):
        replace_workspace_text(tmp_path, "linked.py", "1", "2", hashlib.sha256(original.encode()).hexdigest())
    assert target.read_text() == original


def test_symlink_cannot_read_file_outside_workspace(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    (tmp_path / "outside.py").write_text("VALUE = 1\n")
    (root / "linked.py").symlink_to(tmp_path / "outside.py")
    with pytest.raises(WorkspaceError):
        read_workspace_file(root, "linked.py")


def test_large_file_is_not_read(tmp_path):
    (tmp_path / "large.py").write_text(" " * 400_001)
    with pytest.raises(WorkspaceError):
        read_workspace_file(tmp_path, "large.py")
