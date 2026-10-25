"""O contrato de entrega é propagado sem apagar campos nativos ou aceitar drift."""
import importlib.util
import json
import tomllib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "scripts/sincronizar-relatorio-entrega.py"
SPEC = importlib.util.spec_from_file_location("relatorio_sync", SCRIPT)
SYNC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SYNC)


@pytest.fixture
def workspace(tmp_path):
    contract = SYNC.START + "\nContrato de fixture.\n" + SYNC.END
    sources = {
        SYNC.SOURCE: contract,
        SYNC.CODEX: 'name = "fixture"\ndeveloper_instructions = """Preservar instrução original."""\n',
        SYNC.MANIFEST: json.dumps({"systemPrompt": "Preservar prompt.", "tools": ["read"]}),
        ".github/agents/fixture.agent.md": "---\nname: fixture\n---\nInstrução do papel.\n",
    }
    for target in SYNC.MARKDOWN_TARGETS:
        sources[target] = "Preservar instruções originais.\n"
    for target, content in sources.items():
        path = tmp_path / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return tmp_path


def test_sync_is_idempotent_and_preserves_native_fields(workspace):
    assert SYNC.synchronize(workspace)
    SYNC.synchronize(workspace, apply=True)
    assert SYNC.synchronize(workspace) == []
    toml = tomllib.loads((workspace / SYNC.CODEX).read_text())
    assert toml["name"] == "fixture"
    assert "Preservar instrução original." in toml["developer_instructions"]
    manifest = json.loads((workspace / SYNC.MANIFEST).read_text())
    assert manifest["tools"] == ["read"]
    assert "Preservar prompt." in manifest["systemPrompt"]
    SYNC.synchronize(workspace, apply=True)
    assert SYNC.synchronize(workspace) == []


def test_new_agent_is_detected_and_receives_current_contract(workspace):
    SYNC.synchronize(workspace, apply=True)
    extra = workspace / ".github/agents/new.agent.md"
    extra.write_text("---\nname: novo\n---\n", encoding="utf-8")
    assert SYNC.synchronize(workspace) == [".github/agents/new.agent.md"]
    SYNC.synchronize(workspace, apply=True)
    assert SYNC.contract_from(workspace) in extra.read_text()


def test_broken_marker_fails_before_updating_other_files(workspace):
    target = workspace / SYNC.MANIFEST
    data = json.loads(target.read_text())
    data["systemPrompt"] += SYNC.START
    target.write_text(json.dumps(data))
    before = (workspace / "AGENTS.md").read_text()
    with pytest.raises(ValueError):
        SYNC.synchronize(workspace, apply=True)
    assert (workspace / "AGENTS.md").read_text() == before


def test_actual_repository_contract_has_no_drift():
    assert SYNC.synchronize(SCRIPT.parents[1]) == []


def test_installed_profile_keeps_custom_rules_and_does_not_create_absent_files(workspace, tmp_path):
    profile = tmp_path / "profile"
    target = profile / ".codex/AGENTS.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Kothar\nRegra personalizada mantida.\n", encoding="utf-8")
    foreign = profile / ".claude/agents/kothar.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("Outro agente, sem assinatura gerenciada.\n", encoding="utf-8")
    assert SYNC.synchronize_user(workspace, profile) == [".codex/AGENTS.md"]
    SYNC.synchronize_user(workspace, profile, apply=True)
    assert "Regra personalizada mantida." in target.read_text()
    assert SYNC.contract_from(workspace) in target.read_text()
    assert SYNC.START not in foreign.read_text()
    assert not (profile / ".gemini/GEMINI.md").exists()
    assert SYNC.synchronize_user(workspace, profile) == []

