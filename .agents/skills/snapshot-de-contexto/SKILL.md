---
name: snapshot-de-contexto
description: >-
  Snapshot compacto de sessão que serve de "transferência de memória" para próxima sessão. Disparado manualmente por "vamos encerrar". Garante que nada se perca entre sessões.
---

# Skill: Snapshot de Contexto

> **Função:** gerar arquivo compacto que a próxima sessão do Kothar vai ler pra retomar o trabalho sem perder nada.
>
> **Regra:** tamanho é o necessário pra acertividade. Sem teto. Sem mínimo rígido.

---

## 🎯 O que é e por que existe

**Problema:** o chat do dia acaba. O Kothar de amanhã precisa saber onde parou. Sem snapshot:
- Bruno gasta 5-10 min recapitulando
- Kothar "lembra" errado (alucina contexto)
- Decisões se perdem
- Trabalho grande perde ritmo

**Solução:** ao fim de cada sessão, gerar um snapshot compacto (mas completo) que registra exatamente onde paramos.

**Bônus (2026-06-10):** o snapshot também inclui métricas de qualidade da sessão — quantos erros foram registrados, quais skills mais usadas, etc. Isso permite que o Kothar de amanhã entre calibrado.

---

## 📁 Onde fica

```
Cofre/
└── 00_Memoria/
    └── Snapshots/
        ├── indice.md                  ← índice cronológico
        ├── 2026-06/
        │   ├── 2026-06-10-22-30.md   ← snapshot de fim de sessão
        │   ├── 2026-06-10-20-15.md   ← snapshot após commit
        │   └── ...
        └── ...
```

**Estrutura por mês:** `Snapshots/YYYY-MM/YYYY-MM-DD-HH-MM.md`

**Por que mês separado?** Pra não ter pasta com 100+ arquivos. Cada mês vira subpasta.

---

## 🔴 Gatilho ATIVO (por enquanto)

**Único gatilho ativo agora:** Bruno disser uma das frases:

- "vamos encerrar"
- "vamos parar"
- "até amanhã"
- "encerrar sessão"
- "salvar snapshot"
- "snapshot"

**Comportamento:**
1. Bruno fala a frase
2. Kothar PARA o que estiver fazendo
3. Kothar gera o snapshot da sessão atual
4. Kothar atualiza `indice.md`
5. Kothar confirma: "Snapshot salvo em [caminho]. Até [próxima sessão]."

---

## 🟡 Gatilhos FUTUROS (não ativos ainda, Bruno vai decidir depois)

- Após cada `git commit` (snapshot da decisão commitada)
- A cada 4h de trabalho contínuo (preventivo)
- Mudança grande de contexto (projeto diferente, assunto novo)

Bruno disse: "esses ficam pra depois, agente coloca. Vamos testar primeiro."

---

## 📋 Template do Snapshot

```markdown
---
data: YYYY-MM-DD
hora: HH:MM
projeto: "bioleads" | "kothar" | "cofre" | "geral"
tipo: "snapshot-sessao"
gatilho: "fim-sessao"
sessao_iniciada: "YYYY-MM-DD HH:MM"
duracao_estimada: "X horas"
metricas:
  erros_registrados: N          # erros catalogados nesta sessão
  skills_mais_usadas: ["X", "Y"]  # auditoria via auto-relatabilidade
  decisoes_registradas: N       # quantas R4 executou
  arquivos_criados: N
  arquivos_modificados: N
---

# Snapshot — DD/MM/YYYY HH:MM

## 🎯 Onde paramos
[1-3 frases: estado atual do projeto, em que ponto estamos, o que está em aberto]

## ✅ Decisões desta sessão
- [Decisão 1 — citação direta ou paráfrase + arquivo/link onde foi registrada]
- [Decisão 2]
- [Decisão 3]
- [Adicionar quantas tiver — sem resumir demais]

## 📝 Em andamento
- [ ] [Tarefa em progresso — quem é dono, onde parou]
- [ ] [Tarefa em progresso]
- [Adicionar quantas tiver]

## ⏭️ Próximos passos (próxima sessão)
1. [Ação concreta — sem ambiguidade]
2. [Ação concreta]
3. [Ação concreta]
[Numerar e ser específico]

## ⚠️ Pontos de atenção (NÃO ESQUECER)
- [Coisa crítica que pode se perder]
- [Bloqueio conhecido]
- [Risco em monitoramento]
- [Decisão que precisa de validação]
- [Erro que aconteceu e não pode repetir]

## 📂 Onde encontrar mais detalhes
- Conversa completa: `00_Memoria/Diarias/YYYY-MM/YYYY-MM-DD.md`
- Decisões X, Y, Z: `[caminho do arquivo]`
- Skills relevantes: `[caminho]`
- Specs/projetos: `[caminho]`

## 🔗 Links importantes criados nesta sessão
- [Link 1 — nome do arquivo + caminho]
- [Link 2]

## 💬 Frase do Bruno que resume a sessão
> "[citação exata do Bruno que captura a decisão/tensão do dia]"

## 📊 Métricas de Qualidade (novo 2026-06-10)

### Erros registrados nesta sessão
- [erro-NNN]: [título] — [severidade]
- (ou "nenhum")

### Skills mais usadas (auditoria via auto-relatabilidade)
1. [skill] — K respostas
2. [skill] — K respostas

### Decisões registradas (R4 executou)
- N decisões gravadas

### Arquivos modificados/criados
- N criados, M modificados
```

---

## 📝 Regras de geração

### O que DEVE ter (não negociável)
- ✅ Data, hora, projeto, tipo, gatilho
- ✅ "Onde paramos" em 1-3 frases
- ✅ Lista de decisões (com link pro arquivo onde foi registrada)
- ✅ Lista de tarefas em andamento (com dono e onde parou)
- ✅ Próximos passos (numerados, específicos)
- ✅ Pontos de atenção (crítico — sem isso a sessão seguinte erra)

### O que PODE ter (opcional, mas recomendado)
- 🔵 Frase do Bruno que resume a sessão (humano, dá contexto emocional)
- 🔵 Links importantes criados
- 🔵 Métricas (X commits, Y arquivos, Z decisões)
- 🔵 Erros que aconteceram

### O que NÃO DEVE ter
- ❌ Resumo de TODA a conversa (isso é a diária, não o snapshot)
- ❌ Código (link pro arquivo, não cole código)
- ❌ Texto vago tipo "avançamos no projeto" (sem detalhes = inútil)
- ❌ Promessas de fazer algo que ninguém pediu

---

## 🔄 Fluxo de próxima sessão (como o snapshot é lido)

```
1. Kothar acorda (nova sessão)
2. Carrega MEMORY.md (memória automática)
3. Procura snapshot mais recente:
   `find /home/bruno/Cofre/00_Memoria/Snapshots/ -name "*.md" -type f | sort | tail -1`
4. Lê o snapshot
5. Lê `indice.md` (visão geral)
6. Carrega contexto do projeto mencionado (visao.md, estado-atual.md)
7. Responde: "Vi o snapshot de [data]. Estamos em [projeto], [estado]. Próximo passo era [X]. Confirma?"
```

**Adicionar essa lógica na memória automática** (será feito junto com esta skill).

---

## 📏 Tamanho do snapshot

**Regra do Bruno:** "o tamanho que for necessário pra acertividade, não quero erros, não me importa o tamanho".

**Recomendação empírica:**
- Sessão curta (1-2h, decisões simples): ~500-1000 palavras
- Sessão média (3-4h, decisões múltiplas): ~1500-3000 palavras
- Sessão longa (5h+, várias frentes): ~3000-5000 palavras (ou dividir em 2 snapshots: "manhã" + "tarde")

**Sem teto.** Se precisar de 5000 palavras pra ser assertivo, escreve 5000.

**Sinal de que está bom:** próxima sessão lê o snapshot e **imediatamente sabe** o que fazer, sem perguntar "onde paramos?".

**Sinal de que está ruim:** próxima sessão lê e ainda pergunta. Ou: Bruno corrige algo que "esqueci de mencionar".

---

## 🔗 Skills e regras relacionadas

- `principio-menor-escopo.md` — escopo do snapshot = "tudo que importa retomar", nada além
- `definition-of-done.md` — "snapshot pronto" = próximo Kothar consegue retomar
- `feedback-anti-puxa-saco.md` (memória automática) — snapshot é registro, não implementação
- `manual-operacional.md` — linkado no mapa de situações

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Por enquanto: gatilho manual. Gatilhos automáticos ficam pra depois, depois de testar.*
