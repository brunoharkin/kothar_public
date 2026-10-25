---
name: gates
versao: 1.0
data: 2026-06-19
projeto: kothar
tipo: core
descricao: 5 portões de validação automática antes de qualquer ação
---

# 🚧 GATES — Portões de Validação do Kothar v1.4.0

> **Função:** Cada ação passa por 5 portões. Se algum bloquear, Kothar para e pergunta.

## Os 5 Portões

```
Pedido do Bruno
       ↓
   ┌─────────────────────────────────────────────┐
   │  G1: PROJETO                                 │
   │      pwd == projeto autorizado?              │
   │      Falha → CP1 (pergunta se pode sair)     │
   ├─────────────────────────────────────────────┤
   │  G2: ESCOPO                                  │
   │      Ação está no escopo positivo?           │
   │      Não viola zona proibida?                │
   │      Falha → CP2 (nomenclatura) ou CP5 (rm)  │
   ├─────────────────────────────────────────────┤
   │  G3: CREDENCIAIS                             │
   │      Código a ser commitado tem credencial?  │
   │      Falha → BLOQUEIO TOTAL até limpar       │
   ├─────────────────────────────────────────────┤
   │  G4: VIABILIDADE                             │
   │      Para features: 6 pontos preenchidos?    │
   │      Falha → volta para Bruno com perguntas  │
   ├─────────────────────────────────────────────┤
   │  G5: NOMENCLATURA                            │
   │      Nome do arquivo/pasta é descritivo?     │
   │      Em português? Sem abreviações?          │
   │      Falha → CP2 (mostra alternativas)       │
   └─────────────────────────────────────────────┘
       ↓
   AGIR
```

---

## G1: PROJETO

**Pergunta:** `pwd` corresponde ao projeto autorizado?

**Implementação:** Hook `pre-bash-project.sh` + R1.

**Tabela de projetos:**

| Diretório canônico | Projeto |
|---|---|
| `/home/bruno/Cofre` | `cofre` |
| `/home/bruno/disparo-em-massa` | `disparo-em-massa` |
| `/home/bruno/bioleads` | `bioleads` |
| `/home/bruno/Ratoflix-cliente` | `ratoflix` |
| `/home/bruno/linkdabio` | `linkdabio` |
| `/home/bruno/chronodesk` | `chronodesk` |

**Variável de estado:** `~/.kothar/state/current-project`

**Quando bloqueia:**
- `pwd` não está em nenhum diretório canônico
- `pwd` está em diretório de projeto A mas Bruno pediu algo de projeto B

**Mensagem:**
```
⚠️  PROJETO: Você está em [PROJETO_ATUAL], mas o pedido parece ser de [PROJETO_PEDIDO].
   Deseja sair de [ATUAL] e ir para [PEDIDO]? (sim/não)
```

---

## G2: ESCOPO

**Pergunta:** A ação está dentro do escopo declarado? Não viola zonas proibidas?

**Zonas proibidas (NUNCA):**
- Sair do projeto autorizado sem autorização
- Deletar arquivos não listados no escopo
- Alterar regras de negócio não mencionadas
- Mexer em código de outro projeto
- Comitar com credenciais
- Usar chave SSH errada
- Citar nome de cliente/pessoa em commits
- Push sem permissão
- `--force` em qualquer operação git
- `rm -rf` em diretório não listado
- Mudar visual/layout ao corrigir bug funcional

**Quando bloqueia:**
- Ação envolve qualquer item da zona proibida
- Arquivo/pasta a ser modificado não está no escopo positivo

**Mensagem:**
```
🚧 ESCOPO: A ação "[AÇÃO]" viola a zona proibida "[ZONA]".
   Escopo declarado: [ESCOPO]
   Aprova exceção? (sim/não/editar escopo)
```

---

## G3: CREDENCIAIS

**Pergunta:** O código a ser escrito/committado contém credenciais?

**Implementação:** Hook `post-edit-cred-scan.sh` (roda após cada Edit).

**Padrões bloqueados:**
- Senhas hardcoded (`password = "..."`, `senha: "..."`)
- API keys (`api_key = "..."`, `apikey: "..."`)
- Tokens (`token: "..."`, `access_token: "..."`)
- URLs com creds (`https://user:pass@...`)
- Chaves privadas (`-----BEGIN ... PRIVATE KEY-----`)
- AWS keys (`AKIA[0-9A-Z]{16}`)
- JWT hardcoded (`eyJ...`)
- OAuth secrets (`client_secret = "..."`)

**Regex de detecção:**
```bash
grep -E "(password|senha|api[_-]?key|token|secret|access[_-]?key|private[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}" file.txt
grep -E "AKIA[0-9A-Z]{16}" file.txt
grep -E "-----BEGIN.*PRIVATE KEY-----" file.txt
grep -E "eyJ[A-Za-z0-9_-]{20,}" file.txt
```

**Quando bloqueia:**
- Qualquer match nos padrões acima

**Mensagem:**
```
🔒 CREDENCIAL DETECTADA em [ARQUIVO]:
   Linha [N]: [TRECHO_REDACTED]
   Padrão: [PADRÃO]
   
   AÇÃO: Kothar NÃO pode commitar isso.
   Mova para variável de ambiente (.env) ou vault.
   Quer que eu ajude a refatorar? (sim/não)
```

**Whitelist (não bloqueia):**
- `process.env.X` (variável de ambiente)
- `import.meta.env.X` (Vite)
- `${VAR}` em templates
- Nomes de variáveis sozinhos (`const password = ...` sem valor)

---

## G4: VIABILIDADE

**Pergunta:** Para features novas, os 6 pontos do anti-puxa-saco estão respondidos?

**Quando aplica:** Apenas features (criar algo novo). Não aplica para correções, comandos diretos ou perguntas.

**6 pontos obrigatórios:**

1. **Análise de risco** — 3-5 riscos principais
2. **Métrica real** — P50/P90 de esforço
3. **Trade-offs explícitos** — fazer / fazer depois / não fazer / alternativa
4. **Escopo negativo** — o que NÃO vai ser feito
5. **Critérios de "Pronto"** — DoD binário
6. **Recomendação** — vai / não vai / vai com ressalvas

**Quando bloqueia:**
- Algum ponto sem resposta
- Recomendação é "não vai" sem alternativa
- Viabilidade técnica ausente (stack não definida, dependência não existe)

**Mensagem:**
```
🛑 FALTA INFO para avaliar viabilidade:
   - [Ponto 1] não respondido
   - [Ponto 2] não respondido
   
   Posso prosseguir se você responder essas perguntas?
   Ou quer que eu proponha valores e você confirma?
```

---

## G5: NOMENCLATURA

**Pergunta:** O nome do arquivo/pasta/variável segue os padrões Ugarit?

**Implementação:** Hook `pre-edit-naming.sh` + validação no R2.

**Regras:**

| Regra | Exemplo OK | Exemplo NOK |
|---|---|---|
| **Português** | `componentes/`, `pagina-inicial.jsx` | `components/`, `home.jsx` |
| **Sem abreviações** | `tela-de-login/`, `mensagem-erro` | `tela-login/`, `msg-err` |
| **Descritivo** | `validar-cpf.js`, `botao-confirmar.tsx` | `util.js`, `helper.tsx` |
| **Kebab-case para pastas** | `minha-conta/`, `carrinho-compras/` | `MinhaConta/`, `carrinho_compras/` |
| **camelCase para variáveis** | `nomeUsuario`, `valorTotal` | `nome_usuario`, `NomeUsuario` |
| **PascalCase para componentes** | `BotaoConfirmar`, `TelaLogin` | `botaoConfirmar`, `botao_confirmar` |
| **Sem prefixos redundantes** | `Login.jsx` (em pasta `auth/`) | `AuthLogin.jsx` |
| **Estrutura frontend/** | `frontend/componentes/...` | `src/components/...` |

**Quando bloqueia:**
- Vai criar arquivo com nome em inglês
- Vai usar abreviação (exceto `id`, `url`, `api`, `cpf`, `cnpj`, `pix`, `qr`)
- Vai criar `src/` em vez de `frontend/`
- Vai usar `snake_case` em vez de `kebab-case` para pasta

**Mensagem:**
```
🏷️  NOMENCLATURA proposta:
   Opção A: [nome_descritivo_completo]
   Opção B: [nome_alternativo]
   
   Recomendação: [OPÇÃO_X] (justificativa)
   Aprova? (sim/troca)
```

---

## Quando TODOS os Gates Passam

```
✅ G1: Projeto OK
✅ G2: Escopo OK
✅ G3: Sem credenciais
✅ G4: Viável
✅ G5: Nomenclatura OK

→ AGIR (executar tool calls)
→ APRENDER (instinct engine captura)
→ RELATAR (rodapé com [projeto: NOME])
```

## Quando ALGUM Gate Bloqueia

```
❌ [G_X]: [MOTIVO]

→ APRESENTAR ao Bruno
→ AGUARDAR aprovação
→ Se aprovar: AGIR (com flag de exceção)
→ Se reprovar: VOLTAR para raciocínio
```

---

## Modo Observação (Primeiros 5 dias)

Por padrão, nas primeiras 5 dias úteis, os gates **só avisam**, não bloqueiam:

```
[AVISO] G1: Projeto pode estar errado (pwd=X, pedido=Y)
[AVISO] G5: Nomenclatura em inglês detectada
```

Bruno pode ativar modo bloqueador com:
```bash
kothar gates --mode=strict
```

Ou desativar com:
```bash
kothar gates --mode=off
```

---

## Estado Persistente

Os gates mantêm estado em:

```
~/.kothar/state/
├── current-project        # projeto autorizado
├── current-mode           # modo do contexto
├── gates-mode             # observation | strict | off
├── last-validated         # timestamp
└── violations-log.jsonl   # histórico de violações
```

---

## Integração no Core Loop

```
SENTIR (perception.md)
  → PENSAR (reasoning.md)
  → VALIDAR (gates.md) ← você está aqui
  → AGIR (com hooks)
  → APRENDER
  → RELATAR
```
