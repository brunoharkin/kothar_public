"""
=============================================================
 KOTHAR v4.0 — Smart Context Compressor
 Comprime contexto baseado no modelo selecionado
 maximizando qualidade com mínimo de tokens.
=============================================================
"""

from typing import TypedDict

from backend.core.logger import get_logger
from .task_classifier import TaskClassification, TaskComplexity

log = get_logger("core.context_compressor")


# Limites de tokens por modelo
MODEL_LIMITS = {
    "haiku": {
        "max_system_chars": 3000,
        "max_rag_chunks": 3,
        "max_rag_chars": 2000,
        "include_vault": False,
        "include_codebase": False,
        "include_error_history": False,
    },
    "sonnet": {
        "max_system_chars": 6000,
        "max_rag_chunks": 8,
        "max_rag_chars": 8000,
        "include_vault": False,
        "include_codebase": True,
        "include_error_history": True,
    },
    "opus": {
        "max_system_chars": 12000,
        "max_rag_chunks": 20,
        "max_rag_chars": 20000,
        "include_vault": True,
        "include_codebase": True,
        "include_error_history": True,
    },
}


class CompressedContext(TypedDict):
    system_prompt: str
    rag_chunks: list[str]
    chunk_sources: list[str]
    total_chars: int
    estimated_tokens: int
    compression_ratio: float
    model_used: str


def compress_for_model(
    classification: TaskClassification,
    full_system: str,
    rag_chunks: list[str],
    chunk_sources: list[str],
    vault_context: str = "",
    codebase_context: str = "",
    error_history: str = "",
) -> CompressedContext:
    """
    Comprime contexto para o modelo ideal.

    Estratégia:
    - Haiku: contexto mínimo, só o essencial (~500-700 tokens)
    - Sonnet: contexto moderado, skills e código relevante (~1500-2000 tokens)
    - Opus: contexto completo para decisões complexas (~3000-5000 tokens)
    """
    model = classification["preferred_model"]
    limits = MODEL_LIMITS.get(model, MODEL_LIMITS["sonnet"])

    log.debug(
        f"Compressing context for {model}: "
        f"system<={limits['max_system_chars']}, "
        f"rag<={limits['max_rag_chunks']} chunks"
    )

    # 1. Comprime system prompt
    system_prompt = _truncate_system_prompt(
        full_system,
        limits["max_system_chars"]
    )

    # 2. Seleciona e comprime RAG chunks
    selected_rag = _select_rag_chunks(
        rag_chunks,
        chunk_sources,
        max_chunks=limits["max_rag_chunks"],
        max_chars=limits["max_rag_chars"],
        complexity=classification["complexity"],
    )

    # 3. Adiciona contextos extras se permitido
    extra_contexts = []

    if limits["include_error_history"] and error_history:
        error_context = _compress_error_history(error_history, max_chars=1500)
        if error_context:
            extra_contexts.append(error_context)

    if limits["include_codebase"] and codebase_context:
        code_context = _compress_codebase(codebase_context, max_chars=3000)
        if code_context:
            extra_contexts.append(code_context)

    if limits["include_vault"] and vault_context:
        vault_context_compressed = _summarize_vault(vault_context, max_chars=2000)
        if vault_context_compressed:
            extra_contexts.append(vault_context_compressed)

    # 4. Monta contexto final
    rag_context = build_rag_context_compact(
        selected_rag["chunks"],
        selected_rag["sources"]
    )

    full_context = system_prompt + "\n\n" + rag_context

    if extra_contexts:
        full_context += "\n\n" + "\n\n".join(extra_contexts)

    # 5. Trunca final se necessário
    total_limit = limits["max_system_chars"] + limits["max_rag_chars"]
    if len(full_context) > total_limit:
        # Mantém início (system) e fim (RAG + extras), corta meio
        head = full_context[:limits["max_system_chars"]]
        tail_len = total_limit - limits["max_system_chars"]
        tail = full_context[-tail_len:]
        full_context = head + "\n\n[... contexto intermediário omitido ...]\n\n" + tail

    # 6. Calcula métricas
    estimated_tokens = len(full_context) // 4
    original_tokens = (len(full_system) + sum(len(c) for c in rag_chunks)) // 4
    compression_ratio = estimated_tokens / original_tokens if original_tokens > 0 else 1.0

    log.info(
        f"Context compressed: {original_tokens} → {estimated_tokens} tokens "
        f"({compression_ratio:.1%}) for {model}"
    )

    return CompressedContext(
        system_prompt=system_prompt,
        rag_chunks=selected_rag["chunks"],
        chunk_sources=selected_rag["sources"],
        total_chars=len(full_context),
        estimated_tokens=estimated_tokens,
        compression_ratio=compression_ratio,
        model_used=model,
    )


def _truncate_system_prompt(system: str, max_chars: int) -> str:
    """Trunca system prompt mantendo início (identidade) e regras."""
    if len(system) <= max_chars:
        return system

    # Identidade está no início (~300 chars)
    identity_markers = [
        "Você é", "You are", "Kothar", "Assistant",
        "Responda em", "Use o contexto",
    ]

    identity_end = -1
    for marker in identity_markers:
        pos = system.find(marker)
        if pos != -1:
            identity_end = max(identity_end, pos)

    if identity_end == -1 or identity_end > 500:
        identity_end = min(400, len(system) // 4)

    # Regras estão próximas do fim (~300 chars)
    rules_section = system[max(0, len(system) - 300):]

    # Mantém identidade + meio truncado + regras
    head = system[:identity_end + 100]
    remaining_for_middle = max_chars - len(head) - len(rules_section) - 50

    if remaining_for_middle > 0:
        middle_start = identity_end + 100
        middle_end = len(system) - 300
        if middle_end > middle_start + remaining_for_middle:
            middle = system[middle_start:middle_start + remaining_for_middle]
        else:
            middle = system[middle_start:middle_end]
    else:
        middle = ""

    return head + middle + "\n\n[... contexto omitido ...]\n\n" + rules_section


def _select_rag_chunks(
    chunks: list[str],
    sources: list[str],
    max_chunks: int,
    max_chars: int,
    complexity: TaskComplexity,
) -> dict:
    """Seleciona chunks mais relevantes baseado na complexidade."""
    if not chunks:
        return {"chunks": [], "sources": []}

    # Para tarefas LOW, seleciona só os mais similares
    if complexity == TaskComplexity.LOW:
        selected = chunks[:1]
        source_selected = sources[:1]
    else:
        # Ordena por similaridade (já deve vir ordenado)
        # Pega os N melhores
        selected = chunks[:max_chunks]
        source_selected = sources[:max_chunks]

    # Comprime cada chunk se muito longo
    compressed = []
    compressed_sources = []
    total_len = 0

    for chunk, source in zip(selected, source_selected):
        # Se adicionar este chunk ultrapassa o limite
        if total_len + len(chunk) > max_chars:
            remaining = max_chars - total_len
            if remaining > 100:
                compressed.append(chunk[:remaining] + "\n[... truncado ...]")
                compressed_sources.append(source)
            break

        # Se chunk muito longo, comprime
        if len(chunk) > 2000:
            chunk = _compress_single_chunk(chunk)

        compressed.append(chunk)
        compressed_sources.append(source)
        total_len += len(chunk)

    return {"chunks": compressed, "sources": compressed_sources}


def _compress_single_chunk(chunk: str, max_lines: int = 15) -> str:
    """Comprime um chunk individual mantendo essência."""
    lines = chunk.strip().split("\n")

    if len(lines) <= max_lines:
        return chunk

    # Mantém primeiras e últimas linhas (padrão)
    head = lines[:max_lines // 2]
    tail = lines[-max_lines // 2:]

    return "\n".join(head) + f"\n\n[... {len(lines) - max_lines} linhas omitidas ...]\n\n" + "\n".join(tail)


def _compress_error_history(errors: str, max_chars: int) -> str:
    """Comprime histórico de erros."""
    if len(errors) <= max_chars:
        return "=== HISTÓRICO DE ERROS ANTERIORES ===\n" + errors

    # Extrai apenas os últimos erros relevantes
    lines = errors.split("\n")
    recent_errors = []
    total = 0

    for line in reversed(lines):
        if total + len(line) > max_chars:
            break
        recent_errors.insert(0, line)
        total += len(line)

    return "=== HISTÓRICO DE ERROS ANTERIORES ===\n" + "\n".join(recent_errors)


def _compress_codebase(codebase: str, max_chars: int) -> str:
    """Comprime contexto do codebase."""
    if len(codebase) <= max_chars:
        return "=== CÓDIGO RELEVANTE ===\n" + codebase

    # Extrai apenas imports e assinaturas de funções
    lines = codebase.split("\n")
    important_lines = []
    total = 0

    for line in lines:
        stripped = line.strip()

        # Filtra só linhas importantes
        if any(stripped.startswith(kw) for kw in ["import ", "from ", "def ", "class ", "@"]):
            if total + len(line) <= max_chars:
                important_lines.append(line)
                total += len(line)
            else:
                # Adiciona indicador de continuação
                if important_lines:
                    important_lines.append(f"[... +{len(lines) - len(important_lines)} linhas ...]")
                break

    if not important_lines:
        # Fallback: primeiras linhas
        return "=== CÓDIGO RELEVANTE ===\n" + codebase[:max_chars]

    return "=== CÓDIGO RELEVANTE ===\n" + "\n".join(important_lines)


def _summarize_vault(vault: str, max_chars: int) -> str:
    """Resume contexto do vault para Opus."""
    if len(vault) <= max_chars:
        return "=== SESSÕES SIMILARES DO COFRE ===\n" + vault

    # Extrai sessões recentes ou mais relevantes
    # heuristic: assume sessões são separadas por ===
    sections = vault.split("===")

    recent = []
    total = 0

    for section in reversed(sections):
        if total + len(section) > max_chars:
            break
        recent.insert(0, section)
        total += len(section)

    return "=== SESSÕES SIMILARES DO COFRE ===\n" + "===".join(recent)


def build_rag_context_compact(chunks: list[str], sources: list[str]) -> str:
    """Constrói contexto RAG compactado para injeção."""
    if not chunks:
        return ""

    context = "=== CONTEXTO RAG ===\n"

    for i, (chunk, source) in enumerate(zip(chunks, sources), 1):
        # Limita tamanho de cada chunk
        display_chunk = chunk[:1000] + "..." if len(chunk) > 1000 else chunk

        context += f"\n[Fonte {i}: {source}]\n{display_chunk}\n"
        context += "-" * 40 + "\n"

    context += "=== FIM DO CONTEXTO RAG ===\n"

    return context


# =====================================================
# Quick helpers para uso em outros módulos
# =====================================================

def estimate_tokens_from_chars(chars: int) -> int:
    """Estima tokens a partir de caracteres."""
    # Média: 1 token ≈ 4 caracteres em inglês, 3 em português
    return chars // 4


def should_use_rag(classification: TaskClassification) -> bool:
    """Determina se RAG deve ser usado para esta tarefa."""
    # Tarefas LOW geralmente não precisam de RAG
    if classification["complexity"] == TaskComplexity.LOW:
        return len(classification["context_needed"]) > 1

    return True
