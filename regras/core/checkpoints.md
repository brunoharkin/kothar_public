---
name: checkpoints
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: core
descricao: 6 momentos onde Kothar pede aprovação ao Bruno (única coisa semi-autônoma)
---

# 🛑 CHECKPOINTS — 6 Momentos que Pedem Aprovação

> **Função:** Definir os 6 únicos momentos em que Kothar PARA e espera Bruno.

## Filosofia

```
v1.3.0: Bruno aprova TUDO
v1.4.0: Bruno aprova SÓ 6 COISAS

Tudo o que não for CP1-CP6 → Kothar age sozinho (com log).
```

## Os 6 Checkpoints

---

### CP1 — Mudar de Projeto

**Gatilho:** `pwd` ≠ projeto autorizado OU Bruno pediu algo de outro projeto.

**Variável de contexto:** `~/.kothar/state/current-project`

**Mensagem:**

```
🛑 CP1: MUDANÇA DE PROJETO
   
   Projeto atual: [PROJETO_ATUAL]
   Projeto pedido: [PROJETO_PEDIDO]
   Diretório: [PWD]
   
   ⚠️  Isso pode indicar:
   - Você está no projeto errado
   - Você quer trocar de projeto
   - É continuação de algo de outro dia
   
   Autoriza? (sim/não/verificar)
```

**Se "sim":** Atualiza `current-project`, carrega contexto do novo projeto.

**Se "não":** Mantém projeto atual, Bruno reescreve pedido.

**Se "verificar":** Mostra estado completo dos 2 projetos (R1 estendido).

---

### CP2 — Criar/Renomear Arquivo ou Pasta

**Gatilho:** Kothar vai criar ou renomear arquivo/pasta/variável/função.

**Mensagem:**

```
🏷️  CP2: NOMENCLATURA
   
   Tipo: [arquivo | pasta | variável | função | classe]
   Local: [caminho_completo]
   
   Opção A: [nome_proposto_1]
   Opção B: [nome_proposto_2]
   Opção C: [nome_proposto_3]
   
   Recomendação: [X] — [JUSTIFICATIVA]
   
   Aprova? (sim/troca/[letra])
```

**Padrões de nomenclatura:**
- Arquivo/pasta: `kebab-case`, português, descritivo
- Variável/função: `camelCase`, português
- Classe/componente: `PascalCase`, português

**Exceções permitidas (sem CP2):**
- Arquivos de config óbvios: `package.json`, `tsconfig.json`, `.gitignore`
- Arquivos gerados automaticamente: `node_modules/`, `dist/`, `.next/`
- Arquivos de marca/convenção externa: `README.md`, `LICENSE`

---

### CP3 — Commit

**Gatilho:** Kothar vai executar `git commit`.

**Mensagem:**

```
📦 CP3: COMMIT
   
   Branch: [BRANCH]
   Arquivos: [N modificados, +X/-Y linhas]
   
   Mensagem proposta:
   ┌────────────────────────────────────────┐
   │ tipo(escopo): resumo curto             │
   │                                         │
   │ - detalhe 1                             │
   │ - detalhe 2                             │
   │ - detalhe 3                             │
   └────────────────────────────────────────┘
   
   Diff resumido:
   [ARQUIVO_1]: +15 -3
   [ARQUIVO_2]: +42 -10
   [ARQUIVO_3]: +5 -5
   
   ⚠️  Validações automáticas:
   - [✓] Sem credenciais
   - [✓] Sem nome de cliente/pessoa
   - [✓] Mensagem técnica (sem "Dimitri disse...")
   - [✓] Branch sincronizada com remote
   
   Aprova? (sim/editar mensagem/cancelar)
```

**Bloqueia se:**
- Mensagem cita nome de cliente/pessoa
- Mensagem tem linguagem emocional ("corrigindo bug feio", "finalmente funciona")
- Há credenciais nos arquivos modificados
- Branch está 5+ commits atrás do remote

---

### CP4 — Push

**Gatilho:** Kothar vai executar `git push`.

**Mensagem:**

```
🚀 CP4: PUSH
   
   Remote: [URL_COMPLETA]
   Branch: [BRANCH_LOCAL] → [BRANCH_REMOTE]
   
   Commits a enviar: [N]
   [hash1] tipo: msg
   [hash2] tipo: msg
   [hash3] tipo: msg
   
   ⚠️  Validações automáticas:
   - [✓] Remote correto para projeto [X]
   - [✓] Chave SSH correta: [CHAVE]
   - [✓] Não é --force
   - [✓] Commits anteriores aprovados
   
   Aprova? (sim/cancelar)
```

**Bloqueia se:**
- Remote não bate com projeto atual
- Chave SSH errada
- É `--force` ou `--force-with-lease`
- Commits não foram revisados (CP3 pulado)

---

### CP5 — Deletar

**Gatilho:** Kothar vai executar `rm`, `git rm`, ou delete de arquivo/pasta.

**Mensagem:**

```
🗑️  CP5: DELETAR
   
   Alvo: [ARQUIVO/PASTA_COMPLETO]
   
   Motivo: [POR_QUE_VAMOS_DELETAR]
   
   ⚠️  Isto é IRREVERSÍVEL.
   
   Confirma? (sim/não/backup primeiro)
```

**Bloqueia SEMPRE:**
- `rm -rf` em qualquer diretório
- Delete de arquivo em produção
- Delete sem motivo claro
- Delete de mais de 3 arquivos em um comando

**Para Bruno:**
- A opção "backup primeiro" copia para `~/.kothar/backups/YYYY-MM-DD/`
- Depois Bruno pode deletar o backup se não precisar

---

### CP6 — Validar Feature Nova

**Gatilho:** Bruno pediu para criar algo novo (feature, módulo, projeto).

**Mensagem:**

```
🎯 CP6: VALIDAÇÃO DE FEATURE
   
   Feature: [RESUMO]
   Modo: [dev | estratégia | debug]
   
   📊 VIABILIDADE (6 pontos):
   1. Riscos: [LISTA]
   2. Métricas: P50=[X] P90=[Y] arquivos=[Z]
   3. Trade-offs: [FAZER | FAZER_DEPOIS | NÃO_FAZER | ALTERNATIVA]
   4. Escopo negativo: [LISTA]
   5. DoD: [LISTA_BINÁRIA]
   6. Recomendação: [VAI | VAI_COM_RESSALVAS | NÃO_VAI]
   
   💡 STACK proposta:
   - [CAMADA]: [ESCOLHA] — [JUSTIFICATIVA]
   
   🔍 LACUNAS (15 dimensões):
   - [Lx] [NOME]: [PROBLEMA] → [RECOMENDAÇÃO]
   
   Aprova a feature como descrita? (sim/ajustar escopo/mudar stack/cancelar)
```

**Bloqueia se:**
- Viabilidade = "inviável" sem alternativa
- DoD vazio
- Lacunas críticas sem resposta
- Stack não validada

**Para Bruno:**
- "ajustar escopo" → Bruno edita o que vai/não vai
- "mudar stack" → Kothar propõe 2-3 alternativas
- "cancelar" → vira entrada em `00_Memoria/Projetos/cancelados/`

---

## Resumo Visual

```
┌─────────────────────────────────────────────────────────┐
│ BRUNO faz pedido                                         │
│       ↓                                                  │
│ CORE LOOP: SENTIR → PENSAR → VALIDAR → AGIR             │
│       ↓                                                  │
│ Algum dos 6 CPs dispara?                                 │
│   ├─ NÃO → Age sozinho, loga, relata                    │
│   └─ SIM → Apresenta mensagem acima, espera aprovação    │
└─────────────────────────────────────────────────────────┘
```

---

## Anti-Fricção

Para não cansar Bruno, CPs têm:

| CP | Frequência típica | Fricção |
|---|---|---|
| CP1 (projeto) | 1-2x por dia | Baixa |
| CP2 (nomenclatura) | 5-10x por dia | Média (problema: Bruno pode achar chato) |
| CP3 (commit) | 3-5x por dia | Baixa |
| CP4 (push) | 1-3x por dia | Baixa |
| CP5 (deletar) | 0-1x por dia | Baixa (raro) |
| CP6 (feature) | 1-3x por semana | Média (problema: pode ser longo) |

**Otimizações:**
- CP2 em massa: agrupar 5+ criações e pedir 1 aprovação
- CP3 template: Bruno pode pré-aprovar template "feat: X" para múltiplos commits
- CP6 em fases: dividir feature em MVPs e validar cada um separado

---

## Estado dos Checkpoints

```
~/.kothar/state/
├── checkpoints.log       # histórico de CPs (timestamp, tipo, decisão)
├── pending-approvals     # CPs aguardando Bruno
└── approved-templates    # templates pré-aprovados (ex: "feat: X")
```

---

## Integração no Core Loop

```
SENTIR → PENSAR → VALIDAR (gates) → [CHECKPOINTS?] → AGIR
                                              ↓
                                    SIM → espera Bruno
                                    NÃO → age sozinho
```

---

## Quando ATIVAR modo "confiança total" (futuro)

Após 30 dias de uso estável, Bruno pode ativar:

```bash
kothar trust --level=high
```

**Efeitos:**
- CP2 (nomenclatura) → só avisa, não bloqueia (padrão já recomendado pelo Kothar)
- CP6 (feature) → só pede validação de features grandes (>10 arquivos)
- CP3 (commit) → commit message template "fix:" / "feat:" pré-aprovado

**Quando reverter:**
```bash
kothar trust --level=low   # padrão atual (todos os CPs)
```
