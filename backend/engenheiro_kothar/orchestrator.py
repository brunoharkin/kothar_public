"""
=============================================================
 KOTHAR v4.0 — Engenheiro Kothar (Orchestrador Principal)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 O Maestro do Orquestro Digital.
 Recebe tarefas, cria blueprints, delega para especialistas,
 monitora progresso, compila resultado e cristaliza Skills.

 AGORA COM EXECUÇÃO REAL VIA BlueprintExecutor.
"""

import uuid
from typing import Any, Callable, Optional

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.core.task_classifier import classify_task, get_optimal_model, TaskComplexity
from backend.core.context_compressor import compress_for_model
from backend.core.cascade_executor import get_cascade_executor
from backend.harness.blueprint_executor import blueprint_executor, FlowResult
from backend.memory.cache.redis_client import RedisMemory
from backend.memory.graph.graph_rag import graph_rag
from backend.memory.semantic.chroma_client import chroma_memory
from backend.memory.semantic.hyde_search import HyDESearch
from backend.memory.vault.vault_reader import vault_reader
from backend.trace.models import Blueprint
from backend.trace.session_compiler import session_compiler
from backend.trace.trace_recorder import trace_recorder
from backend.engenheiro_kothar.contracts import (
    transition_contract,
    validate_blueprint_steps,
)

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
            "status": "orchestrating",
            "message": (
                f"Sessão {session_id[:8]} iniciada. "
                f"Blueprint com {len(blueprint.get('steps', []))} passos criado. "
                f"Agentes prontos para execução."
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

        # Executa via harness
        result = await blueprint_executor.execute(
            session_id=session_id,
            task_handler=task_handler,
            task_context={"session_id": session_id},
        )

        log.info(
            f"✅ Execução concluída: {result.status}",
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
            decision="Compilando sessão e gravando no Cofre",
        )

        # Imposição do Bloqueio de QA
        blueprint = await self.redis.get_blueprint(session_id)
        if blueprint:
            qa_steps = [s for s in blueprint.get("steps", []) if s.get("agent") == "qa"]
            if qa_steps:
                last_qa = qa_steps[-1]
                if last_qa.get("status") != "done":
                    log.error("Mandato de QA Violado. Entrega bloqueada.", session_id=session_id)
                    raise ValueError("Bloqueio de Arquitetura: QA Supremo não aprovou a entrega. Os testes E2E falharam ou foram ignorados.")

        # Compila sessão (traces → Vault + análise de erros)
        compilation = await session_compiler.compile(session_id)

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
                            "id": l.get("id"),
                            "pattern": l.get("metadata", {}).get("pattern"),
                            "similarity": l.get("similarity"),
                        }
                        for l in locks
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
    ) -> dict[str, Any]:
        """
        Cria o Blueprint da tarefa.
        Em produção: usa LLM para decompor a tarefa em passos.
        Nesta versão: blueprint estrutural baseado em keywords.
        """
        blueprint_id = str(uuid.uuid4())

        # Decomposição baseada em palavras-chave (determinística)
        steps = self._decompose_task(task_description)

        steps = validate_blueprint_steps(steps)
        blueprint = {
            "id": blueprint_id,
            "session_id": session_id,
            "title": task_description[:200],
            "description": task_description,
            "steps": steps,
            "status": "active",
            "assigned_agent": "engenheiro_kothar",
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
        """
        Decompõe a tarefa em passos baseado em padrões.
        Versão determinística — substituir por LLM em produção.
        """
        base_steps = [
            {"id": 0, "title": "Triagem e Recepção (Prompt Enhancer)", "description": "Lê a instrução curta e gera Dossiê ou devolve Bypass", "status": "pending", "agent": "triage_agent", "reasoning_effort": "low"},
            {"id": 1, "title": "Diagnóstico", "description": "Analisar o estado atual", "status": "pending", "agent": "architect", "reasoning_effort": "high"},
            {"id": 2, "title": "Planejamento", "description": "Criar plano de execução detalhado", "status": "pending", "agent": "architect", "reasoning_effort": "high"},
            {"id": 2.5, "title": "Relational Experience Mapping", "description": "Aplicar Filosofia MuMu-Pattern (Foreshadowing e Intimidade) no planejamento da experiência final", "status": "pending", "agent": "architect", "reasoning_effort": "medium"},
            {"id": 3, "title": "Verificação de Locks", "description": "Verificar travas e erros conhecidos", "status": "pending", "agent": "engenheiro_kothar", "reasoning_effort": "low"},
            {"id": 4, "title": "Busca de Skills", "description": "Buscar skills relevantes no RAG", "status": "pending", "agent": "engenheiro_kothar", "reasoning_effort": "low"},
            {"id": 4.5, "title": "Estrutura (Scaffold) & Portable Design", "description": "Gerar o arquivo DESIGN.md na raiz (Portable Design System) e definir separação em pastas", "status": "pending", "agent": "structure_agent", "reasoning_effort": "medium"},
            {"id": 4.6, "title": "Auditoria de Passo (Supervisor)", "description": "Auditar entrega do Scaffold", "status": "pending", "agent": "supervisor_agent", "reasoning_effort": "medium"},
            {"id": 5, "title": "Execução Frontend", "description": f"Codificar Interface: {task[:50]}", "status": "pending", "agent": "frontend_engineer", "reasoning_effort": "medium"},
            {"id": 5.01, "title": "Auditoria de Passo (Supervisor)", "description": "Auditar entrega do Frontend", "status": "pending", "agent": "supervisor_agent", "reasoning_effort": "medium"},
            {"id": 5.1, "title": "Execução Backend", "description": f"Codificar Lógica e Scripts Locais: {task[:50]}", "status": "pending", "agent": "backend_engineer", "reasoning_effort": "high"},
            {"id": 5.11, "title": "Auditoria de Passo (Supervisor)", "description": "Auditar entrega do Backend", "status": "pending", "agent": "supervisor_agent", "reasoning_effort": "high"},
            {"id": 5.2, "title": "Revisão de Código (Clean Code)", "description": "Inspecionar erros de sintaxe, imports falsos e spaghetti code", "status": "pending", "agent": "code_reviewer", "reasoning_effort": "high"},
            {"id": 6, "title": "Auditoria de Segurança", "description": "Verificar chaves expostas e má práticas", "status": "pending", "agent": "security", "reasoning_effort": "high"},
            {"id": 7, "title": "QA", "description": "Validar resultado", "status": "pending", "agent": "qa", "reasoning_effort": "medium"},
            {"id": 8, "title": "Compilação", "description": "Gravar relatório no Cofre", "status": "pending", "agent": "engenheiro_kothar", "reasoning_effort": "low"},
        ]

        task_lower = task.lower()
        
        # 1. Modo Ofensivo (Teste de Invasão / DAST)
        if any(kw in task_lower for kw in ["teste", "testar", "invasao", "invazao", "invadir", "penetration", "url", "varredura"]):
            # Se for explicitamente um teste de invasão, pula o desenvolvimento e foca no Security Agent
            return [
                {"id": 1, "title": "Diagnóstico de Alvo", "description": "Mapear alvo da invasão", "status": "pending", "agent": "architect"},
                {"id": 2, "title": "Engenharia de Invasão (DAST)", "description": f"Executar Arsenal Nuclei contra: {task[:100]}", "status": "pending", "agent": "security"},
                {"id": 3, "title": "Compilação do Ataque", "description": "Gravar falhas encontradas no Cofre", "status": "pending", "agent": "engenheiro_kothar"},
            ]

        # 2. A Sinfonia do Frontend (Workflow Mestre)
        if any(kw in task_lower for kw in ["página", "pagina", "interface", "frontend", "ui", "componente", "site"]):
            # Insere Copywriter e Artista UI antes da Execução (que está no index 4)
            base_steps.insert(4, {
                "id": 4.1, "title": "Copywriting (PAS/AIDA)",
                "description": "Criar textos persuasivos e CTAs",
                "status": "pending", "agent": "copywriter"
            })
            base_steps.insert(5, {
                "id": 4.2, "title": "Diretrizes WebGL e Design",
                "description": "Definir efeitos visuais High-End",
                "status": "pending", "agent": "ui_artist"
            })

        # 2.5. A Sinfonia Code-to-Video (Redes Sociais / Remotion)
        if any(kw in task_lower for kw in ["vídeo", "video", "reel", "tiktok", "youtube", "criativo ads", "motion"]):
            base_steps.insert(4, {
                "id": 4.3, "title": "Copywriting de Vídeo & Roteiro",
                "description": "Criar roteiro para o vídeo focando no gancho inicial",
                "status": "pending", "agent": "copywriter"
            })
            
            # Se for vídeo com "apresentador", adicionamos o pipeline do PersonaLive
            if any(kw in task_lower for kw in ["apresentador", "porta-voz", "avatar", "humano", "falando", "talking head", "narrador"]):
                base_steps.insert(5, {
                    "id": 4.31, "title": "Geração de Áudio (TTS / Voice Specialist)",
                    "description": "Transformar o roteiro aprovado em arquivo de áudio narrado",
                    "status": "pending", "agent": "voice_specialist"
                })
                base_steps.insert(6, {
                    "id": 4.32, "title": "Animação de Avatar (PersonaLive / Fila Resiliente)",
                    "description": "Renderizar vídeo do Avatar sincronizado com o áudio (Lip-Sync). Aguardar GPU livre, se necessário.",
                    "status": "pending", "agent": "avatar_video_specialist"
                })
                # O Remotion vira o passo 7 (indice 7)
                base_steps.insert(7, {
                    "id": 4.4, "title": "Programação de Vídeo (Remotion)",
                    "description": "Envelopar o MP4 do Avatar gerado na composição final do Remotion",
                    "status": "pending", "agent": "social_media_video_specialist"
                })
            else:
                base_steps.insert(5, {
                    "id": 4.4, "title": "Programação de Vídeo (Remotion)",
                    "description": "Estruturar o projeto React Remotion com as animações baseadas no roteiro",
                    "status": "pending", "agent": "social_media_video_specialist"
                })

        # 3. Engenharia de Dados Suprema (DBA)
        # Injeta o DBA logo após o Arquiteto/Planejamento se envolver banco de dados
        if any(kw in task_lower for kw in ["banco de dados", "bd", "sql", "nosql", "dados", "database", "postgres", "redis", "neo4j", "schema", "tabela"]):
            base_steps.insert(2, {
                "id": 2.5, "title": "Modelagem de Dados (DBA)",
                "description": "Ditar arquitetura do BD e aplicar regra DUMB_FRONTEND",
                "status": "pending", "agent": "data_engineer"
            })

        # 4. LGPD & DPO (Auditor de Compliance)
        if any(kw in task_lower for kw in ["usuário", "usuario", "cliente", "cadastro", "login", "senha", "dados", "banco", "perfil", "lgpd", "pii"]):
            exec_index = next((i for i, s in enumerate(base_steps) if s["agent"] == "engineer"), -1)
            if exec_index != -1:
                base_steps.insert(exec_index + 1, {
                    "id": 5.5, "title": "Auditoria de Compliance (LGPD)",
                    "description": "Verificar criptografia de PII e hash Argon2 (Mandato ENCRYPT_PII)",
                    "status": "pending", "agent": "dpo"
                })

        # Adiciona passo de infra se for tarefa de deploy/docker
        if any(kw in task_lower for kw in ["docker", "deploy", "infra", "porta", "container"]):
            base_steps.insert(len(base_steps) - 1, {
                "id": 7.5, "title": "Containerização & Deploy",
                "description": "Aplicar CI/CD e empacotar (Mandamento #1)",
                "status": "pending", "agent": "devops"
            })

        return base_steps

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
