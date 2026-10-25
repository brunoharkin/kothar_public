# Skill: Context Planner (Planejador de Contexto)

> **Skill:** Planejamento Contextual Automático  
> **Versão:** 2.0  
> **Data:** 2026-08-24  
> **Dependência:** `prompt-enricher.md`, `regras/core/reasoning.md`  

---

## 🎯 Conceito

```
┌─────────────────────────────────────────────────────────────────────┐
│                  CONTEXT PLANNER WORKFLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  BRUNO: "corrige bug no login"                                    │
│                    ↓                                               │
│  ══════════════════════════════════════════════════════════════════   │
│  ║                                                               ║   │
│  ║   🔍 CONTEXT PLANNER ATIVADO                                 ║   │
│  ║   Fazendo análise completa...                                 ║   │
│  ║                                                               ║   │
│  ╚═════════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              ANÁLISE COMPLETA DO PROMPT                       │  │
│  │                                                               │  │
│  │  📥 Prompt original: "corrige bug no login"                 │  │
│  │  🎯 Tipo detectado: CORREÇÃO DE BUG                         │  │
│  │  📊 Complexidade: MÉDIA (3 arquivos afetados)              │  │
│  │  🚨 Prioridade: ALTA                                       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    ↓                                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              MAPA DO CÓDIGO                                 │  │
│  │                                                               │  │
│  │  📁 backend/servicos/auth/login.service.ts                  │  │
│  │     └─ função autenticarUsuario() — POSSÍVEL FALHA         │  │
│  │                                                               │  │
│  │  📁 backend/rotas/auth.routes.ts                           │  │
│  │     └─ rota POST /auth/login — OK                          │  │
│  │                                                               │  │
│  │  📁 frontend/paginas/login/login.page.tsx                   │  │
│  │     └─ componente Login — OK                                │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    ↓                                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              HISTÓRICO RELEVANTE                             │  │
│  │                                                               │  │
│  │  📅 Última sessão: 14:30 - "adição de validação CPF"       │  │
│  │  💬 Decisão: "Usamos JWT para autenticação"                │  │
│  │  🔧 Commit: 47eb6c7 - feat: autenticação JWT               │  │
│  │  ⚠️  Issue: #23 - bug no fluxo de login                   │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    ↓                                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              PLANO DE AÇÃO COMPLETO                          │  │
│  │                                                               │  │
│  │  1️⃣ [ ] Reproduzir o erro                                  │  │
│  │     - Testar POST /auth/login com dados reais               │  │
│  │     - Verificar logs de erro                                 │  │
│  │                                                               │  │
│  │  2️⃣ [ ] Identificar causa raiz                            │  │
│  │     - Analisar função autenticarUsuario()                     │  │
│  │     - Verificar validação de credenciais                    │  │
│  │                                                               │  │
│  │  3️⃣ [ ] Corrigir bug                                      │  │
│  │     - Arquivo: backend/servicos/auth/login.service.ts        │  │
│  │     - Alteração: adicionar try/catch                        │  │
│  │                                                               │  │
│  │  4️⃣ [ ] Testar correção                                   │  │
│  │     - Reexecutar fluxo de login                             │  │
│  │     - Verificar logs                                        │  │
│  │                                                               │  │
│  │  5️⃣ [ ] Commitar changes                                   │  │
│  │     - git add + commit + push                              │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    ↓                                               │
│  ══════════════════════════════════════════════════════════════════   │
│  ║                                                               ║   │
│  ║   ✅ PLANO COMPLETO GERADO                                  ║   │
│  ║   Aprova para executar? (sim/não/editar)                    ║   │
│  ║                                                               ║   │
│  ╚═════════════════════════════════════════════════════════════════   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Gatilhos de Ativação

```
CONTEXT PLANNER ATIVA AUTOMATICAMENTE QUANDO:

🔴 CRITICAL (sempre ativa):
├── "corrige" / "conserta" / "resolve" → bug
├── "cria" / "implementa" / "adiciona" → feature
├── "refatora" / "migra" / "reorganiza" → mudança
└── "plano" / "planeja" / "mapeia" → já é plano

🟡 MEDIUM (ativa se > 1 arquivo):
├── "altera" / "modifica" / "muda"
├── "melhora" / "otimiza"
└── "adiciona" / "remove"

🟢 LOW (vai direto):
├── Comandos diretos (< 5 palavras)
├── "mostra" / "lista" / "explica"
└── Perguntas simples
```

---

## 📋 Template de Saída

```markdown
═══════════════════════════════════════════════════════════════════════
🔍 CONTEXT PLANNER — ANÁLISE COMPLETA
═══════════════════════════════════════════════════════════════════════

📥 PROMPT ORIGINAL
"{prompt}"

───────────────────────────────────────────────────────────────────────

🎯 CLASSIFICAÇÃO
• Tipo: {IMPLEMENTAÇÃO | CORREÇÃO | REFATORAÇÃO | ANÁLISE}
• Complexidade: {BAIXA | MÉDIA | ALTA}
• Urgência: {BAIXA | MÉDIA | ALTA}
• Arquivos afetados: {N}

───────────────────────────────────────────────────────────────────────

📁 MAPA DE ARQUIVOS

{para cada arquivo:}
  📁 {caminho/arquivo}
     ├─ Função/Componente: {nome}
     ├─ Linhas: {X-Y}
     ├─ Status: {OK | POSSÍVEL FALHA | A CORRIGIR}
     └─ Relação: {descreve}

───────────────────────────────────────────────────────────────────────

🧠 CONTEXTO HISTÓRICO

📅 Diário do dia:
{trecho do diário}

💬 Decisões recentes:
• {decisão 1}
• {decisão 2}

🔧 Commits relacionados:
• {commit 1}
• {commit 2}

───────────────────────────────────────────────────────────────────────

📚 SPECS E REGRAS

📋 Spec do projeto:
{referência à spec}

⚠️ Regras ativas:
• Nomenclatura: PT
• Estrutura: backend/frontend/
• G3 (credenciais): ATIVO

───────────────────────────────────────────────────────────────────────

✅ PLANO DE AÇÃO

{para cada passo:}
  {N}️⃣ [ ] {título do passo}
      • Ação: {o que fazer}
      • Arquivo: {arquivo afetado}
      • Teste: {como validar}

───────────────────────────────────────────────────────────────────────

⚠️ RISCOS IDENTIFICADOS
• {risco 1}
• {risco 2}

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
APROVA ESTE PLANO?
  [sim] → Executar plano
  [não] → Cancelar
  [editar] → Modificar passos
═══════════════════════════════════════════════════════════════════════
```

---

## 🔄 Fluxo no Core Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CORE LOOP v3.1 COM CONTEXT PLANNER             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  BRUNO: "implementa webhook de pagamento"                         │
│                    ↓                                               │
│                                                                      │
│  1️⃣ SENTIR (perception)                                          │
│     └── Captura estado: pwd, git, projeto                         │
│                    ↓                                               │
│                                                                      │
│  2️⃣ CLASSIFICAR                                                   │
│     └── "implementa" = FEATURE NOVA                              │
│     └── GATILHO CRÍTICO → CONTEXT PLANNER ATIVA                   │
│                    ↓                                               │
│                                                                      │
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║                                                               ║  │
│  ║   🔍 CONTEXT PLANNER — ANALISANDO...                        ║  │
│  ║                                                               ║  │
│  ║   • Buscando specs do projeto                                ║  │
│  ║   • Mapeando código existente                               ║  │
│  ║   • Verificando histórico                                    ║  │
│  ║   • Gerando plano completo                                   ║  │
│  ║                                                               ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                    ↓                                               │
│                                                                      │
│  3️⃣ APRESENTAR PLANO                                              │
│     └── Mostra análise completa                                     │
│     └── Aguarda aprovação (CP6)                                    │
│                    ↓                                               │
│                                                                      │
│  Bruno aprova                                                      │
│                    ↓                                               │
│                                                                      │
│  4️⃣ PENSAR (reasoning)                                           │
│     └── Recebe plano aprovado                                      │
│     └── Detalha escopo                                             │
│                    ↓                                               │
│                                                                      │
│  5️⃣ VALIDAR (gates)                                              │
│     └── Valida com plano em mãos                                   │
│                    ↓                                               │
│                                                                      │
│  6️⃣ AGIR (execution)                                              │
│     └── Executa com plano validado                                 │
│                    ↓                                               │
│                                                                      │
│  7️⃣ APRENDER (instinct)                                          │
│     └── Registra padrão                                            │
│                    ↓                                               │
│                                                                      │
│  8️⃣ RELATAR (report)                                             │
│     └── Resume execução                                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Exemplo Prático

### Entrada:
```
Bruno: "corrige bug no logout do crm-saphia"
```

### Saída (Context Planner):

```
═══════════════════════════════════════════════════════════════════════
🔍 CONTEXT PLANNER — ANÁLISE COMPLETA
═══════════════════════════════════════════════════════════════════════

📥 PROMPT ORIGINAL
"corrige bug no logout do crm-saphia"

───────────────────────────────────────────────────────────────────────

🎯 CLASSIFICAÇÃO
• Tipo: CORREÇÃO DE BUG
• Complexidade: MÉDIA
• Urgência: ALTA
• Arquivos afetados: 4

───────────────────────────────────────────────────────────────────────

📁 MAPA DE ARQUIVOS

  📁 backend/servicos/auth/auth.service.ts
     ├─ Função: fazerLogout()
     ├─ Linhas: 45-67
     ├─ Status: ⚠️ POSSÍVEL FALHA
     └─ Relação: Remove token mas não limpa cache

  📁 backend/servicos/auth/token.service.ts
     ├─ Função: invalidateToken()
     ├─ Linhas: 23-41
     ├─ Status: ⚠️ A CORRIGIR
     └─ Relação: Não verifica se token existe

  📁 frontend/contextos/auth.context.tsx
     ├─ Componente: AuthProvider
     ├─ Função: logout()
     ├─ Status: OK
     └─ Relação: Chama API de logout

  📁 frontend/hooks/useAuth.hook.ts
     ├─ Hook: useLogout()
     ├─ Status: OK
     └─ Relação: Wrapper para logout

───────────────────────────────────────────────────────────────────────

🧠 CONTEXTO HISTÓRICO

📅 Diário do dia:
- 14:30: Implementado login com JWT
- 15:00: Testei logout mas não funcionou
- 15:15: Pendente: corrigir bug de logout

💬 Decisões recentes:
• "Usamos JWT para autenticação"
• "Tokens expiram em 24h"
• "Cache de usuário no Redis"

🔧 Commits relacionados:
• a3f2b1c - feat: implementação de logout
• b7d4e3f - fix: renovação de token
• c8e5f4a - feat: autenticação JWT

───────────────────────────────────────────────────────────────────────

📚 SPECS E REGRAS

📋 Spec do projeto:
• specs/internos/crm-saphia/spec.md
  → Autenticação: JWT com refresh token
  → Logout: deve invalidar token imediatamente

⚠️ Regras ativas:
• Nomenclatura: PT (funções em português)
• Estrutura: backend/servicos/{feature}/
• G3 (credenciais): ATIVO — Não expor tokens

───────────────────────────────────────────────────────────────────────

✅ PLANO DE AÇÃO

  1️⃣ [ ] Reproduzir o erro
      • Ação: Testar POST /auth/logout com token válido
      • Arquivo: backend/rotas/auth.routes.ts
      • Teste: Verificar se token é removido do Redis

  2️⃣ [ ] Identificar causa raiz
      • Ação: Analisar fluxo de fazerLogout()
      • Arquivo: backend/servicos/auth/auth.service.ts
      • Causa provável: Não chama invalidateToken()

  3️⃣ [ ] Corrigir auth.service.ts
      • Ação: Adicionar chamada a tokenService.invalidateToken()
      • Arquivo: backend/servicos/auth/auth.service.ts:linha 52
      • Alteração: await tokenService.invalidateToken(token)

  4️⃣ [ ] Corrigir token.service.ts
      • Ação: Adicionar verificação se token existe
      • Arquivo: backend/servicos/auth/token.service.ts:linha 28
      • Alteração: if (!token) return;

  5️⃣ [ ] Testar correção
      • Ação: Reexecutar fluxo de logout completo
      • Teste: Login → Logout → Tentar ação autenticada
      • Esperado: Ação deve falhar (token invalidado)

  6️⃣ [ ] Commitar
      • Mensagem: fix: logout agora invalida token corretamente
      • Branch: feature/auth

───────────────────────────────────────────────────────────────────────

⚠️ RISCOS IDENTIFICADOS
• Risco: Usuários logados agora serão deslogados ao fazer logout
  Mitigação: É o comportamento esperado
• Risco: Race condition se múltiplos logout simultâneos
  Mitigação: Redis é atômico, deve funcionar

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
APROVA ESTE PLANO?
  [sim] → Executar plano
  [não] → Cancelar
  [editar] → Modificar passos
═══════════════════════════════════════════════════════════════════════
```

---

## ⚙️ Integração

Para ativar automaticamente, adicione ao `reasoning.md`:

```markdown
### REGRA: CONTEXT PLANNER

```
QUANDO:
  - Prompt contém: "corrige", "cria", "implementa", "refatora"
  - OU quando usuário pedir explicitamente: "plano", "mapeia"

AÇÃO:
  1. Executar Context Planner (análise completa)
  2. Mostrar mapa de arquivos + histórico + plano
  3. Aguardar aprovação (CP6)
  4. Somente depois → executar
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
