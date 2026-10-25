"""Exercise real isolated Git indexes, without committing or touching user staging."""
import importlib.util
import subprocess
from pathlib import Path

MODULE = Path(__file__).resolve().parents[2] / 'scripts/kothar_security_audit.py'
spec = importlib.util.spec_from_file_location('index_audit', MODULE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def repository(tmp_path, monkeypatch):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def stage(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    subprocess.run(['git', 'add', '--', name], cwd=root, check=True)
    return path


def secret():
    return 'sk-' + 'Q' * 40


def test_index_secret_cannot_hide_behind_clean_worktree(tmp_path, monkeypatch, capsys):
    root = repository(tmp_path, monkeypatch)
    path = stage(root, 'sample name.py', 'value = "' + secret() + '"')
    path.write_text('value = None')
    assert audit.run_pre_commit_hook() == 1
    assert secret() not in capsys.readouterr().out


def test_unstaged_secret_does_not_change_scanned_artifact(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    path = stage(root, 'safe.py', 'value = None')
    path.write_text('value = "' + secret() + '"')
    assert audit.run_pre_commit_hook() == 0


def test_non_repository_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert audit.run_pre_commit_hook() == 2


def test_environment_file_blocks(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    stage(root, '.env.production', 'EXAMPLE=synthetic')
    assert audit.run_pre_commit_hook() == 1


def test_migration_and_example_names_do_not_exempt_secrets(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    stage(root, 'migrations/sample.py', 'value = "' + secret() + '"')
    assert audit.run_pre_commit_hook() == 1


def test_invalid_encoding_blocks(tmp_path, monkeypatch):
    root = repository(tmp_path, monkeypatch)
    path = stage(root, 'bad.py', 'valid')
    path.write_bytes(b'\xff')
    subprocess.run(['git', 'add', '--', 'bad.py'], check=True)
    assert audit.run_pre_commit_hook() == 2


def test_read_failure_never_counts_as_clean(tmp_path):
    scanner = audit.SecurityAuditor(str(tmp_path))
    import pytest
    with pytest.raises(OSError):
        scanner.audit_file(tmp_path / 'absent.py')
    assert scanner.files_audited == 0
