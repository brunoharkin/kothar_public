---
name: swarm-router
description: Router principal para delegar tarefas a subagentes paralelizados para aumentar a vazão de código e testes em 200%.
metadata:
  tipo: skill
  data: 2026-06-26
  categoria: orquestracao
  versao: 2.0.0
---

# Skill: Swarm Router (Orquestração Contínua)

> **Princípio:** O Kothar não é apenas um resolvedor serial, ele é um orquestrador Multi-Nó (Swarm). Para qualquer solicitação que afete **mais de 1 arquivo ou contenha complexidade média/alta**, o Kothar automaticamente assume a posição de **Orquestrador**.

---

## 🤖 A Orquestração em Swarm

### 1. Decisão de Delegação
Quando a tarefa sai da fase de "Design" e entra no "Build", o Kothar analisa:
- *Essa feature toca Front e Back?* 
- *Requer refatoração extensa?*
Se sim, ele não codifica arquivo por arquivo sequencialmente. Ele divide em sub-processos paralelos (simulados via hook `swarm-delegate.sh`).

### 2. Papéis dos Subagentes
Os subagentes operam isolados no `project-sandbox` antes do merge:
- **Agente Dev (Frontend):** Responsável por UI/UX, focado na camada `frontend/paginas/`.
- **Agente Dev (Backend):** Responsável por regra de negócio e lógica de dados `backend/`.
- **Agente QA (Testador):** Avalia sintaxe, linters e roda o DoD para validar o trabalho dos Devs.

### 3. Sincronização
Os agentes não "conversam" entre si no vácuo. Todo o estado do que estão fazendo é logado no `00_Memoria/Projetos/estado-atual.md` (no formato Markdown pro usuário ver) e os raciocínios técnicos ficam gravados via `rag-engine` no ChromaDB.

---

## 📋 Regra de Adoção (Novo Padrão)

- **ANTES:** Orquestração era rara e desencorajada.
- **AGORA:** É o padrão de "Build" para ganhar 200% de velocidade. O Kothar principal ("Core") dedica seu tempo a validar (Verify) o trabalho feito pelos sub-agentes, recusando código que viole o "Menor Escopo".

---

*Skill criada em 2026-06-26 — Bruno Harkin / Kothar (v2.0)*
