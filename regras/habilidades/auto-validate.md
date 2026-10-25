# Skill: Auto-Validate Mode (Validação Antes do "Pronto")

> **Skill:** Validação Automática de Correções + Error Tracker  
> **Versão:** 1.0  
> **Data:** 2026-08-24  
> **Dependência:** `error-tracker.md`, `false-positive-detector.py`  

---

## 🎯 Conceito

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AUTO-VALIDATE WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  BRUNO: "corrige bug no login"                                  │
│                    ↓                                               │
│  AGENTE: Faz correção                                            │
│                    ↓                                               │
│  ══════════════════════════════════════════════════════════════════   │
│  🔍 VALIDAÇÃO AUTOMÁTICA ANTES DE FALAR "PRONTO"              ║   │
│  ══════════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│  Valida:                                                          │
│  • Sintaxe do código (compila?)                                  │
│  • Imports (caminhos corretos?)                                   │
│  • Lógica (null checks, async/await?)                            │
│  • Testes (passam?)                                               │
│  • Escopo (só mudou o necessário?)                               │
│                    ↓                                               │
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║  ✅ TUDO OK → Pode falar "Prontinho!"                      ║  │
│  ║  ❌ PROBLEMAS → Mostrar o que está errado                    ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                    ↓                                               │
│  Se Bruno testar e confirmar que funcionou:                       │
│  ══════════════════════════════════════════════════════════════════   │
│  🟢 ACERTO REGISTRADO                                          ║   │
│  💾 Salvo em: error-tracker.json + Cofre                       ║   │
│  ══════════════════════════════════════════════════════════════════   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO AUTO-VALIDATE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. BRUNO: "corrige bug no login"                               │
│                    ↓                                               │
│  2. AGENTE: Implementa correção                                  │
│                    ↓                                               │
│  3. ANTES DE RESPONDER:                                          │
│     ════════════════════════════════════════════════════════════   │
│     Rodar false-positive-detector.py                              │
│     ├── Verificar sintaxe                                        │
│     ├── Verificar imports                                        │
│     ├── Verificar lógica                                        │
│     ├── Verificar testes                                        │
│     └── Verificar escopo                                        │
│     ════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│  4. SE VALIDOU:                                                  │
│     → Mostrar resultado ao Bruno                                  │
│     → Pedir para Bruno testar                                   │
│     → Aguardar confirmação                                       │
│                    ↓                                               │
│  5. SE BRUNO CONFIRMA:                                         │
│     ════════════════════════════════════════════════════════════   │
│     python3 error-tracker.py acerto <id> <solucao>              ║   │
│     ════════════════════════════════════════════════════════════   │
│                    ↓                                               │
│  6. SE BRUNO RELATA ERRO:                                       │
│     ════════════════════════════════════════════════════════════   │
│     python3 error-tracker.py error <descricao>                  ║   │
│     python3 error-tracker.py falsepos <descricao>               ║   │
│     ════════════════════════════════════════════════════════════   │
│     → Registrar erro + tentar novamente                          │
│     → Score de confiança--                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Regras de Validação

```
┌─────────────────────────────────────────────────────────────────────┐
│                 ANTES DE FALAR "PRONTO"                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  OBRIGATÓRIO VALIDAR:                                            │
│                                                                      │
│  1. COMPILAÇÃO                                                     │
│     ├── TypeScript: npx tsc --noEmit                             │
│     ├── JavaScript: node --check                                  │
│     ├── Python: python3 -m py_compile                            │
│     └── Resultado: 0 = OK, ≠0 = ERRO                            │
│                                                                      │
│  2. IMPORTS                                                       │
│     ├── Verificar caminhos relativos                               │
│     ├── Verificar arquivos existem                                │
│     └── Resultado: imports quebrados = ERRO                      │
│                                                                      │
│  3. LÓGICA BÁSICA                                                 │
│     ├── Null checks presentes?                                    │
│     ├── Async/await correto?                                      │
│     ├── Promises com catch?                                       │
│     └── Resultado: problemas = ERRO                              │
│                                                                      │
│  4. TESTES (se existirem)                                        │
│     ├── Rodar testes relacionados                                 │
│     └── Resultado: testes falham = ERRO                          │
│                                                                      │
│  5. ESCOPO                                                        │
│     ├── Não mudou mais do que o solicitado?                       │
│     └── Resultado: escopo rompido = AVISO                        │
│                                                                      │
│  SE QUALQUER UM FALHAR → NÃO FALAR "PRONTO"                      │
│  → Mostrar erro ao Bruno                                          │
│  → Corrigir antes de falar "pronto"                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📋 Comandos do Error Tracker

```bash
# Registrar erro reportado por Bruno
python3 ~/kothar/scripts/error-tracker.py error "o login continua dando erro"

# Registrar acerto (Bruno confirmou que funcionou)
python3 ~/kothar/scripts/error-tracker.py acerto err-20260824-143000-001 "Era o try/catch que não retornava erro"

# Registrar falso positivo (Bruno disse que não funcionou após eu falar "pronto")
python3 ~/kothar/scripts/error-tracker.py falsepos "Falei que corrigi mas erro continua"

# Ver status da sessão
python3 ~/kothar/scripts/error-tracker.py status

# Ver erros pendentes
python3 ~/kothar/scripts/error-tracker.py list
```

---

## 🚨 Alertas e Scores

```
╔══════════════════════════════════════════════════════════════╗
║                    SCORE DE CONFIANÇA                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Início:    ██████████ 100%                               ║
║                                                              ║
║  Após 1 falso positivo:                                     ║
║  ████████░░ 75%                                             ║
║  ⚠️ Alerta: "Verificar mais antes de falar 'pronto'"       ║
║                                                              ║
║  Após 2 falsos positivos:                                   ║
║  ██████░░░░ 50%                                             ║
║  🔶 Alerta: "Parar e pedir para Bruno testar"              ║
║                                                              ║
║  Após 3 falsos positivos:                                   ║
║  ███░░░░░░░ 25%                                             ║
║  🔴 BLOQUEADO: "Intervenção humana requerida"              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 📝 Template de Resposta

### Quando vai falar "pronto":

```
═══════════════════════════════════════════════════════════════════════

✅ CORREÇÃO IMPLEMENTADA

Arquivo: backend/servicos/auth/login.service.ts
Função: autenticarUsuario()

📝 O que foi feito:
   - Adicionado try/catch com retorno de erro
   - Validado null antes de usar

🔍 VALIDAÇÃO AUTOMÁTICA:
   ✅ Sintaxe OK (TypeScript compila)
   ✅ Imports OK (caminhos corretos)
   ✅ Lógica OK (null checks presentes)
   ✅ Testes: rodando...
   
⏳ Por favor, TESTE o fluxo de login para confirmar:
   curl -X POST http://localhost:3000/api/auth/login -d '{"cpf":"123","senha":"456"}'

═══════════════════════════════════════════════════════════════════════
```

### Quando Bruno confirma:

```
═══════════════════════════════════════════════════════════════════════

🎉 PERFEITO! Funcionou!

💾 REGISTRANDO ACERTO...
   ├── Tipo: ERRO_DE_LOGICA
   ├── Solução: try/catch deve retornar erro, não null
   ├── Padrão identificado: Sempre usar try/catch com throw
   └── Salvo em: error-tracker.json + Cofre

📊 Score de Confiança: ████████░░ 80%

═══════════════════════════════════════════════════════════════════════
```

### Quando Bruno reporta erro:

```
═══════════════════════════════════════════════════════════════════════

😔 ENTENDI - Erro continua

💾 REGISTRANDO ERRO...
   ├── Tipo: FALSO_POSITIVO (grave)
   ├── O que eu fiz: "try/catch retornando erro"
   ├── O que aconteceu: Erro persiste
   └── Tentativas: 2/3

⚠️ Score de Confiança: ████████░░ 75%

🔄 Tentando novamente com mais cuidado...
   Vou analisar o código linha por linha...

═══════════════════════════════════════════════════════════════════════
```

---

## 🔗 Integração

### No Core Loop:

```
AGIR (execution)
    ↓
AUTO-VALIDATE ← ANTES DE RELATAR
    ├── Rodar validação automática
    ├── Se falhar: mostrar erro, NÃO falar "pronto"
    └── Se passar: testar com Bruno
    ↓
Se Bruno confirma:
    → APRENDER: registrar acerto
Se Bruno reporta erro:
    → APRENDER: registrar erro
    → Retry com score--
    → Se 3 strikes: bloquear
```

---

## 📁 Arquivos Gerados

```
~/.claude/projects/-home-bruno-kothar/memory/erros/
├── error-tracker.json           # Banco de dados de erros
├── acertos/
│   └── correcoes-2026-08.md    # Correções documentadas
└── padroes/
    ├── erros-comuns.md           # Padrões de erros
    └── acertos-documentados.md   # O que funcionou

Cofre/00_Memoria/Kothar/Erros/
├── 2026-08-Erros.md             # Erros do mês
└── Padroes/
    └── Regras-Geradas.md        # Regras geradas de erros
```

---

*Skill criada em 2026-08-24 — Kothar v3.0*
