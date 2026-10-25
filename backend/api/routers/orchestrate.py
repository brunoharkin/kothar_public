"""Orchestration router."""

from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.core.logger import get_logger
from backend.trace.session_compiler import session_compiler
from backend.engenheiro_kothar.orchestrator import engenheiro_kothar
from backend.harness.blueprint_executor import blueprint_executor

log = get_logger("api.orchestrate")
router = APIRouter()


@router.post("/start")
async def start_orchestration(body: dict):
    """
    Inicia uma nova orquestração.
    Cria blueprint mas NÃO executa - use /execute para rodar.
    """
    task = body.get("task_description", "")
    if not task:
        return JSONResponse(status_code=422, content={"error": "task_description é obrigatório"})

    result = await engenheiro_kothar.orchestrate(
        task_description=task,
        metadata=body.get("metadata", {}),
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
            "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps,
            "skipped_steps": result.skipped_steps,
            "total_duration_ms": result.total_duration_ms,
            "checkpoint_recovered": result.checkpoint_recovered,
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
        "status": "executing",
        "message": "Execução iniciada em background. Use /status para monitorar.",
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
async def compile_session(body: dict):
    """Compila uma sessão e gera relatório no Vault."""
    session_id = body.get("session_id")
    if not session_id:
        return JSONResponse(status_code=422, content={"error": "session_id é obrigatório"})

    result = await session_compiler.compile(session_id)
    return result
