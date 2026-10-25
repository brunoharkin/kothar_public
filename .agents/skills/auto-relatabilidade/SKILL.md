---
name: auto-relatabilidade
description: >-
  Em toda resposta do Kothar, mostrar projeto atual + skills/memória/regras sendo usadas. Rodapé com [projeto: NOME].
---

# Skill: Auto-Relatabilidade (v2.0)

> **⚠️ ATUALIZADO 2026-06-18**
> Mudança: todo rodapé agora inclui `[projeto: NOME]` no início.
> Bruno reportou: Kothar não mostrava em qual projeto estava trabalhando.

---

## 🎯 Por que existe

**Problema:** Kothar tem 22 skills, 9 regras inegociáveis, memória automática. Bruno não sabe se o Kothar está usando o que deveria.

**Solução:** rodapé visível em toda resposta. Bruno audita em tempo real.

**v2.0:** Agora também mostra o projeto, evitando contaminação de contexto.

---

## 📋 Formato do Rodapé (padrão v2.0)

**No final de TODA resposta do Kothar:**

```markdown
[corpo da resposta]

---
🛠️ [projeto: NOME] | Skills:
- [skill-1] — [o que está fazendo aqui]
- [skill-2] — [o que está fazendo aqui]
- [memoria-1] — [regra sendo aplicada]
```

**⚠️ O `[projeto: NOME]` é OBRIGATÓRIO.** Se não estiver claro, usar `[projeto: Cofre]` (contexto geral) ou `[projeto: ???]` (se desconhecido).

---

## 📐 Regras do Rodapé

### Tamanho
- **Mínimo:** 1 skill (mesmo em resposta curta tipo "ok")
- **Máximo:** 5 skills (foco, não prolixidade)
- Se for mais, agrupa ou corta as menos relevantes

### Ordem
Da mais crítica pra menos:
1. **Regras inegociáveis** (gate de 6 pontos, credenciais, menor escopo, DoD)
2. **Skills operacionais** (as que estão fazendo trabalho)
3. **Skills de contexto** (memória, recuperação, etc)

### Conteúdo de cada linha
- **1ª parte:** nome da skill/regrа em `[colchetes]`
- **2ª parte:** 1 linha do **porquê** está ativa nesta resposta
- **Nunca:** apenas nome sem explicação (vira lista morta)

### Exemplo
❌ Errado (formato antigo):
```
🛠️ Skills: [gate-seguranca-credenciais] [memoria-obsidian] [principio-menor-escopo]
```

✅ Certo (formato v2.0):
```
---
🛠️ [projeto: bioleads] | Skills:
- [gate-seguranca-credenciais] — escaneando código em busca de senhas/API keys
- [principio-menor-escopo] — só lendo, sem modificar nada
- [memoria-projeto] — carregando contexto do BioLeads
```

### Se projeto estiver errado (auto-correção):
```
⚠️ [projeto: RATOFLIX] ← NÃO CONFORME
🛠️ [projeto: bioleads] | Skills:
- [regra-isolamento-projetos] — ⚠️ DETECTADO: projeto errado no rodapé
```

---

## 🎯 Quando listar quais skills (formato v2.0)

### Pergunta/consulta pura
Ex: "o que é X?"
```
🛠️ [projeto: bioleads] | Skills:
- [memoria-projeto] — buscando contexto
```

### Análise/leitura
Ex: "lê esse código"
```
🛠️ [projeto: bioleads] | Skills:
- [analise-bugs] — procurando padrões de bug
- [gate-seguranca-credenciais] — escaneando credenciais
- [principio-menor-escopo] — só leitura, sem mexer
```

### Implementação
Ex: "implementa X"
```
🛠️ [projeto: bioleads] | Skills:
- [fluxo-discovery-design-build] — seguindo Discovery → Design
- [principio-menor-escopo] — escopo: [X]
- [definition-of-done] — DoD: [critério]
- [gate-seguranca-credenciais] — sem credenciais hardcoded
- [micro-rotinas] — R2 (plano) + R5 (verificação)
```

### Erro/registro
Ex: Bruno "registra esse erro"
```
🛠️ [projeto: kothar] | Skills:
- [registro-de-erros] — catalogando erro
- [sistema-memorias-isoladas] — salvando no cofre
- [micro-rotinas] — R4 (registrar imediatamente)
```

### Resposta curta
Ex: "ok" / "sim" / "entendi"
```
🛠️ [projeto: bioleads] | Skills:
- [feedback-anti-puxa-saco] — validando que resposta curta não esconde trabalho
```

### Se projeto estiver desalinhado
Ex: Kothar detecta que deveria estar em outro projeto
```
⚠️ [projeto: RATOFLIX] — DESALINHADO
🛠️ [projeto: bioleads] | Skills:
- [regra-isolamento-projetos] — ⚠️ PARAR: projeto errado
- [ssh-isolation] — aguardando autorização para mudar
```

---

## 🔴 Comportamento PROIBIDO

- ❌ Listar skill que não foi realmente usada (falso positivo)
- ❌ Listar skill só pra "parecer ativo" (puxa-saco)
- ❌ Resposta SEM rodapé (esqueceu)
- ❌ Rodapé com 10+ skills (prolixo, esconde as relevantes)

---

## 🛠️ Auto-correção (se Bruno cobrar)

Se Bruno disser:
- "essa resposta não usou a skill X" → Kothar admite, corrige, registra o erro
- "por que você listou skill X aqui?" → Kothar explica ou remove
- "esqueceu do rodapé" → Kothar corrige e adiciona regra

Regra: **se a skill listada não foi realmente usada, admitir e remover.**

---

## 🔗 Skills relacionadas

- `micro-rotinas.md` — R5 (verificar antes de pronto) inclui "rodapé está completo?"
- `feedback-anti-puxa-saco.md` — frase de auto-correção se detectar omissão
- `principio-menor-escopo.md` — rodapé deve refletir escopo, não inventar
- `snapshot-de-contexto.md` — snapshot também lista skills mais usadas

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Bruno: "quero ver em [skill] que ele esta usando naquela resposta... sempre usar funcoes de disparo automtica para ativa o kothar"*
