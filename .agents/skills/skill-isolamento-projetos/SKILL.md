---
name: skill-isolamento-projetos
description: >-
  Skill obrigatória para isolamento rígido de projetos - NUNCA editar fora do projeto atual
---

# Skill: Isolamento Rígido de Projetos (OBRIGATÓRIA)

## 🚫 Regra de Ouro Absoluta

```
╔═══════════════════════════════════════════════════════════════╗
║  🎯 PRINCÍPIO ABSOLUTO:                                     ║
║  O Kothar só pode MODIFICAR arquivos DENTRO do projeto ATUAL  ║
║                                                               ║
║  ✅ Pode LER de outros projetos (buscar referências)          ║
║  ❌ NÃO PODE MODIFICAR arquivos de outros projetos            ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Projetos Registrados

| ID | Nome | Raiz |
|----|------|------|
| `cofre` | Cofre | `/home/bruno-harkin/Cofre` |
| `disparo-em-massa` | Disparo em Massa | `/home/bruno-harkin/disparo-em-massa` |
| `crm-saphia` | CRM Saphia | `/home/bruno-harkin/crm-saphia` |
| `kothar-dashboard` | Kothar Dashboard | `/home/bruno-harkin/kothar` |
| `ratoflix` | Ratoflix | `/home/bruno-harkin/Ratoflix-cliente` |
| `bioleads` | BioLeads | `/home/bruno-harkin/bioleads` |
| `linkdabio` | LinkDaBio | `/home/bruno-harkin/linkdabio` |
| `chronodesk` | ChronoDesk | `/home/bruno-harkin/chronodesk` |

---

## Fluxo Obrigatório

### 1. Selecionar Projeto (Início de Sessão)
```bash
# Se não houver projeto selecionado, PERGUNTAR ao usuário:
kothar-select-project <nome-do-projeto>

# Exemplo:
kothar-select-project disparo-em-massa
# Resultado: ✅ Projeto selecionado: disparo-em-massa
```

### 2. Antes de Qualquer Edit/Write
```bash
# Hook pre-edit-project-guard.sh valida AUTOMATICAMENTE
# Se arquivo fora do projeto → BLOQUEADO com mensagem clara
```

### 3. Se Precisar Trabalhar em Outro Projeto
```bash
# ❌ NÃO SAIR EDITANDO!
# ✅ PARAR e PERGUNTAR:

echo "❌ Esse arquivo pertence ao projeto X, não ao Y atual."
echo "💡 Deseja mudar para o projeto X? (sim/não)"
# Se sim: kothar-select-project x
# Se não: CANCELAR operação
```

---

## Exemplo: Bug QUE NÃO pode mais acontecer

### ❌ ANTES (QUEBRADO)
```
Bruno: "corrige a Evolution API do Ratoflix"
Kothar: pesquisa "evolution" no sistema
Kothar: acha arquivo do Disparo em Massa
Kothar: modifica o Disparo em Massa ← ERRADO! Bug crítico!
```

### ✅ DEPOIS (CORRIGIDO)
```
Bruno: "corrige a Evolution API do Ratoflix"
Kothar: ❌ "Porta 2786 = projeto disparo-em-massa, não ratoflix"
Kothar: "Bruno, qual arquivo/porta pertence ao Ratoflix?"
Bruno: especifica: "é /home/bruno-harkin/Ratoflix-cliente/backend/openwa/..."
Kothar: modifica SOMENTE o Ratoflix ✅
```

---

## Regra Anti-Busca Cega

**ANTES de buscar por "função X" ou "arquivo Y":**

1. ✅ Verificar EM QUAL PROJETO estou (via `~/.kothar/state/current-project`)
2. ✅ Buscar SOMENTE dentro desse projeto
3. ❌ NÃO buscar globalmente no sistema
4. ✅ Se encontrar em outro projeto:
   - Perguntar se deve CLONAR para o projeto atual
   - NUNCA modificar o projeto de origem

---

## Comandos Disponíveis

### Selecionar Projeto
```bash
kothar-select-project <nome-projeto>
```

### Ver Projeto Atual
```bash
cat ~/.kothar/state/current-project
# Retorna: disparo-em-massa
```

### Ver Raiz do Projeto Atual
```bash
cat ~/.kothar/state/current-project-root
# Retorna: /home/bruno-harkin/disparo-em-massa
```

### Listar Projetos Disponíveis
```bash
kothar-select-project
# Mostra lista de projetos
```

---

## Verificação de Isolamento

Quando receber pedido para modificar arquivo:

1. **Extrair caminho do arquivo** da solicitação
2. **Comparar** com `~/.kothar/state/current-project-root`
3. **Se fora do projeto:**
   - ❌ BLOQUEAR imediatamente
   - 📋 Mostrar projeto atual e caminho tentou acessar
   - 💡 Sugerir mudança de projeto

---

## DoD - Verificação de Isolamento

- [ ] `~/.kothar/projects.json` existe e tem todos os projetos
- [ ] `kothar-select-project` funciona corretamente
- [ ] Hook bloqueia edição fora do projeto atual
- [ ] Ao tentar editar arquivo de outro projeto → mensagem clara de erro
- [ ] Ao iniciar sessão → projeto atual é carregado

---

*Skill obrigatória — Kothar v2.2.0*
