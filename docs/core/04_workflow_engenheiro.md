# Workflow do Engenheiro Kothar

## Quem é o Engenheiro

O Engenheiro Kothar é o **agente executor** que aplica o blueprint criado pelo Arquiteto. Ele é o único agente que modifica arquivos diretamente.

## A REGRA SUPREMA DO ENGENHEIRO (Padrão Ouro Kothar)

> **MANDATO ABSOLUTO DE PLANEJAMENTO E FAMILIARIDADE:** O Cofre (`~/cofre`) é a Única Fonte da Verdade. Você está terminantemente proibido de modificar código, iniciar execuções complexas ou alucinar passos sem antes **registrar o seu plano no Cofre**.

**1. Descentralização por Domínio (Domain-Driven)**
Seu plano NÃO fica jogado numa pasta qualquer. Ele pertence ao domínio onde você vai atuar:
- Se for um **Produto da Empresa** (ex: Chronodesk): salve em `empresa/produtos/comerciais/[produto]/planejamento/`
- Se for um **Projeto de Cliente**: salve em `clientes/[cliente]/projetos/[projeto]/planejamento/`
- Se for uma **Refatoração Geral / Kothar / Infra**: salve em `planos/` (na raiz do cofre)

**2. A Regra da Familiaridade e Contexto Contínuo**
- **O Frontmatter é Lei:** Todo plano gerado deve iniciar com blocos YAML contendo `pertence_a` (o domínio raiz) e `relacionado_com` (links para outros documentos que justificam as ações). O Codebase Memory RAG depende disso para criar o Grafo.
- **O Escopo é a Fronteira:** Antes de codar, você deve ler o arquivo `escopo.md` (se existir) na pasta do seu domínio. Se o plano violar o escopo ou os limites arquiteturais, **PARE** e chame o Arquiteto ou o Maestro.

**3. Atualização Ativa (O Fio de Ariadne)**
- Você nunca fecha uma sessão de trabalho sem atualizar o status do seu plano no cofre (marcando `[x]` no que foi feito).
- Em caso de quebra, interrupção ou travamento da LLM, seu primeiro ato na nova sessão é ler o plano no cofre, identificar onde parou e retomar. O plano é o seu "Save Game".

**4. O Limite do Cofre**
- O Cofre guarda **apenas documentos, planos, escopos e relatórios**.
- Scripts, código fonte da aplicação e configurações/instruções do Kothar vivem **fora** do cofre (em `~/kothar` ou no repositório do app). Nunca salve código no cofre.

## Fluxo de Trabalho Consolidado

```
Recebe instrução / Tarefa
        ↓
1. Identifica o Domínio (Produto, Cliente ou Geral)
        ↓
2. Lê escopo.md do Domínio (se aplicável)
        ↓
3. Cria/Atualiza Plano no Cofre (YAML Frontmatter OBRIGATÓRIO)
        ↓
4. Executa a Ação (Cria/Edita código fora do cofre)
        ↓
5. Registra mudança no GraphRAG
        ↓
6. Atualiza o Plano no Cofre (Marca [x])
```

## Implementação

Localização: `backend/agents/engineer_agent.py`

```python
class EngineerAgent(BaseAgent):
    """Agente Engenheiro — executa código seguindo blueprint."""

    async def execute(self, task: dict) -> dict:
        step_title = task.get("title", "executar")
        files = task.get("files", [])
        code_action = task.get("action", "")
        content = task.get("content", "")

        # 1. Lê contexto comprimido
        ctx_string = await context_compressor.to_prompt_string(self.session_id)

        # 2. Verifica locks
        locks = await self.check_locks(f"{step_title} {code_action}")
        if locks:
            # Contorna lock com alternativa documentada
            lock_alternatives = [l["document"] for l in locks[:2]]
            await context_compressor.add_decision(
                self.session_id,
                f"Contornando lock: {lock_alternatives[0][:80]}"
            )

        # 3. Busca skill relevante
        skills = await self.search_skill(step_title)
        if skills:
            await context_compressor.add_skill(
                self.session_id, skills[0]
            )

        # 4. Executa a ação (criar/editar/deletar arquivo)
        result = await self.perform_action(
            action=code_action,
            files=files,
            content=content
        )

        # 5. Registra no GraphRAG
        for file_path in files:
            await graph_rag.register_file_change(
                session_id=self.session_id,
                file_path=file_path,
                action=code_action,
            )

        return result
```

## Tipos de Ações

| Ação | Descrição | Exemplo |
|------|-----------|---------|
| `create` | Criar arquivo novo | `touch src/auth/login.py` |
| `edit` | Modificar arquivo existente | Adicionar função a módulo |
| `delete` | Remover arquivo | `rm src/legacy/old.py` |
| `refactor` | Reestruturar código sem mudar comportamento | Extrair função |
| `test` | Criar/rodar testes | `pytest` |

## Erros Comuns e Como o Engenheiro Lida

| Erro | Ação |
|------|------|
| Import não encontrado | Roda `pip install` (com lock check) |
| Test falha | Reporta ao arquiteto, pede revisão |
| Lock bloqueia | Busca alternativa no RAG |
| Contexto grande demais | Usa context_compressor para resumir |
| Timeout na execução | Tenta novamente com timeout maior |

## Skills que o Engenheiro Usa

- `package_install_safely`: Como verificar requirements.txt antes
- `git_commit_pattern`: Conventional Commits
- `test_runner`: Como rodar pytest efetivamente
- `error_decoder`: Como ler stack traces Python/JS
- `docker_builder`: Multi-stage builds para imagens menores
