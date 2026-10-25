# Skill: Prompt Enricher (Injetor de Contexto)

> **Skill:** Enriquecedor de Prompts com Busca Contextual  
> **Versão:** 1.0  
> **Data:** 2026-08-24  
> **Dependência:** `regras/core/perception.md`, `regras/habilidades/memory-search.md`  

---

## 🎯 Conceito

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROMPT ENRICHER WORKFLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Bruno: "corrige bug no login"                                    │
│                    ↓                                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │           PROMPT ENRICHER (Agente Contextual)              │    │
│  │                                                              │    │
│  │  1. LÊ contexto completo:                                 │    │
│  │     ├── Histórico de conversa                             │    │
│  │     ├── Memórias do projeto (~/.claude/memory/)          │    │
│  │     ├── Specs do projeto (specs/internos/*/)            │    │
│  │     ├── Código existente (pasta atual)                   │    │
│  │     ├── Histórico git (commits, branches)                 │    │
│  │     └── Diário do dia                                    │    │
│  │                                                              │    │
│  │  2. BUSCA informações relevantes:                         │    │
│  │     ├── Arquivos relacionados                             │    │
│  │     ├── Padrões de código usados                         │    │
│  │     ├── Preferências do usuário                           │    │
│  │     └── Contexto de negócio                              │    │
│  │                                                              │    │
│  │  3. MONTA prompt enriquecido:                             │    │
│  │     ├── Contexto do projeto                               │    │
│  │     ├── Estrutura atual                                   │    │
│  │     ├── Histórico relevante                               │    │
│  │     ├── Regras de nomenclatura                           │    │
│  │     └── Exemplo do que já foi feito                      │    │
│  │                                                              │    │
│  │  4. ENTREGA para o agente principal                       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                    ↓                                               │
│  Agente Principal recebe:                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PROMPT ORIGINAL: "corrige bug no login"                  │    │
│  │                                                              │    │
│  │  CONTEXTO INJETADO:                                        │    │
│  │  ─────────────────────                                      │    │
│  │  PROJETO: crm-saphia                                       │    │
│  │  ESTRUTURA: backend/servicos/auth/ + frontend/paginas/login│    │
│  │  HISTÓRICO: Último commit foi às 14:30 sobre "adição de   │    │
│  │  validação de CPF"                                         │    │
│  │  ARQUIVOS RELACIONADOS:                                   │    │
│  │  - backend/servicos/auth/login.service.ts                  │    │
│  │  - frontend/paginas/login/login.page.tsx                    │    │
│  │  - backend/banco/conexao.ts                                │    │
│  │  STACK: Node.js + FastAPI + PostgreSQL                     │    │
│  │  REGRAS: Nomenclatura em PT, estrutura backend/frontend/   │    │
│  │  ÚLTIMAS DECISÕES: "Usamos JWT para autenticação"        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                    ↓                                               │
│  AGENTE PRINCIPAL: Tem tudo para agir com precisão!              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Pipeline de Execução

### ETAPA 1: Captura do Prompt Bruto

```javascript
const prompt_bruto = "corrige bug no login"

// O Prompt Enricher intercepta ANTES do agente principal
if (isSimpleCommand(prompt_bruto)) {
    // Comandos simples (< 5 palavras) → vai direto
    executeDirect(prompt_bruto)
} else {
    // Comandos complexos → PROMPT ENRICHER ATIVA
    activatePromptEnricher(prompt_bruto)
}
```

### ETAPA 2: Busca Contextual (5 Fontes)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      5 FONTES DE CONTEXTO                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 📁 PROJETO ATUAL                                               │
│     ├── pwd + estrutura de pastas                                  │
│     ├── git status + branch + remote                               │
│     ├── arquivos .md de contexto (SPEC.md, README.md)             │
│     └── package.json / requirements.txt                            │
│                                                                      │
│  2. 🧠 MEMÓRIAS DO KOTHAR                                          │
│     ├── ~/.claude/projects/*/memory/                              │
│     ├── Histórico de sessões anteriores                            │
│     └── Padrões aprendidos (instincts)                            │
│                                                                      │
│  3. 📚 SPECS DO PROJETO                                             │
│     ├── specs/internos/{projeto}/spec.md                          │
│     ├── specs/internos/{projeto}/*.md                             │
│     └── Constrained specifications                                 │
│                                                                      │
│  4. 💻 CÓDIGO FONTE                                                │
│     ├── Arquivos relacionados ao prompt                            │
│     ├── Padrões de código usados                                   │
│     └── Imports e dependências                                     │
│                                                                      │
│  5. 📅 DIÁRIO E HISTÓRICO                                          │
│     ├── Diário do dia (pendências)                                 │
│     ├── Histórico recente de commits                               │
│     └── Decisões tomadas previamente                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### ETAPA 3: Montagem do Prompt Enriquecido

```markdown
## 📥 PROMPT ORIGINAL
"{prompt_bruto}"

---

## 🎯 CONTEXTO DO PROJETO

**Projeto:** {nome_projeto}
**Stack:** {stack_tecnologica}
**Estrutura:**
```
{estrutura_de_pastas}
```

---

## 📁 ARQUIVOS RELACIONADOS

| Arquivo | Descrição | Última modificação |
|---------|-----------|-------------------|
| {arquivo_1} | {descricao} | {data} |
| {arquivo_2} | {descricao} | {data} |

---

## 🧠 HISTÓRICO RELEVANTE

**Últimas sessões:**
- {sessao_1}
- {sessao_2}

**Decisões tomadas:**
- {decisao_1}
- {decisao_2}

---

## 📋 REGRAS ATIVAS

- Nomenclatura: {regras}
- Estrutura: backend/frontend/
- Gates ativos: {lista}

---

## 🔍 ANÁLISE DO PROMPT

**Tipo detectado:** {tipo}
**Modo recomendado:** {modo}
**Complexidade:** {baixa/media/alta}
**Arquivos afetados:** {lista}

---

## ✅ PROMPT ENRIQUECIDO PRONTO

**Prompt para agente principal:**
{tudo_junto_formatado}

```

---

## 🔧 Exemplos Práticos

### Exemplo 1: "corrige bug no login"

```
ANTES (prompt original):
"corrige bug no login"

DEPOIS (prompt enriquecido):
═══════════════════════════════════════════════════════════════

📥 PROMPT ORIGINAL: "corrige bug no login"

🎯 CONTEXTO DO PROJETO
- Projeto: crm-saphia
- Stack: Node.js + FastAPI + PostgreSQL + Redis
- Estrutura: backend/servicos/auth/ + frontend/paginas/login/

📁 ARQUIVOS RELACIONADOS
- backend/servicos/auth/login.service.ts (última mod: 14:30)
- backend/rotas/auth.routes.ts
- frontend/paginas/login/login.page.tsx
- backend/banco/queries/usuario.query.ts

🧠 HISTÓRICO RELEVANTE
- Sessão anterior (14:00): "adição de validação de CPF"
- Decisão: "Usamos JWT para autenticação"
- Pendência: "Testar fluxo de login após mudanças"

📋 REGRAS ATIVAS
- Nomenclatura: PT, PascalCase para componentes
- Estrutura: backend/frontend/
- G3 (credenciais): ATIVO

🔍 ANÁLISE
- Tipo: correção de bug
- Modo: debug
- Complexidade: média (2 arquivos)
- Escopo: apenas login

═══════════════════════════════════════════════════════════════

AGENTE PRINCIPAL RECEBE TUDO MAPEADO E PRONTO PARA EXECUTAR!
```

### Exemplo 2: "cria página de login"

```
ANTES (prompt original):
"cria página de login"

DEPOIS (prompt enriquecido):
═══════════════════════════════════════════════════════════════

📥 PROMPT ORIGINAL: "cria página de login"

🎯 CONTEXTO DO PROJETO
- Projeto: crm-saphia
- Stack: React + TypeScript + CSS Modules
- Estrutura: frontend/paginas/login/

📁 HISTÓRICO DE CONVERSAS
- "Usuário mencionou que clientes precisam de login rápido"
- "Spec diz: página de login com validação de CPF"
- "Estilo deve seguir: ugarit-ui"

🎨 DESIGN PATTERNS
- Componentes compartilhados disponíveis:
  - BotaoConfirmar.component.tsx
  - InputPadrao.component.tsx
  - CardAuth.component.tsx

📋 REGRAS DE UI
- Cores: paleta ugarit (veja frontend/README.md)
- Fontes: Inter (já configurado)
- Responsivo: mobile-first
- Acessibilidade: ARIA labels obrigatórios

🔍 ANÁLISE
- Tipo: criar feature
- Modo: ENTERPLANMODE (obrigatório)
- Complexidade: alta
- Arquivos: frontend/paginas/login/ + backend/rotas/auth

═══════════════════════════════════════════════════════════════

AGENTE PRINCIPAL JÁ SABE:
✓ Onde criar (frontend/paginas/login/)
✓ Como nomear (PT, PascalCase)
✓ Que componentes usar (componentes-compartilhados)
✓ Que estilo seguir (ugarit-ui)
✓ Qual backend chamar (backend/rotas/auth.routes.ts)
```

---

## ⚙️ Integração com Core Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CORE LOOP COM PROMPT ENRICHER                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 👁️ SENTIR (perception)                                        │
│     └── Captura pwd, git, contexto                                  │
│                      ↓                                              │
│  2. 🔄 PROMPT ENRICHER (NOVO!)                                     │
│     └── Busca contexto em 5 fontes                                  │
│     └── Monta prompt enriquecido                                    │
│     └── Entrega para reasoning                                       │
│                      ↓                                              │
│  3. 🧩 PENSAR (reasoning)                                          │
│     └── Recebe prompt JÁ ENRIQUECIDO                              │
│     └── Classifica tipo                                             │
│     └── Define escopo                                               │
│                      ↓                                              │
│  4. 🚧 VALIDAR (gates)                                             │
│     └── Valida com contexto completo                                │
│                      ↓                                              │
│  5. ⚡ AGIR                                                         │
│     └── Executa com informações completas                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Template de Prompt Enriquecido

```markdown
## 📥 Prompt Original
{bruto}

## 🎯 Contexto do Projeto
**Projeto:** {nome}
**Stack:** {stack}
**pwd:** {pwd}
**branch:** {branch}

## 📁 Estrutura Atual
```
{estrutura}
```

## 🧠 Histórico Relevante
**Pendências:** {pendencias}
**Decisões:** {decisoes}
**Commits recentes:** {commits}

## 📚 Specs Carregadas
- {spec_1}
- {spec_2}

## 🔍 Análise de Escopo
**Tipo:** {tipo}
**Modo:** {modo}
**Complexidade:** {nivel}
**Arquivos afetados:** {lista}

## 📋 Regras Ativas
- {regra_1}
- {regra_2}

## ✅ Prompt para Agente Principal
[Prompt completo, formatado, pronto para execução]
```

---

## 🚀 Como Ativar

### Automático (Recomendado)
O Prompt Enricher ativa automaticamente quando:
- Prompt tem mais de 5 palavras
- Não é comando direto
- Envolve criação, correção ou análise

### Manual
```
Bruno: "/enrich [seu prompt]"
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
