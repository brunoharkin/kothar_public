# Skills Cristalizadas

## O que são

Skills cristalizadas são **conhecimento validado** que foi extraído de sessões reais e indexado no RAG para ser recuperado quando relevante. Diferente de documentação estática, skills representam **o que funcionou** na prática.

## Estrutura

Cada skill tem:
- **Conteúdo**: O conhecimento em si (snippet de código, decisão arquitetural, padrão)
- **Metadata**:
  - `source`: arquivo/sessão de origem
  - `created_at`: timestamp
  - `validated`: true/false (passou por revisão humana)
  - `tags`: list[str] para categorização

## Como cristalizar

Uma skill vira cristalizada quando:

1. **Validada na prática**: Apareceu em sessão real e resolveu o problema
2. **Reutilizável**: Pode ser aplicada em contextos similares
3. **Documentada**: Tem explicação clara de quando usar

```python
# backend/memory/semantic/chroma_client.py
async def add_skill(
    self,
    content: str,
    metadata: dict[str, Any] = None,
    collection: str = "kothar_skills"
) -> str:
    """Adiciona skill cristalizada ao RAG."""
    skill_id = generate_id()
    self.client.get_or_create_collection(collection).add(
        ids=[skill_id],
        documents=[content],
        metadatas={**(metadata or {}), "crystallized_at": now_iso()}
    )
    return skill_id
```

## Quando cristalizar

- Solução que funcionou para bug recorrente
- Padrão arquitetural validado em produção
- Otimização que melhorou performance significativamente
- Decisão de stack que se mostrou correta

## Quando NÃO cristalizar

- Solução one-off que não vai se repetir
- Decisão controversa que pode mudar
- Conhecimento já óbvio para a equipe

## Fluxo de Cristalização

```
Sessão resolvida com sucesso
        ↓
Engenheiro identifica padrão reutilizável
        ↓
session_archivist extrai skill
        ↓
Humano revisa e valida
        ↓
Skill indexada no ChromaDB
        ↓
Próximas sessões recuperam via RAG
```

## Categorias

| Categoria | Exemplo |
|-----------|---------|
| `bug_fix` | "Connection pool exhaustion em FastAPI: aumentar pool_size para 20" |
| `optimization` | "Query lenta em Postgres: adicionar índice em (user_id, created_at)" |
| `pattern` | "Para retry em API: usar exponential backoff com jitter" |
| `integration` | "Stripe webhook: validar assinatura com stripe.Webhook.construct_event" |
| `config` | "Para Django em produção: DEBUG=False, ALLOWED_HOSTS restrito" |

## Estatísticas

- Total de skills cristalizadas: ~150 (atual)
- Taxa de reuso: 78% (skill é recuperada em 78% das sessões relevantes)
- Skills obsoletas (>90 dias sem uso): 12 (candidatas a remoção)
