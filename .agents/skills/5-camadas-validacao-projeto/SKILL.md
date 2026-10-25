---
name: 5-camadas-validacao-projeto
description: >-
  Skill do Kothar: 🛡️ 6 CAMADAS DE VALIDAÇÃO E AUTO-CURA. Ativar quando necessário para execução da habilidade 5-camadas-validacao-projeto.
---

# 🛡️ 6 CAMADAS DE VALIDAÇÃO E AUTO-CURA

> **Função:** Tornar IMPOSSÍVEL o erro 009 (contaminação de projetos via SSH/chave errada).

## Visão

```
┌──────────────────────────────────────────────────────────────┐
│  CAMADA 1: R1 (Percepção) — INÍCIO DE SESSÃO                 │
│  Detecta pwd + compara com projeto do snapshot                │
│  Status: ✅ Implementado (perception.md)                     │
│  Hook: session-init.sh                                        │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 2: R2 (Planejamento) — DECLARAÇÃO EXPLÍCITA          │
│  Todo plano declara "este plano é para [PROJETO]"             │
│  Status: ✅ Implementado (reasoning.md)                      │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 3: Hook pre-bash-project — VALIDAÇÃO POR TOOL CALL   │
│  Cada Bash valida pwd vs projeto autorizado                   │
│  Status: ✅ Implementado (pre-bash-project.sh)               │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 4: Hook pre-bash-ssh — VALIDAÇÃO DE CHAVE            │
│  Cada git op valida chave SSH correta + remote                │
│  Status: ✅ Implementado (pre-bash-ssh.sh)                   │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 5: Memórias Isoladas — ISOLAMENTO DE CONTEXTO        │
│  R1 só carrega memórias do projeto atual                      │
│  Status: ⏳ Implementar em D6                                 │
├──────────────────────────────────────────────────────────────┤
│  CAMADA 6: AST Validation — AUTO-CURA (v2.0)                 │
│  Hook pre-edit impede falhas sintáticas antes de salvar       │
│  Status: ✅ Implementado (pre-edit-ast-guard.sh)             │
└──────────────────────────────────────────────────────────────┘
```

---

## Fluxo de Detecção em Cada Camada

### Camada 1: R1 — Percepção

**Quando:** Toda nova sessão.

**Como funciona:**
1. `pwd` é capturado
2. Detectado projeto via tabela de paths
3. Se projeto do snapshot ≠ projeto do pwd → **PERGUNTA**
4. Se nenhum → autoriza novo

**Implementação:** `01_Kothar/core/perception.md` (S1) + `~/.kothar/hooks/session-init.sh`

**Estado:** `~/.kothar/state/current-project`

---

### Camada 2: R2 — Planejamento

**Quando:** Toda nova tarefa.

**Como funciona:**
1. Plano gerado em `reasoning.md`
2. Plano **declara explicitamente** "para [PROJETO]"
3. Bruno vê e confirma antes da execução

**Implementação:** `01_Kothar/core/reasoning.md` (etapa 4 — escopo)

**Estado:** dentro do próprio plano exibido.

---

### Camada 3: Hook pre-bash-project

**Quando:** Cada tool call Bash.

**Como funciona:**
1. Hook lê `~/.kothar/state/current-project`
2. Hook detecta projeto via `pwd`
3. Se diferentes → **BLOQUEIA** (strict) ou **AVISA** (observation)
4. Modo controlado por `~/.kothar/state/gates-mode`

**Implementação:** `~/.kothar/hooks/pre-bash-project.sh`

**Comando para trocar:**
```bash
kothar project switch novo-projeto
```

---

### Camada 4: Hook pre-bash-ssh

**Quando:** Cada `git clone/pull/push/fetch`.

**Como funciona:**
1. Hook detecta projeto via `pwd`
2. Hook verifica se `~/.ssh/id_ed25519_[projeto]` existe
3. Hook verifica se chave está carregada no ssh-agent
4. Hook valida se remote bate com projeto
5. Se algo falhar → **BLOQUEIA** (strict) ou **AVISA** (observation)

**Implementação:** `~/.kothar/hooks/pre-bash-ssh.sh`

---

### Camada 5: Memórias Isoladas

**Quando:** R1 carrega contexto.

**Como funciona:**
1. Estrutura: `~/.claude/projects/-home-bruno-[projeto]/memory/`
2. R1 lê APENAS a memória do projeto atual
3. Outras memórias = invisíveis

**Implementação:** ⏳ D6

---

### Camada 6: AST Validation (Auto-Cura Preventiva)

**Quando:** Antes de qualquer arquivo `.js`, `.ts`, `.tsx`, `.py` ser salvo.

**Como funciona:**
1. Hook lê o arquivo temporário gerado pelo agente.
2. Analisa a árvore sintática abstrata (AST) do arquivo.
3. Se houver erro fatal de sintaxe (ex: código cortado no meio), bloqueia e avisa.

**Implementação:** `01_Kothar/core/pre-edit-ast-guard.sh`

---

## Tabela de Projetos Canônicos

| Diretório | Projeto | Chave SSH Esperada |
|---|---|---|
| `/home/bruno/Cofre` | `kothar` | `id_ed25519_kothar` |
| `/home/bruno/Cofre/03_Empresa/Produtos/disparo-em-massa` | `disparo-em-massa` | `id_ed25519_disparo_em_massa` |
| `/home/bruno/Cofre/04_Clientes/bioleads` | `bioleads` | `id_ed25519_bioleads` |
| `/home/bruno/Cofre/04_Clientes/ratoflix` | `ratoflix` | `id_ed25519_ratoflix` |
| `/home/bruno/Cofre/04_Clientes/linkdabio` | `linkdabio` | `id_ed25519_linkdabio` |
| `/home/bruno/Cofre/site-novo-modelo` | `site-novo-modelo` | `id_ed25519_site_novo_modelo` |

**Adicionar novo projeto:** editar esta tabela em:
- `01_Kothar/core/perception.md` (S1)
- `01_Kothar/core/gates.md` (G1)
- `01_Kothar/habilidades/5-camadas-validacao-projeto.md` (este arquivo)
- `~/.kothar/hooks/pre-bash-project.sh`
- `~/.kothar/hooks/pre-bash-ssh.sh`

---

## Por que 5 Camadas?

| Ameaça | Camada que bloqueia |
|---|---|
| Bruno esquece qual projeto está | **1 — R1 detecta e pergunta** |
| Plano é para projeto errado | **2 — declaração explícita** |
| Bash roda em projeto errado | **3 — hook bloqueia por pwd** |
| Git usa chave errada | **4 — hook valida chave** |
| Memória de outro projeto vaza | **5 — memórias isoladas** |

**Cada camada pega o que a anterior deixou passar.**

---

## DoD — Validação de Projeto

- [x] Camada 1: R1 detecta pwd
- [x] Camada 2: Planos declaram projeto
- [x] Camada 3: Hook pre-bash-project ativo
- [x] Camada 4: Hook pre-bash-ssh ativo
- [ ] Camada 5: Memórias isoladas (D6)

**Status:** 4/5 camadas ativas. Erro 009 já é impossível de ocorrer.

---

## Como Bruno Interage

**Cenário 1: Sessão normal**
- Bruno abre sessão em `/home/bruno/Cofre/04_Clientes/ratoflix`
- Hook session-init detecta → grava `current-project=ratoflix`
- Tudo funciona normalmente

**Cenário 2: Bruno pula para outro projeto**
- Bruno muda para `/home/bruno/Cofre/04_Clientes/bioleads`
- Próximo Bash dispara pre-bash-project
- Hook detecta `bioleads` ≠ `ratoflix` (autorizado)
- Em strict: BLOQUEIA
- Bruno: `kothar project switch bioleads`
- Hook atualiza `current-project=bioleads`
- Tudo funciona

**Cenário 3: git pull com chave errada**
- Bruno está em `ratoflix`, vai fazer `git pull`
- Hook pre-bash-ssh detecta
- Verifica `~/.ssh/id_ed25519_ratoflix` → OK
- Verifica se está carregada → carrega
- Verifica remote → bate
- Permite

**Cenário 4: git pull sem chave do projeto**
- Bruno está em novo projeto sem chave
- Hook detecta `~/.ssh/id_ed25519_[projeto]` não existe
- Em strict: BLOQUEIA com mensagem clara
- Bruno cria/copia a chave, adiciona ao ssh-agent
- Tenta novamente → OK

---

## Métricas de Sucesso

| Métrica | Meta |
|---|---|
| Falsos positivos (bloqueio indevido) | < 5% |
| Tempo adicional por sessão | < 30s |
| Erros do tipo 009 após deploy | 0 |
| Confiança de Bruno no sistema | ≥ 8/10 |
