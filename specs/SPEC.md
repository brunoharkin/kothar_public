# SPEC — Kothar Ugarit v2.1.4: Migração Gemini + Gates de Validação + Anti-Alucinação

> **Versão:** 2.1.4
> **Data:** 2026-07-19
> **Autor:** Kothar (correções estruturais aplicadas)
> **Status:** ✅ ESTÁVEL - Integrado ao Gemini (Antigravity)

---

## 🎯 Visão

Transformar o Kothar de "agente com regras manuais" para "agente com auto-evolução + fault tolerance + RAG real", seguindo padrões do Kothar NousResearch e OpenClaw.

**Resultado esperado:**
- Zero perda de contexto entre sessões
- Auto-correção sem intervenção manual
- Logging estruturado para debugging
- Isolamento total de projetos
- Métricas de qualidade por sessão
- Busca semântica em contexto histórico
- Recuperação automática de falhas

---

## 📊 Comparativo: v2.0.0 vs v2.1.1

| Aspecto | v2.0.0 | v2.1.1 |
|---------|---------|---------|
| Memória RAG | ChromaDB (spec) | **ChromaDB REAL** |
| Fault Tolerance | Spec (JS) | **Hook REAL** |
| Stall Detector | Spec (JS) | **Hook REAL** |
| Hooks wired | 11 | **13** |
| Skills Ativas | 52 | 52 |

---

## 🛡️ NOVOS HOOKS v2.1.1

### 1.4 Fault Tolerance Hook (REAL)

**Status:** ✅ IMPLEMENTADO

- Retry automático (max 3 tentativas)
- Exponential backoff (1s → 2s → 4s)
- Jitter ±10%
- Detecta erros retryable vs permanent
- Logging em JSONL

**Arquivo:** `~/.kothar/hooks/post-tool-fault-tolerance.sh`

### 1.5 Stall Detector Hook (REAL)

**Status:** ✅ IMPLEMENTADO

- Detecta sessões travadas
- Thresholds: 30s healthy, 2min long_running, 5min stalled, 10min stuck
- Notificações automáticas
- Estado persistido

**Arquivo:** `~/.kothar/hooks/post-tool-stall-detector.sh`

### 1.6 RAG Embedder (REAL)

**Status:** ✅ IMPLEMENTADO

- ChromaDB persistente em `~/.kothar/vector-db/`
- Modelo: all-MiniLM-L6-v2 (rápido)
- Indexação de decisões e contexto
- Busca semântica

**Arquivo:** `~/.kothar/scripts/embedder.py`

---

## 🔧 FASE 1 — IMPLEMENTADO: Instinct Engine

### 1.1 Instinct Analyzer (v1.5.0)

**Status:** ✅ IMPLEMENTADO

**Problema:** Kothar não aprende com padrões de comportamento passados.

**Solução:** Instinct Engine que detecta padrões e gera instincts pendentes.

**Arquitetura:**

```
┌─────────────────────────────────────────────────────────────┐
│ INSTINCT ENGINE                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Eventos] ──→ [Instinct Analyzer] ──→ [Pending YAMLs]      │
│      │                │                     │                │
│      │                │              [Aprovação]             │
│      │                │                     │                │
│      └───────────────┴─────────────────────┴────────────────  │
│                                                              │
│  PADRÕES DETECTADOS:                                        │
│  - Repeated edits (mesmo arquivo editado 3+ vezes)           │
│  - Workflow patterns (sequências de tools)                  │
│  - High-frequency tools (uso excessivo)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Arquivos:**
- `~/.kothar/scripts/instinct-analyzer.py` — Análise de padrões
- `~/.kothar/hooks/post-tool-instinct-collector.sh` — Coleta de eventos
- `~/.kothar/instincts/` — Pendentes, aprovados, rejeitados

**DoD:**
- [x] Instinct analyzer detecta 3 tipos de padrões
- [x] Gera YAMLs pendentes com confidence score
- [x] Coleta eventos de todas as tools
- [x] Limite de 20 pending instincts
- [x] **v2.1.1:** Deduplicação de patterns

### 1.2 Memory Nudge System (v1.5.0)

**Status:** ✅ IMPLEMENTADO

**Problema:** Kothar perde contexto entre sessões.

**Solução:** Sistema de nudges automáticos para salvar contexto importante.

**Arquivos:**
- `~/.kothar/scripts/memory-nudge.sh` — Trigger e avaliação
- `~/.kothar/scripts/memory-search.sh` — Busca em memórias
- `~/.kothar/scripts/memory-summarize.sh` — Sumarização

**DoD:**
- [x] Gatilhos: 30min, decisão R4, erro, mudança de projeto
- [x] Nudge aparece em SessionEnd
- [x] Memórias salvas em formato estruturado

### 1.3 Hooks Wiring (v1.5.0)

**Status:** ✅ IMPLEMENTADO + EXPANDIDO

**13 hooks wired em `settings.json`:**

| Hook | Tipo | Função |
|------|------|--------|
| `pre-bash-guard.sh` | PreToolUse[Bash] | Bloqueia comandos perigosos |
| `pre-bash-project.sh` | PreToolUse[Bash] | Valida projeto |
| `pre-bash-ssh.sh` | PreToolUse[Bash] | Valida SSH |
| `mode-switcher.sh` | PreToolUse[Bash] | Auto mode/effort |
| `post-edit-cred-scan.sh` | PostToolUse[Edit] | Detecta credenciais |
| `post-edit-dod.sh` | PostToolUse[Edit] | Valida DoD |
| `post-tool-instinct-collector.sh` | PostToolUse[*] | Captura patterns |
| `post-tool-stall-detector.sh` | PostToolUse[*] | **NOVO v2.1.1** |
| `post-tool-fault-tolerance.sh` | PostToolUse[*] | **NOVO v2.1.1** |
| `session-init.sh` | SessionStart | R1 automático |
| `session-snapshot.sh` | SessionEnd | Snapshot + métricas |
| `mode-loader.sh` | SessionStart | Mostra modo |

**DoD:**
- [x] 13 hooks funcionais
- [x] Todos testados
- [x] Logs em JSONL
- [x] Modo strict configurável

---

## 📊 STATUS IMPLEMENTAÇÃO v2.1.1

### ✅ Implementações Feitas Hoje (2026-06-26)

| Item | Status | Resultado |
|------|--------|-----------|
| Instincts pending limpos | ✅ | 20 duplicados → rejected |
| Strict mode ativado | ✅ | gates-mode = strict |
| pre-bash-guard.sh expandido | ✅ | 7 → 20 padrões |
| post-edit-dod.sh expandido | ✅ | 3 → 10 padrões |
| instinct-analyzer.py corrigido | ✅ | dedup implementado |
| Hooks validados | ✅ | Todos passam nos testes |
| ChromaDB real | ✅ | venv + sentence-transformers |
| RAG embedder | ✅ | ~/.kothar/scripts/embedder.py |
| Fault tolerance hook | ✅ | ~/.kothar/hooks/post-tool-fault-tolerance.sh |
| Stall detector hook | ✅ | ~/.kothar/hooks/post-tool-stall-detector.sh |
| Hooks wired | ✅ | 13 hooks no settings.json |
| Integração Gemini | ✅ | ~/.gemini/config/skills/kothar/SKILL.md |
| Gate 3: Credenciais | ✅ | ~/.kothar/hooks/post-edit-cred-scan.sh |
| Gate 5: Nomenclatura | ✅ | ~/.kothar/hooks/pre-edit-naming.sh |
| Anti-Alucinação | ✅ | ~/.kothar/hooks/post-tool-hallucination-detector.sh |

### 🛡️ Padrões no pre-bash-guard

| # | Padrão | Ação |
|---|--------|------|
| 1-8 | Originais | Block/Aviso |
| 9 | git stash | Aviso |
| 10 | git reset --hard | **BLOCK** |
| 11 | chmod -R /home | **BLOCK** |
| 12 | mkfs.* | **BLOCK** |
| 13 | sudo npm install | **BLOCK** |
| 14 | kill -9 | Aviso |
| 15 | echo >> /etc/* | **BLOCK** |
| 16 | Build sem type-check | Aviso |
| 17 | rm -rf node_modules | Aviso |
| 18 | git clean -fd | **BLOCK** (strict) |
| 19 | curl script \| bash | **BLOCK** |
| 20 | history -c | **BLOCK** |

### 📊 Versões

| Versão | Data | Feature Principal |
|--------|------|------------------|
| v1.3.0 | 2026-06-18 | Auto-Evolução + Fault Tolerance |
| v1.4.0 | 2026-06-19 | Hooks Foundation |
| v1.5.0 | 2026-06-25 | Instinct Engine + Integration |
| v1.6.0 | 2026-06-26 | Auto-Mode + Auto-Effort Switching |
| v2.0.0 | 2026-06-26 | RAG Engine + Swarm Router |
| **v2.1.1** | **2026-06-26** | **RAG REAL + Fault Tolerance REAL + Stall Detector REAL** |
| **v2.1.2** | **2026-06-28** | **Estabilização: Fim de Recursão, RAG Assíncrono e Projetos Reais** |
| **v2.1.3** | **2026-06-28** | **CORREÇÕES CRÍTICAS: ChromaDB Wrapper + Sem JavaScript + Prompt Unificado** |
| **v2.1.4** | **2026-07-19** | **MIGRAÇÃO GEMINI: Correção de contexto, Gates reais (Credenciais e Nomenclatura) e Anti-Alucinação** |

---

*SPEC atualizada em 2026-07-19 para v2.1.4 por Kothar (migração e correções completas aplicadas)*
