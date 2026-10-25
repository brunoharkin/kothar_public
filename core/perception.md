---
name: perception
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: core
descricao: 5 sensores que observam o estado antes de qualquer ação
---

# 👁️ PERCEPTION — Sensores do Kothar v1.4.0

> **Função:** Mapear o estado real do mundo antes de planejar/agir.

## Os 5 Sensores

### S1. Diretório Atual (`pwd`)

**O que detecta:**
- Em qual pasta está
- Se está dentro de um projeto Ugarit válido
- Se está em `/tmp`, `/home`, ou outro lugar indefinido

**Comando:**
```bash
pwd
basename $(pwd)
```

**Tabela de projetos:**

| Diretório | Projeto |
|---|---|
| `/home/bruno/Cofre` | `cofre` (raiz Kothar) |
| `/home/bruno/Cofre/03_Empresa/Produtos/disparo-em-massa` | `disparo-em-massa` |
| `/home/bruno/Cofre/04_Clientes/bioleads` | `bioleads` |
| `/home/bruno/Cofre/04_Clientes/ratoflix` | `ratoflix` |
| `/home/bruno/Cofre/04_Clientes/linkdabio` | `linkdabio` |
| `/home/bruno/Cofre/site-novo-modelo` | `site-novo-modelo` |
| `/home/bruno/kothar` | `kothar` (se externo) |

**Se pwd não está na tabela:**
```
⚠️ Diretório [PWD] não é um projeto Ugarit conhecido.
Deseja trabalhar em qual projeto? Ou criar contexto novo?
```

---

### S2. Estado Git (`git status` + `git remote`)

**O que detecta:**
- Se há mudanças não commitadas
- Se está em branch errada
- Se remote está correto
- Se há conflitos

**Comando:**
```bash
cd $(pwd) && git status --short
git branch --show-current
git remote -v
```

**Validações:**

| Condição | Ação |
|---|---|
| Working tree limpo | OK |
| Mudanças não commitadas | Avisa: "Há [N] mudanças pendentes" |
| Branch ≠ main/master/dev | Avisa: "Você está em [BRANCH], não na principal" |
| Remote não bate com projeto | **BLOQUEIA** (projeto errado) |

---

### S3. Chaves SSH (`~/.ssh/config`)

**O que detecta:**
- Quais chaves existem
- Qual chave está mapeada para qual host
- Se a chave do projeto está disponível

**Comando:**
```bash
cat ~/.ssh/config 2>/dev/null
ls ~/.ssh/id_* 2>/dev/null
ssh-add -l 2>/dev/null
```

**Mapeamento esperado:**

| Projeto | Chave | Host |
|---|---|---|
| `bioleads` | `id_ed25519_bioleads` | github.com-bioleads |
| `disparo-em-massa` | `id_ed25519_disparo-em-massa` | github.com-disparo |
| `ratoflix` | `id_ed25519_ratoflix` | github.com-ratoflix |
| `linkdabio` | `id_ed25519_linkdabio` | github.com-linkdabio |
| `kothar` | `id_ed25519_kothar` | github.com-kothar |

**Se chave do projeto não existe:**
```
⚠️ Projeto [X] requer chave [Y], mas ela não existe em ~/.ssh/.
Operação git BLOQUEADA até Bruno criar/copiar a chave.
```

---

### S4. Diário do Dia

**O que detecta:**
- O que Bruno estava fazendo hoje
- Qual era o último estado
- Se a sessão anterior ficou pendente

**Comando:**
```bash
ls /home/bruno/Cofre/00_Memoria/Diarias/$(date +%Y-%m)/$(date +%Y-%m-%d).md 2>/dev/null
```

**Se existe:**
- Carrega contexto do dia anterior
- Mostra: "Vi o diário de hoje. Estávamos em [PROJETO], [ESTADO]."
- Lista pendências se houver

**Se não existe:**
- Cria com template mínimo
- Pergunta: "Nova sessão. Em qual projeto estamos?"

---

### S5. Modo de Contexto

**O que detecta:**
- Em qual modo o Kothar deve operar
- Pode ser: `default`, `dev`, `pesquisa`, `cliente`, `debug`, `estratégia`

**Detecção automática:**

| Padrão na mensagem | Modo ativado |
|---|---|
| `git`, `npm`, `pnpm`, `build`, `commit`, `push` | `dev` |
| `pesquise`, `analise`, `compare`, `investigue` | `pesquisa` |
| `cliente`, `demanda`, `atendimento`, `suporte` | `cliente` |
| `bug`, `erro`, `quebrou`, `debug` | `debug` |
| `estratégia`, `viabilidade`, `MVP`, `lançamento` | `estratégia` |
| Nada específico | `default` |

**Ativação manual:** Bruno fala "modo dev" / "modo cliente" / etc.

---

## Saída Consolidada

Quando R1 roda, a percepção gera:

```yaml
estado:
  pwd: /home/bruno/Cofre/04_Clientes/ratoflix
  projeto_detectado: ratoflix
  projeto_autorizado: ratoflix  # mesmo → OK
  
  git:
    branch: feature/d-41-comentarios
    working_tree: dirty (3 mudanças)
    remote: git@github.com-appsugarit-dev/ratoflix.git  # OK
  
  ssh:
    chave_projeto: id_ed25519_ratoflix  # OK
    carregada: sim
  
  diario:
    existe: sim
    projeto: ratoflix
    pendencias: ["D-41 comentários (em andamento)"]
  
  modo:
    detectado: dev
    ativo: dev

proximos_passos:
  - "Continuar D-41 conforme pendência do diário"
  - "Fazer commit das 3 mudanças pendentes"
```

---

## Uso no Core Loop

A percepção é o **passo 1** do Core Loop:

```
SENTIR (perception.md) 
  → PENSAR (reasoning.md)
  → VALIDAR (gates.md)
  → AGIR
```

Sem percepção, Kothar age no escuro. **Sempre rodar primeiro.**
