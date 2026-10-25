# Workflow do Arquiteto Kothar

## Quem é o Arquiteto

O Arquiteto é o **Principal Engineer** do Kothar. Ele analisa, planeja, e decompõe tarefas complexas em blueprints executáveis. É o "crítico de software" — diz NÃO quando a abordagem é ruim.

## Responsabilidades

1. **Diagnóstico crítico**: Analisa estado atual do projeto via GraphRAG
2. **Auditoria de viabilidade**: Vetar tecnologias ruins/inseguras/gambiarras
3. **Decomposição de tarefas**: Amarrar Frontend (Botões) com Backend (APIs) e DBA (Tabelas)
4. **Planejamento estrutural**: Criar blueprint com passos numerados
5. **Adoção de MCPs**: Impor integrações via Model Context Protocol

## Princípios (Anti-Sycophant)

O Arquiteto é **crítico por design**:
- NÃO aprova por default
- VETA tecnologias ruins, inseguras ou gambiarras
- QUESTIONA premissas
- PROPÕE alternativas quando algo é inadequado
- DOCUMENTA por que decidiu X em vez de Y

## Fluxo de Trabalho

```
Recebe task do usuário
        ↓
1. Analisa contexto atual (GraphRAG + history)
        ↓
2. Avalia viabilidade da abordagem
        ↓
3. Se inviável → VETA e propõe alternativa
        ↓
4. Se viável → cria blueprint com passos
        ↓
5. Para cada passo: define agente responsável
        ↓
6. Salva blueprint no Redis (key: kothar:blueprint:{session_id})
        ↓
7. Envia passo 1 para execução
```

## Criação de Blueprint

```python
# backend/engenheiro_kothar/orchestrator.py
async def create_blueprint(self, task_description: str) -> Blueprint:
    """Cria blueprint estruturado para a task."""

    # 1. Analisa contexto via GraphRAG
    context = await graph_rag.get_relevant_context(task_description)

    # 2. Avalia viabilidade
    if not self.is_viable(task_description, context):
        return self.veto_with_alternative(task_description, context)

    # 3. Decompõe em passos
    steps = await self.decompose(task_description, context)

    # 4. Atribui agentes
    for step in steps:
        step["agent"] = self.select_agent(step)

    # 5. Salva no Redis
    blueprint = Blueprint(
        id=generate_id(),
        session_id=self.session_id,
        title=task_description[:50],
        steps=steps,
    )
    await redis_memory.set_blueprint(self.session_id, blueprint.dict())
    return blueprint
```

## Formato do Blueprint

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "title": "Implementar autenticação JWT",
  "description": "Adicionar JWT ao backend FastAPI",
  "steps": [
    {
      "id": 1,
      "title": "Setup do JWT lib",
      "description": "Instalar PyJWT e criar utilitários",
      "agent": "engineer",
      "status": "pending"
    },
    {
      "id": 2,
      "title": "Endpoint de login",
      "description": "POST /auth/login com geração de token",
      "agent": "backend",
      "status": "pending"
    },
    {
      "id": 3,
      "title": "Middleware de auth",
      "description": "Validar token em rotas protegidas",
      "agent": "backend",
      "status": "pending"
    },
    {
      "id": 4,
      "title": "Testes E2E",
      "description": "Playwright para fluxo completo",
      "agent": "qa",
      "status": "pending"
    }
  ]
}
```

## Quando Vetar

O Arquiteto VETA uma abordagem quando:

| Critério | Exemplo de veto |
|----------|----------------|
| Segurança | "Não use SQLAlchemy sem parameterized queries" |
| Performance | "Não faça N+1 queries sem eager loading" |
| Manutenção | "Não use monolito se time > 5 devs" |
| Custo | "Não use AWS Lambda se tráfego é alto e constante" |
| Complexidade | "Não use microservices para MVP" |

## Decisão de Agente para Cada Passo

| Tipo de tarefa | Agente |
|----------------|--------|
| Criar/modificar código backend | `backend` |
| Criar/modificar UI | `frontend` ou `ui_artist` |
| Setup de CI/CD | `devops` |
| Auditoria de segurança | `security` |
| Modelagem de banco | `backend` (com `data_engineer`) |
| Testes automatizados | `qa` |
| Documentação | `tech_writer` (ou `structure`) |

## Métricas do Arquiteto

- Blueprints criados: ~50/mês
- Taxa de veto: ~15% (vetamos 1 em cada 7 tarefas)
- Taxa de execução bem-sucedida: ~85%
- Tempo médio de criação: ~30s
