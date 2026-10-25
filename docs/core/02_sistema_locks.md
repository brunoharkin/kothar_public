# Sistema de Locks do Kothar

## O que é

O sistema de **Locks** do Kothar é um mecanismo de proteção que **marca padrões problemáticos já tentados** para evitar que agentes repitam erros conhecidos.

## Como funciona

1. **Detecção**: Quando um agente (especialmente o Engenheiro) tenta uma ação que falha, o sistema registra o padrão como lock
2. **Verificação**: Antes de cada nova ação, `search_locks()` consulta o ChromaDB por padrões similares
3. **Bloqueio**: Se match ≥ threshold, o agente é alertado e pode propor alternativa

## Implementação

Localização no código:
- `backend/memory/semantic/hyde_search.py:search_locks()`
- Storage: ChromaDB collection `kothar_locks`

```python
async def search_locks(self, query: str, n_results: int = 3) -> list[dict]:
    """Busca locks que podem bloquear a ação atual."""
    results = await self.chroma.search_locks(query, n_results)
    return [
        {
            "pattern": r["content"],
            "alternative": r["metadata"].get("alternative"),
            "created_at": r["metadata"].get("created_at"),
        }
        for r in results
    ]
```

## Quando criar um lock

- Tentou instalar `package==1.0` e quebrou → lock "não usar package 1.0"
- Tentou comando que corrompeu dados → lock "não rodar X sem backup"
- API externa mudou contrato → lock "API Y mudou, atualizar integração"

## Exemplo de uso

```python
# No engineer_agent.py
locks = await self.check_locks(f"{step_title} {code_action}")
if locks:
    lock_alternatives = [l["document"] for l in locks[:2]]
    await context_compressor.add_decision(
        self.session_id,
        f"Contornando lock em '{step_title}': {lock_alternatives[0][:80]}"
    )
```

## Métricas

- **Lock hits**: Quantas vezes o sistema bloqueou uma ação ruim
- **Lock bypasses**: Quantas vezes o lock foi ignorado conscientemente
- **Taxa de prevenção**: locks_bloqueados / acoes_bloqueaveis_total

## Limpeza

Locks antigos (> 30 dias) devem ser revisados mensalmente. Lock obsoleto vira ruído.
