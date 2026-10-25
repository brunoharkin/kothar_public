"""Integração em SQLite isolado: nenhuma chamada externa nem sessão de produção."""

import json
import re
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.servicos.evolucao.avaliacoes import (
    BehaviorVerdict,
    EvalCase,
    ExecutionResult,
    JudgeResult,
    ToolTrace,
)
from backend.servicos.evolucao.feedback import FeedbackSubmission
from backend.servicos.evolucao.habilidades import SkillCatalog
from backend.servicos.evolucao.integracao import EvolutionCoordinator
from backend.servicos.evolucao.modelos import BudgetLimitInput, EvolutionError, TaskInput
from backend.servicos.evolucao.repositorio import metadata
from backend.servicos.prospeccao import DiscoveryRequest, ProspeccaoService
from backend.servicos.prospeccao.transport import FetchResult


class ArithmeticWorkflow:
    """Executa aritmética real e limitada; não simula modelo nem usa eval/shell."""

    def __init__(self):
        self.executions = []

    async def __call__(self, case):
        self.executions.append(case)
        match = re.fullmatch(r"eval (\d{1,4}) \+ (\d{1,4})", case.prompt)
        if match is None:
            raise ValueError("unsupported_local_workflow")
        result = sum(map(int, match.groups()))
        return ExecutionResult(execution_id=uuid4().hex, response=f"resultado: {result}",
                               executor_kind="local_workflow", tokens_input=0, tokens_output=0,
                               tools=(ToolTrace(id=uuid4().hex, name="local_arithmetic", status="completed"),))


class ControlledProspectTransport:
    def __init__(self):
        self.requests = []

    async def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        if url == "https://overpass-api.de/api/interpreter":
            return FetchResult(json.dumps({"elements": [{"type": "node", "id": 123,
                "tags": {"name": "Negócio Sintético", "website": "https://negocio.example/"}}]}), "application/json")
        assert url == "https://negocio.example/"
        return FetchResult("<html><script src='/wp-content/test.js'></script><a href='mailto:contato@negocio.example'>Contato</a></html>", "text/html")


@pytest_asyncio.fixture
async def integration_environment(tmp_path, monkeypatch):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'integration.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, info={"evolution_test_database": True})

    @asynccontextmanager
    async def scope():
        async with factory() as db, db.begin():
            yield db

    skill_root = tmp_path / ".agents" / "skills"
    skill_path = skill_root / "eval-check" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    skill_path.write_text("---\nname: eval-check\ndescription: Avaliação eval de cálculo local.\nversion: 1\n---\nExecute o cálculo e registre evidência.\n", encoding="utf-8")
    routing = tmp_path / "routing.json"
    routing.write_text(json.dumps({"schema_version": 1, "rules": [{"keywords": ["eval"], "skills": ["eval-check"], "required": True}]}), encoding="utf-8")
    catalog = SkillCatalog(skill_root, routing)
    monkeypatch.setattr("backend.servicos.evolucao.integracao.ROOT", tmp_path)
    monkeypatch.setenv("KOTHAR_PROSPECCAO_ENABLED", "1")
    transport = ControlledProspectTransport()
    executor = ArithmeticWorkflow()

    def collector(**kwargs):
        return ProspeccaoService(enabled=True, transport=transport, **kwargs)

    def coordinator(owner="owner-a", project="project-a", **kwargs):
        current = EvolutionCoordinator(owner, project, session_scope=scope,
            executor_factory=kwargs.pop("executor_factory", lambda: executor),
            prospect_factory=collector, **kwargs)
        current.catalog = lambda: catalog
        return current

    try:
        yield {"make": coordinator, "scope": scope, "db": factory, "root": tmp_path,
               "transport": transport, "executor": executor, "catalog": catalog}
    finally:
        await engine.dispose()


def case(**updates):
    return EvalCase.model_validate({"id": "arithmetic", "project_id": "project-a",
        "prompt": "eval 2 + 2", "expected_contains": ["resultado: 4"],
        "required_tools": ["local_arithmetic"], **updates})


async def allow_budget(coordinator, **updates):
    return await coordinator.call("set_budget", "default", BudgetLimitInput(
        tokens=updates.get("tokens", 1000000), calls=updates.get("calls", 100), cost_microunits=0))


async def test_real_local_workflow_records_skill_evidence_and_budget(integration_environment):
    current = integration_environment["make"]()
    await allow_budget(current)
    report = await current.evaluate((case(),))
    assert report["all_passed"] and not report["contains_test_doubles"]
    assert report["results"][0]["executor_kind"] == "local_workflow"
    assert report["budget_accounting"] == "measured_tokens_reserved_calls"
    assert ".agents/skills/eval-check/SKILL.md" in {item["path"] for item in report["results"][0]["artifacts"]}
    assert report["selections"]["arithmetic"]
    assert "response" not in report["executions"][0]
    budget = await current.call("get_budget")
    assert budget["spent"] == {"tokens": 0, "calls": 1, "cost_microunits": 0}
    assert all(value == 0 for value in budget["reserved"].values())


async def test_budget_blocks_execution_and_external_collection_before_work(integration_environment):
    current = integration_environment["make"]()
    with pytest.raises(EvolutionError):
        await current.evaluate((case(),))
    with pytest.raises(EvolutionError):
        await current.discover(DiscoveryRequest(category="Dentista", city="São Paulo", state="SP", latitude=-23.55, longitude=-46.63))
    assert not integration_environment["executor"].executions
    assert not integration_environment["transport"].requests
    await allow_budget(current, tokens=1, calls=0)
    with pytest.raises(EvolutionError):
        await current.evaluate((case(),))
    assert not integration_environment["executor"].executions
    budget = await current.call("get_budget")
    assert not any(budget["spent"].values()) and not any(budget["reserved"].values())


async def test_case_scope_and_duplicate_ids_rejected_before_executor(integration_environment):
    current = integration_environment["make"]()
    await allow_budget(current)
    with pytest.raises(EvolutionError):
        await current.evaluate((case(project_id="other-project"),))
    with pytest.raises(EvolutionError):
        await current.evaluate((case(), case()))
    assert not integration_environment["executor"].executions
    assert not any((await current.call("get_budget"))["reserved"].values())


async def test_judge_usage_is_counted_without_claiming_fixture_is_live(integration_environment):
    class ExplicitTestDouble:
        async def __call__(self, _case):
            return ExecutionResult(execution_id=uuid4().hex, response="resultado: 4", executor_kind="test_double", tokens_input=5, tokens_output=3)

        async def judge(self, selected_case, execution):
            return JudgeResult(evaluator="test_double:semantic", tokens_input=7, tokens_output=11,
                verdicts=tuple(BehaviorVerdict(criterion=criterion, passed=True, response_quote=execution.response) for criterion in selected_case.required_behaviors))

    current = integration_environment["make"](executor_factory=ExplicitTestDouble)
    await allow_budget(current)
    report = await current.evaluate((case(required_tools=[], required_behaviors=["Explicar o resultado"]),))
    assert report["contains_test_doubles"]
    assert report["results"][0]["semantic_evaluator"] == "test_double:semantic"
    assert (await current.call("get_budget"))["spent"]["tokens"] == 26
    assert (await current.call("get_budget"))["spent"]["calls"] == 2


async def test_task_skills_is_durable_and_resumes_completed_checkpoint(integration_environment):
    current = integration_environment["make"]()
    task = await current.call("create_task", TaskInput(title="Selecionar instruções", dedupe_key="skills-run", retry_safe=True,
        payload={"operation": "skills", "context": "eval", "budget_tokens": 1500}))
    result = await current.run_next()
    assert result["id"] == task["id"] and result["status"] == "completed"
    assert result["checkpoint"]["result"]["selected"][0]["name"] == "eval-check"
    assert (await integration_environment["make"]().call("get_task", task["id"]))["status"] == "completed"
    assert await current.run_next() == {"status": "idle"}


async def test_feedback_versions_remain_immutable_and_create_reviewable_regression(integration_environment):
    current = integration_environment["make"]()
    submission = FeedbackSubmission(id="feedback-1", project_id="project-a", prompt="eval 2 + 2",
        observed_response="resultado: 5", correction="Calcular corretamente", expected_contains=("resultado: 4",))
    first = await current.feedback(submission)
    second = await current.feedback(submission.model_copy(update={"correction": "Calcular e apresentar a soma corretamente"}))
    assert first["version"] == 1 and second["version"] == 2
    assert second["previous_sha256"] == first["content_sha256"]
    persisted = await current.call("get_record", "feedback_proposal", first["proposal_id"])
    assert persisted["proposed_instruction"] == "Calcular corretamente"
    assert persisted["automatic_application"] is False
    assert second["regression"]["status"] == "draft_requires_review"
    assert second["regression"]["case"]["required_behaviors"] == ["Calcular e apresentar a soma corretamente"]
    with pytest.raises(EvolutionError, match="invalid_feedback_scope"):
        await current.feedback(submission.model_copy(update={"project_id": "other"}))


async def test_discovery_profile_draft_and_scoped_approval_use_durable_owner_data(integration_environment):
    current = integration_environment["make"]()
    await allow_budget(current)
    discovered = await current.discover(DiscoveryRequest(category="Dentista", city="São Paulo", state="SP", latitude=-23.55, longitude=-46.63))
    prospect = discovered["prospects"][0]
    await current.profile(prospect["id"])
    drafted = await current.draft(prospect["id"], "automação de atendimento", "wordpress")
    action = drafted["action"]
    assert drafted["sent"] is False and drafted["draft"]["sent"] is False
    assert action["status"] == "prepared"
    with pytest.raises(EvolutionError, match="approval_scope_mismatch"):
        await current.call("approve_action", action["id"], {"payload_hash": action["payload_hash"], "scope": "different", "expires_at": action["expires_at"]})
    accepted = await current.call("approve_action", action["id"], {"payload_hash": action["payload_hash"], "scope": action["scope"], "expires_at": action["expires_at"]})
    assert accepted["status"] == "approved"
    assert len(integration_environment["transport"].requests) == 2
    assert (await current.overview())["capabilities"]["external_dispatch"] is False
    for outsider in [integration_environment["make"]("owner-b"), integration_environment["make"](project="other")]:
        with pytest.raises(EvolutionError, match="not_found"):
            await outsider.profile(prospect["id"])
        with pytest.raises(EvolutionError, match="not_found"):
            await outsider.draft(prospect["id"], "automação")
