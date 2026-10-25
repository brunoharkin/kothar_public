# Skill: Model Router (Roteamento de Modelos)

> **Skill:** Roteamento Inteligente de Modelos de IA  
> **Versão:** 1.0  
> **Data:** 2026-08-24  
> **Dependência:** `regras/core/reasoning.md`  

---

## 🎯 Conceito

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MODEL ROUTER                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   BRUNO: "corrige bug complexo no login"                          │
│                       ↓                                             │
│   CLASSIFICAÇÃO DE COMPLEXIDADE:                                   │
│   ├── Tipo: CORREÇÃO DE BUG                                       │
│   ├── Complexidade: ALTA (vários arquivos, lógica crítica)        │
│   └── Decisão: USAR CLAUDE OPUS                                  │
│                       ↓                                             │
│   ══════════════════════════════════════════════════════════════   │
│   🤖 MODELO SELECIONADO: Claude Opus 5                           ║
│   💰 Custo estimado: ~$0.02                                      ║
│   🎯 Motivo: Bug complexo, múltiplos arquivos                    ║
│   ══════════════════════════════════════════════════════════════   │
│                       ↓                                             │
│   EXECUTA COM OPUS                                               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Hierarquia de Modelos

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MODEL TIERS                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🟢 TIER 1: FAST & CHEAP (Tarefas Simples)                       │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Modelos:                                                           │
│  • Claude Haiku (更快, mais barato)                                │
│  • GPT-4o-mini (barato, rápido)                                   │
│  • Gemini Flash (baixo custo)                                       │
│                                                                      │
│  Usar para:                                                         │
│  • "mostra logs", "lista arquivos"                                │
│  • "explica o que esse código faz"                                 │
│  • "traduz isso", "formata JSON"                                  │
│  • Tarefas < 2 min, < 5 linhas de código                        │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🟡 TIER 2: BALANCED (Tarefas Médias)                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Modelos:                                                           │
│  • Claude Sonnet 5 (equilibrado)                                    │
│  • GPT-4o (bom custo-benefício)                                    │
│  • Gemini Pro (versátil)                                            │
│                                                                      │
│  Usar para:                                                         │
│  • "cria endpoint de users"                                        │
│  • "implementa autenticação básica"                                │
│  • "refatora função X"                                            │
│  • Tarefas de 5-30 min, 1-3 arquivos                             │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  🔴 TIER 3: PREMIUM (Tarefas Complexas)                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  Modelos:                                                           │
│  • Claude Opus 5 (melhor raciocínio)                               │
│  • GPT-5 / GPT-4-turbo (máximo poder)                             │
│  • Gemini Ultra (raciocínio complexo)                               │
│                                                                      │
│  Usar para:                                                         │
│  • "corrige bug crítico de autenticação"                           │
│  • "projeta arquitetura de microsserviços"                         │
│  • "debug deadlock em produção"                                     │
│  • "refatora sistema inteiro"                                      │
│  • Tarefas > 30 min, múltiplos arquivos, alta criticidade         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Roteamento

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ROUTING DECISION TREE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  PEDIDO RECEBIDO                                                    │
│         ↓                                                           │
│  CLASSIFICAR COMPLEXIDADE:                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  1. ANALISAR TIPO:                                         │  │
│  │     ├── COMANDO DIRETO → TIER 1 (Fast)                     │  │
│  │     │   "ls", "mostra status", "traduz"                    │  │
│  │     │                                                        │  │
│  │     ├── CRIAÇÃO/IMPLEMENTAÇÃO → TIER 2 (Balanced)          │  │
│  │     │   "cria página", "implementa feature"                 │  │
│  │     │                                                        │  │
│  │     ├── CORREÇÃO DE BUG → TIER 3 (se crítico)              │  │
│  │     │   ou TIER 2 (se simples)                             │  │
│  │     │                                                        │  │
│  │     └── ARQUITETURA/ESTRATÉGIA → TIER 3 (Premium)         │  │
│  │         "projeta sistema", "planeja migração"                │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         ↓                                                           │
│  ANALISAR FATORES:                                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  • Quantos arquivos afetados?                                │  │
│  │  • É crítico para negócio?                                    │  │
│  │  • Tempo estimado?                                           │  │
│  │  • Histórico de erros do usuário?                            │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         ↓                                                           │
│  SELECIONAR MODELO:                                                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │  TIER 1: Haiku / GPT-4o-mini / Gemini Flash                  │  │
│  │  TIER 2: Sonnet / GPT-4o / Gemini Pro                        │  │
│  │  TIER 3: Opus / GPT-5 / Gemini Ultra                         │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│         ↓                                                           │
│  EXECUTAR + LOGAR                                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Matriz de Decisão

| Pedido | Tipo | Arquivos | Complexidade | Modelo |
|--------|------|----------|--------------|--------|
| "ls" | Comando | 0 | trivial | Haiku |
| "mostra logs" | Leitura | 0 | trivial | Haiku |
| "explica código" | Análise | 1 | baixa | Haiku |
| "cria função simples" | Criação | 1 | baixa | Sonnet |
| "cria endpoint" | Criação | 2-3 | média | Sonnet |
| "implementa feature" | Feature | 3-5 | média | Sonnet |
| "corrige bug simples" | Bug | 1 | baixa | Sonnet |
| "corrige bug crítico" | Bug | 3+ | alta | Opus |
| "refatora código" | Refatoração | 2-3 | média | Sonnet |
| "refatora sistema" | Refatoração | 10+ | alta | Opus |
| "projeta arquitetura" | Arquitetura | N/A | crítica | Opus |
| "estratégia MVP" | Estratégia | N/A | alta | Opus |
| "debug produção" | Debug | N/A | crítica | Opus |

---

## ⚙️ Configuração (.env)

```env
# ═══════════════════════════════════════════════════════════════════════
# MODEL ROUTER - CONFIGURAÇÃO DE API KEYS
# ═══════════════════════════════════════════════════════════════════════

# ANTHROPIC (Claude)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# OPENAI (GPT)
OPENAI_API_KEY=sk-xxxxx

# GOOGLE (Gemini)
GOOGLE_API_KEY=xxxxx

# ═══════════════════════════════════════════════════════════════════════
# MODEL ROUTING - SELEÇÃO DE MODELOS POR TIER
# ═══════════════════════════════════════════════════════════════════════

# TIER 1: Fast & Cheap (tarefas simples)
MODEL_TIER1=claude-haiku-4-20250514
MODEL_TIER1_PROVIDER=anthropic
MODEL_TIER1_COST_PER_1K_TOKENS=0.00025

# TIER 2: Balanced (tarefas médias)
MODEL_TIER2=claude-sonnet-5-20250514
MODEL_TIER2_PROVIDER=anthropic
MODEL_TIER2_COST_PER_1K_TOKENS=0.003

# TIER 3: Premium (tarefas complexas)
MODEL_TIER3=claude-opus-5-20250514
MODEL_TIER3_PROVIDER=anthropic
MODEL_TIER3_COST_PER_1K_TOKENS=0.015

# Alternativas (se quiser usar GPT)
MODEL_TIER1_GPT=gpt-4o-mini
MODEL_TIER2_GPT=gpt-4o
MODEL_TIER3_GPT=gpt-5

# MODELO PADRÃO (fallback)
MODEL_DEFAULT=claude-sonnet-5-20250514
```

---

## 🔧 Script de Roteamento

```python
# model_router.py

TIER_MODELS = {
    "tier1": {
        "claude": "claude-haiku-4-20250514",
        "gpt": "gpt-4o-mini",
        "gemini": "gemini-flash-1.5"
    },
    "tier2": {
        "claude": "claude-sonnet-5-20250514",
        "gpt": "gpt-4o",
        "gemini": "gemini-1.5-pro"
    },
    "tier3": {
        "claude": "claude-opus-5-20250514",
        "gpt": "gpt-5",
        "gemini": "gemini-ultra-1.0"
    }
}

PROVIDER_PRIORITY = ["anthropic", "openai", "google"]

def classify_request(prompt: str, context: dict) -> str:
    """Classifica complexidade do pedido"""
    
    prompt_lower = prompt.lower()
    
    # CRITICAL: Sempre usar Tier 3
    critical_keywords = [
        "produção", "crítico", "urgent", "imediato",
        "architeto", "projeta sistema", "estratégia",
        "deadlock", "vazamento", "security"
    ]
    if any(kw in prompt_lower for kw in critical_keywords):
        return "tier3"
    
    # HIGH: Bugs complexos, refatorações grandes
    high_keywords = [
        "bug", "corrige", "conserta", "resolve",
        "refatora", "migra", "reorganiza",
        "debug", "profiling"
    ]
    if any(kw in prompt_lower for kw in high_keywords):
        if context.get("arquivos_afetados", 0) > 2:
            return "tier3"
        return "tier2"
    
    # MEDIUM: Features, implementações
    medium_keywords = [
        "cria", "implementa", "adiciona", "construa",
        "integra", "conecta", "configura"
    ]
    if any(kw in prompt_lower for kw in medium_keywords):
        return "tier2"
    
    # LOW: Comandos simples, leituras
    low_keywords = [
        "mostra", "lista", "explica", "traduz",
        "formata", "le", "busca", "pesquise"
    ]
    if any(kw in prompt_lower for kw in low_keywords):
        return "tier1"
    
    # DEFAULT
    return "tier2"

def route(prompt: str, context: dict) -> dict:
    """Roteia para o modelo apropriado"""
    
    tier = classify_request(prompt, context)
    provider = os.getenv("PREFERRED_PROVIDER", "anthropic")
    
    model = TIER_MODELS[tier].get(provider, TIER_MODELS[tier]["claude"])
    
    return {
        "tier": tier,
        "model": model,
        "provider": provider,
        "cost_estimate": COST_PER_TIER[tier],
        "reason": get_routing_reason(tier, prompt)
    }
```

---

## 📊 Dashboard de Custos

```markdown
## 💰 Model Router - Custos

### Por Tier
| Tier | Modelo | Custo/1K tokens | Quando usar |
|------|--------|------------------|--------------|
| T1 | Haiku | $0.00025 | Tarefas simples |
| T2 | Sonnet | $0.003 | Tarefas médias |
| T3 | Opus | $0.015 | Tarefas complexas |

### Economia Estimada
```
100 pedidos simples:
  ❌ Sonnet: $0.30
  ✅ Haiku: $0.025 (92% economia)
```

### Logs
```json
{
  "timestamp": "2026-08-24T14:30:00",
  "tier": "tier2",
  "model": "claude-sonnet-5",
  "tokens_used": 500,
  "cost": "$0.0015"
}
```

---

## 🚀 Como Usar

```bash
# 1. Configurar .env com suas chaves
cp model-router.env.example .env
# Editar .env com suas chaves

# 2. Testar roteamento
python3 model-router.py "mostra logs"
# → TIER 1: Haiku

python3 model-router.py "corrige bug crítico no login"
# → TIER 3: Opus

# 3. Ver dashboard
python3 model-router.py stats
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
