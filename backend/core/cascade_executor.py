"""
=============================================================
 KOTHAR v4.0 — Cascade Model Executor
 Executa tarefa começando com modelo menor,
 escala automaticamente se necessário.
=============================================================
"""

import asyncio
import time
from typing import Callable, Any, TypedDict, Optional
from dataclasses import dataclass, field

from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("core.cascade_executor")


@dataclass
class ExecutionResult:
    """Resultado de uma execução."""
    success: bool
    output: str
    model_used: str
    tokens_used: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    escalated: bool = False
    escalation_count: int = 0
    error: str = ""
    duration_ms: int = 0
    quality_score: float = 0.0


@dataclass
class CascadeConfig:
    """Configuração do cascade executor."""
    max_escalations: int = 2
    quality_threshold: float = 0.7
    escalation_chain: dict = field(default_factory=lambda: {
        "haiku": "sonnet",
        "sonnet": "opus",
    })
    enable_learning: bool = True
    cache_results: bool = True


class QualityEvaluator:
    """
    Avalia qualidade do output do modelo.
    """

    UNCERTAINTY_PHRASES = [
        "não sei", "não tenho certeza", "não consigo",
        "não tenho informações", "não encontrado", "não disponível",
        "i'm not sure", "i don't know", "cannot", "unable to",
        "uncertain", "maybe", "possibly", "perhaps",
    ]

    def evaluate(self, output: str, task: str, complexity: str) -> float:
        """
        Avalia qualidade do output (0-1).

        Fatores:
        - Completude: output substancial para a complexidade
        - Precisão: responde o que foi perguntado
        - Confiança: sem incertezas excessivas
        """
        if not output:
            return 0.0

        output_lower = output.lower()
        task_lower = task.lower()

        # 1. Avalia completude (40% do peso)
        completeness = self._evaluate_completeness(output, task, complexity)

        # 2. Avalia precisão (40% do peso)
        precision = self._evaluate_precision(output, task_lower, output_lower)

        # 3. Penaliza incertezas (20% do peso negativo)
        uncertainty_penalty = self._evaluate_uncertainty(output_lower)

        # Score final
        quality = (completeness * 0.4 + precision * 0.4 - uncertainty_penalty * 0.2)

        return max(0.0, min(1.0, quality))

    def _evaluate_completeness(self, output: str, task: str, complexity: str) -> float:
        """Avalia se output é substancial para a tarefa."""
        task_lower = task.lower()
        output_len = len(output)

        # Tarefas de criação devem ter output substancial
        if any(kw in task_lower for kw in ["criar", "implementar", "escrever", "gerar"]):
            if output_len < 200:
                return 0.3
            elif output_len < 500:
                return 0.6
            elif output_len < 1000:
                return 0.8

        # Tarefas de análise
        if any(kw in task_lower for kw in ["analisar", "auditar", "revisar"]):
            if output_len < 300:
                return 0.3
            elif output_len < 1000:
                return 0.7

        # Tarefas simples
        if output_len < 100:
            return 0.5
        elif output_len < 500:
            return 0.8

        return 0.9

    def _evaluate_precision(self, output: str, task_lower: str, output_lower: str) -> float:
        """Avalia se output responde o que foi perguntado."""
        # Extrai keywords da task
        task_keywords = [w for w in task_lower.split() if len(w) > 4]

        if not task_keywords:
            return 1.0

        # Conta quantas keywords aparecem no output
        matched = sum(1 for kw in task_keywords if kw in output_lower)
        ratio = matched / len(task_keywords)

        # Bônus por ter palavras da task
        return min(1.0, ratio + 0.2)

    def _evaluate_uncertainty(self, output_lower: str) -> float:
        """Penaliza incertezas no output."""
        penalty = 0.0

        for phrase in self.UNCERTAINTY_PHRASES:
            if phrase in output_lower:
                penalty += 0.15

        return min(0.5, penalty)


class CascadeExecutor:
    """
    Executor que começa com modelo menor e escala se necessário.

    Fluxo:
    1. Executa com modelo recomendado
    2. Avalia qualidade do output
    3. Se insuficiente → escala para cima
    4. Aprende para otimizar próximas execuções
    """

    def __init__(self, config: CascadeConfig = None):
        self.config = config or CascadeConfig()
        self.quality_evaluator = QualityEvaluator()
        self._history: dict[str, list[float]] = {}

        # Tenta importar o tracker de métricas (não bloqueia se falhar)
        try:
            from backend.trace.cascade_metrics import record_cascade_execution
            self._record_metric = record_cascade_execution
        except ImportError:
            self._record_metric = None

    async def execute(
        self,
        task: str,
        system_prompt: str,
        complexity: str,
        rag_chunks: list[str] = None,
        chunk_sources: list[str] = None,
        initial_model: str = None,
        on_stream: Callable[[str], None] = None,
    ) -> ExecutionResult:
        """
        Executa tarefa com modelo ideal, escalando se necessário.
        """
        from .task_classifier import classify_task

        classification = classify_task(task)
        current_model = initial_model or classification.preferred_model

        start_time = time.time()
        escalation_count = 0
        final_output = ""
        total_tokens = 0

        while escalation_count <= self.config.max_escalations:
            try:
                from_model = current_model if escalation_count > 0 else None
                # Executa com modelo atual
                result = await self._call_model(
                    model=current_model,
                    task=task,
                    system_prompt=system_prompt,
                    rag_chunks=rag_chunks,
                    on_stream=on_stream,
                )

                final_output = result.get("output", "")
                tokens_used = result.get("tokens_used", 0)

                # Avalia qualidade
                quality_score = self.quality_evaluator.evaluate(
                    output=final_output,
                    task=task,
                    complexity=complexity,
                )

                log.debug(
                    f"Cascade: {current_model} quality={quality_score:.2f}",
                    task=task[:50],
                )

                # Registra métrica desta execução
                if self._record_metric:
                    self._record_metric(
                        model=current_model,
                        tokens=tokens_used,
                        escalated=escalation_count > 0,
                        from_model=from_model,
                    )

                # Verifica se é suficiente
                if quality_score >= self.config.quality_threshold:
                    duration_ms = int((time.time() - start_time) * 1000)

                    return ExecutionResult(
                        success=True,
                        output=final_output,
                        model_used=current_model,
                        tokens_used=tokens_used,
                        escalated=escalation_count > 0,
                        escalation_count=escalation_count,
                        duration_ms=duration_ms,
                        quality_score=quality_score,
                    )

                # Verifica se pode escalar
                next_model = self.config.escalation_chain.get(current_model)
                if not next_model:
                    # Já está no modelo máximo
                    duration_ms = int((time.time() - start_time) * 1000)
                    return ExecutionResult(
                        success=True,  # Ainda retorna o que temos
                        output=final_output,
                        model_used=current_model,
                        tokens_used=tokens_used,
                        escalated=True,
                        escalation_count=escalation_count,
                        duration_ms=duration_ms,
                        quality_score=quality_score,
                    )

                # Escalona para próximo modelo
                log.info(
                    f"Escalando de {current_model} para {next_model} "
                    f"(quality={quality_score:.2f} < {self.config.quality_threshold})"
                )
                current_model = next_model
                escalation_count += 1

                # Pausa breve entre escalações
                await asyncio.sleep(0.1)

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                log.error(f"Cascade execution error: {e}")

                return ExecutionResult(
                    success=False,
                    output="",
                    model_used=current_model,
                    tokens_used=0,
                    escalated=escalation_count > 0,
                    escalation_count=escalation_count,
                    duration_ms=duration_ms,
                    error=str(e),
                )

        # Máximo de escalações atingido
        duration_ms = int((time.time() - start_time) * 1000)
        return ExecutionResult(
            success=False,
            output=final_output,
            model_used=current_model,
            tokens_used=0,
            escalated=True,
            escalation_count=escalation_count,
            duration_ms=duration_ms,
            error="Max escalations exceeded",
        )

    async def _call_model(
        self,
        model: str,
        task: str,
        system_prompt: str,
        rag_chunks: list[str] = None,
        on_stream: Callable[[str], None] = None,
    ) -> dict:
        """
        Chama o provedor LLM com o modelo especificado.
        Usa provedores remotos (Claude, OpenAI).
        """
        # Monta contexto com RAG chunks
        context = ""
        if rag_chunks:
            context = "\n\n".join(rag_chunks[:5])

        # Prepara prompt completo
        full_prompt = f"{system_prompt}\n\nContexto relevante:\n{context}\n\nTarefa:\n{task}" if context else f"{system_prompt}\n\nTarefa:\n{task}"

        # Chama Claude via API
        try:
            return await self._call_claude(model, full_prompt)
        except Exception as claude_error:
            log.error(f"Claude API falhou: {claude_error}")
            return await self._simulate_output(task, model)

    async def _call_claude(self, model: str, prompt: str) -> dict:
        """Chama Claude via API interna do Kothar."""
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://localhost:8080/api/llm/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code}")

            data = response.json()
            return {
                "output": data.get("response", ""),
                "tokens_used": data.get("tokens_used", 0),
                "model": model,
            }

    async def _simulate_output(self, task: str, model: str) -> dict:
        """Fallback: simulação quando nenhum LLM está disponível."""
        log.warn(f"Usando output simulado para task: {task[:50]}...")

        await asyncio.sleep(0.1)

        return {
            "output": f"[SIMULATED] Task processed by {model}: {task[:100]}...",
            "tokens_used": len(task) // 4,
            "model": model,
        }

    def learn_from_result(self, task_pattern: str, quality: float, model_used: str) -> None:
        """
        Aprende do resultado para ajustar modelos futuros.

        Args:
            task_pattern: Hash ou pattern da tarefa
            quality: Score de qualidade (0-1)
            model_used: Modelo que foi usado
        """
        if not self.config.enable_learning:
            return

        if task_pattern not in self._history:
            self._history[task_pattern] = []

        self._history[task_pattern].append({
            "quality": quality,
            "model": model_used,
            "timestamp": time.time(),
        })

        # Mantém apenas últimos 20 resultados
        self._history[task_pattern] = self._history[task_pattern][-20:]

        # Atualiza cadeia de escalação se necessário
        self._update_escalation_chain(task_pattern, quality, model_used)

    def _update_escalation_chain(self, task_pattern: str, quality: float, model_used: str) -> None:
        """Atualiza a cadeia de escalação baseado em histórico."""
        if task_pattern not in self._history:
            return

        history = self._history[task_pattern]

        # Se últimos 5 resultados com Haiku tiveram qualidade >= 0.8
        haiku_results = [h for h in history[-5:] if h["model"] == "haiku"]
        if len(haiku_results) >= 3:
            avg_quality = sum(h["quality"] for h in haiku_results) / len(haiku_results)
            if avg_quality >= 0.8:
                log.debug(
                    f"Learning: Haiku works well for {task_pattern[:30]}... "
                    f"(avg quality: {avg_quality:.2f})"
                )


class LLMCascadeProvider:
    """
    Provedor de LLM para o CascadeExecutor.
    Usa provedores remotos (Claude, OpenAI).
    Modelos locais Ollama foram removidos.
    """

    def __init__(self, provider_type: str = "claude"):
        self.provider_type = provider_type

    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
    ) -> dict:
        """Executa chat com o modelo."""
        if self.provider_type == "claude":
            return await self._chat_claude(model, messages, stream)
        elif self.provider_type == "openai":
            return await self._chat_openai(model, messages, stream)
        else:
            raise ValueError(f"Unknown provider: {self.provider_type}")

    async def _chat_claude(self, model: str, messages: list[dict], stream: bool) -> dict:
        """Chat via Claude API."""
        import httpx

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        claude_url = "http://localhost:8080/api/llm/chat"

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(claude_url, json=payload)

                if response.status_code != 200:
                    raise Exception(f"Claude API error: {response.status_code}")

                data = response.json()
                output = data.get("output", "")

                tokens = data.get("tokens_used", len(output) // 4)

                return {
                    "output": output,
                    "tokens_used": tokens,
                    "model": model,
                }

            except httpx.ConnectError:
                raise Exception("Claude API not connected")

    async def _chat_openai(self, model: str, messages: list[dict], stream: bool) -> dict:
        """Chat via OpenAI API."""
        import httpx
        import os

        api_key = os.environ.get("OPENAI_API_KEY", "")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )

                if response.status_code != 200:
                    raise Exception(f"OpenAI error: {response.status_code}")

                data = response.json()
                output = data["choices"][0]["message"]["content"]

                usage = data.get("usage", {})
                tokens = (usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0))

                return {
                    "output": output,
                    "tokens_used": tokens,
                    "model": model,
                }

            except httpx.ConnectError:
                raise Exception("OpenAI not connected")


# =====================================================
# Singleton para uso global
# =====================================================

_cascade_executor: Optional[CascadeExecutor] = None


def get_cascade_executor() -> CascadeExecutor:
    """Retorna instância singleton do CascadeExecutor."""
    global _cascade_executor
    if _cascade_executor is None:
        _cascade_executor = CascadeExecutor()
    return _cascade_executor
