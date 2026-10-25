---
name: release-v1.4.0
versao: 1.4.0
data: 2026-06-19
projeto: kothar
tipo: release
status: completo
---

# 🚀 HERMES v1.4.0 — RELEASE NOTES

> **Data de release:** 2026-06-19  
> **Versão anterior:** 1.3.0 (2026-06-18)  
> **Filosofia:** Semi-autônomo — age sozinho, pede aprovação em 6 CPs

---

## 🎯 O QUE MUDA

### Antes (v1.3.0)
- 15 regras manuais que Kothar "lembrava" quando podia
- 0 hooks ativos (documentados, não wired)
- 0 contexto dinâmico (system prompt fixo)
- Validação de projeto em 1 camada (R1)
- 0 auto-aprendizado (só registra erro quando Bruno pede)
- 50 skills, 6 obsoletas no disco

### Agora (v1.4.0)
- 15 regras viraram **gates automáticos no Core Loop**
- **8 hooks ativos** (bash guard, cred scan, project validate, ssh validate, dod, instinct collector, session init/snapshot)
- **7 contextos dinâmicos** (default + dev + pesquisa + cliente + debug + estratégia + encerramento)
- **5 camadas de validação de projeto** (torna erro 009 impossível)
- **Instinct Engine** captura 100% das tool calls, detecta padrões, gera propostas
- **49 skills ativas** + 5 deprecadas (em `_deprecated/`)
- **CLI `kothar`** com 9 comandos (status, gates, project, trust, snapshot, log, hooks, instincts, help)

---

## 📦 ENTREGÁVEIS

### 1. Core Loop (5 arquivos)

```
01_Kothar/core/
├── core-loop.md         # Orquestrador central (SENTIR→PENSAR→VALIDAR→AGIR→APRENDER→RELATAR)
├── perception.md        # 5 sensores (pwd, git, ssh, diário, modo)
├── reasoning.md         # Como planeja (classificar, ativar modo, skills, escopo, plano, viabilidade)
├── gates.md             # 5 portões automáticos
└── checkpoints.md       # 6 CPs que pedem aprovação
```

### 2. 15 Mandamentos Consolidados

```
01_Kothar/instrucoes/evolucao/MANDAMENTOS-v1.4.0.md
```

Cada mandamento agora tem: **Regra → Gate → Checkpoint → Aprendizado**.

### 3. 8 Hooks Ativos em `~/.kothar/hooks/`

| Hook | Função | Bloqueia? |
|---|---|---|
| `pre-bash-guard.sh` | Bloqueia `rm -rf`, fork bomb, `git push --force`, etc. | Sim (strict) |
| `pre-bash-project.sh` | Valida `pwd` vs projeto autorizado | Sim (strict) |
| `pre-bash-ssh.sh` | Valida chave SSH correta por projeto | Sim (strict) |
| `post-edit-cred-scan.sh` | Detecta senhas/tokens hardcoded | Sim (strict) |
| `post-edit-dod.sh` | Avisa sobre TODO/console.log/debugger | Avisa |
| `post-tool-instinct-collector.sh` | Captura 100% das tool calls | Não (silencioso) |
| `session-init.sh` | R1 automático em SessionStart | Não |
| `session-snapshot.sh` | Snapshot automático em SessionEnd | Não |

**Configuração:** `~/.claude/settings.json` (8 hooks wired em 6 eventos)

### 4. 7 Contextos Dinâmicos

```
00_Memoria/Contextos/
├── default.md           # sempre carregado
├── dev.md               # implementar código
├── pesquisa.md          # pesquisar/analisar
├── cliente.md           # atender cliente
├── debug.md             # corrigir bug
├── estrategia.md        # viabilidade/GTM
├── encerramento.md      # fim de sessão
└── deteccao-modo.md     # lógica de detecção automática
```

### 5. Instinct Engine

```
~/.kothar/
├── instincts/
│   ├── raw-events.jsonl         # stream bruto de tool calls
│   ├── pending/                 # instincts detectados
│   ├── approved/                # viraram regra
│   └── rejected/                # descartados
├── hooks/post-tool-instinct-collector.sh
└── scripts/instinct-analyzer.py
```

**Comandos:**
- `kothar instincts list` — ver pendentes
- `kothar instincts analyze` — rodar analisador
- `kothar instincts approve <id>` — promover
- `kothar instincts reject <id>` — descartar

### 6. Memórias Isoladas por Projeto

```
~/.claude/projects/
├── -home-bruno-kothar/memory/          # sempre carregado
├── -home-bruno-cofre/memory/
├── -home-bruno-bioleads/memory/
├── -home/bruno-ratoflix/memory/
├── -home-bruno-linkdabio/memory/
├── -home-bruno-disparo-em-massa/memory/
└── -home-bruno-site-novo-modelo/memory/
```

**Regra:** R1 só carrega memória do projeto atual. Cross-project requer aprovação explícita.

### 7. CLI `kothar`

```bash
kothar status         # dashboard
kothar gates [mode]   # observation | strict | off
kothar project [show|switch <nome>]
kothar trust [low|medium|high]
kothar snapshot       # manual
kothar log [N]        # últimas N linhas
kothar hooks          # listar ativos
kothar instincts [list|analyze|approve|reject]
```

---

## 🛡️ 6 CHECKPOINTS DE APROVAÇÃO (semi-autonomia)

Fora desses 6, Kothar age sozinho:

| CP | Quando | Mensagem |
|---|---|---|
| **CP1** | Mudar de projeto | "Você está em [A], pediu algo de [B]. Autoriza?" |
| **CP2** | Criar/renomear arquivo | "Nome: [X]. Opções: [A, B, C]. Recomendação: [X]. Aprova?" |
| **CP3** | Commit | "Mensagem: [MSG]. Diff: [+X/-Y]. Aprova?" |
| **CP4** | Push | "Remote: [URL]. Branch: [B]. Aprova?" |
| **CP5** | Deletar | "Vou deletar [X]. Certeza?" |
| **CP6** | Validar feature | "Plano: [...]. Viabilidade: OK. Aprova?" |

---

## 🧪 MODO OBSERVAÇÃO (5 dias)

Por padrão, os gates **só avisam**, não bloqueiam. Mensagens aparecem como:

```
⚠️  [HERMES AVISO] rm -rf em diretório não listado
   Comando: rm -rf /etc/test
   (modo observação — em strict seria BLOQUEADO)
```

Bruno pode ativar modo strict:
```bash
kothar gates strict
```

Ou desligar tudo:
```bash
kothar gates off
```

---

## 🐛 BUGS DO TIPO 009 E 010 — IMPOSSÍVEIS AGORA

### Erro 009 (contaminação de projetos via SSH)
**Bloqueado por 4 camadas:**
1. R1 detecta pwd
2. R2 declara projeto no plano
3. Hook `pre-bash-project.sh` valida pwd por tool call
4. Hook `pre-bash-ssh.sh` valida chave SSH por git op
5. Memórias isoladas por projeto

### Erro 010 (estrutura em inglês no site-novo-modelo)
**Bloqueado por:**
1. Gate G5 (nomenclatura) + CP2 (preview obrigatório)
2. Skill `frontend-ugarit-ui` com regra PT-BR em destaque
3. Hook `post-edit-cred-scan.sh` (paralelo — não mistura com credenciais)

### Erro 008 (commits citam cliente)
**Bloqueado por:**
1. CP3 com validação de mensagem
2. Template de commit sem nomes
3. Memory nudge ao detectar padrão

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Meta |
|---|---|
| Falsos positivos (bloqueio indevido) | < 5% |
| Erros tipo 009/010/008 | 0 |
| Tempo adicional por sessão | < 30s |
| Instincts detectados por semana | 5-10 |
| Taxa de aprovação de instincts | > 40% |
| Skills ativas | 49/49 (100%) |
| Skills obsoletas no disco | 5 (em `_deprecated/`) |

---

## 🆕 NOVIDADES vs v1.3.0

| Categoria | Mudança |
|---|---|
| **Core** | 5 novos arquivos (core-loop, perception, reasoning, gates, checkpoints) |
| **Mandamentos** | 1 arquivo único com 15 regras integradas |
| **Hooks** | 0 → 8 hooks ativos |
| **Contextos** | 1 fixo → 7 dinâmicos |
| **Validação projeto** | 1 camada → 5 camadas |
| **Auto-aprendizado** | Manual → Instinct Engine automático |
| **Memórias** | 1 bucket global → 7 buckets isolados |
| **Skills** | 50 mistas → 49 ativas + 5 deprecadas |
| **CLI** | Não existia → `kothar` com 9 comandos |
| **Dashboard** | Não existia → `kothar status` |
| **Auditoria de bugs** | 0 → post-edit-dod.sh |

---

## 📂 ESTRUTURA FINAL

```
/home/bruno/Cofre/
├── 01_Kothar/
│   ├── core/                              # 🆕 Orquestrador
│   │   ├── core-loop.md
│   │   ├── perception.md
│   │   ├── reasoning.md
│   │   ├── gates.md
│   │   └── checkpoints.md
│   ├── habilidades/                       # 49 ativas + 5 _deprecated/
│   ├── instrucoes/evolucao/
│   │   └── MANDAMENTOS-v1.4.0.md         # 🆕 Sistema integrado
│   ├── propostas/v1.4.0/                  # 🆕 Instincts promovidos
│   └── SPEC.md                            # atualizado
└── 00_Memoria/
    └── Contextos/                         # 🆕 7 contextos dinâmicos
        ├── default.md
        ├── dev.md
        ├── pesquisa.md
        ├── cliente.md
        ├── debug.md
        ├── estrategia.md
        ├── encerramento.md
        └── deteccao-modo.md

/home/bruno/.claude/
├── projects/                              # 🆕 memórias isoladas
│   ├── -home-bruno-kothar/memory/
│   ├── -home-bruno-bioleads/memory/
│   ├── -home-bruno-ratoflix/memory/
│   ├── -home-bruno-linkdabio/memory/
│   ├── -home-bruno-disparo-em-massa/memory/
│   └── -home-bruno-site-novo-modelo/memory/
└── settings.json                          # 8 hooks wired

/home/bruno/.kothar/
├── hooks/                                 # 🆕 8 hooks
│   ├── pre-bash-guard.sh
│   ├── pre-bash-project.sh
│   ├── pre-bash-ssh.sh
│   ├── post-edit-cred-scan.sh
│   ├── post-edit-dod.sh
│   ├── post-tool-instinct-collector.sh
│   ├── session-init.sh
│   └── session-snapshot.sh
├── scripts/
│   ├── instinct-analyzer.py               # 🆕 analisador
│   └── skill-promoter.sh                  # 🆕 promoter
├── instincts/                             # 🆕 engine
│   ├── raw-events.jsonl
│   ├── pending/
│   ├── approved/
│   └── rejected/
├── state/                                 # 🆕 estado
│   ├── current-project
│   ├── gates-mode
│   └── trust-level
├── logs/                                  # estruturado
└── metrics/                               # métricas

/home/bruno/.local/bin/
└── kothar                                 # 🆕 CLI com 9 comandos
```

---

## 🎯 PRÓXIMOS PASSOS

### Semana 1 (modo observação)
- [ ] Usar Kothar em modo `observation` por 5 dias úteis
- [ ] Rodar `kothar instincts analyze` 1x por dia
- [ ] Avaliar se gates estão atrapalhando ou ajudando
- [ ] Ajustar thresholds de confiança

### Semana 2 (modo strict)
- [ ] Ativar `kothar gates strict`
- [ ] Validar que hooks bloqueiam sem atrapalhar
- [ ] Aprovar instincts que fazem sentido
- [ ] Marcar bug recorrente que vire regra

### Semana 3+ (confiança alta)
- [ ] Avaliar `kothar trust high` (CP2 em batch, CP6 só em features grandes)
- [ ] Adicionar mais skills conforme necessário
- [ ] Expandir instinct patterns

---

## 📚 DOCUMENTAÇÃO

| Arquivo | Conteúdo |
|---------|----------|
| `01_Kothar/SPEC.md` | Spec atualizada para v1.4.0 |
| `01_Kothar/core/*.md` | 5 documentos do Core Loop |
| `01_Kothar/instrucoes/evolucao/MANDAMENTOS-v1.4.0.md` | 15 mandamentos |
| `01_Kothar/habilidades/5-camadas-validacao-projeto.md` | Camadas |
| `01_Kothar/habilidades/instinct-engine.md` | Engine |
| `01_Kothar/habilidades/memorias-isoladas.md` | Memórias |
| `01_Kothar/habilidades/catalogo-habilidades.md` | 49 skills |
| `01_Kothar/habilidades/_deprecated/README.md` | 5 deprecadas |
| `00_Memoria/Contextos/*.md` | 7 contextos |
| `00_Memoria/Aprendizados/erros/` | 10 erros registrados |

---

## 🤖 AUTO-RELATABILIDADE v2 (sempre aplicar)

Toda resposta do Kothar agora DEVE terminar com:

```
---
🛠️ [projeto: NOME] | Modo: MODO | Skills ativas:
- [skill-1] — [o que faz aqui]
- [skill-2] — [o que faz aqui]
```

---

**Status:** ✅ IMPLEMENTAÇÃO COMPLETA  
**Data:** 2026-06-19  
**Próximo marco:** 5 dias úteis de uso real em modo observação
