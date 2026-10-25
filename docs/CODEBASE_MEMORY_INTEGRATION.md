# Kothar Codebase Intelligence

Integração do **Codebase Memory MCP** com o Engenheiro Kothar.

## O que é

O Codebase Memory MCP (CBM) é um servidor MCP de código inteligente que:
- Indexa codebases em um grafo de conhecimento
- Suporta 162 linguagens via Tree-sitter
- Executa queries Cypher no código
- Detecta código morto e dependências circulares
- Rastreia impacto de mudanças

## Instalação

```bash
# Executar setup
bash ~/kothar/scripts/setup_codebase_memory.sh

# Ou manual:
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

## Uso Rápido

### CLI

```bash
# Indexar projeto atual
codebase-memory-mcp cli index_repository --repo-path .

# Listar projetos
codebase-memory-mcp cli list_projects

# Buscar símbolos
codebase-memory-mcp cli search_graph --project meu-projeto --query "auth"

# Rastrear dependências
codebase-memory-mcp cli trace_path --project meu-projeto --function-name "login" --direction both

# Query Cypher
codebase-memory-mcp cli query_graph --project meu-projeto --query "MATCH (f:Function) RETURN f"

# Arquitetura
codebase-memory-mcp cli get_architecture --project meu-projeto

# Detectar código morto
codebase-memory-mcp cli detect_dead_code --project meu-projeto
```

### Hook do Kothar

```bash
# Preload automático
python3 ~/kothar/hooks/cbm_preload.py preload "analisar dependências de autenticação"

# Arquitetura do projeto
python3 ~/kothar/hooks/cbm_preload.py arch

# Buscar símbolos
python3 ~/kothar/hooks/cbm_preload.py search handler

# Rastrear função
python3 ~/kothar/hooks/cbm_preload.py trace process_request
```

### API Python

```python
from backend.code_intelligence import CBMClient, QueryEngine

# Cliente básico
cbm = CBMClient()
projects = cbm.list_projects()

# Motor de queries
engine = QueryEngine(cbm)

# Busca por nome
functions = engine.find_functions_by_name("meu-projeto", "handler")

# Call graph
graph = engine.get_full_call_graph("meu-projeto", "process_request")

# Código morto
dead = engine.find_dead_functions("meu-projeto")

# Análise de impacto
impact = engine.analyze_change_impact("meu-projeto", "src/auth.py")
```

## Ferramentas MCP

O servidor MCP do Kothar expõe 12 ferramentas de code intelligence:

| Ferramenta | Descrição |
|-------------|-----------|
| `mcp_index_repository` | Indexa repositório |
| `mcp_list_projects` | Lista projetos indexados |
| `mcp_index_status` | Status de indexação |
| `mcp_search_graph` | Busca símbolos no grafo |
| `mcp_trace_path` | Rastreia dependências |
| `mcp_query_cypher` | Query Cypher |
| `mcp_get_architecture` | Overview da arquitetura |
| `mcp_search_code` | Busca texto em código |
| `mcp_get_code_snippet` | Obtém snippet por nome |
| `mcp_find_dead_code` | Detecta código morto |
| `mcp_detect_circular_deps` | Detecta deps circulares |
| `mcp_analyze_impact` | Analisa impacto de mudança |
| `mcp_get_call_graph` | Grafo de chamadas completo |

## Casos de Uso

### 1. Antes de modificar função crítica
```bash
# Entender contexto
codebase-memory-mcp cli trace_path --project meu-projeto --function-name "process_payment" --direction both
```

### 2. Detectar código não utilizado
```bash
# Encontrar funções nunca chamadas
codebase-memory-mcp cli detect_dead_code --project meu-projeto
```

### 3. Analisar impacto de refatoração
```bash
# Ver o que seria afetado
codebase-memory-mcp cli detect_changes --project meu-projeto --git-diff "HEAD~1"
```

### 4. Entender arquitetura
```bash
# Resumo completo
codebase-memory-mcp cli get_architecture --project meu-projeto
```

### 5. Query Cypher avançada
```bash
# Funções com muitas dependências
codebase-memory-mcp cli query_graph --project meu-projeto --query "
MATCH (f:Function)
WHERE f.out_degree > 10
RETURN f.name, f.out_degree
ORDER BY f.out_degree DESC
LIMIT 20
"
```

## Visualização 3D

```bash
# Iniciar servidor web
codebase-memory-mcp --ui=true --port=9749

# Abrir no navegador
open http://localhost:9749
```

## Integração com RAG do Kothar

O CBM complementa o sistema RAG existente:

```
┌─────────────────────────────────────────────────────┐
│                 KOTHAR RAG SYSTEM                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Keywords (rag_preload.py)                         │
│    └─ Busca textual básica                         │
│                                                     │
│  Semantic (ChromaDB)                               │
│    └─ Embeddings, similaridade                     │
│                                                     │
│  Graph (Neo4j)                                     │
│    └─ Grafos de conhecimento                       │
│                                                     │
│  CODE INTELLIGENCE (CBM) ◄── NOVO                  │
│    ├─ AST parsing (162 linguagens)                │
│    ├─ Call graphs                                  │
│    ├─ Dependências estruturais                     │
│    └─ Queries Cypher no código                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Fluxo de Trabalho

```
1. Nova tarefa
   ↓
2. Hooks executam:
   ├─ rag_preload.py (skills + keywords)
   ├─ cbm_preload.py (contexto estrutural) ◄── NOVO
   └─ pre_exec_hook.py (locks + validações)
   ↓
3. Contexto combinado enviado ao LLM
4. LLM executa tarefa
5. QA valida resultado
```

## Troubleshooting

### CBM não encontrado
```bash
# Verificar instalação
which codebase-memory-mcp

# Reinstalar
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash
```

### Projeto não indexado
```bash
# Indexar manualmente
codebase-memory-mcp cli index_repository --repo-path /caminho/do/projeto

# Ver status
codebase-memory-mcp cli index_status --project nome-do-projeto
```

### Timeout em projetos grandes
```bash
# Aumentar timeout
export CBM_MEM_BUDGET_MB=8192
export CBM_WORKERS=4
```
