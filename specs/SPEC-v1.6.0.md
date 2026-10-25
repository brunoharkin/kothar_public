# SPEC — Kothar Ugarit v1.6.0: Auto-Mode + Auto-Effort Switching

> **Versão:** 1.6.0
> **Data:** 2026-06-26
> **Autor:** Kothar (auto-especificação aprovada por Bruno)
> **Status:** ✅ IMPLEMENTADO
> **Sucessor de:** SPEC v1.5.0 (2026-06-25)

---

## 🎯 Visão

Transformar o Kothar em um agente que **controla o próprio Claude Code** — trocando `permission_mode` (plan/auto/acceptEdits) e `effort_level` (low/high/xhigh) automaticamente baseado em keywords do Bruno, sem precisar ir em `/config` manualmente.

**Resultado esperado:**
- Bruno fala "crie um plano" → Claude entra em Plan Mode automaticamente
- Bruno fala "use ultracode" → Claude usa Workflow tool em tarefas complexas
- Bruno fala "modo auto" → Claude executa sem pedir approval
- Bruno fala "rápido" → Claude responde direto, sem deep dive

---

## 📊 Comparativo: v1.5.1 vs v1.6.0

| Aspecto | v1.5.1 | v1.6.0 |
|---------|--------|--------|
| Detecção de skills | ✅ 19 skills | ✅ 19 skills |
| Detecção de permission_mode | ❌ Não detectava | ✅ plan/auto/acceptEdits/default |
| Detecção de effort_level | ❌ Não detectava | ✅ low/medium/high/xhigh |
| Hook mode-switcher | ❌ Inexistente | ✅ PreToolUse wired |
| Hook mode-loader | ❌ Inexistente | ✅ SessionStart wired |
| Estado persistido | ❌ Inexistente | ✅ `claude-mode.json` |
| Combinação skill+mode+effort | ❌ Impossível | ✅ Uma frase, 3 efeitos |
| Total de hooks wired | 8 | **11** |

---

## 🔧 FASE 2 — IMPLEMENTADO: Auto-Mode Switching

### 2.1 Mode Switcher Hook (v1.6.0)

**Status:** ✅ IMPLEMENTADO

**Problema:** Bruno tinha que abrir `/config` toda vez que queria trocar permission_mode ou effort_level.

**Solução:** Hook PreToolUse que detecta keywords e persiste estado em JSON.

**Arquivos:**
- `~/.kothar/hooks/mode-switcher.sh` — Detecta e troca
- `~/.kothar/hooks/mode-loader.sh` — Mostra estado no SessionStart
- `~/.kothar/state/claude-mode.json` — Estado persistido

**Keywords para permission_mode:**

| Keyword | permission_mode |
|---|---|
| "plano", "planejar", "spec", "design antes", "arquitetura", "como desenhar" | `plan` |
| "modo auto", "se vire", "você decide", "autônomo" | `auto` |
| "edita direto", "pode editar" | `acceptEdits` |
| "pergunte antes", "resetar modo" | `default` |

**Keywords para effort_level:**

| Keyword | effort_level |
|---|---|
| "ultracode", "exaustivo", "workflows", "fan out agents" | `xhigh` |
| "high effort", "deep think", "pense muito" | `high` |
| "low effort", "rápido", "tldr" | `low` |
| (nada) | `xhigh` (padrão Kothar) |

### 2.2 State File (claude-mode.json)

```json
{
  "permission_mode": "plan",
  "effort_level": "xhigh",
  "updated_at": "2026-06-26T17:34:48-03:00",
  "version": "1.6.0",
  "triggers": {
    "mode": "keyword:plano/planejar/spec",
    "effort": "keyword:ultracode"
  }
}
```

### 2.3 Intent Detector Expandido

**Antes (v1.5.1):** só detectava skill (19 padrões).
**Agora (v1.6.0):** detecta skill + mode + effort simultaneamente.

Comandos novos:
```bash
kothar intent detect "crie um plano ultracode"  # → skill+mode+effort
kothar intent mode "use plan mode"               # → plan
kothar intent effort "use ultracode"             # → xhigh
kothar intent all "crie landing page ultracode"  # → frontend-ugarit + plan + xhigh
```

---

## 📋 DoD v1.6.0

### FASE 2 (Mode + Effort Switching)
- [x] Hook mode-switcher.sh criado e executável
- [x] Hook mode-loader.sh criado e executável
- [x] Wireado em settings.json (PreToolUse + SessionStart)
- [x] intent-detector.sh estendido com detect_mode() e detect_effort()
- [x] Estado persistido em claude-mode.json
- [x] SKILL.md atualizado com tabelas de trigger
- [x] perception.md S5 com modos do Claude Code
- [x] reasoning.md ETAPA 2 com detecção automática
- [x] Testes: 5 cenários passaram (plano, ultracode, auto, low, combinado)

### Testes Manuais Validados
- [x] "crie um plano para API" → permission_mode: plan
- [x] "use ultracode" (de low) → effort_level: xhigh
- [x] "modo auto, se vire" → permission_mode: auto
- [x] "resumo rápido tldr" → effort_level: low
- [x] "crie um plano ultracode para landing page" → plan + xhigh + frontend-ugarit

---

## 🔗 Referências

- Kothar NousResearch: https://github.com/NousResearch/kothar-agent
- OpenClaw: https://github.com/openclaw/openclaw
- OpenClaw Docs: https://docs.openclaw.ai
- Honcho: https://github.com/plastic-labs/honcho
- agent-skills.io: https://agentskills.io

---

## 📋 Changelog

### v1.6.0 (2026-06-26) — Auto-Mode + Auto-Effort Switching

**Features implementadas:**
- ✅ Hook mode-switcher.sh (PreToolUse) detecta e troca permission_mode
- ✅ Hook mode-loader.sh (SessionStart) mostra estado atual
- ✅ intent-detector.sh estendido com detect_mode() e detect_effort()
- ✅ Estado persistido em `~/.kothar/state/claude-mode.json`
- ✅ SKILL.md com tabelas de keywords (v1.6.0)
- ✅ perception.md S5 com 4 modos do Claude Code
- ✅ reasoning.md ETAPA 2 com detecção automática

**Arquivos novos:**
- `~/.kothar/hooks/mode-switcher.sh`
- `~/.kothar/hooks/mode-loader.sh`
- `~/.kothar/state/claude-mode.json` (criado em runtime)

**Arquivos modificados:**
- `~/.claude/settings.json` (2 hooks novos wirados)
- `~/.kothar/hooks/intent-detector.sh` (3 funções novas)
- `~/.claude/skills/kothar/SKILL.md` (v1.6.0)
- `01_Kothar/core/perception.md` (v1.2)
- `01_Kothar/core/reasoning.md` (v1.1)

### v1.5.0 (2026-06-25) — Instinct Engine + Integration

**Features implementadas:**
- ✅ Instinct Engine completo (analyzer + collector)
- ✅ Memory Nudge System funcional
- ✅ 8 hooks wired no settings.json
- ✅ Structured logging em JSONL
- ✅ Session snapshot com métricas expandidas
- ✅ Integration test script

### v1.4.0 (2026-06-19) — Hooks Foundation

**Features implementadas:**
- 5 hooks base (pre-bash-guard, pre-bash-project, pre-bash-ssh, post-edit-cred-scan, post-edit-dod)
- session-init.sh
- session-snapshot.sh

### v1.3.0 (2026-06-18) — Auto-Evolução + Fault Tolerance

**Especificação criada com visão completa de 4 fases.

---

*SPEC v1.6.0 criada em 2026-06-26 por Kothar — implementa Auto-Mode + Auto-Effort Switching conforme solicitação de Bruno*
