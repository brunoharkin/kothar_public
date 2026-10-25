"""
=============================================================
 KOTHAR v4.0 — Engenheiro Kothar (Orchestrador Principal)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 O Maestro do Orquestro Digital.
 Recebe tarefas, cria blueprints, delega para especialistas,
 monitora progresso, compila resultado e cristaliza Skills.

 Execução via BlueprintExecutor exige handler real; ausência bloqueia o fluxo.
"""

import uuid
from collections.abc import Callable
from typing import Any

from backend.contracts.security import approved_result, security_coverage_approved
from backend.contracts.task_execution import TaskExecutionPlan
from backend.core.cascade_executor import get_cascade_executor
from backend.core.context_compressor import compress_for_model
from backend.core.logger import get_logger
from backend.core.task_classifier import classify_task
from backend.engenheiro_kothar.contracts import (
    transition_contract,
    validate_blueprint_steps,
)
from backend.engenheiro_kothar.routing import TaskRequirements, route_task
from backend.engenheiro_kothar.task_executor import prepare_task_executor
from backend.harness.blueprint_executor import FlowResult, blueprint_executor
from backend.memory.cache.redis_client import RedisMemory
from backend.memory.graph.graph_rag import graph_rag
from backend.memory.semantic.chroma_client import chroma_memory
from backend.memory.semantic.hyde_search import HyDESearch
from backend.memory.vault.vault_reader import vault_reader
from backend.trace.session_compiler import session_compiler
from backend.trace.trace_recorder import trace_recorder

log = get_logger("engenheiro_kothar.orchestrator")


class EngenheiroKothar:
    """
    O Orchestrador Principal — O Engenheiro Kothar.
    
    Fluxo de orquestração:
    1. Recebe tarefa do usuário
    2. Cria Blueprint (plano de execução)
    3. Verifica Locks e Skills relevantes
    4. Delega para agentes especializados
    5. Monitora progresso via Redis
    6. Ao fim: compila sessão → Cofre + Travas
    
    Mandamentos respeitados:
    - #1: Verifica portas antes de subir serviços
    - #2: Consulta Skills antes de inventar soluções
    - #3: Handoff explícito entre agentes
    - #4: 3 erros → para e escala para humano
    - #5: Contexto base (blueprint) nunca modificado mid-task
    """

    def __init__(self):
        self.redis = RedisMemory()
        self.cascade = get_cascade_executor()

    async def orchestrate(
        self,
        task_description: str,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        requirements: TaskRequirements | dict | None = None,
        execution_plan: TaskExecutionPlan | dict | None = None,
    ) -> dict[str, Any]:
        """
        Ponto de entrada principal do Engenheiro Kothar.
        Orquestra uma tarefa do início ao fim.

        FLUXO:
        1. Cria sessão e classifica tarefa
        2. Cria Blueprint
        3. Salva no Redis
        4. RETORNA - a execução real é feita via execute()
        """
        # Falha cedo se o contrato de transições estiver inválido.
        transition_contract()

        # Inicia sessão se não fornecida
        if not session_id:
            session_id = await trace_recorder.start_session(
                agent_name="engenheiro_kothar",
                llm_model="orchestrator",
                task_summary=task_description[:200],
                metadata=metadata or {},
            )

        log.info(
            "🎵 Engenheiro Kothar — Orquestração iniciada",
            session_id=session_id,
            task=task_description[:80],
        )

        # =====================================================
        # MULTI-MODEL: Classifica tarefa ANTES de qualquer coisa
        # =====================================================
        classification = classify_task(task_description)

        log.info(
            f"🎯 Tarefa classificada: {classification['complexity'].value} / {classification['type'].value}",
            session_id=session_id,
            preferred_model=classification['preferred_model'],
            estimated_tokens=classification['estimated_tokens'],
        )

        # Armazena classificação para uso posterior
        context_data = {
            "tarefa_atual": task_description,
            "status": "planejando",
            "classification": {
                "complexity": classification['complexity'].value,
                "type": classification['type'].value,
                "preferred_model": classification['preferred_model'],
                "context_needed": classification['context_needed'],
                "reason": classification['reason'],
            },
        }

        # Registra sessão no GraphRAG
        await graph_rag.register_session(
            session_id=session_id,
            agent_name="engenheiro_kothar",
        )

        # 1. VERIFICAÇÃO DE LOCKS - Verifica travas antes de qualquer ação
        await self._check_locks(session_id, task_description)

        # 2. COFRE - Busca sessões similares para contexto
        await self._vault_search(session_id, task_description)

        # 3. Diagnóstico — contexto inicial
        await trace_recorder.record_decision(
            session_id=session_id,
            agent_name="engenheiro_kothar",
            decision="Iniciando diagnóstico da tarefa",
            reasoning=task_description,
        )

        # 2. Cria blueprint da tarefa
        blueprint = await self._create_blueprint(
            session_id=session_id,
            task_description=task_description,
            requirements=requirements,
            execution_plan=execution_plan,
        )

        # 3. Salva blueprint e contexto no Redis (agentes vão ler daqui)
        await self.redis.set_blueprint(session_id, blueprint)
        await self.redis.set_context(session_id, context_data)

        log.info(
            "Blueprint criado",
            session_id=session_id,
            steps_count=len(blueprint.get("steps", [])),
        )

        return {
            "session_id": session_id,
            "blueprint": blueprint,
            "status": "blocked" if blueprint["routing"]["blockers"] else "orchestrating",
            "routing": blueprint["routing"],
            "message": (
                f"Sessão {session_id[:8]} iniciada. "
                f"Blueprint com {len(blueprint.get('steps', []))} passos criado. "
                f"Execução depende de operações tipadas e workspace configurado."
            ),
        }

    async def execute(
        self,
        session_id: str,
        task_handler: Callable = None,
    ) -> FlowResult:
        """
        Executa o blueprint completo via BlueprintExecutor.

        Args:
            session_id: ID da sessão (deve ter blueprint criado via orchestrate())
            task_handler: Função customizada para executar passos (opcional)

        Returns:
            FlowResult com resultado da execução completa
        """
        log.info("🚀 Iniciando execução do blueprint", session_id=session_id)

        # Valida que existe blueprint
        blueprint = await self.redis.get_blueprint(session_id)
        if not blueprint:
            raise ValueError(f"Blueprint não encontrado para sessão {session_id}")

        if task_handler is None:
            task_handler, blockers = prepare_task_executor(blueprint)
            if blockers:
                blueprint["execution_status"] = "blocked"
                blueprint["execution_error"] = "; ".join(blockers)
                blueprint["production_ready"] = False
                await self.redis.set_blueprint(session_id, blueprint)
                return FlowResult(
                    session_id=session_id, status="blocked",
                    total_steps=len(blueprint.get("steps", [])), completed_steps=0,
                    failed_steps=0, skipped_steps=0, error="; ".join(blockers),
                )

        # Executa via harness
        result = await blueprint_executor.execute(
            session_id=session_id,
            task_handler=task_handler,
            task_context={"session_id": session_id},
        )

        # Preserva os passos atualizados pelo executor ao registrar a situação final.
        current_blueprint = await self.redis.get_blueprint(session_id)
        if current_blueprint:
            current_blueprint["execution_status"] = result.status
            current_blueprint["execution_error"] = result.error
            current_blueprint["production_ready"] = False
            await self.redis.set_blueprint(session_id, current_blueprint)

        log.info(
            f"Execução retornou: {result.status}",
            session_id=session_id,
            completed=result.completed_steps,
            failed=result.failed_steps,
        )

        return result

    async def complete_session(self, session_id: str) -> dict[str, Any]:
        """
        Finaliza a orquestração: compila sessão, grava Cofre, analisa travas.
        """
        log.info("Finalizando orquestração", session_id=session_id)

        await trace_recorder.record_decision(
            session_id=session_id,
            agent_name="engenheiro_kothar",
            decision="Verificando condições de finalização da sessão",
        )

        # Imposição do Bloqueio de QA
        blueprint = await self.redis.get_blueprint(session_id)
        steps = blueprint.get("steps") if isinstance(blueprint, dict) else None
        if not isinstance(steps, list) or not steps or any(
            not isinstance(step, dict) or step.get("status") != "done" for step in steps
        ):
            raise ValueError("Entrega bloqueada: blueprint ausente, inválido ou incompleto.")
        security_steps = [step for step in steps if step.get("agent") == "security"]
        qa_steps = [step for step in steps if step.get("agent") == "qa"]
        if not security_steps or any(
            not security_coverage_approved(step.get("result")) for step in security_steps
        ):
            raise ValueError("Entrega bloqueada: segurança sem aprovação e cobertura verificáveis.")
        if not qa_steps or any(
            not approved_result(step.get("result"), "passed") for step in qa_steps
        ):
            raise ValueError("Entrega bloqueada: QA sem aprovação verificável.")

        # Compila sessão (traces → Vault + análise de erros)
        compilation = await session_compiler.compile(session_id)
        if compilation.get("error"):
            raise ValueError("Entrega bloqueada: falha na compilação da sessão.")
        compilation["production_ready"] = False
        compilation["limitations"] = [
            "Scanner de credenciais e QA não substituem gate de produção e revisão independente."
        ]

        # Encerra sessão no trace
        await trace_recorder.end_session(
            session_id=session_id,
            status="completed",
            tokens_input=compilation.get("tokens_total", 0) // 2,
            tokens_output=compilation.get("tokens_total", 0) // 2,
        )

        # Limpa cache da sessão
        await self.redis.delete_session(session_id)

        log.info(
            "✅ Orquestração concluída",
            session_id=session_id,
            vault_report=compilation.get("vault_report"),
        )
        return compilation

    async def _vault_search(self, session_id: str, task_description: str) -> None:
        """
        Busca sessões similares no Cofre para contexto de longo prazo.
        Executado no início da orquestração.
        """
        try:
            context = vault_reader.get_session_context(task_description)
            sessions_found = context.get("sessions_found", 0)
            similar = context.get("similar_sessions", [])

            if sessions_found > 0:
                log.info(
                    f"Encontradas {sessions_found} sessões similares no Cofre",
                    session_id=session_id,
                )
                await trace_recorder.record(
                    session_id=session_id,
                    event_type="vault_search",
                    agent_name="engenheiro_kothar",
                    content=f"Vault encontrou {sessions_found} sessões similares",
                    tool_name="vault_reader",
                    tool_input={"task": task_description},
                    tool_output={
                        "sessions_found": sessions_found,
                        "similar": [
                            {"name": s.get("name"), "date": s.get("date"), "snippet": s.get("snippet", "")[:100]}
                            for s in similar[:3]
                        ],
                    },
                    metadata={"task": task_description[:200], "count": sessions_found},
                )
            else:
                await trace_recorder.record(
                    session_id=session_id,
                    event_type="vault_search",
                    agent_name="engenheiro_kothar",
                    content="Nenhuma sessão similar encontrada no Cofre",
                    tool_name="vault_reader",
                    tool_input={"task": task_description},
                    tool_output={"sessions_found": 0},
                )
        except Exception as e:
            log.debug(f"Vault search falhou (não bloqueia): {e}")

    async def _check_locks(self, session_id: str, task_description: str) -> None:
        """
        Verifica locks antes de iniciar a orquestração.
        Se houver travas, registra no trace para que os agentes as evitem.
        """
        hyde = HyDESearch(chroma_memory)
        locks = await hyde.search_locks(task_description)

        if locks:
            log.warn(
                f"⛔ {len(locks)} trava(s) detectada(s) para esta tarefa",
                session_id=session_id,
                lock_count=len(locks),
            )

            # Registra no trace para visibilidade completa
            await trace_recorder.record(
                session_id=session_id,
                event_type="locks_found",
                agent_name="engenheiro_kothar",
                content=f"⛔ {len(locks)} trava(s) detectada(s) antes de iniciar",
                tool_name="lock_check",
                tool_input={"task": task_description},
                tool_output={
                    "locks": [
                        {
                            "id": lock.get("id"),
                            "pattern": lock.get("metadata", {}).get("pattern"),
                            "similarity": lock.get("similarity"),
                        }
                        for lock in locks
                    ]
                },
                metadata={"lock_count": len(locks), "task": task_description[:200]},
            )
        else:
            await trace_recorder.record(
                session_id=session_id,
                event_type="locks_check",
                agent_name="engenheiro_kothar",
                content="Nenhuma trava detectada para esta tarefa",
                tool_name="lock_check",
                tool_input={"task": task_description},
                tool_output={"locks_found": 0},
            )

    async def _create_blueprint(
        self,
        session_id: str,
        task_description: str,
        requirements: TaskRequirements | dict | None = None,
        execution_plan: TaskExecutionPlan | dict | None = None,
    ) -> dict[str, Any]:
        """
        Cria o Blueprint da tarefa.
        O mapa declara agentes, skills, capacidades e dependências necessárias.
        """
        blueprint_id = str(uuid.uuid4())

        routing = route_task(task_description, requirements)
        plan = execution_plan if isinstance(execution_plan, TaskExecutionPlan) else TaskExecutionPlan.model_validate(execution_plan or {})
        steps = routing["steps"]

        steps = validate_blueprint_steps(steps)
        blueprint = {
            "id": blueprint_id,
            "session_id": session_id,
            "title": task_description[:200],
            "description": task_description,
            "steps": steps,
            "status": "active",
            "assigned_agent": "engenheiro_kothar",
            "routing": routing,
            "execution_plan": plan.model_dump(),
            "execution_status": "blocked" if routing["blockers"] else "pending",
            "execution_error": "; ".join(routing["blockers"]) or None,
            "production_ready": False,
        }

        await trace_recorder.record(
            session_id=session_id,
            event_type="blueprint_created",
            agent_name="engenheiro_kothar",
            content=f"Blueprint '{task_description[:60]}' com {len(steps)} passos",
            tool_name="blueprint_manager",
            tool_output={"blueprint_id": blueprint_id, "steps": len(steps)},
        )

        return blueprint

    @staticmethod
    def _decompose_task(task: str) -> list[dict[str, Any]]:
        """Compatibilidade: a fonte de decomposição é o mapa de necessidades."""
        return route_task(task)["steps"]

    async def get_session_status(self, session_id: str) -> dict[str, Any]:
        """Retorna status atual da sessão via Redis."""
        blueprint = await self.redis.get_blueprint(session_id)
        context = await self.redis.get_context(session_id)

        if not blueprint:
            return {"session_id": session_id, "status": "not_found"}

        completed = sum(1 for s in blueprint.get("steps", []) if s.get("status") == "done")
        total = len(blueprint.get("steps", []))

        return {
            "session_id": session_id,
            "context": context,
            "status": blueprint.get("execution_status", "pending"),
            "error": blueprint.get("execution_error"),
            "production_ready": False,
            "progress": f"{completed}/{total}",
            "progress_pct": round(completed / total * 100) if total > 0 else 0,
            "blueprint_id": blueprint.get("id"),
            "current_step": next(
                (s for s in blueprint.get("steps", []) if s.get("status") == "in_progress"),
                None,
            ),
        }

    async def handle_agent_failure(self, session_id: str, failed_agent: str, error_report: dict) -> bool:
        """
        Gatilho do Loop de Rejeição. Se o QA E2E falhar, o orquestrador
        injeta uma nova tarefa de Correção para o Engenheiro, forçando o conserto.
        Limita a 3 tentativas para evitar loop infinito.
        """
        blueprint = await self.redis.get_blueprint(session_id)
        if not blueprint:
            return False

        # Conta quantas vezes já falhou (limite de 3 tentativas)
        retries = sum(1 for s in blueprint.get("steps", []) if "Correção E2E" in s.get("title", ""))
        if retries >= 3:
            log.error("Limite de 3 tentativas de QA atingido. Falha crítica.", session_id=session_id)
            return False

        if failed_agent == "qa":
            log.warn("QA Falhou. Injetando Correção no Blueprint.", session_id=session_id)
            
            # Adiciona a Correção e o Re-Teste no final da fila pendente
            steps = blueprint.get("steps", [])
            new_exec = {
                "id": len(steps) + 1, 
                "title": f"Correção E2E ({retries + 1}/3)",
                "description": f"Consertar erro reportado pelo QA: {error_report.get('error')}",
                "status": "pending", 
                "agent": "engineer",
                "logs": error_report.get("console", [])
            }
            new_qa = {
                "id": len(steps) + 2, 
                "title": f"Re-Teste E2E ({retries + 1}/3)",
                "description": "Rodar bateria de testes E2E novamente",
                "status": "pending", 
                "agent": "qa"
            }
            
            steps.extend([new_exec, new_qa])
            blueprint["steps"] = steps
            await self.redis.set_blueprint(session_id, blueprint)
            
            await trace_recorder.record(
                session_id=session_id,
                event_type="orchestrator_loop",
                agent_name="engenheiro_kothar",
                content=f"Loop de Rejeição ativado (Tentativa {retries + 1}). QA reportou falha.",
                tool_name="loop_handler"
            )
            return True
        return False

    # =====================================================
    # MULTI-MODEL: Execução com modelo ideal
    # =====================================================

    async def execute_step_with_model(
        self,
        step: dict,
        session_id: str,
        system_prompt: str = "",
        rag_chunks: list[str] = None,
        chunk_sources: list[str] = None,
    ) -> dict[str, Any]:
        """
        Executa um passo do blueprint com o modelo IDEAL.
        Substitui a execução direta por modelo fixo.

        Fluxo:
        1. Classifica o passo
        2. Comprime contexto para o modelo
        3. Executa com cascade executor
        4. Registra resultado e aprende
        """
        step_title = step.get("title", "")
        step_description = step.get("description", "")
        combined_task = f"{step_title}. {step_description}"

        # 1. Classifica o passo
        classification = classify_task(combined_task)

        # 2. Seleciona modelo (pode ser forçado pelo agente)
        model = step.get("forced_model") or classification["preferred_model"]

        log.info(
            f"Executing step with {model}: {step_title[:50]}",
            session_id=session_id,
            model=model,
            complexity=classification["complexity"].value,
        )

        # 3. Comprime contexto para o modelo
        compressed = compress_for_model(
            classification=classification,
            full_system=system_prompt,
            rag_chunks=rag_chunks or [],
            chunk_sources=chunk_sources or [],
        )

        # 4. Executa com cascade
        result = await self.cascade.execute(
            task=combined_task,
            system_prompt=compressed["system_prompt"],
            complexity=classification["complexity"].value,
            rag_chunks=compressed["rag_chunks"],
            chunk_sources=compressed["chunk_sources"],
            initial_model=model,
        )

        # 5. Registra no trace
        await trace_recorder.record(
            session_id=session_id,
            event_type="step_executed",
            agent_name=step.get("agent", "unknown"),
            content=f"Executado com {result.model_used} "
                    f"(escalou: {result.escalated}, quality: {result.quality_score:.2f})",
            metadata={
                "step_id": step.get("id"),
                "model": result.model_used,
                "tokens": result.tokens_used,
                "quality": result.quality_score,
                "duration_ms": result.duration_ms,
                "escalation_count": result.escalation_count,
            }
        )

        # 6. Aprende do resultado
        self.cascade.learn_from_result(
            task_pattern=combined_task[:50],
            quality=result.quality_score,
            model_used=result.model_used,
        )

        return {
            "success": result.success,
            "output": result.output,
            "model_used": result.model_used,
            "tokens_used": result.tokens_used,
            "escalated": result.escalated,
            "escalation_count": result.escalation_count,
            "quality_score": result.quality_score,
            "duration_ms": result.duration_ms,
        }

    def get_recommended_model(self, task: str) -> dict[str, Any]:
        """
        Retorna modelo recomendado para uma tarefa (sem executar).
        Útil para preview no frontend.
        """
        classification = classify_task(task)

        return {
            "model": classification["preferred_model"],
            "complexity": classification["complexity"].value,
            "type": classification["type"].value,
            "reason": classification["reason"],
            "estimated_tokens": classification["estimated_tokens"],
            "context_needed": classification["context_needed"],
        }


# Instância singleton
engenheiro_kothar = EngenheiroKothar()
