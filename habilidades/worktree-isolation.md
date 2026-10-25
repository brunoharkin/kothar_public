---
name: worktree-isolation
description: Isolamento por feature usando Git Worktrees — permite trabalhar em múltiplas features do mesmo projeto em paralelo sem conflito. Complementa o project-sandbox (isolamento por projeto) com isolamento por feature dentro do projeto.
version: 1.0.0
projeto: kothar
tipo: habilidade
data: 2026-08-12
---

# Skill: Worktree Isolation (Git Worktrees por Feature)

> **Fonte:** Boris Cherny: "Use git worktrees to run 5+ Claudes in parallel on separate features."
> 
> O `pre-edit-project-guard.sh` isola por **projeto**. Esta skill isola por **feature** dentro do mesmo projeto.

---

## 🎯 Quando Usar

- Trabalhando em 2+ features diferentes do mesmo projeto simultaneamente
- Feature longa que não pode bloquear hotfixes
- Experimentos que podem precisar ser descartados sem afetar o branch principal
- Code review enquanto continua desenvolvendo

---

## 🌲 Conceito: Worktree

Um **worktree** é uma cópia do repositório em um diretório diferente, com seu próprio branch, mas compartilhando o mesmo histórico git.

```
/home/bruno-harkin/disparo-em-massa/          ← branch: main
/home/bruno-harkin/disparo-em-massa-feat-A/   ← branch: feat/integracao-pix
/home/bruno-harkin/disparo-em-massa-feat-B/   ← branch: feat/relatorio-mensal
```

Cada worktree é um projeto independente do ponto de vista do Kothar.

---

## 🛠️ Comandos

### Criar Worktree para Nova Feature
```bash
# Na raiz do projeto:
cd /home/bruno-harkin/{projeto}

# Criar worktree + branch
git worktree add ../{projeto}-feat-{slug} -b feat/{slug}

# Registrar no Kothar (para o guard funcionar)
echo "/home/bruno-harkin/{projeto}-feat-{slug}" >> ~/.kothar/state/worktrees-ativos.txt
```

### Listar Worktrees Ativos
```bash
git worktree list
cat ~/.kothar/state/worktrees-ativos.txt
```

### Remover Worktree após Merge
```bash
# Fazer merge primeiro:
git checkout main
git merge feat/{slug}

# Remover worktree:
git worktree remove ../{projeto}-feat-{slug}

# Remover do registro Kothar:
sed -i "/{slug}/d" ~/.kothar/state/worktrees-ativos.txt
```

---

## 🔒 Integração com o Kothar Guard

O `pre-edit-project-guard.sh` precisa ser informado sobre worktrees para não bloquear edições neles.

**Como funciona:**
1. O guard verifica se o arquivo está dentro de `current-project-root`
2. Worktrees estão em diretórios diferentes → seriam bloqueados
3. **Solução:** Ao criar um worktree, selecionar ele como projeto ativo no Kothar:

```bash
# Mudar para o worktree da feature:
kothar-select-project {projeto}-feat-{slug}

# O guard agora permite edições no worktree
# Ao terminar, voltar para o projeto principal:
kothar-select-project {projeto}
```

---

## 📋 Fluxo Completo com RPI + Worktree

```
1. Bruno: "Quero implementar PIX no disparo-em-massa"

2. [RPI] Criar REQUEST.md para a feature

3. [Worktree] Criar worktree para a feature:
   git worktree add ../disparo-em-massa-pix -b feat/integracao-pix

4. [Kothar] Selecionar worktree como projeto ativo:
   kothar-select-project disparo-em-massa-pix

5. [RPI] Executar RESEARCH + PLAN no worktree

6. [Build] Implementar com commits no branch feat/integracao-pix

7. [Verify] Rodar validador.sh + playwright no worktree

8. [Ship] Abrir PR do feat/integracao-pix → main

9. [Cleanup] Remover worktree após merge
```

---

## ⚠️ Regras

1. **Um worktree = uma feature** — não misturar features no mesmo worktree
2. **Sempre selecionar o worktree** como projeto ativo no Kothar antes de editar
3. **Não commitar shared dependencies** (node_modules, .env) no worktree
4. **Limpar worktrees** após merge — não acumular worktrees abandonados
5. **Máximo 3 worktrees simultâneos** — mais que isso vira confusão

---

## 🔗 Skills Relacionadas

- `project-sandbox.md` — isolamento por projeto (nível acima)
- `rpi-workflow.md` — cada feature RPI idealmente tem seu worktree
- `pre-edit-project-guard.sh` — guard que precisa ser informado do worktree

*Skill criada em 2026-08-12 — Inspirada no worktree workflow do Boris Cherny*
