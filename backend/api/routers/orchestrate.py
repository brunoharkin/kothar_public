"""Orchestration router."""


from fastapi import APIRouter, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field

from backend.contracts.task_execution import TaskExecutionPlan
from backend.core.logger import get_logger
from backend.engenheiro_kothar.orchestrator import engenheiro_kothar
from backend.engenheiro_kothar.routing import TaskRequirements
from backend.trace.session_compiler import session_compiler

log = get_logger("api.orchestrate")


class SafeValidationRoute(APIRoute):
    """Erros de contrato não devolvem conteúdo de arquivos ou credenciais."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                return JSONResponse(status_code=422, content={"detail": [
                    {"loc": error["loc"], "type": error["type"],
                     "msg": "Requisição inválida para o contrato de orquestração."}
                    for error in exc.errors()
                ]})

        return safe_handler


router = APIRouter(route_class=SafeValidationRoute)


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_description: str = Field(min_length=1, max_length=20_000)
    metadata: dict = Field(default_factory=dict)
    requirements: TaskRequirements | None = None
    execution_plan: TaskExecutionPlan | None = None


class CompileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")


@router.post("/start")
async def start_orchestration(body: StartRequest):
    """
    Inicia uma nova orquestração.
    Cria blueprint mas NÃO executa - use /execute para rodar.
    """
    result = await engenheiro_kothar.orchestrate(
        task_description=body.task_description,
        metadata=body.metadata,
        requirements=body.requirements,
        execution_plan=body.execution_plan,
    )
    return result


@router.post("/{session_id}/execute")
async def execute_blueprint(session_id: str):
    """
    Executa o blueprint de uma sessão.
    Este é o endpoint que REALMENTE roda o fluxo.
    """
    log.info("Executando blueprint", session_id=session_id)

    try:
        result = await engenheiro_kothar.execute(session_id=session_id)

        return {
            "session_id": session_id,
            "status": result.status,
            "error": result.error,
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "skipped_steps": result.skipped_steps,
            "total_duration_ms": result.total_duration_ms,
            "checkpoint_recovered": result.checkpoint_recovered,
            "production_ready": result.production_ready,
            "step_results": [
                {
                    "step_id": r.step_id,
                    "title": r.step_title,
                    "agent": r.agent_name,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "retries": r.retries,
                    "error": r.error,
                }
                for r in result.step_results
            ],
        }
    except ValueError as e:
        return JSONResponse(status_code=404, content={"error": str(e)})
    except Exception as e:
        log.error(f"Erro na execução: {e}", session_id=session_id)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/{session_id}/execute/background")
async def execute_blueprint_background(session_id: str, background_tasks: BackgroundTasks):
    """
    Executa o blueprint em background e retorna imediatamente.
    Use /status para monitorar o progresso.
    """
    async def run_in_background():
        try:
            await engenheiro_kothar.execute(session_id=session_id)
        except Exception as e:
            log.error(f"Execução background falhou: {e}", session_id=session_id)

    background_tasks.add_task(run_in_background)

    return {
        "session_id": session_id,
        "status": "accepted",
        "message": "Solicitação aceita. Execução depende de executor real; consulte /status.",
    }


@router.post("/{session_id}/complete")
async def complete_orchestration(session_id: str):
    """Finaliza e compila uma sessão de orquestração."""
    result = await engenheiro_kothar.complete_session(session_id)
    return result


@router.get("/{session_id}/status")
async def get_orchestration_status(session_id: str):
    """Status atual da sessão de orquestração."""
    status = await engenheiro_kothar.get_session_status(session_id)
    return status


@router.post("/compile")
async def compile_session(body: CompileRequest):
    """Compila uma sessão e gera relatório no Vault."""
    result = await session_compiler.compile(body.session_id)
    return result
