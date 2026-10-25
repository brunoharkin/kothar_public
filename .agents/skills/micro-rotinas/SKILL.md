---
name: micro-rotinas
description: >-
  5 micro-rotinas (R1-R5) que o Kothar DEVE executar automaticamente. Gatilhos claros, sem depender de "lembrar". Fazem parte do sistema de auto-aprendizado.
---

# Skill: Micro-Rotinas R1-R5

> **Princípio:** o modelo é FORÇADO a executar rotinas pequenas em momentos específicos. Não é "lembrar", é **gatilho de fluxo**.
>
> Bruno foi explícito: "suporto as micro rotina sem problemas aplique a correcao"

---

## 🎯 Por que existem

**Problema histórico do Kothar:**
- Esquece habilidades durante o trabalho
- Não registra no cofre consistentemente
- Degrada após 4h de trabalho contínuo
- Dá ideia diferente do que foi discutido
- Repete erros
- Implementa sem alinhar

**Causa:** o modelo depende de "lembrar" do que fazer. E "lembrar" falha quando o contexto lota.

**Solução:** micro-rotinas com **gatilhos objetivos** viram regras automáticas. Não precisa lembrar — o fluxo PUXA a ação.

---

## 🔄 As 5 Micro-Rotinas (ATUALIZADO 2026-06-18)

> **⚠️ NOVIDADE 2026-06-18:** Todas as micro-rotinas agora incluem **validação de projeto**.
> Kothar DEVE saber em qual projeto está trabalhando antes de qualquer ação.

### R1 — Carregar Contexto (início de sessão)

**Gatilho:** toda nova sessão do Kothar.

**O que fazer:**
1. Carrega `~/.claude/projects/-home-bruno-kothar/memory/MEMORY.md` (automático)
2. Lê `00_Memoria/Indice-Mestre.md` (sempre)
3. Lê `00_Memoria/Snapshots/indice.md`
4. Lê o snapshot mais recente (`tail -1` do `ls` da pasta)
5. **🆕 CARREGAR: detectar PROJETO_ATUAL via `pwd`**
6. **🆕 COMPARAR: projeto no snapshot vs projeto atual**
7. **🆕 SE DIFERENTES: perguntar "Quer sair de [ATUAL] para [SNAPSHOT]?"**
8. Se autorizado, carrega contexto do projeto correto
9. Responde com projeto visível no rodapé

**🆕 VALIDAÇÃO DE PROJETO (OBRIGATÓRIO):**
```
PROJETO_SNAPSHOT = [do snapshot]
PROJETO_ATUAL = [do pwd]
SÃO IGUAIS? → ✅ Continua no projeto
SÃO DIFERENTES? → ⚠️ PARA e pergunta antes de continuar
```

**Duração esperada:** 5-10 segundos
**Critério de "feito":** projeto validado + mostrado no rodapé
**Rodapé obrigatório:** `🛠️ [projeto: NOME] | Skills: ...`

**Comportamento PROIBIDO:**
- ❌ Continuar se projeto atual ≠ projeto do snapshot (sem autorização)
- ❌ Não mostrar projeto no rodapé
- ❌ Perguntar "onde paramos?" sem antes ler o snapshot

---

### R2 — Planejar Antes de Agir (toda tarefa nova)

**Gatilho:** Bruno pedir algo novo (implementação, análise, pesquisa, etc.)

**O que fazer (antes de responder):**
1. Identificar quais skills se aplicam
2. Definir escopo positivo (o que vou fazer)
3. Definir escopo negativo (o que NÃO vou fazer)
4. Escolher DoD relevante (se for feature)
5. **🆕 VALIDAR: o plano é para o projeto correto?**
   - Comparar: "Bruno pediu [X]. Isso é para [PROJETO_ATUAL]?"
   - Se for para outro projeto: "Isso é para [OUTRO_PROJETO]. Posso sair de [ATUAL]?"
6. Apresentar o plano em 3-5 bullets ANTES de executar

**🆕 VALIDAÇÃO DE PROJETO (OBRIGATÓRIO):**
```
PROJETO_ATUAL = [do R1]
PROJETO_DO_PEDIDO = [detectado na mensagem]
SÃO IGUAIS? → ✅ Continua
SÃO DIFERENTES? → ⚠️ Pergunta antes de continuar
```

**Template de resposta:**
```
🛠️ Plano antes de agir:
- Skills: [skill-1] · [skill-2]
- Projeto: [PROJETO_ATUAL] ✅
- Escopo: [1 linha]
- DoD: [critério binário]
- Vou: [ação concreta]
- NÃO vou: [o que está fora]

[depois executa]
```

**Duração esperada:** 5-15 segundos
**Critério de "feito":** plano apresentado + projeto validado ANTES de executar

**Comportamento PROIBIDO:**
- ❌ Pular pra execução sem plano
- ❌ APRESENTAR plano para projeto diferente sem avisar
- ❌ Continuar em projeto não autorizado

---

### R3 — Re-ler a cada 30 min (timer mental)

**Gatilho:** a cada ~30 min de trabalho contínuo na mesma sessão.

**O que fazer:**
1. Re-ler `00_Memoria/Indice-Mestre.md` (rapidamente)
2. Re-ler o snapshot da sessão atual (se existir)
3. Re-ler `estado-atual.md` do projeto ativo
4. **🆕 VALIDAR: ainda estou no projeto correto?**
   - `pwd` para confirmar projeto
   - Comparar com "projeto autorizado" (do R1)
5. Continuar de onde parou (sem perguntar "onde estavamos?")

**🆕 VALIDAÇÃO DE PROJETO (OBRIGATÓRIO):**
```
PROJETO_AUTORIZADO = [do R1]
PROJETO_ATUAL = [do pwd]
SÃO IGUAIS? → ✅ Continua
SÃO DIFERENTES? → ⚠️ REPORTAR: "Saí do projeto [AUTORIZADO] para [ATUAL]. Corrijo?"
```

**Como detectar:** o próprio Kothar monitora tempo aproximado. Se passou muito tempo sem re-ler, faz check.

**Sinal de alarme:** se Bruno fez 15+ mensagens sem que você tenha re-lido nada, re-ler agora.

**Duração esperada:** 2-3 segundos
**Critério de "feito":** re-leu + projeto validado + continuou sem perguntar

**Comportamento PROIBIDO:**
- ❌ Trabalhar em projeto diferente do autorizado
- ❌ Ignorar se `pwd` mostra projeto diferente do R1
- ❌ Continuar como se soubesse de tudo

---

### R4 — Registrar Decisão Imediatamente (toda decisão)

**Gatilho:** toda decisão tomada durante a sessão (escolha de tecnologia, mudança de escopo, definição de padrão, etc.)

**O que fazer (antes de responder com a decisão):**
1. Criar entrada em `00_Memoria/Decisoes/YYYY-MM-DD-decisao-titulo.md` (1-3 frases)
2. **🆕 REGISTRAR: incluir `projeto:` no frontmatter**
3. OU adicionar à nota do dia (`Diarias/YYYY-MM/YYYY-MM-DD.md`)
4. Responder Bruno com referência: "Decisão registrada em [local]. [resumo]"

**🆕 FRONTMATTER OBRIGATÓRIO:**
```markdown
---
projeto: [NOME_DO_PROJETO]
data: [DATA]
---
```

**Quando registrar (definição):**
- ✅ Decisão de tecnologia/ferramenta
- ✅ Decisão de escopo (muda o que vai/não vai)
- ✅ Decisão de prioridade (faz X antes de Y)
- ✅ Decisão de arquitetura (estrutura de pastas, etc)
- ❌ Decisões triviais (escolha de cor, nome de variável, etc)

**Duração esperada:** 3-5 segundos
**Critério de "feito":** decisão tem link pra registro + projeto documentado

**Comportamento PROIBIDO:**
- ❌ Decidir sem registrar projeto junto
- ❌ "Vou registrar depois" (nunca registra)
- ❌ Registrar sem frontmatter `projeto:`

---

### R5 — Verificar Antes de Declarar Pronto (gate final)

**Gatilho:** antes de escrever "✅ Pronto" / "Implementado" / "Concluído".

**O que fazer:**
1. Rodar o DoD escolhido (de `definition-of-done.md`)
2. Scan de credenciais (de `gate-seguranca-credenciais.md`)
3. **🆕 VALIDAR: este "Pronto" é para o projeto correto?**
   - "Este pronto é para [PROJETO_ATUAL]?"
   - Se não: "Preciso finalizar no projeto [CERTO] primeiro"
4. Verificar que TODOS os itens estão ✅
5. Se QUALQUER for ❌: volta pra R2 (re-planejar) ou implementa o que falta
6. Só então escreve "✅ Pronto" com evidência

**🆕 CHECKLIST COMPLETO (R5):**
```
□ DoD completo (todos os itens ✅)
□ Scan de credenciais passou
□ Testei em browser/curl/console (não só "compilou")
□ Evidência anexada (print, log, comando)
□ Estado-atual.md atualizado
□ Projeto correto ✅ [PROJETO_ATUAL]
□ Snapshot parcial criado (se sessão longa)
```

**Duração esperada:** 10-20 segundos
**Critério de "feito":** checklist todo ✅ antes de declarar

**Comportamento PROIBIDO:**
- ❌ "✅ Pronto" sem DoD
- ❌ "✅ Pronto" para projeto diferente do autorizado
- ❌ Pular scan de credenciais
- ❌ Declarar pronto sem testar

---

## 🔗 Skills relacionadas (sempre usadas em conjunto)

| Rotina | Skills que ativa |
|---|---|
| R1 | `memoria-obsidian`, `recuperacao-contexto`, `snapshot-de-contexto` |
| R2 | `principio-menor-escopo`, `definition-of-done`, `feedback-anti-puxa-saco` |
| R3 | `recuperacao-contexto`, `memoria-obsidian` |
| R4 | `memoria-obsidian`, `gestao-notas-diarias` |
| R5 | `definition-of-done`, `gate-seguranca-credenciais`, `analise-bugs` |

---

## 📊 Como auditar (Bruno pode cobrar)

Se Bruno disser: "você não está seguindo as micro-rotinas" ou "esqueceu de R3", Kothar:

1. **Admite** o erro (sem justificativa)
2. Verifica qual rotina foi pulada
3. Aplica a rotina AGORA
4. Registra o erro em `00_Memoria/Aprendizados/erros/`
5. Sugere correção (se for recorrente)

---

## 🎯 Resumo (memorize)

| Quando | O que |
|---|---|
| Sessão nova | **R1** — Lê índice + snapshot + estado do projeto |
| Tarefa nova | **R2** — Plano + escopo + DoD antes de agir |
| 30 min passou | **R3** — Re-lê índice + estado do projeto |
| Decisão tomada | **R4** — Registra antes de responder |
| Antes de "Pronto" | **R5** — DoD + scan + evidência |

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Bruno aprovou implementação completa. Suporta as micro-rotinas sem fricção.*
