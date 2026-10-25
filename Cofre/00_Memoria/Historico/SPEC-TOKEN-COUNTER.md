# SPEC — Kothar Token Counter: Contabilização de Uso de Tokens

> **Versão:** 1.0.0
> **Data:** 2026-09-16
> **Autor:** Kothar
> **Inspirado em:** https://github.com/vinzdg/codenotch
> **Status:** 🔄 EM IMPLEMENTAÇÃO

---

## 🎯 Visão

Implementar um sistema de contabilização de consumo de tokens inspirado no Codenotch, integrado à estrutura Kothar para monitorar o uso de tokens em sessões do Claude Code.

**Fontes de dados:**
1. **CLI do Claude** (`claude /usage`) —via comando direto
2. **Claude Desktop Cache** — leitura do cache do app
3. **API de Usage** — dados oficiais via OAuth/token

---

## 📊 Modelo de Dados

### Estruturas Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    USAGE MODEL                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ProviderSnapshot                                            │
│  ├── id: str                    # Identificador único       │
│  ├── name: str                  # Nome do provedor          │
│  ├── fidelity: Fidelity         # official/derived/manual   │
│  ├── status: ProviderStatus     # ok/stale/needsAuth/etc    │
│  ├── windows: [LimitWindow]     # Limites (session/week)     │
│  ├── context: UsageContext      # Timestamp, metadata        │
│  └── ledger: TokenLedger        # Contador local            │
│                                                              │
│  LimitWindow                                                 │
│  ├── type: WindowType            # session/monthly/weekly    │
│  ├── usedFraction: float         # 0.0 - 1.0                │
│  ├── used: int                   # Tokens usados             │
│  ├── limit: int                  # Limite total             │
│  ├── remaining: int               # Restante                 │
│  ├── resetsAt: datetime          # Quando reseta             │
│  └── spentMoney: Money           # Custo monetário           │
│                                                              │
│  TokenLedger                                                 │
│  ├── days: {instance: {date: Totals}}  # Agregação por dia │
│  ├── totalInputTokens: int       # Acumulado input         │
│  ├── totalOutputTokens: int      # Acumulado output         │
│  └── totalReasoningTokens: int   # Acumulado reasoning     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Enum de Fidelidade

```python
class Fidelity(Enum):
    OFFICIAL = "official"    # Dados do fornecedor (API real)
    DERIVED = "derived"       # Calculado pelo sistema
    MANUAL = "manual"         # Inserido pelo usuário
```

### Enum de Status do Provider

```python
class ProviderStatus(Enum):
    OK = "ok"                          # Dados válidos
    STALE = "stale"                    # Dados antigos (>15min)
    NEEDS_AUTH = "needsAuth"           # Requer autenticação
    ACCESS_DENIED = "accessDenied"    # Sem acesso
    RATE_LIMITED = "rateLimited"        # Rate limit atingido
    ERROR = "error"                    # Erro genérico
```

---

## 🔧 Provider: Claude Usage CLI

Inspirado em `ClaudeUsageCLI.swift` do Codenotch.

### Fluxo

```
1. Localizar binário claude
   - ~/.local/bin/claude
   - ~/.claude/local/claude
   - ~/.bun/bin/claude
   - /opt/homebrew/bin/claude

2. Executar comando
   claude --print --no-session-persistence --strict-mcp-config /usage

3. Parsear saída
   "Current session: 38% used · resets Sep 7 at 2:59pm"
   → Extrai: percentage, reset_date

4. Retornar ProviderSnapshot
```

### Formato de Saída Esperado

```
Current session: 38% used · resets Sep 7 at 2:59pm (Asia/Jakarta)
Current week (all models): 4% used · resets Sep 14 at 5:59am (Asia/Jakarta)
```

---

## 📁 Arquitetura de Arquivos

```
backend/
├── token_counter/
│   ├── __init__.py
│   ├── models.py              # UsageModel, TokenLedger, etc
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py           # UsageProvider (protocolo)
│   │   └── claude_cli.py    # Claude CLI Provider
│   ├── store.py              # UsageStore (polling + cache)
│   ├── ledger.py             # LocalTokenLedger
│   └── api.py                # Endpoints da API
```

---

## 🔄 UsageStore — Estratégia de Polling

Inspirado em `UsageStore.swift` do Codenotch.

### Intervalos Adaptativos

| Estado | Intervalo |
|--------|-----------|
| Ativo | 60 segundos |
| Idle | 5 minutos |
| Deadline | 60 segundos por provider |

### Decadência Gradual

```
1. Fetch falha → mostrar última leitura boa (stale after 15min)
2. Erro needsAuth → descartar cache
3. Erro rateLimited → manter cache
4. Retry com exponential backoff
```

### Proteção contra Condições de Corrida

- **Generation counter**: incrementa em reconexão/cancelamento
- Respostas de gerações antigas são descartadas silenciosamente

---

## 🧮 LocalTokenLedger — Contador Local

Inspirado em `LocalTokenLedger.swift` do Codenotch.

### Estrutura

```python
@dataclass
class LocalPrediction:
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    draft_tokens: int = 0
    accepted_draft_tokens: int = 0
    timestamp: datetime

@dataclass
class Totals:
    requests: int
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    
    def add(self, prediction: LocalPrediction):
        self.requests += 1
        self.input_tokens += prediction.input_tokens or 0
        self.output_tokens += prediction.output_tokens or 0
        self.reasoning_tokens += prediction.reasoning_tokens or 0

class LocalTokenLedger:
    days: dict[str, dict[date, Totals]]  # instance → day → totals
    
    def record(self, prediction: LocalPrediction, instance: str):
        # Acumula no dia correto
        day = calendar.startOfDay(for: prediction.timestamp)
        
    def totals_today(self) -> Totals:
        # Soma todos os totals do dia atual
        
    def cleanup_old_days(self, keep_days: int = 60):
        # Remove dias com mais de 60 dias
```

---

## 🌐 API Endpoints

```
GET  /api/usage/snapshots           # Lista todos os snapshots
GET  /api/usage/snapshot/{provider} # Snapshot específico
GET  /api/usage/ledger              # Dados do ledger local
GET  /api/usage/limits              # Limites configurados
POST /api/usage/refresh             # Força refresh de um provider
```

---

## ⚙️ Integração com Kothar

### 1. Hook de Coleta

Criar hook que coleta tokens após cada resposta do Claude:

```
~/.kothar/hooks/post-response-token-counter.sh
```

### 2. Persistência

- Dados armazenados em `~/.kothar/token-usage/`
- Formato: JSON por dia
- Arquivo de ledger acumulado

### 3. Dashboard

Adicionar ao harness API:
```
GET /api/dashboard/token-usage
```

---

## ✅ Definition of Done

- [x] Modelo de dados implementado
- [x] Claude CLI Provider funcional
- [x] UsageStore com polling adaptativo
- [x] LocalTokenLedger com agregação por dia
- [x] API endpoints expostos
- [x] Persistência em disco
- [x] Hook de contabilização criado
- [x] Testes unitários (10/10 passing)

## 📁 Estrutura Implementada

```
backend/token_counter/
├── __init__.py
├── models.py              # UsageModel, Totals, LocalPrediction, etc
├── ledger.py              # LocalTokenLedger (contador local)
├── store.py               # UsageStore (polling + cache)
├── api.py                 # Endpoints REST
└── providers/
    ├── __init__.py
    ├── base.py           # UsageProvider (protocolo)
    └── claude_cli.py     # Claude CLI Provider

hooks/
└── token-counter-hook.py  # Hook de integração
```

---

## 📚 Referências

- Codenotch: https://github.com/vinzdg/codenotch
- ClaudeUsageCLI.swift: Leitura via CLI
- ClaudeDesktopUsageCache.swift: Cache do app
- UsageModel.swift: Estruturas de dados
- UsageStore.swift: Polling e cache
- LocalTokenLedger.swift: Contador local
