# HARNESS KOTHAR v4.0

## Visão Geral

O **Harness** é o sistema de controle de execução do Kothar. Ele garante que os agentes trabalhem de forma **controlada**, **observável** e **recuperável**.

```
┌─────────────────────────────────────────────────────────────────┐
│                         HARNESS KOTHAR                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    ORCHESTRATOR                           │   │
│  │  Recebe tarefa → Cria Blueprint → Salva no Redis          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               BLUEPRINT EXECUTOR                          │   │
│  │                                                           │   │
│  │  Para cada passo:                                         │   │
│  │  1. Valida dependências (StepValidator)                   │   │
│  │  2. Verifica locks (HyDE)                                │   │
│  │  3. Verifica circuit breaker (CircuitBreaker)            │   │
│  │  4. Executa com timeout e retry                          │   │
│  │  5. Salva checkpoint                                     │   │
│  │  6. Registra no trace                                   │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    TRACE (PostgreSQL)                     │   │
│  │  Eventos: flow_*, step_*, agent_*, thinking, decision   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               METRICS (Prometheus)                        │   │
│  │  sessions_total, steps_duration, lock_count, failures     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Circuit Breaker (`harness/circuit_breaker.py`)

Protege contra falhas em cascata.

```python
from backend.harness import CircuitBreakerRegistry, CircuitBreakerOpen

# Verifica se agente pode executar
cb = await CircuitBreakerRegistry.get("qa")
if not cb.is_available():
    raise CircuitBreakerOpen("QA está bloqueado após múltiplas falhas")
```

**Estados:**
- `CLOSED`: Funcionando normalmente
- `OPEN`: Bloqueado (múltiplas falhas)
- `HALF_OPEN`: Testando recuperação

**Configuração por agente:**
```python
AGENT_CONFIGS = {
    "qa": CircuitBreakerConfig(failures_threshold=2, open_duration_seconds=120),
    "security": CircuitBreakerConfig(failures_threshold=2),
    "frontend_engineer": CircuitBreakerConfig(failures_threshold=3),
}
```

### 2. Step Validator (`harness/step_validator.py`)

Valida se um passo pode ser executado.

```python
from backend.harness import StepValidator

validator = StepValidator(session_id, blueprint, locks)
validation = validator.validate(step)

if not validation.can_execute:
    print(f"Bloqueado: {validation.reason}")
    print(f"Dependências pendentes: {validation.blocked_by}")
```

**Validações:**
1. ✅ Passo já concluído
2. ✅ Passo em execução
3. ✅ Dependências atendidas
4. ✅ Locks não afetam

**Dependências padrão:**
```python
STEP_DEPENDENCIES = {
    "Planejamento": ["Diagnóstico"],
    "Execução Frontend": ["Auditoria de Passo (Supervisor)"],
    "QA": ["Auditoria de Segurança", "Execução Frontend"],
    "Compilação": ["QA"],
}
```

### 3. Checkpoint Manager (`harness/checkpoint.py`)

Salva estado para recuperação.

```python
from backend.harness import checkpoint_manager

# Salva checkpoint
checkpoint = await checkpoint_manager.save_checkpoint(
    session_id=session_id,
    step_id=step_id,
    step_title="Execução Backend",
    status="done",
    result={"files_created": 5},
)

# Recupera último checkpoint
last = await checkpoint_manager.get_last_checkpoint(session_id)

# Verifica se pode retomar
can_resume, reason = await checkpoint_manager.can_resume_from_checkpoint(session_id)
```

### 4. Blueprint Executor (`harness/blueprint_executor.py`)

Executor principal do fluxo.

```python
from backend.harness import blueprint_executor

result = await blueprint_executor.execute(
    session_id=session_id,
    task_handler=my_custom_handler,  # opcional
    task_context={"extra": "data"},
)

print(f"Status: {result.status}")  # completed, failed, partial
print(f"Concluídos: {result.completed_steps}/{result.total_steps}")
```

## API de Execução

### Fluxo Completo

```bash
# 1. Cria blueprint
curl -X POST http://localhost:8000/api/orchestrate/start \
  -d '{"task_description": "Criar página de login"}'

# 2. Executa blueprint
curl -X POST http://localhost:8000/api/orchestrate/{session_id}/execute

# 3. Monitora progresso
curl http://localhost:8000/api/flow/{session_id}

# 4. Executa em background
curl -X POST http://localhost:8000/api/orchestrate/{session_id}/execute/background
```

### Endpoints de Fluxo

| Endpoint | Descrição |
|----------|-----------|
| `GET /api/flow/{session_id}` | Status completo do fluxo |
| `GET /api/flow/{session_id}/timeline` | Timeline de eventos |
| `GET /api/flow/{session_id}/gantt` | Dados para Gantt |
| `GET /api/flow/{session_id}/checkpoints` | Histórico de checkpoints |
| `GET /api/flow/circuit-breakers` | Status dos circuit breakers |
| `POST /api/flow/circuit-breakers/{agent}/reset` | Reset circuit breaker |

## Eventos de Trace

### Tipos de Evento

| Evento | Descrição |
|--------|-----------|
| `flow_start` | Início da execução do blueprint |
| `flow_end` | Fim da execução |
| `step_start` | Início de um passo |
| `step_done` | Passo concluído |
| `step_failed` | Passo falhou |
| `step_locked` | Passo bloqueado (dep/lock) |
| `agent_start` | Início de agente |
| `agent_complete` | Agente concluído |
| `agent_retry` | Agente fazendo retry |
| `circuit_breaker` | Evento de circuit breaker |
| `checkpoint` | Checkpoint salvo |
| `thinking` | Pensamento do modelo (completo) |
| `decision` | Decisão estratégica |
| `lock_check` | Verificação de locks |

## Exemplo de Uso

```python
from backend.engenheiro_kothar import engenheiro_kothar
from backend.harness import blueprint_executor

async def main():
    # 1. Cria orquestração
    result = await engenheiro_kothar.orchestrate(
        task_description="Criar dashboard de métricas"
    )
    session_id = result["session_id"]

    # 2. Executa blueprint
    flow_result = await engenheiro_kothar.execute(session_id)

    print(f"Resultado: {flow_result.status}")
    for step_result in flow_result.step_results:
        print(f"  {step_result.step_title}: {step_result.status}")

    # 3. Completa sessão
    await engenheiro_kothar.complete_session(session_id)

# Ou com handler customizado:
async def my_handler(step, session_id, context):
    # Lógica customizada de execução
    return {"custom": "result"}

flow_result = await engenheiro_kothar.execute(session_id, task_handler=my_handler)
```

## Migrações

```bash
# Executar migração do FlowExecution
python -m backend.migrations.add_flow_execution
```

## Métricas Prometheus

```
kothar_flow_completed_total{session_id, status}
kothar_flow_duration_seconds{session_id}
kothar_step_duration_seconds{agent, step}
kothar_circuit_breaker_state{agent, state}
kothar_checkpoint_total{session_id, status}
```
