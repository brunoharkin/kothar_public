---
name: fluxo-gsd-desenvolvimento
description: Fluxo de desenvolvimento estruturado (Git, Ship, Done) para evitar degradação de contexto e garantir entregas previsíveis
version: 1.0.0
ferramenta: gsd-core (open-gsd/gsd-core)
---

# Habilidade: Fluxo GSD de Desenvolvimento

## Por que existe

Conforme as interações com o modelo avançam, o histórico do chat acumula logs longos, códigos redundantes e conversas informais. Isso gera **degradação de contexto** (context rot), fazendo a IA alucinar, esquecer regras de nomenclatura ou ignorar diretrizes visuais. 

Esta habilidade força a separação do estado ativo em **artefatos duráveis no segundo cérebro (Obsidian)**, garantindo que qualquer agente que assuma o trabalho comece com contexto limpo e estruturado.

---

## 🔄 Ciclo de Vida GSD (pt-BR)

O desenvolvimento de qualquer feature ou projeto segue 5 etapas obrigatórias:

```
[Discussão] ➔ [Planejamento] ➔ [Execução] ➔ [Verificação] ➔ [Entrega]
```

### 1. Discussão (Discuss)
Alinhamento de escopo e clarificação de ambiguidades.
* **Artefato**: `visao.md` (Objetivos macro, público-alvo, restrições e regras máximas).

### 2. Planejamento (Plan)
Desenho da solução técnica e arquitetura das pastas (em pt-BR).
* **Artefato**: `roteiro.md` (Milestones e cronograma de entrega).
* **Artefato**: `estado-atual.md` (Checklist de tarefas e estados do sprint).

### 3. Execução (Execute)
Escrita de código com commits curtos e updates contínuos de progresso.
* **Ação**: Atualização de `estado-atual.md` marcando progresso (`[ ]` para pendente, `[/]` para em progresso, `[x]` para concluído).

### 4. Verificação (Verify)
Rodar bateria de testes locais, build de produção e verificação estética.
* **Ferramenta**: Rodar linters e obrigatoriamente `/react-doctor` em projetos React.

### 5. Entrega (Ship)
Envio para produção/repositório e documentação final de handover.
* **Artefato**: `entrega-sucesso.md` (O que foi testado, logs de sucesso e links de homologação).

---

## 📂 Estrutura dos Artefatos contra Degradação de Contexto

Estes arquivos devem ser criados/atualizados na pasta de documentação técnica do projeto no cofre (`03_Empresa/Produtos/{produto}/docs/` ou `01_Kothar/specs/{projeto}/`):

### 📄 `visao.md`
```markdown
# Visão Geral - [Nome do Projeto]
- **Objetivo**: O que resolve e por quê.
- **Pilha Tecnológica**: Lista de frameworks e linguagens.
- **Restrições de Arquitetura**: Padrões de nomenclatura pt-BR e pastas.
```

### 📄 `roteiro.md`
```markdown
# Roteiro de Entregas (Roadmap)
- [x] Marco 1 — Scaffold e Banco de Dados (Finalizado YYYY-MM-DD)
- [/] Marco 2 — Integração e APIs (Ativo)
- [ ] Marco 3 — Interface Visual Premium
```

### 📄 `estado-atual.md` (Atualizado dinamicamente)
> [!IMPORTANT]
> Este arquivo é a única fonte de verdade de estado para evitar context rot. A IA lê este arquivo ao iniciar uma sessão em vez de reanalisar todo o chat histórico.
```markdown
# Estado Atual - [Data]
## Sprint Ativo
- [x] Rota de autenticação backend
- [/] Tela de login frontend (estilização pendente)
- [ ] Conectar com API do WhatsApp

## Bloqueadores
- Nenhuma chave de teste fornecida para o serviço X.
```

### 📄 `entrega-sucesso.md`
```markdown
# Entrega e Handoff - [Feature]
- **O que mudou**: Resumo técnico da implementação.
- **Evidências de Teste**: Prints de tela, logs de console, output do linter e score do `react-doctor`.
```

---

## 🛠️ Regra Operacional

Antes de iniciar qualquer código:
1. Verifique se `visao.md` e `estado-atual.md` existem no diretório do projeto.
2. Se não existirem, crie-os antes de gerar arquivos de backend ou frontend.
3. Ao finalizar sua sessão de trabalho, atualize `estado-atual.md` e escreva no diário de interações diárias.

---

## Voltar
← [[catalogo-habilidades]]
