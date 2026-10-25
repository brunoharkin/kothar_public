"""
=============================================================
 KOTHAR v4.0 — Model Preview Router
 Mostra ao usuário qual modelo será usado e por quê
 ANTES de executar a tarefa.
=============================================================
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.core.logger import get_logger
from backend.core.task_classifier import classify_task, TaskComplexity

log = get_logger("api.model_preview")
router = APIRouter()


class PreviewRequest(BaseModel):
    task: str


class ModelPreview(BaseModel):
    task: str
    complexity: str
    task_type: str
    recommended_model: str
    model_description: str
    alternative_models: dict[str, str]
    estimated_tokens: int
    estimated_cost_units: float
    reason: str
    context_to_load: list[str]
    optimization_tips: list[str]
    will_use_rag: bool


# Descrições dos modelos
MODEL_DESCRIPTIONS = {
    "haiku": "🟢 Ultra-rápido. Para tarefas simples, consultas e geração básica.",
    "sonnet": "🟡 Equilibrado. Para código rotineiro, correções e QA.",
    "opus": "🔴 Máximo poder. Para arquitetura, decisões complexas e auditoria profunda.",
}

# Custo relativo (tokens por unidades)
MODEL_COST = {
    "haiku": 1.0,
    "sonnet": 3.0,
    "opus": 10.0,
}


@router.post("/preview/model", response_model=ModelPreview)
async def preview_model_selection(req: PreviewRequest) -> ModelPreview:
    """
    Preview da seleção de modelo para uma tarefa.

    Returns:
    - Modelo recomendado
    - Por que este modelo foi escolhido
    - Modelos alternativos
    - Dicas de otimização
    - Contexto que será carregado
    """
    if not req.task or len(req.task.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Tarefa muito curta para classificar"
        )

    classification = classify_task(req.task)

    # Gera tips de otimização
    tips = _generate_optimization_tips(classification)

    # Modelos alternativos
    alternatives = _get_alternative_models(classification)

    # Estima custo
    estimated_cost = (
        MODEL_COST[classification["preferred_model"]]
        * classification["estimated_tokens"]
        / 1000
    )

    # Verifica se usará RAG
    will_use_rag = (
        classification["complexity"] in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]
        or len(classification["context_needed"]) > 2
    )

    return ModelPreview(
        task=req.task,
        complexity=classification["complexity"].value,
        task_type=classification["type"].value,
        recommended_model=classification["preferred_model"],
        model_description=MODEL_DESCRIPTIONS.get(classification["preferred_model"], ""),
        alternative_models=alternatives,
        estimated_tokens=classification["estimated_tokens"],
        estimated_cost_units=round(estimated_cost, 2),
        reason=classification["reason"],
        context_to_load=classification["context_needed"],
        optimization_tips=tips,
        will_use_rag=will_use_rag,
    )


def _generate_optimization_tips(classification) -> list[str]:
    """Gera dicas de otimização baseadas na classificação."""
    tips = []

    complexity = classification.complexity
    context_needed = classification.context_needed

    # Dicas por complexidade
    if complexity == TaskComplexity.CRITICAL:
        tips.append("⚠️ Tarefa crítica: contexto completo será carregado")
        tips.append("💡 Considere quebrar em tarefas menores se possível")
        tips.append("⏱️ Execução pode ser mais lenta (modelo Opus)")
    elif complexity == TaskComplexity.HIGH:
        tips.append("🔍 Tarefa complexa: análise profunda será feita")
        tips.append("💡 Contexto de código será carregado")
    elif complexity == TaskComplexity.MEDIUM:
        tips.append("📝 Tarefa moderada: contexto parcial será usado")
    else:
        tips.append("⚡ Tarefa simples: execução rápida esperada")
        tips.append("💡 Contexto mínimo será usado")

    # Dicas por contexto
    if "codebase" in context_needed:
        tips.append("📁 Código do projeto será analisado")

    if "skills" in context_needed:
        tips.append("🛠️ Skills relevantes serão buscadas no RAG")

    if "vault" in context_needed:
        tips.append("📚 Sessões similares do Cofre serão carregadas")

    if "error_history" in context_needed:
        tips.append("🔄 Histórico de erros será considerado")

    # Dica geral
    if complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]:
        tips.append("💡 Para economizar tokens, especifique melhor o escopo")

    return tips


def _get_alternative_models(classification) -> dict[str, str]:
    """Retorna modelos alternativos com justificativas."""
    current = classification.preferred_model
    alternatives = {}

    if current == "haiku":
        alternatives["sonnet"] = "Se precisar de mais precisão na análise"
        alternatives["opus"] = "Se a tarefa for mais complexa que aparenta"
    elif current == "sonnet":
        alternatives["haiku"] = "Para execução mais rápida (se aceitar risco)"
        alternatives["opus"] = "Se precisar de maior profundidade"
    elif current == "opus":
        alternatives["sonnet"] = "Se quiser sacrificar precisão por velocidade"

    return alternatives


# =====================================================
# Batch preview (para blueprints)
# =====================================================

class BatchPreviewRequest(BaseModel):
    tasks: list[str]


class BatchPreviewResponse(BaseModel):
    previews: list[ModelPreview]
    total_estimated_tokens: int
    total_estimated_cost: float
    models_distribution: dict[str, int]


@router.post("/preview/model/batch", response_model=BatchPreviewResponse)
async def batch_preview(req: BatchPreviewRequest) -> BatchPreviewResponse:
    """
    Preview de múltiplas tarefas (ex: blueprint completo).
    Retorna distribuição de modelos e custos totais.
    """
    previews = []
    total_tokens = 0
    models_dist = {"haiku": 0, "sonnet": 0, "opus": 0}
    total_cost = 0.0

    for task in req.tasks:
        if len(task.strip()) < 3:
            continue

        preview = await preview_model_selection(PreviewRequest(task=task))
        previews.append(preview)

        total_tokens += preview.estimated_tokens
        total_cost += preview.estimated_cost_units
        models_dist[preview.recommended_model] += 1

    return BatchPreviewResponse(
        previews=previews,
        total_estimated_tokens=total_tokens,
        total_estimated_cost=round(total_cost, 2),
        models_distribution=models_dist,
    )


# =====================================================
# Force model override
# =====================================================

class ForceModelRequest(BaseModel):
    task: str
    force_model: str  # haiku, sonnet, ou opus


@router.post("/preview/model/force")
async def force_model_preview(req: ForceModelRequest) -> dict:
    """
    Permite forçar um modelo específico (com justificativa).
    """
    valid_models = ["haiku", "sonnet", "opus"]
    if req.force_model not in valid_models:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo inválido. Use: {valid_models}"
        )

    classification = classify_task(req.task)

    # Calcula impacto
    current_cost = MODEL_COST[classification.preferred_model]
    forced_cost = MODEL_COST[req.force_model]
    cost_increase = (forced_cost / current_cost - 1) * 100

    # Gera warning se downgrading
    model_order = {"haiku": 1, "sonnet": 2, "opus": 3}
    is_downgrade = model_order[req.force_model] < model_order[classification.preferred_model]

    return {
        "task": req.task,
        "original_model": classification.preferred_model,
        "forced_model": req.force_model,
        "cost_impact_percent": round(cost_increase, 1),
        "is_downgrade": is_downgrade,
        "warning": (
            "⚠️ Downgrade detectado: qualidade pode ser comprometida"
            if is_downgrade
            else None
        ),
        "reason": f"Forçado pelo usuário para {req.force_model}",
    }
