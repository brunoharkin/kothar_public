# ANÁLISE: Automação de Skills do Kothar

> **Data:** 2026-06-25
> **Objetivo:** Kothar detectar intenções e invocar skills AUTOMATICAMENTE

---

## Situação Atual

### Skills Disponíveis: ~90+

| Categoria | Count | Exemplos |
|-----------|-------|----------|
| Marketing | 15+ | cold-email, copywriting, cro, seo-audit, social |
| Frontend | 10+ | frontend-ugarit, gsap-*, react-doctor |
| Analytics | 3 | ga4, analytics, instagram |
| Security | 2 | security, cyber-neo |
| Ops | 3 | client-ops, mercadopago-mcp |
| Development | 5+ | bug-analyst, react-doctor, ship |

### Skills com `user-invocable: true`

```
kothar      — Agente principal
frontend-ugarit — Frontend de agência
bug-analyst    — Análise de bugs
client-ops     — Operações de cliente
copywriter     — Copy de conversão
```

### O Problema

```
┌─────────────────────────────────────────────────────────────┐
│ BRUNO DIZ                                                    │
│ "faz uma landing page"                                      │
│                                                              │
│ ❌ HOJE:                                                     │
│    - Kothar tenta fazer sozinho (genérico)                   │
│    - Não detecta que frontend-ugarit deveria ser invocada    │
│                                                              │
│ ✅ DEVERIA SER:                                               │
│    - Kothar detecta: "landing page" → frontend-ugarit        │
│    - Auto-invoca a skill                                     │
│    - Aplica design de agência                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Como Skills São Detectadas (Sistema Atual)

### 1. `user-invocable: true`
- Habilita comando `/skill-name`
- Mas NÃO auto-invoca

### 2. `description:` 
- Texto que descreve quando usar
- O modelo LÊ isso para decidir se invoca
- MAS precisa estar no contexto

### 3. System Reminder
- Skills aparecem em `<system-reminder>` na conversa
- Lista skills disponíveis com descrições
- Isso que mostra "/frontend-ugarit" etc

---

## O que Falta: AUTO-DETECÇÃO

### Solução Proposta: Intent Detection Hook

Criar um hook que analiza mensagens e detecta intenções:

```
~/.kothar/hooks/intent-detector.sh
```

**Funcionamento:**

```bash
# Input: mensagem do usuário
# Output: skills a invocar + ação recomendada

Input: "faz uma landing page para meu produto"
Output: 
  - invoke: frontend-ugarit
  - invoke: gsap-scrolltrigger  
  - context: marketing
```

### Padrões de Detecção

| Palavra-Chave | Skill | Ação |
|--------------|-------|------|
| "landing page" / "site" | frontend-ugarit | Criar página |
| "bug" / "erro" / "falha" | bug-analyst | Analisar |
| "métricas" / "analytics" / "GA4" | ga4 | Consultar dados |
| "instagram" / "insta" | instagram | Analytics Instagram |
| "email" / "sequência" / "nurture" | cold-email | Escrever emails |
| "copy" / "texto" / "headline" | copywriter | Escrever copy |
| "segurança" / "vulnerabilidade" | cyber-neo | Audit |
| "cliente" / "demanda" | client-ops | Classificar |
| "preço" / "pricing" / "quanto cobrar" | pricing | Estratégia |
| "comparar" / "concorrente" | competitor-profiling | Pesquisar |
| "conversão" / "CRO" / "otimizar" | cro | Otimizar |
| "lançar" / "launch" / "beta" | launch | Planejar |

---

## Implementação: Kothar Auto-Skill

### 1. Criar Hook de Detecção

```bash
# ~/.kothar/hooks/intent-detector.sh

#!/usr/bin/env bash
# Detecta intenções e sugere skills

HERMES_HOME="${HERMES_HOME:-$HOME/.kothar}"

detect_intent() {
    local message="$1"
    message_lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # Padrões de detecção
    case "$message_lower" in
        *"landing page"*|*"criar site"*|*"fazer site"*)
            echo "frontend-ugarit"
            ;;
        *"bug"*|*"erro"*|*"falha"*|*"não funciona"*)
            echo "bug-analyst"
            ;;
        *"métricas"*|*"analytics"*|*"ga4"*)
            echo "ga4"
            ;;
        *"instagram"*|*"insta"*|*"stories"*)
            echo "instagram"
            ;;
        *"email"*|*"sequência"*|*"nurture"*|*"automação"*)
            echo "cold-email"
            ;;
        *"copy"*|*"headline"*|*"texto"*|*"copywriting"*)
            echo "copywriter"
            ;;
        *"segurança"*|*"vulnerabilidade"*|*"audit"*)
            echo "cyber-neo"
            ;;
        *"cliente"*|*"demanda"*|*"chegou"*|*"pedido"*)
            echo "client-ops"
            ;;
        *"preço"*|*"pricing"*|*"quanto cobrar"*)
            echo "pricing"
            ;;
        *"comparar"*|*"concorrente"*|*"competitor"*)
            echo "competitor-profiling"
            ;;
        *"conversão"*|*"cro"*|*"otimizar"*|*"conversão"*)
            echo "cro"
            ;;
        *"lançar"*|*"launch"*|*"beta"*|*"lançamento"*)
            echo "launch"
            ;;
        *)
            echo ""
            ;;
    esac
}
```

### 2. Criar Memory de Auto-Detecção

```markdown
# Auto-Skill Detection — Kothar

## Regra de Ouro

**Quando Bruno mencionar uma palavra-chave, INVOCAR a skill automaticamente.**

## Trigger → Skill

| Quando Bruno diz... | Invocar skill... |
|---------------------|------------------|
| "criar site" / "landing" / "frontend" | `/frontend-ugarit` |
| "bug" / "erro" / "falha" | `/bug-analyst` |
| "métricas" / "GA4" / "analytics" | `/ga4` |
| "instagram" / "insta" | `/instagram` |
| "email" / "sequência" / "nurture" | `/cold-email` |
| "copy" / "headline" / "texto" | `/copywriter` |
| "segurança" / "vulnerabilidade" | `/cyber-neo` |
| "cliente" / "demanda" | `/client-ops` |
| "preço" / "pricing" | `/pricing` |
| "comparar" / "concorrente" | `/competitor-profiling` |
| "conversão" / "CRO" | `/cro` |
| "lançar" / "launch" | `/launch` |
| "GSAP" / "animação" | `/gsap-scrolltrigger` |
| "React" / "componente" | `/react-doctor` |
| "segurança" | `/security` |

## Como Funciona

1. Kothar recebe mensagem
2. Hook detecta palavra-chave
3. Auto-invoca skill relevante
4. Skill carrega contexto
5. Kothar age com skill ativa

## Nunca

- ❌ Ignorar palavras-chave
- ❌ Tentar fazer sem skill quando skill existe
- ❌ Pedir para Bruno invocar manualmente
```

---

## Arquivos a Criar/Atualizar

| Arquivo | Ação | Prioridade |
|---------|------|------------|
| `~/.kothar/hooks/intent-detector.sh` | Criar | 🔴 Alta |
| `~/.claude/projects/-home-bruno-Cofre/memory/auto-skill-detection.md` | Criar | 🔴 Alta |
| `/home/bruno/Cofre/01_Kothar/guias/intent-detection.md` | Criar | 🟡 Média |
| Skill kothar (atualizar) | Atualizar | 🔴 Alta |

---

## Fluxo de Auto-Detecção

```
┌─────────────────────────────────────────────────────────────┐
│ BRUNO: "faz uma landing page"                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ HERMES DETECTA:                                              │
│   - "landing page" → frontend-ugarit                        │
│   - Contexto: marketing                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ AUTO-INVOCA:                                                 │
│   /frontend-ugarit                                           │
│   Skill carrega: design tokens, leis anti-IA, presets         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ HERMES EXECUTA:                                              │
│   - Shape (aprovação de direção)                            │
│   - Aplica 4 camadas do frontend                             │
│   - Design de agência                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Checklist de Implementação

- [ ] Criar intent-detector.sh
- [ ] Criar memory de auto-detection
- [ ] Atualizar skill kothar com regra de auto-invoke
- [ ] Testar com mensagens de exemplo
- [ ] Adicionar mais padrões conforme uso
