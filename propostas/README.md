# Skill Workshop — Propostas

> **Diretório:** `01_Kothar/propostas/`  
> **Sistema:** Skill Workshop Pipeline  
> **Versão:** 1.0  

---

## O que é este diretório?

Aqui ficam as **propostas de skills** criadas pelo Kothar automaticamente quando detecta padrões reutilizáveis.

---

## Pipeline

```
Detectar padrão (2+ vezes)
        ↓
Criar proposta aqui
        ↓
Bruno aprova/edita/rejeita
        ↓
Se aprovado → skill criada em habilidades/
```

---

## Como funciona

### Proposta criada
Kothar detecta que você fez a mesma coisa 2+ vezes:
- Criou modal QR 4x
- Validou input 3x
- Logou decisão 5x

### Bruno decide
- **yes** → skill é criada
- **edit** → você edita, depois yes
- **no** → proposta descartada

---

## Comandos

```bash
# Listar propostas pendentes
kothar workshop list

# Ver detalhes
kothar workshop inspect 001

# Aplicar
kothar workshop apply 001

# Rejeitar
kothar workshop reject 001
```

---

## Formato de Proposta

```markdown
---
name: proposta-skill-NNN
type: skill-proposal
created: YYYY-MM-DD
status: pending
---

# Proposta: [Nome da Skill]

## Resumo
[1-2 linhas]

## Gatilho
[Quando ativa]

## Conteúdo Proposed
\`\`\`markdown
[Skill completa]
\`\`\`

---

## Aprovação

| Opção | Ação |
|-------|------|
| yes | Cria skill |
| edit | Edita + cria |
| no | Descarta |

