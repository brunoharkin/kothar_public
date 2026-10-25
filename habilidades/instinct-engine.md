---
name: instinct-engine
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: habilidade
descricao: Sistema de auto-aprendizado que captura tool calls e gera instincts
---

# 🧠 INSTINCT ENGINE v1.4.0

> **Função:** Sistema de auto-aprendizado. Captura 100% das tool calls, detecta padrões, gera "instincts" atômicos que viram regras/skills/ajustes.

## Inspiração

**ECC `continuous-learning-v2`** — Affaan Mustafa: 100% das tool calls via hooks → análise em background → instintos atômicos.

## Arquitetura

```
TOOL CALL (Edit, Write, Bash, Read, Glob, Grep)
       ↓
[Hook: post-tool-instinct-collector.sh]  ← Captura 100% das ações
       ↓
[raw-events.jsonl]  ← Stream bruto (timestamp, tool, project, input_preview)
       ↓
[instinct-analyzer.py]  ← Roda sob demanda ou fim de sessão
       ↓
Detecta 3 tipos de padrão:
  1. repeated-edits    (mesmo arquivo editado 3+ vezes)
  2. workflow          (mesma sequência de tools 5+ vezes)
  3. high-frequency-tool (tool usada 30+ vezes)
  4. context-fatigue   (leitura de 4+ arquivos de regras antes de 1 ação)
       ↓
[Gera YAML atômico em pending/]
       ↓
[kothar instincts list/approve/reject]
       ↓
Aprovado → vira skill/regra/ajuste
Rejeitado → arquivado para histórico
```

## Comandos

```bash
# Ver instincts pendentes
kothar instincts list

# Rodar analisador (sob demanda)
kothar instincts analyze

# Aprovar instinct
kothar instincts approve instinct-20260619-190000-001

# Rejetar instinct
kothar instincts reject instinct-20260619-190000-001
```

## Estrutura de Arquivos

```
~/.kothar/instincts/
├── raw-events.jsonl              # Stream bruto de tool calls
├── daily-count-YYYY-MM-DD.txt    # Contador diário
├── pending/                      # Instincts detectados, aguardando Bruno
│   └── instinct-*.yaml
├── approved/                     # Viraram regra/skill
│   └── instinct-*.yaml
└── rejected/                     # Descartados (com motivo)
    └── instinct-*.yaml
```

## Quando o Analyzer Roda

| Quando | Como |
|---|---|
| **Manual** | `kothar instincts analyze` |
| **Fim de sessão** | Hook session-snapshot.sh pode disparar |
| **Sob demanda** | Quando Bruno pede "analisa os instincts" |

**Recomendação:** rodar `kothar instincts analyze` 1x por dia (final do dia).

## Tipos de Instinct Detectados

### 1. Repeated Edits

**Gatilho:** Mesmo arquivo editado 3+ vezes na sessão.

**Exemplo de YAML gerado:**

```yaml
---
name: instinct-20260619-190000-001
type: instinct
confidence: 0.7
domain: code-editing
---

# Instinct: validacao-cpf.js editado 5x

## Padrão detectado
Arquivo `validacao-cpf.js` foi editado 5 vezes entre 14:00 e 14:25.

## Possível interpretação
- Bruno está corrigindo a mesma coisa repetidamente
- Pode indicar: bug recorrente, escopo mal definido
- Ação: revisar skill fluxo-completo-debug

## Próximos passos
- Aprovar para virar regra
- Rejeitar se for caso isolado
```

### 2. Workflow Repetido

**Gatilho:** Mesma sequência de 3 tools aparece 5+ vezes.

**Exemplo:** `Bash → Read → Bash` (rodar comando, ver erro, rodar de novo) 8x → sugere "criar loop de retry automático".

### 3. High-Frequency Tool

**Gatilho:** Tool usada 30+ vezes na sessão.

**Exemplo:** `Bash` 50x → pode indicar: (a) tarefa complexa legítima, ou (b) loop infinito disfarçado.

### 4. Context Fatigue (Fadiga de Burocracia)

**Gatilho:** O agente lê repetidamente arquivos de core/regras (ex: `prompt-principal.md`, `gates.md`, `core-loop.md`) sem realizar alterações no código (Write/Bash produtivo).

**Exemplo:** `Read prompt-principal` -> `Read gates` -> `Read reasoning` -> `Bash ls`. 
**Ação Sugerida:** Acender alerta crítico apontando que o sistema está em "Falsa Sensação de Segurança Burocrática" e propor a desburocratização das regras lidas.

## Promoção: de Instinct a Regra

Quando Bruno aprova, o sistema:

1. Move YAML de `pending/` para `approved/`
2. Copia para `01_Kothar/propostas/v1.4.0/`
3. Kothar (próxima sessão) carrega como proposta no Skill Workshop
4. Bruno decide: yes → vira skill/regra | edit | no

## Limites e Cuidados

- **Confiança mínima:** 0.5 para gerar YAML. Abaixo disso, descarta.
- **Máximo pendentes:** 20 (para não inundar Bruno)
- **Privacidade:** `input_preview` é cortado em 200 chars. Conteúdo sensível não vai para instincts.
- **Falsos positivos:** 30-50% dos instincts podem ser ruído. Bruno filtra.

## Métricas de Sucesso

| Métrica | Meta |
|---|---|
| Instincts gerados por semana | 5-10 |
| Taxa de aprovação (relevantes) | > 40% |
| Tempo de revisão de 1 instinct | < 30s |
| Regras/skills gerados a partir de instincts | 1+ por mês |

## Diferença vs Skill Workshop (v1.3.0)

| Aspecto | v1.3.0 Skill Workshop | v1.4.0 Instinct Engine |
|---|---|---|
| **Detecção** | Manual (Kothar propõe) | Automática (analisador) |
| **Dados** | Observação de conversa | Stream de tool calls |
| **Granularidade** | Skill completa | Instinct atômico |
| **Trigger** | "padrão reutilizável 2x" | "mesmo arquivo 3x" / "sequência 5x" |
| **Workflow** | Propor → Aprovar → Criar | Capturar → Analisar → Aprovar → Promover |

Os dois são **complementares**: Skill Workshop para padrões de comportamento, Instinct Engine para padrões técnicos.
