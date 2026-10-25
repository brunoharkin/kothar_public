import importlib.util
import json
from pathlib import Path


MODULE = Path(__file__).parents[2] / "scripts" / "kothar-agent-security-audit.py"
SPEC = importlib.util.spec_from_file_location("kothar_agent_security_audit", MODULE)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def test_blocks_literal_secret(tmp_path):
    (tmp_path / ".github" / "agents").mkdir(parents=True)
    (tmp_path / ".github" / "agents" / "bad.agent.md").write_text(
        "api_" + 'key = "not-a-real-secret-value"\n', encoding="utf-8"
    )
    report = AUDIT.audit(tmp_path)
    assert report["counts"]["BLOCK"] == 1


def test_reviews_external_mcp_without_network(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text(
        json.dumps({"servers": {"remote": {"type": "http", "url": "https://example.test/mcp"}}}),
        encoding="utf-8",
    )
    report = AUDIT.audit(tmp_path)
    assert report["counts"]["BLOCK"] == 0
    assert report["counts"]["REVIEW"] == 1


def test_clean_surface_has_no_findings(tmp_path):
    (tmp_path / ".agents" / "skills" / "safe").mkdir(parents=True)
    (tmp_path / ".agents" / "skills" / "safe" / "SKILL.md").write_text(
        "---\nname: safe\n---\nUse somente leitura.\n", encoding="utf-8"
    )
    report = AUDIT.audit(tmp_path)
    assert report["findings"] == []
