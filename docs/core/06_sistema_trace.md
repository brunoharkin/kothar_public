# Sistema de Trace do Kothar

## O que é

O sistema de Trace do Kothar **registra 100% das operações** dos agentes — toda chamada de ferramenta, decisão, lock bloqueado, skill usada. É a "caixa preta" do sistema.

## Componentes

### 1. Trace Recorder
Localização: `backend/trace/trace_recorder.py`

Responsável por gravar cada operação em batch no SQLite/Postgres.

```python
class TraceRecorder:
    """Grava traces de operações dos agentes."""

    async def record(
        self,
        session_id: str,
        tool: str,
        input_data: dict,
        output_data: dict,
        duration_ms: int = None,
        tokens: dict = None,
    ) -> str:
        """Registra uma operação."""
        trace_id = generate_id()
        trace = Trace(
            id=trace_id,
            session_id=session_id,
            tool=tool,
            input=input_data,
            output=output_data,
            duration_ms=duration_ms,
            tokens_input=tokens.get("input", 0) if tokens else 0,
            tokens_output=tokens.get("output", 0) if tokens else 0,
        )
        await self.db.save(trace)
        return trace_id
```

### 2. Tipos de Trace

| Event Type | Quando ocorre |
|------------|---------------|
| `chat` | Mensagem entre user e assistant |
| `tool_call` | Agente chama uma ferramenta |
| `thinking` | Raciocínio interno (DeepSeek R1) |
| `rag_query` | Busca no RAG (HyDE Search) |
| `lock_blocked` | Lock bloqueou uma ação |
| `skill_used` | Skill cristalizada foi usada |
| `error` | Erro em qualquer operação |

### 3. Estrutura do Trace

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "timestamp": "2026-09-02T01:00:00Z",
  "event_type": "chat",
  "agent_name": "kothar-local-ai",
  "tool_name": "claude-sonnet",
  "tool_input": "Como organizar 3 projetos paralelos?",
  "tool_output": "Por dependências...",
  "duration_ms": 12500,
  "tokens_input": 486,
  "tokens_output": 38,
  "is_error": false,
  "metadata": {
    "rag_chunks_used": 3,
    "model": "gemma2:2b"
  }
}
```

## Visualização

A página `/trace` do frontend mostra:
- Timeline de eventos
- Detalhes de cada trace
- Métricas agregadas (tokens, tempo, taxa de erro)
- Filtros por agente, tipo, período

## Métricas Rastreadas

| Métrica | Descrição |
|---------|-----------|
| `total_traces` | Total de operações registradas |
| `avg_duration_ms` | Tempo médio por operação |
| `total_tokens` | Tokens consumidos (in + out) |
| `error_rate` | % de traces com erro |
| `top_tools` | Ferramentas mais usadas |
| `top_agents` | Agentes mais ativos |

## Hooks de Captura

Os traces são capturados via hooks em pontos críticos:

```python
# backend/hooks/post_tool_use.py
@trace_recorder.record(event_type="tool_call")
async def on_tool_use(tool_name: str, input_data: dict, output_data: dict):
    """Hook automático após qualquer uso de ferramenta."""
    pass
```

## Limpeza

Traces > 90 dias são arquivados (não deletados). Mantém últimos 30 dias "quentes" no Postgres.

## Por que é importante

1. **Debug**: Ver exatamente o que cada agente fez
2. **Auditoria**: Quem mudou o quê e quando
3. **Métricas**: Performance real do sistema
4. **Treinamento**: Dados reais para fine-tuning
5. **Compliance**: LGPD exige rastreabilidade
