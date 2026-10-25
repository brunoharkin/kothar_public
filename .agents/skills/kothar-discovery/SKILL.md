---
name: kothar-discovery
description: >-
  Skill do Kothar: Fluxo Discovery → Design → Build → Verify → Ship.
  Ativar quando Bruno fizer pedido vago, MVP, feature nova, sistema novo ou qualquer
  solicitação sem especificações técnicas completas. SUBSTITUI o fluxo GSD fraco.
  Nunca pular para implementação sem Discovery aprovado por Bruno.
---

# Skill: Kothar Discovery → Design → Build → Verify → Ship

> **Esta skill SUBSTITUI o GSD fraco.** Nenhum código antes de Discovery aprovado.

## Visão Geral dos 3 Modos

```
[Bruno faz pedido]
      ↓
┌─────────────────────────────────────┐
│ MODO DISCOVERY                       │
│ - Analisa lacunas e riscos           │
│ - Recomenda stack                    │
│ - Gera mapa de integração            │
│ - Define DoD                         │
│ → Resposta FECHADA → Bruno aprova   │
└─────────────────────────────────────┘
      ↓ (Bruno aprova)
┌─────────────────────────────────────┐
│ MODO BUILD                           │
│ - Implementa seguindo design travado │
│ - Uma mudança por vez com teste      │
│ → Código + commit                   │
└─────────────────────────────────────┘
      ↓ (Bruno pede ajuste)
┌─────────────────────────────────────┐
│ MODO MUDANÇA                         │
│ - Mostra diff + impacto da mudança   │
│ - Aplica após aprovação              │
│ → Volta pro MODO BUILD              │
└─────────────────────────────────────┘
```

---

## MODO 1 — DISCOVERY

**Quando:** Bruno pede feature/MVP/sistema sem detalhar.

**Kothar faz:**
1. Lê o pedido completo
2. Mapeia 15 dimensões de lacunas:
   - Usuários-alvo, Volume, Dados sensíveis, Integrações, Offline?
   - Performance esperada, Testes obrigatórios, Deploy, Manutenção
   - Stack existente, Prazo real, Orçamento, Equipe, Riscos top-3
3. Recomenda stack por critérios de escala
4. Gera mapa de integração: Frontend ↔ Backend ↔ DB ↔ UX
5. Define DoD binário (critérios de "Pronto")
6. Lista riscos e trade-offs
7. **NÃO implementa. Espera Bruno aprovar.**

**Template de resposta Discovery:**
```markdown
## Discovery: [Nome do Pedido]

### Entendimento
[O que Bruno quer em 2-3 linhas]

### Lacunas Identificadas
[Lista das dimensões analisadas]

### Stack Recomendada
[Tecnologias + justificativa por critério de escala]

### Mapa de Integração
Frontend → Backend → DB → Serviços externos

### Riscos (Top 3)
1. [Risco + mitigação]
2. [Risco + mitigação]
3. [Risco + mitigação]

### DoD
- [ ] [Critério binário 1]
- [ ] [Critério binário 2]

### Recomendação
vai / não vai / vai com ressalvas: [justificativa crua]

→ Aguardando aprovação de Bruno para iniciar Build.
```

---

## MODO 2 — BUILD

**Quando:** Bruno disse "aprovo" / "pode implementar" / "vai".

**Kothar faz:**
1. Salva design travado em `design.md`
2. Cria checklist de implementação (Fase por Fase)
3. Implementa seguindo EXATAMENTE o design (sem improvisar)
4. Uma mudança por vez com teste antes de avançar
5. Aplica gate de segurança a cada arquivo
6. DoD completo antes de declarar "Pronto"

---

## MODO 3 — MUDANÇA

**Quando:** Bruno pede ajuste no design já aprovado.

**Kothar faz:**
1. Mostra o que estava no design atual (diff)
2. Mostra impacto da mudança (o que quebra, o que muda)
3. Aguarda aprovação de Bruno
4. Aplica mudança no `design.md` e volta pro Build

---

## Fases Obrigatórias (gate a gate)

1. **Discovery** → `discovery.md` com problema, restrições, escopo. Bruno aprova.
2. **Design** → `design.md` com stack+versões, schema, componentes, fluxos, DoD. Bruno aprova.
3. **Build** → código + commits curtos + smoke test local
4. **Verify** → DoD completo, scan de credenciais, teste em browser
5. **Ship** → commit + push (com permissão CP4) + nota de entrega

---

*Kothar v4.0 — Discovery obrigatório | Ugarit Digital*

