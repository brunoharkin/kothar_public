---
name: instinct-engine
description: >-
  Skill do Kothar: 🧠 INSTINCT ENGINE v1.4.0. Ativar quando necessário para execução da habilidade instinct-engine.
---

# 🧠 INSTINCT ENGINE v1.4.0

> **Função pretendida:** Sistema de auto-aprendizado. A captura, análise e promoção só
> podem ser consideradas automáticas quando os hooks, o analisador e os comandos forem
> encontrados e testados no runtime ativo.

## Estado de implementação verificado

Na revisão desta skill, o repositório contém esta especificação, mas não foi encontrado
`instinct-analyzer.py`, `raw-events.jsonl`, diretório `~/.kothar/instincts` nem comando
`instincts` no `kothar-cli.sh`. Portanto, não afirmar que 100% das ações são capturadas,
que os comandos abaixo funcionam ou que existe aprendizado automático ativo. Até esses
componentes serem implementados e testados, a análise é manual e qualquer aprendizado
deve ser incorporado a uma regra existente ou apresentado como proposta.

Não persistir transcrições brutas. Extrair evidências mínimas, remover credenciais,
dados pessoais e conteúdo do cliente; guardar somente padrão, causa confirmada,
prevenção e teste verificável. Não promover heurística isolada a regra automática.

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
  5. repeated-failure  (mesmo fluxo falha em verificações sucessivas ou é reportado novamente pelo usuário)
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

### 5. Falha recorrente / validação não representativa

**Gatilho:** a mesma falha reaparece depois de uma correção, o usuário informa que o
erro continua ou a verificação usada não representa o runtime de produção.

**Aprendizado mínimo:** sintoma esperado/observado; runtime e fluxo realmente usados;
tentativas e resultados; causa raiz confirmada; prevenção; teste que prova a correção.
Uma compilação isolada não valida extensão, autenticação, captura, sessão, publicação
ou deploy. Repetição de falha exige reabrir o debug, não aumentar a confiança do
instinct.

### Aprendizado aplicado: sessão de extensão Chrome (25/09/2026)

A análise local da sessão encontrou 34 mensagens do usuário e 211 chamadas de
ferramenta, mas atividade alta não impediu falhas repetidas. Entre as evidências:
um container `unhealthy` foi descrito como pronto; a extensão foi testada como página
Vite em vez de validar somente o pacote Manifest V3 carregado no Chromium; houve
falhas de sintaxe/build, recurso do content script ausente, autenticação inválida,
captura não iniciada e pendências de publicação/CI reportadas pelo usuário.

**Prevenções promovidas:** readiness real para serviços; matriz de aceite de extensão
separada do frontend hospedeiro; reproduzir no mesmo runtime do usuário; bloquear
progresso e declaração de sucesso após falha; validar pacote, permissões, publicação e
CI antes de declarar pronto. O transcript bruto não deve ser copiado para a memória.

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
