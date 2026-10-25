---
name: fluxo-discovery-design-build
description: 3 modos integrados — Discovery (resposta final pronta) → Build (implementação) → Mudança (diff + impacto). Substitui GSD fraco. Força estrutura completa ANTES de codar.
metadata:
  tipo: skill
  data: 2026-06-10
  categoria: fluxo-principal
  substitui: fluxo-gsd-desenvolvimento.md
---

# Skill: Fluxo Discovery → Design → Build → Verify → Ship (v2.0)

> **Esta skill SUBSTITUI o GSD fraco E integra os 3 modos (Discovery/Build/Mudança).**
> A skill antiga (`fluxo-gsd-desenvolvimento.md`) fica mantida como referência histórica.
>
> Bruno: "quero a resposta final direta... ja com a minha ideia completamente viabilizada... ja deu a recomentacao final apartir dai eu mudo oque eu quero mais"

---

## 🔄 Visão Geral dos 3 Modos

```
[Bruno faz pedido]
     ↓
┌─────────────────────────────────────┐
│ MODO DISCOVERY (resposta-final-pronta) │
│ - Analisa 15 lacunas                 │
│ - Recomenda stack (escala)           │
│ - Gera mapa de amarração lógica      │
│ - Popula DoD                         │
│ - Mostra risco + impacto             │
│ → Resposta FECHADA, Bruno aprova     │
└─────────────────────────────────────┘
     ↓ (Bruno aprova)
┌─────────────────────────────────────┐
│ MODO BUILD                            │
│ - Implementa seguindo EXATAMENTE     │
│   o design travado                    │
│ - Aplica R4 (registrar decisão)       │
│ - Aplica R5 (DoD antes de "Pronto")  │
│ → Código + commit                    │
└─────────────────────────────────────┘
     ↓ (Bruno pede ajuste)
┌─────────────────────────────────────┐
│ MODO MUDANÇA (diff + impacto)         │
│ - Puxa design.md atual               │
│ - Mostra diff + impacto              │
│ - Aplica após aprovação              │
│ - Atualiza histórico                 │
│ → Volta pro MODO BUILD               │
└─────────────────────────────────────┘
```

---

## 🔴 MODO 1 — DISCOVERY (sempre que pedido for vago)

**Quando:** Bruno pede feature, MVP, sistema, etc., sem detalhar.

**O que Kothar faz:**

1. Lê o pedido
2. Aplica `analise-de-lacunas.md` (15 dimensões)
3. Consulta `recomendador-stack.md` (7 critérios)
4. Gera `amarracao-logica.md` (frontend ↔ backend ↔ DB ↔ UX)
5. Lista riscos
6. Define DoD (de `definition-of-done.md`)
7. **Popula o template de `resposta-final-pronta.md`**
8. **NÃO implementa. Espera Bruno aprovar.**

**Skill usada:** `resposta-final-pronta.md` (a principal deste modo)

---

## 🛠️ MODO 2 — BUILD (depois de Discovery aprovado)

**Quando:** Bruno disse "aprovo" / "pode implementar" / "vai".

**O que Kothar faz:**

1. Puxa o design travado (do Discovery aprovado)
2. Implementa EXATAMENTE o que tá no design
3. Aplica `principio-menor-escopo.md` (não mexe no que não foi pedido)
4. Aplica `definition-of-done.md` (DoD antes de "Pronto", exigindo sucesso no `validador.sh` e score >= 90 no `analise-codigo.py`)
5. Aplica `gate-seguranca-credenciais.md` (scan antes de commit)
6. Aplica R4 (registra decisão) + R5 (verificação sintática e de assertividade antes de pronto) + R6 (auto-aprendizado se necessário)
7. Atualiza estado-atual.md do projeto
8. **NÃO implementa nada que não estava no design aprovado**

**Se Bruno pedir algo NOVO no meio do Build:** volta pro MODO 1 (Discovery) só pro item novo.

---

## 🔄 MODO 3 — MUDANÇA (depois de Bruno pedir ajuste)

**Quando:** Bruno diz "troca X por Y" / "muda W" / "remove Z".

**O que Kothar faz:**

1. Puxa o design.md atual (não trabalha do zero)
2. Aplica `modo-mudanca.md`:
   - Mostra diff (remover/adicionar/modificar)
   - Estima impacto (esforço/risco/componentes)
   - Plano de aplicação
   - Mudanças em cascata (verificar dependências)
3. Espera Bruno aprovar
4. Aplica a mudança
5. Atualiza o design.md (adiciona entrada no histórico)
6. Volta pro MODO 2 (Build) com novo design

**Se a mudança for GRANDE (refatorar 30%+ do projeto):** volta pro MODO 1 (Discovery) com novo pedido.

---

## 📋 Templates por modo

### Template de Discovery
Ver `resposta-final-pronta.md`. Estrutura fixa:
- 📋 Pedido
- 🏗️ Arquitetura
- 🔍 Lacunas (15 dimensões)
- 🧠 Lógica amarrada
- ⚠️ Riscos
- 📊 DoD
- 💡 Stack (escala)
- 🛠️ Próximo passo
- ✅ Aprovo / Quero mudar

### Template de Build
Resposta curta (5-15 linhas):
- O que foi feito
- Onde (arquivos)
- Smoke test (passou/falhou)
- Próximo passo
- Aguardando "pode commitar"

### Template de Mudança
Ver `modo-mudanca.md`. Estrutura fixa:
- 🔄 Mudança
- 📊 Diff
- ⚠️ Impacto
- 🛠️ Plano
- 🔗 Cascata
- ✅ Aprovo

---

## 🔴 Comportamento PROIBIDO (geral)

- ❌ Pular MODO 1 (ir direto pro código sem Discovery)
- ❌ Implementar no MODO 1 (só depois de aprovado)
- ❌ Mudar design sem mostrar diff (MODO 3)
- ❌ Inventar feature que não estava no pedido
- ❌ Mexer no que Bruno não pediu (princípio do menor escopo)

---

## 🛠️ Auto-correção

Se Bruno disser:
- "você pulou a parte de discovery" → Kothar volta pro MODO 1
- "implementou sem eu aprovar" → Kothar reverte
- "mudou sem avisar" → Kothar mostra o diff retroativo
- "criou botão sem função" → Kothar volta no `amarracao-logica.md`, vê o que faltou

---

## 🔗 Skills usadas em conjunto

### Sempre
- `resposta-final-pronta.md` (MODO 1)
- `auto-relatabilidade.md` (rodapé)
- `principio-menor-escopo.md` (escopo)
- `definition-of-done.md` (DoD)

### Por modo
| Modo | Skills |
|---|---|
| Discovery | `resposta-final-pronta` + `analise-de-lacunas` + `recomendador-stack` + `amarracao-logica` |
| Build | `principio-menor-escopo` + `definition-of-done` + `gate-seguranca-credenciais` + `micro-rotinas` (R4, R5) |
| Mudança | `modo-mudanca` + `principio-menor-escopo` |

### Memória automática
- `feedback-anti-puxa-saco.md` (regra-mãe)
- `sistema-completo-kothar.md` (sistema consolidado)

---

*Skill atualizada em 2026-06-10 — Bruno Harkin / Kothar*
*v2.0: integrou 3 modos (Discovery/Build/Mudança) + resposta-final-pronta*
