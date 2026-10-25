# TASKS — Kothar Ugarit v1.3.0

> **Versão:** 1.3.0  
> **Data:** 2026-06-18  
> **Status:** EM IMPLEMENTAÇÃO  

---

## 📋 Índice de Tarefas

| Fase | Tarefa | Status | Prioridade |
|------|--------|--------|-----------|
| **FASE 1** | | | |
| 1.1 | Memory Nudge System | ⏳ | CRÍTICA |
| 1.2 | Skill Workshop Pipeline | ⏳ | CRÍTICA |
| 1.3 | Fault Tolerance Loop | ⏳ | CRÍTICA |
| **FASE 2** | | | |
| 2.1 | Structured Logging | ⏳ | ALTA |
| 2.2 | Execution Metrics | ⏳ | ALTA |
| 2.3 | Trace Correlation | ⏳ | ALTA |
| **FASE 3** | | | |
| 3.1 | Command Allowlist | ⏳ | MÉDIA |
| 3.2 | Project Sandbox | ⏳ | MÉDIA |
| **FASE 4** | | | |
| 4.1 | User Modeling | ⏳ | LONGE |
| 4.2 | FTS5 Search | ⏳ | LONGE |

---

## 🔴 FASE 1 — CRÍTICA: Auto-Correção + Memória

---

### TASK 1.1: Memory Nudge System

**Descrição:** Sistema de lembretes automáticos para salvar contexto relevante.

**Dependências:** Nenhuma  
**Estimativa:** 1 hora  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **1.1.1** Criar `habilidades/memory-nudge.md`
  - Definir 5 gatilhos de nudge:
    - A cada 30min de conversa
    - Após decisão importante (R4)
    - Após erro registrado
    - Quando contexto muda de projeto
    - Quando sessão está por encerrar
  - Implementar lógica de "vale a pena salvar?"
  - Template de nudge para o Bruno

- [ ] **1.1.2** Criar `habilidades/memory-search.md`
  - Formato de memória: frontmatter + content
  - Índice de memórias por tipo (user, feedback, project, reference)
  - Função de busca por keyword
  - Função de busca por data/projeto

- [ ] **1.1.3** Criar `habilidades/memory-summarize.md`
  - Lógica de sumarização (truncar > 500 chars)
  - Extração de keywords
  - Link para memórias relacionadas

- [ ] **1.1.4** Integrar com skill Kothar (prompt-principal.md)
  - Adicionar R1.5: Memory Nudge Check
  - Adicionar ao rodapé de auto-relatabilidade

- [ ] **TESTE** Validar 5 sessões com nudge funcionando

---

### TASK 1.2: Skill Workshop Pipeline

**Descrição:** Pipeline de proposta/aprovação para criação de skills.

**Dependências:** TASK 1.1  
**Estimativa:** 45 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **1.2.1** Criar `habilidades/skill-workshop.md`
  - Gatilho: padrão reutilizável detectado 2+ vezes
  - Template de proposta:
    ```markdown
    ---
    name: nome-da-skill
    description: o que faz
    trigger: quando ativar
    confidence: 0-100
    ---
    
    ## Conteúdo proposed
    ...
    ```
  - Fluxo: detectar → propor → Bruno approve/edit/reject → aplicar

- [ ] **1.2.2** Criar diretório `propostas/`
  - README.md com instruções
  - Sistema de numeração (proposta-001.md, etc)

- [ ] **1.2.3** Criar `habilidades/skill-gating.md`
  - Gating por projeto
  - Gating por configuração
  - Habilitar/desabilitar skills

- [ ] **1.2.4** Integrar com skill Kothar
  - Novo comando: "cria proposta"
  - Novo comando: "lista propostas"

- [ ] **TESTE** Propor e criar 1 skill de teste

---

### TASK 1.3: Fault Tolerance Loop

**Descrição:** Retry automático + hooks + timeout + stall detection.

**Dependências:** TASK 2.1 (Logging)  
**Estimativa:** 1.5 horas  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **1.3.1** Criar `habilidades/fault-tolerance.md`
  - Retry logic: max 3 tentativas
  - Buffer reset entre retries
  - Exponential backoff (1s, 2s, 4s)
  - Track de retry_count em metadata

- [ ] **1.3.2** Criar `habilidades/hooks-system.md`
  - Hooks:
    - `before_tool_call`: validação de params
    - `after_tool_call`: logging de resultado
    - `on_error`: tratamento de erro específico
    - `on_retry`: logging de retry
  - Interface de registro de hooks

- [ ] **1.3.3** Criar `habilidades/timeout-manager.md`
  - Timeout por tool:
    - read: 30s
    - write: 60s
    - bash: 120s
    - agent: 300s
  - Timeout global de sessão: 2h
  - Timeout idle: 30min

- [ ] **1.3.4** Criar `habilidades/stall-detector.md`
  - Detectar sessões "processing" > 10min
  - Classificar: long_running, stalled, stuck
  - Alertar Bruno: "Sessão travou há X min"
  - Opção de abortar

- [ ] **TESTE** Simular 3 erros e validar retry + buffer reset

---

## 📊 FASE 2 — ALTA: Observabilidade

---

### TASK 2.1: Structured Logging

**Descrição:** Sistema de logs JSONL com níveis e redação.

**Dependências:** TASK 1.3  
**Estimativa:** 45 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **2.1.1** Criar `habilidades/structured-logging.md`
  - Formato JSONL:
    ```json
    {
      "ts": "ISO8601",
      "level": "trace|debug|info|warn|error",
      "traceId": "uuid",
      "msg": "mensagem",
      "project": "nome",
      "skill": "nome",
      "meta": {}
    }
    ```
  - Níveis: trace, debug, info, warn, error
  - Integração com skill atual

- [ ] **2.1.2** Criar `habilidades/log-redaction.md`
  - Padrões de redação:
    - API keys: `sk-...`, `api_key=...`
    - Senhas: `senha=...`, `password=...`
    - Tokens: `Bearer ...`, `jwt:...`
  - Redaction de tool payloads

- [ ] **2.1.3** Criar script shell `kothar-logs.sh`
  - `kothar logs --follow`
  - `kothar logs --level error`
  - `kothar logs --project kothar`
  - Rotação: max 100MB, 5 files

- [ ] **2.1.4** Criar `.kothar/logs/` dir
  - `.gitkeep` para manter estrutura

- [ ] **TESTE** Gerar 10 logs de diferentes níveis

---

### TASK 2.2: Execution Metrics

**Descrição:** Coleta de métricas de execução por tool call.

**Dependências:** TASK 2.1  
**Estimativa:** 30 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **2.2.1** Criar `habilidades/execution-metrics.md`
  - Métricas por tool call:
    - `tool_name`
    - `tool_execution_ms`
    - `success: boolean`
    - `retry_count: number`
    - `error_type: string | null`
    - `session_id`
    - `project`
  - Storage em `.kothar/metrics/sessions/`

- [ ] **2.2.2** Criar `habilidades/quality-score.md`
  - Score por sessão (0-100):
    - Sucesso de tools: 40%
    - Tempo de resposta: 30%
    - Zero erros: 30%
  - Score histórico

- [ ] **2.2.3** Criar script `kothar-metrics.sh`
  - `kothar metrics show`
  - `kothar metrics quality`
  - `kothar metrics history`

- [ ] **2.2.4** Criar `.kothar/metrics/` dir
  - `sessions/`
  - `quality/`

- [ ] **TESTE** Medir 10 tool calls e calcular score

---

### TASK 2.3: Trace Correlation

**Descrição:** traceId para correlacionar logs de uma operação.

**Dependências:** TASK 2.1  
**Estimativa:** 30 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **2.3.1** Criar `habilidades/trace-correlation.md`
  - Gerar traceId no início de cada "operação"
  - Propagar traceId em todos os logs
  - Filtro por traceId

- [ ] **2.3.2** Integrar com logging
  - Adicionar `traceId` em todo log
  - Hook para injetar traceId

- [ ] **2.3.3** Script de busca
  - `kothar logs --trace-id abc123`

- [ ] **TESTE** Operações complexas com trace correlacionado

---

## 🔒 FASE 3 — MÉDIA: Isolamento

---

### TASK 3.1: Command Allowlist

**Descrição:** Sistema de allowlist para comandos perigosos.

**Dependências:** TASK 1.3  
**Estimativa:** 30 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **3.1.1** Criar `habilidades/command-allowlist.md`
  - SAFE (executa direto):
    - `ls`, `cat`, `grep`, `find`, `pwd`, `echo`, `head`, `tail`, `wc`
  - CONFIRM (pede confirmação):
    - `rm [arquivo]`, `mv`, `cp`, `git commit`, `git branch`
  - DANGERous (bloqueia):
    - `rm -rf`, `dd`, `mkfs`, `git push --force`
  - CRITICAL (nega sempre):
    - `fork bomb`, `:(){ :|:& };:`

- [ ] **3.1.2** Criar `habilidades/dangerous-commands.md`
  - Lista completa de comandos perigosos
  - Regex patterns para detecção

- [ ] **3.1.3** Integrar com Bash tool
  - Checar allowlist antes de executar
  - Alertar se bloqueado
  - Log de comandos bloqueados

- [ ] **TESTE** Tentar 3 comandos perigosos e validar bloqueio

---

### TASK 3.2: Project Sandbox

**Descrição:** Isolamento de contexto por projeto.

**Dependências:** TASK 1.1, TASK 3.1  
**Estimativa:** 30 minutos  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **3.2.1** Criar `habilidades/project-sandbox.md`
  - Regras de isolamento:
    - PWD válido para projeto
    - SSH key corresponde
    - Memórias isoladas
  - Validação em R1, R2, R3

- [ ] **3.2.2** Criar `habilidades/ssh-validator.md`
  - Mapear: projeto → SSH key
  - Validar antes de git clone/pull/push
  - Alertar se chave errada

- [ ] **3.2.3** Integrar com Kothar init
  - Adicionar validação de projeto em R1
  - Criar `.kothar/sandbox/` para config

- [ ] **TESTE** Simular mudança de projeto e validar isolamento

---

## 🎭 FASE 4 — LONGE: User Modeling

---

### TASK 4.1: Dialectic User Modeling

**Descrição:** Extrair e armazenar preferências de Bruno automaticamente.

**Dependências:** TASK 1.1, TASK 2.2  
**Estimativa:** 1 hora  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **4.1.1** Criar `habilidades/user-modeling.md`
  - Extrair preferências de:
    - Aprovações (positivas)
    - Rejeições (negativas)
    - Correções
    - Tom de comunicação
  - Atualizar USER.md automaticamente

- [ ] **4.1.2** Criar `habilidades/dialectic-loop.md`
  - Ciclo:
    1. Interação
    2. Extract preference
    3. Score confidence
    4. Update model
  - Threshold: 3 confirmações = learned

- [ ] **4.1.3** Criar/atualizar `USER.md`
  - Estrutura:
    ```markdown
    ---
    name: Bruno Harkin
    updated: 2026-06-18
    ---
    
    ## Preferências de Comunicação
    - [x] Prefere respostas fechadas
    - [x] Quer métricas
    
    ## Padrões de Erro
    - [x] Ignora isolamento de projeto
    - [x] Reage a puxa-saco
    ```

- [ ] **TESTE** 5 interações com extração funcionando

---

### TASK 4.2: FTS5 Search

**Descrição:** Busca full-text em conversas passadas.

**Dependências:** TASK 4.1  
**Estimativa:** 1 hora  
**Responsável:** Kothar  

#### Subtarefas:

- [ ] **4.2.1** Criar `habilidades/transcript-storage.md`
  - Salvar transcripts por sessão
  - Formato: `YYYY-MM/session-YYYY-MM-DD-HHMM.md`
  - Comprimir > 100KB

- [ ] **4.2.2** Criar `habilidades/fts5-search.md`
  - Schema FTS5:
    ```sql
    CREATE VIRTUAL TABLE transcripts USING fts5(
      title,
      content,
      session_id UNINDEXED,
      date UNINDEXED,
      project UNINDEXED
    );
    ```
  - Query + reranking via LLM

- [ ] **4.2.3** Criar `.kothar/transcripts/` dir
  - Estrutura: `YYYY-MM/`

- [ ] **4.2.4** Script de busca
  - `kothar recall "query"`
  - `kothar recall --project disparo --date 2026-06 "erro"`

- [ ] **TESTE** Buscar em 10 sessões passadas

---

## ✅ CHECKLIST DE FINALIZAÇÃO

Para cada TASK:

- [ ] Código implementado
- [ ] Documentação atualizada
- [ ] Testes passaram
- [ ] DoD validado
- [ ] Commit feito (com permissão)
- [ ] Snapshot atualizado

---

## 📊 Progresso

```
FASE 1: ░░░░░░░░░░ 0%
FASE 2: ░░░░░░░░░░ 0%
FASE 3: ░░░░░░░░░░ 0%
FASE 4: ░░░░░░░░░░ 0%
TOTAL:  ░░░░░░░░░░ 0%
```

---

*Tasks criada em 2026-06-18 por Kothar*
