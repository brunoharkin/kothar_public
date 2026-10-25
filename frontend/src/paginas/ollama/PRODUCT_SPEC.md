# Kothar Local — Especificação do Produto

## O que o kothar local FAZ

O Kothar local é um **arquiteto de produto full-stack** que cria planos completos de aplicações que o usuário depois executa no Claude Code ou outro agente de terminal.

### Capacidades principais

#### 1. **Planejamento completo de produto**
- Stack tecnológica (frontend + backend + banco + infra)
- Arquitetura de telas (wireframes em texto/markdown)
- Schema de banco de dados completo
- Lista de APIs/endpoints
- Configurações de ambiente
- Definição de agentes especialistas por etapa

#### 2. **Geração de frontend visual**
- Código **completo e definitivo** de frontend (HTML/CSS/React)
- Componentes reutilizáveis
- Botão de **preview** após cada página criada
- Renderização ao vivo no chat (usuário VÊ a página real)

#### 3. **Documentação estruturada**
- Salva tudo no **cofre** automaticamente
- Cada plano vira um documento versionado
- Links entre documentos relacionados

#### 4. **Trechos de código backend (não completo)**
- Mostra a estrutura principal
- Assinaturas de endpoints
- Schemas de banco
- **NÃO** cria o backend inteiro (gasta muitos tokens)

---

## O que o kothar local NÃO FAZ

### 1. **Não cria código backend completo**
- O usuário não está conectado a terminal
- Backend seria desperdício de tokens sem execução
- Usuário passa o plano para Claude Code criar

### 2. **Não executa comandos**
- Sem acesso a shell/terminal
- Sem execução de migrations
- Sem testes locais

### 3. **Não integra com Git diretamente**
- Usuário faz commit/push manualmente
- Kothar gera apenas os arquivos finais

---

## Fluxo de Trabalho

```
1. Usuário: "Quero criar um app de tarefas colaborativas"
        ↓
2. Kothar: Analisa contexto, sugere stack
        ↓
3. Kothar: Cria PLANO COMPLETO (salvo no cofre)
        ↓
4. Kothar: Começa frontend página por página
        ↓
5. Kothar: Renderiza HTML/CSS/React inline
        ↓
6. Usuário: Vê preview ao vivo
        ↓
7. Kothar: Salva cada página como artefato
        ↓
8. Usuário: Aprova ou pede ajustes
        ↓
9. Kothar: Plano final pronto para execução
        ↓
10. Usuário: Passa para Claude Code com contexto completo
        ↓
11. Claude Code: Executa o plano no terminal
```

---

## Estrutura do Plano Gerado

```markdown
# Plano: [Nome do Projeto]

## 1. Visão Geral
- Problema que resolve
- Público-alvo
- Diferencial

## 2. Stack Escolhida
- Frontend: React + Vite + TypeScript
- Backend: Python + FastAPI
- Banco: PostgreSQL + Redis
- Infra: Docker + nginx

## 3. Schema do Banco
[SQL completo com CREATE TABLE]

## 4. APIs / Endpoints
[Lista de endpoints com método, path, request, response]

## 5. Telas (Frontend)
[Para cada tela:]
- Rota
- Componentes usados
- Props/state
- Interações

## 6. Wireframes (ASCII)
┌─────────────────────────┐
│  Logo    Search   User   │
├─────────────────────────┤
│  [+ New]      [Filter]  │
├─────────────────────────┤
│  □ Task 1      [edit]   │
│  □ Task 2      [edit]   │
└─────────────────────────┘

## 7. Configurações
- Variáveis de ambiente
- Secrets necessários
- Dependências externas

## 8. Agentes Especialistas Envolvidos
- frontend_agent → cria todas as telas
- backend_agent → implementa APIs
- database_agent → migrations
- devops_agent → CI/CD

## 9. Critérios de Aceitação
- [ ] Login funciona
- [ ] CRUD de tarefas completo
- [ ] Real-time sync funciona
- [ ] Deploy em produção

## 10. Próximos Passos
1. Claude Code: começar pelo backend (modelos)
2. Claude Code: implementar endpoints
3. Claude Code: criar frontend página por página
4. Claude Code: setup de deploy
```

---

## Como o Frontend Preview Funciona

Quando o kothar gera código HTML/React de uma tela:

1. **Código completo** aparece em bloco de código
2. **Botão "Preview"** aparece logo abaixo
3. Usuário clica → vê a página renderizada em iframe/sandbox
4. Pode pedir ajustes específicos

### Stack de Preview
- **HTML/CSS**: iframe com srcdoc
- **React**: CodeSandbox API ou render local com styled-components

---

## Output para Claude Code

Quando o plano estiver completo, o kothar gera um **bloco de comando** que o usuário copia e cola no Claude Code:

```
@claude-code

Implemente este plano completo do projeto [Nome]:

[link para documento no cofre]

Contexto:
- Stack: [stack definida]
- Banco: [schema]
- Telas: [wireframes]
- APIs: [endpoints]

Salve cada arquivo na estrutura definida no plano.
```

---

## Métricas de Sucesso

- **Tempo de planejamento**: < 30min para apps simples
- **Qualidade do plano**: critérios de aceitação completos
- **Visual fidelity**: preview bate com código final
- **Redução de tokens**: backend = só estrutura, frontend = completo
