"""
=============================================================
 KOTHAR v4.0 — Task Classifier
 Classifica tarefa e estima complexidade ANTES da execução
 para selecionar o modelo ideal (Haiku/Sonnet/Opus).
=============================================================
"""

from enum import Enum
from typing import TypedDict
import re

from backend.core.logger import get_logger

log = get_logger("core.task_classifier")


class TaskComplexity(Enum):
    LOW = "low"          # Haiku
    MEDIUM = "medium"    # Sonnet
    HIGH = "high"        # Opus
    CRITICAL = "critical"  # Opus + contexto completo


class TaskType(Enum):
    SIMPLE = "simple"       # Query, busca direta
    ROUTINE = "routine"     # Código padrão
    COMPLEX = "complex"     # Lógica elaborada
    CREATIVE = "creative"   # Arquitetura, design
    AUDIT = "audit"        # Análise, QA


class TaskClassification(TypedDict):
    complexity: TaskComplexity
    type: TaskType
    estimated_tokens: int
    preferred_model: str
    context_needed: list[str]
    reason: str


# Padrões de complexidade (ordenados do mais específico ao menos)
COMPLEXITY_PATTERNS = {
    TaskComplexity.CRITICAL: [
        r"seguran[cç]a|security|vulnerabil|vulnerability",
        r"compliance|lgpd|gdpr|pii|dados\s+pessoais",
        r"refatora[cç][ãa]o\s+(total|micro|sistema|completa)",
        r"desenhar\s+(novo|do\s+zero|from\s+scratch)",
        r"payment|pagamento|cartão|cartao|credito",
    ],
    TaskComplexity.HIGH: [
        r"arquitetura|architecture",
        r"design\s+(de|do|system)",
        r"planejar|planning",
        r"refatora[cç][ãa]o\s+(grande|major|grande\s+porte)",
        r"migrar|migration",
        r"otimizar\s+(performance|escalabilidade|lat[eê]ncia)",
        r"(decidir|avaliar|comparar|benchmark)",
        r"integra[cç][ãa]o\s+(api|service|third[\s-]party)",
        r"microservi[cç]os|microservices",
    ],
    TaskComplexity.MEDIUM: [
        r"criar.*(fun[cç][ãa]o|funcao|endpoint|rota|componente|classe|service)",
        r"implementar.*(auth|login|api|crud|webhook)",
        r"refatorar.*(m[oó]dulo|modulo|classe|fun[cç][ãa]o)",
        r"(corrigir|consertar|fixar)\s+(bug|erro|defeito)",
        r"adicionar.*(feature|funcionalidade|campo|campoadicional)",
        r"modificar.*(fun[cç][ãa]o|endpoint|componente)",
        r"teste\s+(unit[ãa]rio|e2e|integra[cç][ãa]o)",
        r"script|automação|automa[cç][ãa]o",
        r"configurar|setup|instalar|deploy",
        r"autentica[cç][ãa]o|oauth|jwt|token",
        r"(criar|implementar|escrever)\s+(um?\s+)?(c[oó]digo|fun[cç][ãa]o|endpoint|service)",
    ],
    TaskComplexity.LOW: [
        # Mais específico primeiro
        r"^(criar|gerar|escrever)\s+(um?\s+)?(readme|documenta[cç][ãa]o|coment[ãa]rio|doc|arquivo\s+txt)",
        r"^(criar|gerar|escrever)\s+(um?\s+)?(nota|lista|resumo)",
        r"^(corrigir|fixar)\s+(erro|bug)\s+(de\s+)?(sintaxe|typo|ortografia|simples)",
        r"^(o\s+que[ée]|defina|explique)\s+\w+",
        r"liste|busque|procure|encontre",
        r"\?$",
        r"resum[oa]|somariz",
        r"traduz[oa]",
        r"format[oa]",
        r"renome[oa]",
        r"delet[oa]|remov[oa]",
        r"^verifique\s+(se|se\s+existe|exist[eê]ncia)",
        r"^qual\s+(é|são)",
    ],
}

# Padrões de tipo de tarefa
TYPE_PATTERNS = {
    TaskType.SIMPLE: [
        r"^(o\s+que[ée]|quem|onde|quando|como|por\s+qu[eé])",
        r"\?$",
        r"liste|busque|procure|encontre",
        r"defina|explique|resuma",
        r"traduz[oa]",
        r"o\s+que[ée]\s+(um?\s+)?\w+",
    ],
    TaskType.ROUTINE: [
        r"(criar|implementar|escrever)\s+(um?\s+)?(c[oó]digo|fun[cç][ãa]o|endpoint)",
        r"(corrigir|fixar)\s+(bug|erro)",
        r"adicionar.*teste",
        r"(formatar|limpar)\s+(c[oó]digo)",
        r"atualizar.*(depend[eê]ncia|package|biblioteca)",
        r"gerar.*(migration|seed|fixture)",
    ],
    TaskType.COMPLEX: [
        r"refatorar",
        r"otimizar",
        r"migrar",
        r"(analisar|auditar)\s+(c[oó]digo|performance|arquitetura)",
        r"reescrever|reimplementar",
        r"desacoplar|cuplar",
    ],
    TaskType.CREATIVE: [
        r"criar\s+(do\s+zero|from\s+scratch)",
        r"desenhar",
        r"arquitetar",
        r"planejar\s+(estratégia|estrategia|roadmap)",
        r"projetar",
        r"brainstorm",
    ],
    TaskType.AUDIT: [
        r"auditar|revisar",
        r"validar",
        r"verificar\s+(seguran[cç]a|compliance|qualidade)",
        r"testar\s+(e2e|e2e|integra[cç][ãa]o|penetra[cç][ãa]o)",
        r"analisar.*performance|benchmark",
        r"debugar",
        r"inspecionar",
    ],
}

# Mapeamento de complexidade + tipo → modelo
MODEL_PREFERENCES = {
    # (complexity, type): (model, reason)
    (TaskComplexity.LOW, TaskType.SIMPLE): ("haiku", "Consulta direta"),
    (TaskComplexity.LOW, TaskType.ROUTINE): ("haiku", "Tarefa simples/básica"),
    (TaskComplexity.LOW, TaskType.AUDIT): ("sonnet", "Auditoria requer análise"),
    (TaskComplexity.MEDIUM, TaskType.ROUTINE): ("sonnet", "Código padrão"),
    (TaskComplexity.MEDIUM, TaskType.COMPLEX): ("sonnet", "Lógica moderada"),
    (TaskComplexity.MEDIUM, TaskType.AUDIT): ("sonnet", "QA sistemático"),
    (TaskComplexity.MEDIUM, TaskType.CREATIVE): ("sonnet", "Design com contexto"),
    (TaskComplexity.MEDIUM, TaskType.SIMPLE): ("haiku", "Tarefa simples"),
    (TaskComplexity.HIGH, TaskType.COMPLEX): ("opus", "Análise profunda"),
    (TaskComplexity.HIGH, TaskType.CREATIVE): ("opus", "Design complexo"),
    (TaskComplexity.HIGH, TaskType.AUDIT): ("opus", "Auditoria rigorosa"),
    (TaskComplexity.HIGH, TaskType.ROUTINE): ("sonnet", "Código complexo mas rotineiro"),
    (TaskComplexity.CRITICAL, None): ("opus", "TAREFA CRÍTICA"),
}


def classify_task(task_description: str) -> TaskClassification:
    """
    Classifica uma tarefa de forma rápida e determinística.

    Returns:
        TaskClassification com:
        - complexity: LOW/MEDIUM/HIGH/CRITICAL
        - type: SIMPLE/ROUTINE/COMPLEX/CREATIVE/AUDIT
        - estimated_tokens: int
        - preferred_model: "haiku" | "sonnet" | "opus"
        - context_needed: list de contextos necessários
        - reason: justificativa da classificação
    """
    task_lower = task_description.lower()
    task_clean = re.sub(r'[^\w\s]', ' ', task_lower)

    # 1. Detecta complexidade (do mais específico ao menos)
    complexity = TaskComplexity.MEDIUM  # default

    # Prioridade: CRITICAL > HIGH > MEDIUM > LOW
    for comp in [TaskComplexity.CRITICAL, TaskComplexity.HIGH,
                  TaskComplexity.MEDIUM, TaskComplexity.LOW]:
        patterns = COMPLEXITY_PATTERNS.get(comp, [])
        for pattern in patterns:
            if re.search(pattern, task_clean, re.IGNORECASE):
                complexity = comp
                break
        if complexity != TaskComplexity.MEDIUM:
            break

    # 2. Detecta tipo
    task_type = TaskType.ROUTINE  # default

    for t, patterns in TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, task_clean, re.IGNORECASE):
                task_type = t
                break
        if task_type != TaskType.ROUTINE:
            break

    # 3. Estima tokens
    token_estimates = {
        TaskComplexity.LOW: 500,
        TaskComplexity.MEDIUM: 2000,
        TaskComplexity.HIGH: 5000,
        TaskComplexity.CRITICAL: 10000,
    }
    estimated_tokens = token_estimates[complexity]

    # 4. Seleciona modelo
    model, reason = MODEL_PREFERENCES.get(
        (complexity, task_type),
        MODEL_PREFERENCES.get((complexity, None), ("sonnet", f"Default: {complexity.value}"))
    )

    # Override baseado em keywords específicas
    if any(kw in task_clean for kw in ["corrigir", "bug", "erro", "fix"]):
        model = "sonnet"
        reason = "Correção requer análise de contexto"

    if any(kw in task_clean for kw in ["criar", "gerar", "escrever"]):
        if any(kw in task_clean for kw in ["readme", "doc", "comentário", "comentario"]):
            model = "haiku"
            reason = "Geração de documentação simples"

    # 5. Determina contextos necessários
    context_needed = ["session"]  # sempre

    if complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]:
        context_needed.extend(["codebase", "skills", "vault"])
    elif complexity == TaskComplexity.MEDIUM:
        context_needed.extend(["skills", "codebase"])

    if any(kw in task_clean for kw in ["arquivo", "código", "codigo", "função", "funcao", "classe"]):
        context_needed.append("codebase")

    if any(kw in task_clean for kw in ["erro", "bug", "falha", "problema", "não funciona", "erro"]):
        context_needed.append("error_history")

    if any(kw in task_clean for kw in ["banco", "database", "sql", "postgres", "redis"]):
        context_needed.append("database_schema")

    # Remove duplicatas mantendo ordem
    seen = set()
    context_needed = [x for x in context_needed if not (x in seen or seen.add(x))]

    # 6. Gera reason se não definido
    if not reason:
        reason_map = {
            TaskComplexity.LOW: "Tarefa simples/rápida",
            TaskComplexity.MEDIUM: "Tarefa moderada requer contexto",
            TaskComplexity.HIGH: "Tarefa complexa requer análise profunda",
            TaskComplexity.CRITICAL: "TAREFA CRÍTICA - análise completa obrigatória",
        }
        reason = reason_map[complexity]

    log.debug(
        f"Task classified: {complexity.value}/{task_type.value} → {model}",
        task=task_description[:50],
    )

    return TaskClassification(
        complexity=complexity,
        type=task_type,
        estimated_tokens=estimated_tokens,
        preferred_model=model,
        context_needed=context_needed,
        reason=reason,
    )


def get_optimal_model(task: str) -> str:
    """Helper rápido: retorna apenas o modelo ideal."""
    return classify_task(task)["preferred_model"]


# =====================================================
# Extensões para código
# =====================================================

CODE_COMPLEXITY_PATTERNS = {
    TaskComplexity.LOW: [
        r"def\s+\w+\s*\([^)]*\)\s*:",  # Função simples
        r"class\s+\w+:",  # Classe simples sem herança
        r"@app\.(get|post|put|delete)",  # Rota simples
        r"SELECT\s+\*\s+FROM",  # Query simples
    ],
    TaskComplexity.MEDIUM: [
        r"class\s+\w+\s*\(\w+\):",  # Classe com herança
        r"async\s+def",  # Função assíncrona
        r"@app\.(router|include_router)",  # Rotas com router
        r"JOIN\s+",  # Query com JOIN
        r"transaction",  # Transação
    ],
    TaskComplexity.HIGH: [
        r"class\s+\w+\s*\([^)]*,\s*\w+\)",  # Herança múltipla
        r"metaclass",  # Metaclasses
        r"asyncio\.(gather|create_task)",  # Tarefas paralelas
        r"cursor\.executemany",  # Bulk operations
        r"threading|multiprocessing",  # Concorrência
    ],
}


def estimate_code_complexity(code_snippet: str) -> TaskComplexity:
    """Estima complexidade de um snippet de código."""
    complexity = TaskComplexity.LOW

    for comp, patterns in CODE_COMPLEXITY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, code_snippet, re.IGNORECASE):
                complexity = comp
                break
        if complexity != TaskComplexity.LOW:
            break

    # Conta linhas (heurística)
    lines = code_snippet.strip().split("\n")
    if len(lines) > 100:
        complexity = TaskComplexity(max(complexity.value, TaskComplexity.MEDIUM.value))
    if len(lines) > 300:
        complexity = TaskComplexity.HIGH

    return complexity
