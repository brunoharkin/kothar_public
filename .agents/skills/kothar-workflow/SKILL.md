---
name: kothar-workflow
description: >-
  Skill do Kothar: Fluxo de trabalho obrigatório em 6 fases para toda e qualquer tarefa.
  Ativar quando o usuário pedir para implementar, criar, corrigir ou refatorar qualquer coisa.
  Fases: Entender → Pesquisar → Planejar → Implementar → Testar → Salvar.
---

# Skill: Kothar Workflow — 6 Fases Obrigatórias

> **REGRA MÁXIMA:** Não existe "ajuste rápido". Todas as 6 fases são obrigatórias.

## Sequência

```
1. ENTENDER → 2. PESQUISAR → 3. PLANEJAR → 4. IMPLEMENTAR → 5. TESTAR → 6. SALVAR
```

---

## FASE 1 — ENTENDER
- Ler a mensagem INTEIRA do usuário
- Identificar objetivo final, restrições e dados sensíveis envolvidos
- Identificar projeto atual (`pwd`) e escopo exato
- **PERGUNTAR se houver dúvida — nunca suposição**
- ❌ NÃO começar a codar sem entender completamente

**Perguntas obrigatórias de validação:**
```
□ Qual é o objetivo final?
□ Quais são as restrições (segurança, prazo)?
□ Existem dados sensíveis?
□ Qual projeto? Qual escopo exato?
□ O que está FORA do escopo (zonas proibidas)?
```

---

## FASE 2 — PESQUISAR
- Buscar código existente no projeto (grep, find)
- Consultar memória/histórico de decisões
- Verificar `visao.md` e `estado-atual.md` do projeto
- ✅ SE encontrou código similar → reusar
- ❌ NÃO criar código novo se existir similar

---

## FASE 3 — PLANEJAR
- Criar plano detalhado antes de qualquer código
- Salvar plano em `planos/YYYY-MM-DD-tarefa.md`
- Mostrar plano ao Bruno e **aguardar aprovação** (CP2)
- Incluir: arquivos a modificar, mudanças específicas, riscos, como testar
- ❌ NÃO implementar sem plano aprovado

---

## FASE 4 — IMPLEMENTAR
```
REGRA DE OURO: "UMA ALTERAÇÃO POR VEZ"
1. Fazer UMA mudança pequena
2. Testar
3. Se OK → próxima mudança
4. Se ERRO → corrigir ANTES de continuar
```
- ❌ NÃO fazer 10 mudanças de uma vez
- ❌ NÃO ignorar erros e seguir em frente

---

## FASE 5 — TESTAR
Para cada alteração:
```
□ Compilação OK? (npm run build / python -m pytest)
□ Console do browser: zero erros vermelhos?
□ Funcionalidade específica funciona?
□ Funcionalidades relacionadas não quebraram?
□ Segurança: sem credenciais expostas?
```
- ❌ NÃO prosseguir se algum teste falhar

---

## FASE 6 — SALVAR
```bash
# Formato de commit:
tipo(escopo): descrição em português
feat(autenticacao): adiciona validação de email
fix(menu): corrige colapso em mobile
```
- ❌ NÃO commitar código quebrado (gate G3 obrigatório)
- Informar Bruno com relatório de entrega

---

*Kothar v4.0 — Ugarit Digital*

