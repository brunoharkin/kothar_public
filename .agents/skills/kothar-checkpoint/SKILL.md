---
name: kothar-checkpoint
description: >-
  Skill do Kothar: Sistema de checkpoints e handoff automático para sessões longas.
  Ativar quando tokens estiverem altos (>80k), quando uma fase importante for concluída,
  ou quando Bruno disser "snapshot", "checkpoint" ou "vamos encerrar".
  Previne perda de contexto em tarefas multi-sessão.
---

# Skill: Kothar Checkpoint — Handoff Automático

> **Princípio Zen Init:** Sessão nova começa limpa, mas retomada é rápida. Zero burocracia de re-leitura se handoff existe.

## Quando Criar Checkpoint

```
✅ Criar automaticamente quando:
   - Tokens da sessão > 80k
   - Uma fase do plano de voo foi concluída
   - Bruno diz "snapshot" / "checkpoint" / "encerrar"
   - Erro crítico que exige nova sessão limpa

✅ Criar obrigatoriamente antes de:
   - Sugerir /clear ou reinício de sessão
   - Tarefa que vai durar >30 min de trabalho
```

---

## Formato do Handoff Ativo

Salvar em `00_Memoria/Snapshots/handoff-ativo.md`:

```markdown
---
versao: kothar-handoff-v2
data: YYYY-MM-DD HH:MM
projeto: [nome-do-projeto]
fase-atual: [Discovery|Design|Build|Verify|Ship]
tokens-usados: [estimativa]
---

# Handoff Ativo — [Projeto] — [Data]

## Contexto Essencial (3-5 linhas)
[O que está sendo feito e por quê]

## Stack em Uso
[Tecnologias + versões]

## Estado Atual
[O que foi feito até aqui — bullet points]

## Próxima Etapa Imediata
[A PRÓXIMA AÇÃO específica — não vaga]

## Checklist de Retomada
- [ ] [Passo 1 da retomada]
- [ ] [Passo 2 da retomada]
- [ ] [Passo 3 da retomada]

## Arquivos Críticos para Ler ao Retomar
- `[arquivo1.md]` — [por que ler]
- `[arquivo2.ts]` — [por que ler]

## Decisões Tomadas (não repetir discovery)
- [Decisão 1]: [justificativa]
- [Decisão 2]: [justificativa]

## Problemas Conhecidos / Cuidados
- [Armadilha 1]: [como evitar]
```

---

## Protocolo de Retomada (Zen Init)

Quando existe `handoff-ativo.md`:

1. **NÃO** re-ler `prompt-principal.md` completo
2. **NÃO** re-executar discovery do zero
3. **LER APENAS:** `handoff-ativo.md` + arquivo de plano ativo
4. Executar **imediatamente** a "Próxima Etapa Imediata" do handoff
5. Banner de retomada: `[Kothar v4.0] Conectado | Projeto: X | Retomando Checkpoint... Pronto.`

---

## Arquivamento de Checkpoints

Após criar handoff-ativo.md, também salvar cópia em:
```
00_Memoria/Snapshots/checkpoints/cp-YYYYMMDD-HHMM-[slug].md
```

Isso permite rollback para estados anteriores se necessário.

---

## Limpeza de Handoff

Ao **concluir definitivamente** uma tarefa:
1. Remover `handoff-ativo.md` (limpar máquina de estado)
2. Salvar relatório final em `00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md`
3. Apresentar relatório de entrega para Bruno

---

## Economia de Tokens (Zen Init)

O handoff ativo economiza até **15.000 tokens** por sessão de retomada:
- Evita re-leitura de `prompt-principal.md`
- Evita re-execução de buscas ChromaDB já feitas
- Foca apenas no estado comprimido essencial

---

*Kothar v4.0 — Checkpoint System | Ugarit Digital*

