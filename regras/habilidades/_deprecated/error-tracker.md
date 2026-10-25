# Skill: Error Tracker (Rastreador de Erros e Acertos)

> **Skill:** Sistema de Auto-Aprendizado de Erros e Correções  
> **Versão:** 1.0  
> **Data:** 2026-08-24  
> **Dependência:** `regras/core/reasoning.md`, `regras/habilidades/instinct-engine.md`  

---

## 🎯 Conceito

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ERROR TRACKER WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  BRUNO: "corrige bug no login"                                    │
│                    ↓                                               │
│  AGENTE: "Corrigido! A função estava retornando null..."          │
│                    ↓                                               │
│  BRUNO: "não, o erro continua"                                   │
│                    ↓                                               │
│  ══════════════════════════════════════════════════════════════════   │
│  🔴 ERRO REGISTRADO                                             ║   │
│  - Tipo: FALSE POSITIVE                                         ║   │
│  - Arquivo: login.service.ts                                    ║   │
│  - Função: autenticarUsuario()                                  ║   │
│  - O que disse: "Corrigido"                                     ║   │
│  - Realidade: Erro continua                                     ║   │
│  ══════════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│  AGENTE: "Desculpa, vou analisar novamente..."                   │
│                    ↓                                               │
│  AGENTE: "Agora sim! O problema era no catch..."                  │
│                    ↓                                               │
│  BRUNO: "agora funcionou!"                                       │
│                    ↓                                               │
│  ══════════════════════════════════════════════════════════════════   │
│  🟢 ACERTO REGISTRADO                                           ║   │
│  - Arquivo: login.service.ts                                    ║   │
│  - Correção: adicionar try/catch no catch original              ║   │
│  - Padrão: erro estava em catch que não retornava erro           ║   │
│  ══════════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│  💾 SALVO EM:                                                   │
│  - ~/.claude/projects/-home-bruno-kothar/memory/         │
│  - Cofre/00_Memoria/Kothar/Erros/                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Tipos de Erro Rastreados

```
ERRO_TIPO_1: ERRO_DE_CODIGO
├── Definição: Código não compila ou dá erro em runtime
├── Exemplo: "TypeError: Cannot read property 'x' of undefined"
└── Ação: Registra linha, função, arquivo

ERRO_TIPO_2: ERRO_DE_LOGICA
├── Definição: Código funciona mas resultado está errado
├── Exemplo: "Função retorna true quando deveria retornar false"
└── Ação: Registra expectativa vs realidade

ERRO_TIPO_3: FALSO_POSITIVO
├── Definição: Agente disse que corrigiu mas erro continua
├── Exemplo: "Corrigido!" → usuário testa → mesmo erro
└── Ação: Registra como ERRO GRAVE + score de confiança--

ERRO_TIPO_4: ERRO_DE_TESTE
├── Definição: Agente testa mas não valida resultado real
├── Exemplo: "Teste passou" → mas não testou o fluxo completo
└── Ação: Registra tipo de teste que faltou

ERRO_TIPO_5: ERRO_DE_ESCOPO
├── Definição: Agente mudou algo fora do que foi pedido
├── Exemplo: Pediu corrigir login, ele alterou logout
└── Ação: Registra o que mudou vs o que deveria mudar
```

---

## 🔄 Pipeline de Detecção

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ERRO DETECTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1️⃣ BRUNO RELATA ERRO                                           │
│     "não funcionou", "continua o mesmo erro", "deu outro erro"   │
│                    ↓                                               │
│  2️⃣ PARSAR TIPO DE ERRO                                         │
│     ├── "deu erro" → ERRO_DE_CODIGO                              │
│     ├── "não funcionou" → ERRO_DE_LOGICA                        │
│     ├── "você disse que corrigiu" → FALSO_POSITIVO               │
│     └── "agora deu outro erro" → ERRO_DE_TESTE                  │
│                    ↓                                               │
│  3️⃣ REGISTRAR EM error-tracker.json                             │
│     ├── timestamp                                                 │
│     ├── erro_tipo                                                 │
│     ├── arquivo                                                    │
│     ├── função                                                     │
│     ├── o_que_foi_feito                                          │
│     ├── o_que_deveria_ter_sido_feito                             │
│     └── confianca_score (0-100)                                   │
│                    ↓                                               │
│  4️⃣ AJUSTAR COMPORTAMENTO                                        │
│     ├── Se FALSO_POSITIVO: score-- (3 strikes = pause)           │
│     ├── Se ERRO_DE_CODIGO: analisar sintaxe                       │
│     └── Se ERRO_DE_LOGICA: analisar fluxo                        │
│                    ↓                                               │
│  5️⃣ GERAR INSTINCT SE NECESSÁRIO                                │
│     └── Se mesmo erro 2x: propor regra                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Template de Registro

```json
{
  "id": "err-20260824-143052-001",
  "timestamp": "2026-08-24T14:30:52",
  "projeto": "crm-saphia",
  "sessao": "session-uuid",
  
  "erro": {
    "tipo": "FALSO_POSITIVO | ERRO_DE_CODIGO | ERRO_DE_LOGICA",
    "descricao": "Descrição do erro reportado por Bruno",
    "erro_original": "O que foi pedido para corrigir",
    "o_que_agente_fez": "O que o agente tentou fazer",
    "o_que_aconteceu": "O que aconteceu quando Bruno testou"
  },
  
  "codigo": {
    "arquivo": "caminho/arquivo.ts",
    "funcao": "nomeDaFuncao()",
    "linhas_afetadas": "45-67",
    "codigo_original": "... (trecho)",
    "codigo_tentado": "... (trecho)"
  },
  
  "correcao": {
    "registrado": true,
    "data_correcao": "2026-08-24T14:35:00",
    "solucao_encontrada": "Descrição da solução",
    "codigo_correto": "... (trecho)",
    "padroes_identificados": ["sempre usar try/catch", "validar null"]
  },
  
  "metricas": {
    "tentativas": 3,
    "confianca_score": 75,
    "tempo_gasto": "5min",
    "falsos_positivos_agente": 1
  }
}
```

---

## ⚡ Regras de Auto-Save

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTO-SAVE RULES                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  REGISTRAR ERRO AUTOMATICAMENTE QUANDO:                           │
│                                                                      │
│  1. Bruno reporta erro:                                            │
│     "não funcionou", "continua", "deu erro", "errado"            │
│     → Salvar em error-tracker.json                                 │
│     → Salvar em Cofre/00_Memoria/Kothar/Erros/                    │
│                                                                      │
│  2. Bruno confirma acerto:                                         │
│     "funcionou", "pronto", "correto", "perfeito"                 │
│     → Atualizar registro com solução                               │
│     → Gerar padrão se aplicável                                    │
│                                                                      │
│  3. Agente dá falso positivo:                                     │
│     "corrigido", "pronto", "feito"                                │
│     → Bruno reporta que não funcionou                              │
│     → Registrar como FALSO_POSITIVO (erro grave)                  │
│     → Reduzir confiança score                                     │
│                                                                      │
│  4. Agente persiste no erro:                                       │
│     → Após 2 tentativas falhas                                     │
│     → Parar e pedir ajuda humana                                   │
│     → Registrar "BLOQUEADO - requer intervenção"                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
~/.claude/projects/-home-bruno-kothar/
├── memory/
│   ├── erros/
│   │   ├── error-tracker.json          # Banco de erros
│   │   ├── acertos/
│   │   │   └── correcoes-2026-08.md    # Correções feitas
│   │   └── padroes/
│   │       ├── erros-comuns.md         # Padrões de erros
│   │       └── acertos-documentados.md # O que funcionou
│   └── session/
│       └── current-session-errors.json # Erros da sessão atual
│
Cofre/00_Memoria/Kothar/
├── Erros/
│   ├── 2026-08-Erros.md
│   └── Padroes/
│       ├── Erros-JavaScript.md
│       ├── Erros-TypeScript.md
│       └── Erros-Python.md
└── Aprendizados/
    └── Regras-Geradas.md
```

---

## 🔧 Integração com Core Loop

```
SENTIR (perception)
    ↓
PENSAR (reasoning)
    ↓
CONTEXT PLANNER (análise)
    ↓
VALIDAR (gates)
    ↓
AGIR (execution)
    ↓
VERIFICAR (error-tracker) ← NOVO!
    ├── Antes de falar "pronto": validar que realmente funciona
    ├── Se não validar: pedir Bruno para testar
    └── Se Bruno confirmar erro: registrar + tentar novamente
    ↓
APRENDER (instinct)
    ├── Registrar erro cometido
    ├── Registrar acerto
    └── Se padrão identificado: gerar instinct
    ↓
RELATAR (report)
```

---

## 📊 Dashboard de Métricas

```markdown
## 📊 Error Tracker - Sessão Atual

### Erros Cometidos
| # | Erro | Tipo | Tentativas | Status |
|---|------|------|------------|--------|
| 1 | login.service.ts | FALSO_POSITIVO | 2 | ✅ Corrigido |
| 2 | auth.context.tsx | ERRO_DE_LOGICA | 1 | ✅ Corrigido |

### Score de Confiança
```
Agente: ████████░░ 80%
        (3 acertos, 1 falso positivo)
```

### Padrões Aprendidos
- ✅ Sempre validar null antes de usar
- ✅ Try/catch deve retornar erro, não undefined
- ✅ Testar fluxo completo, não só a função

### A Evitar
- ⚠️ Não confiar em "Teste passou" sem testar o fluxo
- ⚠️ Verificar se função existe antes de chamar
```

---

## 🚨 Alertas

```
⚠️ ALERTA: FALSO_POSITIVO DETECTADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agente disse: "Corrigido!"
Bruno reportou: "Continua o mesmo erro"

Arquivo: backend/auth/login.service.ts
Função: autenticarUsuario()
Tentativas: 2/3

Recomendação: Parar e analisar manualmente
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
