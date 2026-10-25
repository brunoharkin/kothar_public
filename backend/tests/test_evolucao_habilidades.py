"""Seleção contextual, orçamento, catálogo versionado e recibos baseados em artefatos reais."""

import hashlib
import json
from pathlib import Path

import pytest

from backend.servicos.evolucao.avaliacoes import Artifact, ExecutionResult, ToolTrace
from backend.servicos.evolucao.habilidades import SkillCatalog, SkillError


def create_skill(root, name, description="corrigir erro teste", body="Valide o resultado."):
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {description}\nversion: 1.0\n---\n{body}\n")


@pytest.fixture
def catalog(tmp_path):
    root = tmp_path / "skills"
    create_skill(root, "debug")
    create_skill(root, "marketing", "escrever marketing campanhas", "Pesquise o público.")
    return SkillCatalog(root)


def test_contextual_selection_is_deterministic_and_within_budget(catalog):
    selection = catalog.select("corrigir erro do teste", "kothar", budget_tokens=100)
    again = catalog.select("corrigir erro do teste", "kothar", budget_tokens=100)
    assert [item.name for item in selection.selected] == ["debug"]
    assert selection.estimated_tokens <= selection.budget_tokens
    assert selection.catalog_version == again.catalog_version
    assert selection.selected[0].version == "1.0"
    assert len(selection.selected[0].sha256) == 64
    assert selection.selected[0].instructions.endswith("Valide o resultado.\n")


def test_partial_word_in_compound_skill_name_is_not_an_explicit_request(catalog):
    create_skill(catalog.root, "validacao-projeto", "verificar qualidade entrega", "Valide o projeto.")
    assert not catalog.select("Quero salvar uma decisão do projeto", "kothar").selected
    assert [skill.name for skill in catalog.select("Execute validacao projeto", "kothar").selected] == ["validacao-projeto"]


def test_mandatory_skills_are_budgeted_before_high_score_optional_matches(catalog, tmp_path):
    create_skill(catalog.root, "marketing", "escrever marketing campanhas", "x" * 150)
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schema_version": 1, "rules": [
        {"keywords": ["execute"], "skills": ["debug"], "required": True},
        *[{"keywords": ["execute"], "skills": ["marketing"], "required": False} for _ in range(20)],
    ]}))
    result = SkillCatalog(catalog.root, routing).select("execute", "kothar", budget_tokens=100)
    assert [skill.name for skill in result.selected] == ["debug"]
    assert result.omitted == ("marketing",)


def test_catalog_accepts_yaml_quoted_names(catalog):
    path = catalog.root / "debug/SKILL.md"
    path.write_text(path.read_text().replace("name: debug", 'name: "debug"'))
    assert catalog.select("corrigir erro teste", "kothar").selected[0].name == "debug"


def test_explicit_skill_is_required_and_never_silently_dropped(catalog):
    create_skill(catalog.root, "large", body="x" * 1000)
    with pytest.raises(SkillError, match="obrigatórias excedem"):
        catalog.select("tarefa", "kothar", requested=("large",), budget_tokens=100)
    with pytest.raises(SkillError, match="não existe"):
        catalog.select("tarefa", "kothar", requested=("absent",))


def test_routing_matches_full_words_and_accents(catalog, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schema_version": 1, "rules": [
        {"keywords": ["correção"], "skills": ["debug"], "required": True},
    ]}))
    configured = SkillCatalog(catalog.root, routing)
    assert configured.select("correcao", "kothar").selected[0].name == "debug"
    assert not configured.select("autocorrecao", "kothar").selected


@pytest.mark.parametrize(("context", "surface"), [
    ("login", "authentication"), ("logout", "authentication"),
    ("autenticacao", "authentication"), ("autenticação", "authentication"),
    ("sessao", "authentication"), ("credenciais", "authentication"),
    ("entrada de usuário", "user_input_api"), ("endpoint", "user_input_api"),
    ("persistência", "persistence"), ("banco de dados", "persistence"),
    ("api externa", "external_api"), ("logs", "logging_tracing"),
    ("whatsapp", "whatsapp_agent"), ("implantação", "deployment"),
])
def test_canonical_routing_requires_policy_skills_in_portuguese(context, surface):
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "configuracao/kothar-security-policy.json").read_text())
    catalog = SkillCatalog(root / ".agents/skills", root / "configuracao/kothar-skill-routing.json")
    selected = catalog.select(context, "kothar", budget_tokens=32000)
    assert set(policy["surfaces"][surface]) <= {skill.name for skill in selected.selected}
    if context == "whatsapp":
        assert "engenharia-de-ia-producao" in {skill.name for skill in selected.selected}


def test_security_routing_does_not_activate_for_unrelated_simple_output():
    root = Path(__file__).resolve().parents[2]
    catalog = SkillCatalog(root / ".agents/skills", root / "configuracao/kothar-skill-routing.json")
    assert not catalog.select("Responda somente o número resultante de 2 + 2", "kothar").selected
    with pytest.raises(SkillError, match="obrigatórias excedem"):
        catalog.select("login", "kothar", budget_tokens=100)


def test_security_policy_and_routing_drift_fail_closed(catalog, tmp_path):
    root = Path(__file__).resolve().parents[2]
    policy = (root / "configuracao/kothar-security-policy.json").read_bytes()
    routing = json.loads((root / "configuracao/kothar-skill-routing.json").read_text())
    target = tmp_path / "kothar-skill-routing.json"
    policy_target = target.with_name("kothar-security-policy.json")
    policy_target.write_bytes(policy)
    configured = SkillCatalog(catalog.root, target)
    for mutation in ("missing_gate", "not_required", "missing_surface", "missing_all_surfaces"):
        data = json.loads(json.dumps(routing))
        if mutation == "missing_gate":
            data["rules"][1]["skills"].remove("gate-producao")
        elif mutation == "not_required":
            data["rules"][1]["required"] = False
        elif mutation == "missing_surface":
            data["rules"].pop(1)
        else:
            data["rules"] = [rule for rule in data["rules"] if "security_surface" not in rule]
        target.write_text(json.dumps(data))
        with pytest.raises(SkillError, match="Roteamento"):
            configured._routing()
    target.write_text(json.dumps(routing))
    assert configured._routing()[0] == routing
    policy_target.write_bytes(policy + b" ")
    with pytest.raises(SkillError, match="Roteamento"):
        configured._routing()


def test_missing_required_routed_skill_fails(catalog, tmp_path):
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schema_version": 1, "rules": [
        {"keywords": ["execute"], "skills": ["missing"], "required": True},
    ]}))
    with pytest.raises(SkillError, match="indisponível"):
        SkillCatalog(catalog.root, routing).select("execute", "kothar")


def test_metadata_and_audit_do_not_change_skills(catalog):
    create_skill(catalog.root, "duplicate", body="Valide o resultado.")
    before = {path: path.read_bytes() for path in catalog.root.glob("*/SKILL.md")}
    metadata = catalog.list_metadata()
    assert all("instructions" not in item for item in metadata)
    report = catalog.audit()
    assert report["skill_count"] == 3
    assert ("debug", "duplicate") in report["duplicate_bodies"]
    assert report["automatic_changes"] is False
    assert before == {path: path.read_bytes() for path in before}


def execution_for(artifact, *, kind="local_workflow", tools=True):
    return ExecutionResult(execution_id="execution-1", response="teste concluído", executor_kind=kind,
                           artifacts=(artifact,), tools=(ToolTrace(id="test-1", name="pytest", status="completed"),) if tools else ())


def test_receipt_links_selected_version_real_trace_and_evidence(catalog, tmp_path):
    selection = catalog.select("corrigir erro teste", "kothar")
    raw = b'{"passed": 1}'
    (tmp_path / "result.json").write_bytes(raw)
    artifact = Artifact(path="result.json", sha256=hashlib.sha256(raw).hexdigest())
    receipt = catalog.receipt(selection, "debug", (artifact,), artifact_root=tmp_path, execution=execution_for(artifact))
    assert receipt.status == "evidence_recorded"
    assert receipt.execution_id == "execution-1" and receipt.trace_ids == ("test-1",)
    assert receipt.skill_sha256 == selection.selected[0].sha256
    assert "approved" not in receipt.model_dump_json()


def test_receipt_rejects_changed_skill_missing_trace_double_and_tampering(catalog, tmp_path):
    selection = catalog.select("corrigir erro teste", "kothar")
    raw = b'{"passed": 1}'
    (tmp_path / "result.json").write_bytes(raw)
    artifact = Artifact(path="result.json", sha256=hashlib.sha256(raw).hexdigest())
    for execution in (execution_for(artifact, kind="test_double"), execution_for(artifact, tools=False)):
        with pytest.raises(SkillError):
            catalog.receipt(selection, "debug", (artifact,), artifact_root=tmp_path, execution=execution)
    (tmp_path / "result.json").write_bytes(b"changed")
    with pytest.raises(SkillError):
        catalog.receipt(selection, "debug", (artifact,), artifact_root=tmp_path, execution=execution_for(artifact))
    (catalog.root / "debug/SKILL.md").write_text((catalog.root / "debug/SKILL.md").read_text() + "Mudança\n")
    with pytest.raises(SkillError, match="mudou"):
        catalog.receipt(selection, "debug", (artifact,), artifact_root=tmp_path, execution=execution_for(artifact))


def test_receipt_rejects_evidence_not_declared_by_execution(catalog, tmp_path):
    selection = catalog.select("corrigir erro teste", "kothar")
    artifact = Artifact(path="result.json", sha256=hashlib.sha256(b"{}").hexdigest())
    other = Artifact(path="other.json", sha256=artifact.sha256)
    with pytest.raises(SkillError, match="vinculados"):
        catalog.receipt(selection, "debug", (artifact,), artifact_root=tmp_path, execution=execution_for(other))


def test_skill_symlink_and_invalid_routing_fail_closed(catalog, tmp_path):
    target = catalog.root / "debug/SKILL.md"
    (catalog.root / "debug" / "copy").write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(catalog.root / "debug/copy")
    with pytest.raises(SkillError):
        catalog.list_metadata()
    routing = tmp_path / "invalid.json"
    routing.write_text('{"schema_version":1,"rules":[{"required":true}]}')
    create_skill(catalog.root, "debug")  # symlink aponta para fixture local, ainda deve reprovar antes de uso.
    with pytest.raises(SkillError):
        SkillCatalog(catalog.root, routing)._routing()
