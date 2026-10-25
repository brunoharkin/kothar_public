---
name: registro-de-erros
description: >-
  Catálogo de erros do Kothar. Bruno fala "registra esse erro" e Kothar cria entrada estruturada em 00_Memoria/Aprendizados/erros/. Erros viram dados, dados viram regras, regras viram comportamento.
---

# Skill: Registro de Erros

> **Princípio:** erros viram dados. Dados viram regras. Regras viram comportamento. Loop fechado.
>
> Bruno: "depois agente analia e corrigi para ele nao cometer os mesmo erros como erros frequentes assim agente cria a regra"

---

## 🎯 Por que existe

**Problema histórico:** Kothar repete erros. Mesmo erro acontece 3x, ninguém cataloga, vira padrão.

**Solução:**
1. Bruno percebe erro → fala "registra esse erro"
2. Kothar cria entrada estruturada
3. Periodicamente: Bruno pede "analisa os erros"
4. Kothar identifica recorrências, **sugere** correções
5. Bruno aprova ("cria regra / atualiza skill")
6. Kothar implementa
7. Erro não acontece mais

---

## 🔴 Gatilho (único, manual)

**Bruno disser uma das frases:**
- "registra esse erro"
- "registra erro"
- "anota esse erro"
- "catalogar erro"
- "salva esse erro"

**Kothar DEVE:**
1. PARAR o que está fazendo
2. Perguntar (se necessário): "qual foi o erro? o que eu fiz de errado?"
3. Se Bruno já descreveu: criar entrada direto
4. Criar arquivo em `00_Memoria/Aprendizados/erros/YYYY-MM-DD-erro-NNN.md`
5. Atualizar `00_Memoria/Indice-Mestre.md` (seção "Aprendizados Recentes")
6. Confirmar: "Erro registrado em [caminho]. ID: erro-NNN"

---

## 📁 Estrutura de Pastas

```
00_Memoria/Aprendizados/
├── erros/                    ← 1 arquivo por erro
│   ├── _template.md          ← template padrão
│   ├── 2026-06-10-erro-001.md
│   ├── 2026-06-10-erro-002.md
│   └── ...
├── regras-criadas/           ← regras geradas a partir de erros recorrentes
│   ├── _template.md
│   └── 2026-06-XX-regra-NNN.md
└── analises/                 ← análises periódicas
    ├── _template.md
    └── 2026-06-analise-mensal.md
```

**Numeração:** `erro-NNN` reinicia a cada ano. Em 2026: erro-001, erro-002, etc.

---

## 📋 Template do Erro

```markdown
---
id: erro-NNN
data: YYYY-MM-DD
hora: HH:MM
tipo: "codigo" | "processo" | "comunicacao" | "memoria" | "seguranca"
severidade: "baixa" | "media" | "alta" | "critica"
skill-relacionada: "nome-da-skill"
regra-violada: "regra-X" (se aplicável)
status: "registrado" | "em-analise" | "regra-criada" | "resolvido"
recorrencia: 1
---

# Erro-NNN — [título curto e descritivo]

## Contexto
[Onde/quando aconteceu: sessão, projeto, tarefa]

## O que o Kothar fez
[Descrição concreta do erro — cite as palavras/ações exatas se possível]

## O que deveria ter feito
[Comportamento correto, com referência à skill/regra]

## Por que é erro
[Impacto: por que isso é problema. Referência à regra violada.]

## Como evitar
[O que mudar pra não repetir — pode virar regra nova]

## Ocorrências
- YYYY-MM-DD HH:MM: 1ª (esta)

## Status
- [x] Registrado
- [ ] Regra/skill identificada pra prevenir
- [ ] Bruno validou correção
- [ ] Regra implementada e ativa
```

---

## 📝 Classificação de Erros (taxonomia)

### Por tipo
| Tipo | Exemplos |
|---|---|
| `codigo` | Botão sem handler, import quebrado, typo em variável |
| `processo` | Pulou Discovery, declarou pronto sem DoD, mexeu fora do escopo |
| `comunicacao` | Resposta vaga, não respondeu pergunta, info incorreta |
| `memoria` | Esqueceu regra, esqueceu skill, contexto errado |
| `seguranca` | Credencial exposta, .env commitado, scan pulado |

### Por severidade
| Severidade | Definição |
|---|---|
| `baixa` | Cosmético, sem impacto funcional |
| `media` | Funcional mas recuperável, sem perda de dados |
| `alta` | Quebra funcionalidade principal, precisa correção urgente |
| `critica` | Perda de dados, vazamento segurança, comportamento irreversível |

---

## 🔄 Fluxo Completo (loop fechado)

```
[ERRO ACONTECE]
     ↓
[Bruno fala "registra esse erro"]
     ↓
[Kothar cria entrada em erros/]
     ↓
[Atualiza Indice-Mestre: +1 erro registrado]
     ↓
[Periodicamente: Bruno fala "analisa os erros"]
     ↓
[Kothar gera análise em analises/]
     ↓
[Identifica recorrências (mesmo erro 2+ vezes)]
     ↓
[SUGERE correção: criar regra / atualizar skill]
     ↓
[Bruno aprova: "cria regra X" / "atualiza skill Y"]
     ↓
[Kothar cria regra em regras-criadas/]
     ↓
[Se crítica: vai pra memória automática]
     ↓
[Indice-Mestre atualizado]
     ↓
[REGRA ATIVA NO PRÓXIMO CONTEXTO]
     ↓
[Loop fecha — erro não acontece mais]
```

---

## 🎯 Regra de Promoção (quando erro vira regra)

**Erro vira regra quando:**
- 1ª vez: só registra
- 2ª vez: marca como "recorrente — atenção"
- 3ª vez: Kothar **sugere proativamente** criar regra (sem Bruno pedir)
- Bruno aprova → regra vira permanente

**Onde a regra vai (decisão):**

| Tipo de erro | Onde a regra vai |
|---|---|
| Crítico de segurança | **Memória automática** (sempre carrega) |
| Erro de processo (recorrente) | **Skill nova** ou **atualizar skill existente** |
| Regra absoluta (nunca pode violar) | **Regra-mãe em `evolucao/`** |
| Erro de memória | **Adicionar ao `Indice-Mestre.md`** ou **prompt-principal** |
| Erro de código (padrão) | **Atualizar `definition-of-done.md`** |

---

## 🔴 Comportamento PROIBIDO

- ❌ Kothar criar regras sozinho sem aprovação
- ❌ Catalogar erro falso (falso positivo = ruído)
- ❌ Esquecer de atualizar `Indice-Mestre` após registro
- ❌ Não seguir fluxo (ir direto de erro → regra sem análise)

---

## 🔗 Skills e regras relacionadas

- `micro-rotinas.md` — R4 (registrar decisão) cobre parte do fluxo
- `analise-de-erros.md` — próxima skill, gera relatório
- `auto-relatabilidade.md` — skill listada no rodapé quando cataloga erro
- `feedback-anti-puxa-saco.md` — se erro for "puxa-saco", reforça gate

---

*Skill criada em 2026-06-10 — Bruno Harkin / Kothar*
*Fluxo manual, controlado por Bruno. Erros viram dados, dados viram regras, regras viram comportamento.*
