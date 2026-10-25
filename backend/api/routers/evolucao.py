"""Operação autenticada da evolução: identidade e capacidades são resolvidas no servidor."""

from __future__ import annotations

import re
import time
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy.exc import SQLAlchemyError

from backend.servicos.evolucao.avaliacoes import EvalCase, EvalResult, EvaluationError
from backend.servicos.evolucao.feedback import FeedbackSubmission
from backend.servicos.evolucao.habilidades import SkillError, SkillSelection
from backend.servicos.evolucao.integracao import ROOT, EvolutionCoordinator
from backend.servicos.evolucao.modelos import (
    ActionInput,
    ApprovalInput,
    BudgetLimitInput,
    EvolutionError,
    FactInput,
    TaskInput,
)
from backend.servicos.prospeccao import (
    BANTRequest,
    DiscoveryRequest,
    ICPRequest,
    Profile,
    ProspeccaoError,
    qualify_bant,
    score_icp,
)
from backend.servicos.prospeccao.schemas import SignalCode


class OperationalRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                if request.method not in {"GET", "HEAD", "OPTIONS"}:
                    chunks, size = [], 0
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > 131072:
                            return JSONResponse({"detail": "Requisição acima de 128 KiB."}, status_code=413)
                        chunks.append(chunk)
                    request._body = b"".join(chunks)
                return await handler(request)
            except (RequestValidationError, ValidationError):
                return JSONResponse({"detail": "Dados inválidos para esta operação."}, status_code=422)
            except EvolutionError as exc:
                code = exc.code if re.fullmatch(r"[a-z_]{1,100}", exc.code) else "operation_failed"
                status = 404 if code == "not_found" else 409
                if "unconfigured" in code or "unresolved" in code or code == "postgresql_required":
                    status = 503
                elif code.startswith("invalid") or code.startswith("unsupported"):
                    status = 422
                return JSONResponse({"detail": "Operação não concluída.", "code": code}, status_code=status)
            except (SkillError, EvaluationError):
                return JSONResponse({"detail": "Seleção ou avaliação indisponível para o contrato informado."}, status_code=422)
            except ProspeccaoError:
                return JSONResponse({"detail": "Coleta indisponível: confira habilitação, cota e fonte pública."}, status_code=503)
            except (SQLAlchemyError, httpx.HTTPError, OSError):
                return JSONResponse({"detail": "Dependência operacional indisponível."}, status_code=503)
        return safe_handler


router = APIRouter(route_class=OperationalRoute)
Project = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")]
ItemID = Annotated[str, Path(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")]


def coordinator(request: Request, project: str):
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, str) or not principal:
        raise HTTPException(401, "Autenticação necessária")
    factory = getattr(request.app.state, "evolution_factory", EvolutionCoordinator)
    return factory(principal, project)


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SkillRequest(Input):
    context: str = Field(min_length=1, max_length=12000)
    budget_tokens: int = Field(default=1500, ge=100, le=16000)


class EvaluationRequest(Input):
    cases: list[EvalCase] = Field(default_factory=list, max_length=20)
    use_canonical: bool = False

    @model_validator(mode="after")
    def one_source(self):
        if self.use_canonical == bool(self.cases):
            raise ValueError("Escolha casos explícitos ou conjunto canônico")
        return self


class DraftInput(Input):
    offer: str = Field(min_length=3, max_length=240)
    signal_code: SignalCode | None = None
    objection: str | None = Field(default=None, pattern=r"^(price|timing|existing_supplier|not_interested)$")


class QualificationInput(Input):
    icp: ICPRequest
    bant: BANTRequest = Field(default_factory=BANTRequest)


class ReceiptInput(Input):
    selection_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=100)
    case_id: str = Field(min_length=1, max_length=128)
    skill_name: str = Field(min_length=1, max_length=128)


@router.get("/{project}")
@router.get("/{project}/overview")
async def overview(project: Project, request: Request):
    return await coordinator(request, project).overview()


@router.post("/{project}/facts", status_code=201)
async def add_fact(project: Project, value: FactInput, request: Request):
    return await coordinator(request, project).call("add_fact", value)


@router.get("/{project}/facts/context")
async def fact_context(project: Project, request: Request, query: str = Query(default="", max_length=2000)):
    return await coordinator(request, project).memory_context(query)


@router.put("/{project}/facts/{item_id}")
async def correct_fact(project: Project, item_id: ItemID, value: FactInput, request: Request,
                       revision: int = Query(ge=1)):
    return await coordinator(request, project).call("correct_fact", item_id, value, revision)


@router.delete("/{project}/facts/{item_id}")
async def revoke_fact(project: Project, item_id: ItemID, request: Request, revision: int = Query(ge=1)):
    return await coordinator(request, project).call("revoke_fact", item_id, revision)


@router.put("/{project}/budget")
async def set_budget(project: Project, value: BudgetLimitInput, request: Request):
    return await coordinator(request, project).call("set_budget", "default", value)


@router.post("/{project}/tasks", status_code=201)
async def create_task(project: Project, value: TaskInput, request: Request):
    data = value.payload
    operation = data.get("operation")
    allowed = {"skills": {"operation", "context", "budget_tokens"},
               "evaluation": {"operation", "cases", "use_canonical"},
               "discovery": {"operation", "request"}, "profile": {"operation", "prospect_id"}}
    if operation not in allowed or set(data) - allowed[operation]:
        raise EvolutionError("unsupported_task_operation")
    if operation == "skills":
        SkillRequest.model_validate({key: val for key, val in data.items() if key != "operation"})
    elif operation == "evaluation":
        case_request = EvaluationRequest.model_validate({key: val for key, val in data.items() if key != "operation"})
        if any(case.project_id != project for case in case_request.cases):
            raise EvolutionError("invalid_evaluation_scope")
    elif operation == "discovery":
        DiscoveryRequest.model_validate(data.get("request", {}))
    elif not re.fullmatch(r"[A-Za-z0-9_.:-]{1,100}", str(data.get("prospect_id", ""))):
        raise EvolutionError("invalid_prospect_id")
    return await coordinator(request, project).call("create_task", value)


@router.post("/{project}/tasks/run")
async def run_next(project: Project, request: Request):
    return await coordinator(request, project).run_next()


@router.post("/{project}/skills/select")
async def select_skills(project: Project, value: SkillRequest, request: Request):
    return await coordinator(request, project).select_skills(value.context, value.budget_tokens)


@router.post("/{project}/skills/receipt")
async def record_receipt(project: Project, value: ReceiptInput, request: Request):
    current = coordinator(request, project)
    selected = await current.call("get_record", "selection", value.selection_id)
    selected = {key: val for key, val in selected.items() if key not in {"id", "revision"}}
    report = await current.call("get_record", "evaluation", value.run_id)
    if report.get("selections", {}).get(value.case_id) != value.selection_id:
        raise EvolutionError("invalid_execution_selection")
    result = next((item for item in report["results"] if item["case_id"] == value.case_id), None)
    if result is None:
        raise EvolutionError("not_found")
    selection = SkillSelection.model_validate(selected)
    execution = EvalResult.model_validate(result)
    record = next((skill for skill in selection.selected if skill.name == value.skill_name), None)
    if record is None:
        raise EvolutionError("invalid_skill_selection")
    evidence = tuple(artifact for artifact in execution.artifacts
                     if artifact.path == f".agents/skills/{value.skill_name}/SKILL.md")
    receipt = current.catalog().receipt(selection, value.skill_name, evidence,
                                        artifact_root=ROOT, execution=execution)
    data = receipt.model_dump(mode="json")
    await current.call("put_record", "skill_receipt", receipt.receipt_id, data)
    return data


@router.post("/{project}/evaluations")
async def evaluate(project: Project, value: EvaluationRequest, request: Request):
    return await coordinator(request, project).evaluate(tuple(value.cases), canonical=value.use_canonical)


@router.post("/{project}/feedback", status_code=201)
async def feedback(project: Project, value: FeedbackSubmission, request: Request):
    return await coordinator(request, project).feedback(value)


@router.post("/{project}/feedback/{item_id}/evaluate")
async def evaluate_feedback(project: Project, item_id: ItemID, request: Request):
    current = coordinator(request, project)
    proposal = await current.call("get_record", "feedback_proposal", item_id)
    case = EvalCase.model_validate(proposal["regression"]["case"])
    return await current.evaluate((case,))


@router.post("/{project}/actions", status_code=201)
async def prepare_action(project: Project, value: ActionInput, request: Request):
    if value.tool != "email_draft":
        raise HTTPException(403, "Ferramenta externa não configurada")
    return await coordinator(request, project).call("prepare_action", value)


@router.post("/{project}/actions/{item_id}/decision")
async def decide_action(project: Project, item_id: ItemID, value: ApprovalInput, request: Request):
    method = "approve_action" if value.decision == "approve" else "reject_action"
    return await coordinator(request, project).call(method, item_id, value)


@router.post("/{project}/prospects/discover")
async def discover(project: Project, value: DiscoveryRequest, request: Request):
    return await coordinator(request, project).discover(value)


@router.post("/{project}/prospects/{item_id}/profile")
async def profile(project: Project, item_id: ItemID, request: Request):
    return await coordinator(request, project).profile(item_id)


@router.get("/{project}/prospects/{item_id}/profile")
async def stored_profile(project: Project, item_id: ItemID, request: Request):
    return await coordinator(request, project).call("get_record", "profile", item_id)


@router.post("/{project}/prospects/{item_id}/draft")
async def draft(project: Project, item_id: ItemID, value: DraftInput, request: Request):
    return await coordinator(request, project).draft(item_id, value.offer, value.signal_code, value.objection)


@router.post("/{project}/prospects/{item_id}/qualify")
async def qualify(project: Project, item_id: ItemID, value: QualificationInput, request: Request):
    current = coordinator(request, project)
    saved = await current.call("get_record", "profile", item_id)
    profile_data = Profile.model_validate(saved["profile"])
    if profile_data.expires_at.timestamp() <= time.time():
        raise EvolutionError("profile_expired")
    qualification = {"icp": score_icp(profile_data, value.icp).model_dump(mode="json"),
                     "bant": qualify_bant(value.bant).model_dump(mode="json")}
    await current.call("put_record", "profile", item_id,
                       {"profile": saved["profile"], "qualification": qualification},
                       expected_revision=saved["revision"])
    return qualification
