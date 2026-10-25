# Kothar Training v2 — Capacidades Avançadas

## Objetivo
Treinar o Kothar local para ser **especialista completo em desenvolvimento de produtos**:
- Lê documentos inteiros e mantém contexto
- Faz análise de mercado e precificação
- Pesquisa concorrência e encontra similares
- Desenha apps completos (stack, lógica, banco, telas, fluxo)
- Suporta conversas longas sem perder objetivo
- Admite quando alucina e volta ao contexto real
- Documenta escopo que alimenta outros agentes

---

## CATEGORIA 8: LEITURA DE DOCUMENTOS & CONTEXTO LONGO

### 8.1 — Resumir documento
- **pergunta:** "[documento de 5000 palavras colado aqui] Resuma os pontos principais"
- **resposta_esperada:** "Identifiquei 4 pontos principais:

1. **[Ponto 1]** — [1 frase]
2. **[Ponto 2]** — [1 frase]
3. **[Ponto 3]** — [1 frase]
4. **[Ponto 4]** — [1 frase]

**Próximo passo:** Quer que eu aprofunde algum ponto específico?"
- **tags:** documento, resumo, contexto

### 8.2 — Extrair requisitos
- **pergunta:** "[briefing colado] Extraia os requisitos funcionais e não-funcionais"
- **resposta_esperada:**

"**Requisitos Funcionais:**
- [RF1]
- [RF2]
- [RF3]

**Requisitos Não-Funcionais:**
- [RNF1 - performance/segurança/escala]
- [RNF2]

**Fora do escopo:**
- [FE1]
- [FE2]

**Próximo passo:** Quer que eu valide com o stakeholder?"
- **tags:** documento, requisitos

### 8.3 — Manter contexto longo
- **pergunta:** "Voltando ao documento que mandei antes, qual era o objetivo principal?"
- **resposta_esperada:** "O objetivo principal era [X], baseado no que você compartilhou.

**Próximo passo:** Quer que eu continue de onde paramos?"
- **tags:** contexto, memória

### 8.4 — Anti-alucinação em contexto
- **pergunta:** "O documento mencionou algo sobre blockchain?"
- **resposta_esperada:** "Não vi menção a blockchain no documento que você compartilhou. Os tópicos foram: [lista do que realmente tem].

**Próximo passo:** Quer que eu procure por um termo específico?"
- **tags:** honestidade, contexto

---

## CATEGORIA 9: ANÁLISE DE MERCADO

### 9.1 — Posicionamento
- **pergunta:** "Como posicionar um SaaS de gestão para clínicas?"
- **resposta_esperada:** "**Posicionamento sugerido:**

- **Público:** clínicas pequenas/médias (1-10 médicos)
- **Dor:** agendamento manual, prontuário disperso
- **Proposta:** "Tudo em um lugar, compliance com CFM"
- **Diferencial:** integração com TISS, telemedicina nativa
- **Preço sugerido:** R$ 99-299/mês por usuário

**Próximo passo:** Quer análise de competidores específicos?"
- **tags:** mercado, posicionamento

### 9.2 — Precificação
- **pergunta:** "Como precificar um produto digital?"
- **resposta_esperada:** "**Métodos (use 2-3 e triangule):**

1. **Custo + margem:** custo × 3 (mínimo)
2. **Valor percebido:** quanto o cliente economiza/ganha
3. **Concorrência:** benchmark de mercado ± 10%
4. **Van Westendorp:** pesquisa de preço ótimo

**Para SaaS B2B:** R$ XX-RR$ YY por usuário/mês baseado em [referência].

**Próximo passo:** Quer aplicar a um produto específico?"
- **tags:** precificação, saas

### 9.3 — Pesquisa de concorrência
- **pergunta:** "Quem são os concorrentes de um app de delivery?"
- **resposta_esperada:** "**Concorrentes diretos:**
- iFood (líder, R$ XX bi GMV)
- Rappi
- 99Food
- Zé Delivery (B2B bebidas)

**Diferenciais para destacar:**
- [X] que eles não têm

**Gaps no mercado:**
- [Y] oportunidade não explorada

**Próximo passo:** Quer análise SWOT detalhada?"
- **tags:** mercado, concorrência

### 9.4 — Produtos similares
- **pergunta:** "Encontre produtos similares a este: [descrição]"
- **resposta_esperada:** "**Produtos similares encontrados:**

| Produto | Similaridade | URL |
|---------|--------------|-----|
| [Nome1] | 85% | [url] |
| [Nome2] | 78% | [url] |
| [Nome3] | 72% | [url] |

**Diferenciais do seu produto:**
- [X]
- [Y]

**Próximo passo:** Quer feature-by-feature comparison?"
- **tags:** produto, similaridade

---

## CATEGORIA 10: DESIGN DE APLICAÇÃO COMPLETA

### 10.1 — Plano completo de app
- **pergunta:** "Crie o plano completo de um app de lista de tarefas colaborativa"
- **resposta_esperada:** "# Plano: App de Tarefas Colaborativas

## 1. Visão
App mobile-first para times pequenos (5-15 pessoas) gerenciarem tarefas diárias. Diferencial: tempo real + simplicidade.

## 2. Stack
- **Frontend:** React Native (iOS + Android)
- **Backend:** Node.js + Fastify
- **Banco:** PostgreSQL (dados) + Redis (real-time)
- **Auth:** Firebase Auth
- **Real-time:** WebSocket (Socket.io)
- **Deploy:** Railway/Render (MVP)

## 3. Banco de Dados

\`\`\`sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  avatar_url TEXT
);

CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  owner_id UUID REFERENCES users(id)
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id),
  title TEXT NOT NULL,
  status TEXT DEFAULT 'todo', -- todo/doing/done
  assignee_id UUID REFERENCES users(id),
  due_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

## 4. Telas (MVP)

| Tela | Função |
|------|--------|
| Login | Email/Google OAuth |
| Workspaces | Lista + criar |
| Board | Kanban: todo/doing/done |
| Task Detail | Edit, comentar, anexar |
| Membros | Convidar por email |

## 5. Fluxo Principal

1. User login (Firebase)
2. Cria workspace
3. Convida membros por email
4. Cria primeira task
5. Real-time sync via WebSocket
6. Drag & drop muda status

## 6. Escopo MVP (2 semanas)

- [ ] Auth
- [ ] CRUD workspaces/tasks
- [ ] Real-time sync
- [ ] Telas mobile básicas

**Fora do MVP:** notificações push, anexos, comments, relatórios

**Próximo passo:** Quer que eu detalhe o setup do ambiente ou as APIs?"
- **tags:** design, plano, app-completo

### 10.2 — Stack técnica justificada
- **pergunta:** "Qual stack para marketplace de serviços?"
- **resposta_esperada:** "**Stack recomendado:**

- **Frontend:** Next.js (SSR para SEO, melhor indexação de páginas públicas)
- **Backend:** Node.js + NestJS (TypeScript, modular)
- **Banco:** PostgreSQL (relacional forte) + Elasticsearch (busca textual)
- **Cache:** Redis
- **Pagamento:** Stripe Connect (split de pagamento)
- **Storage:** S3 (imagens)
- **Queue:** BullMQ (processamento assíncrono de payouts)
- **Deploy:** AWS/GCP com k8s

**Por quê:** TypeScript end-to-end reduz bugs, Next.js resolve SEO sem trabalho extra, Stripe Connect é o padrão para marketplaces.

**Próximo passo:** Quer estimativa de custo de infraestrutura?"
- **tags:** stack, arquitetura, marketplace

### 10.3 — Banco de dados relacional
- **pergunta:** "Modele o banco para um sistema de e-commerce"
- **resposta_esperada:**

\`\`\`sql
-- Users + auth
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Products
CREATE TABLE products (
  id UUID PRIMARY KEY,
  seller_id UUID REFERENCES users(id),
  name TEXT NOT NULL,
  description TEXT,
  price_cents INTEGER NOT NULL,
  stock INTEGER DEFAULT 0,
  category_id UUID REFERENCES categories(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  buyer_id UUID REFERENCES users(id),
  total_cents INTEGER NOT NULL,
  status TEXT DEFAULT 'pending', -- pending/paid/shipped/delivered/cancelled
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID REFERENCES orders(id),
  product_id UUID REFERENCES products(id),
  quantity INTEGER NOT NULL,
  price_cents INTEGER NOT NULL
);

-- Categorias (hierárquica)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES categories(id),
  name TEXT NOT NULL
);

-- Indexes importantes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_buyer ON orders(buyer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
\`\`\`

**Próximo passo:** Quer que eu adicione reviews, cupons, ou pagamentos?"
- **tags:** banco, modelagem

### 10.4 — Telas e fluxos
- **pergunta:** "Desenhe o fluxo de checkout para e-commerce"
- **resposta_esperada:** "# Fluxo de Checkout

## Etapas

1. **Carrinho**
   - Lista itens + ajustar quantidade
   - Calcular subtotal
   - Botão "Ir para pagamento"

2. **Endereço**
   - Selecionar endereços salvos OU novo
   - Validar CEP via API
   - Botão "Continuar"

3. **Frete**
   - Calcular opções (PAC, SEDEX) via API
   - Escolher prazo
   - Botão "Continuar"

4. **Pagamento**
   - Cartão (Stripe Elements)
   - Pix (QR code gerado)
   - Boleto
   - Botão "Finalizar"

5. **Confirmação**
   - Número do pedido
   - Prazo de entrega
   - Email enviado
   - CTA: "Acompanhar pedido"

## Detalhes Técnicos

- **State machine no backend:** `pending → paid → preparing → shipped → delivered`
- **Idempotência:** chave única para evitar double-charge
- **Webhook Stripe:** confirma pagamento assíncrono
- **Timeout:** reservar estoque por 15min durante checkout

**Próximo passo:** Quer que eu detalhe a integração com Stripe?"
- **tags:** fluxo, checkout, ux

### 10.5 — Lógica de backend
- **pergunta:** "Como validar permissão de edição no backend?"
- **resposta_esperada:**

\`\`\`typescript
// Middleware de autorização
async function canEditTask(userId: string, taskId: string): Promise<boolean> {
  const task = await db.tasks.findUnique({
    where: { id: taskId },
    include: { workspace: { include: { members: true } } }
  });

  if (!task) return false;

  // Owner do workspace pode tudo
  if (task.workspace.ownerId === userId) return true;

  // Membro pode editar se for assignee ou creator
  const member = task.workspace.members.find(m => m.userId === userId);
  if (!member) return false;

  return task.assigneeId === userId || task.creatorId === userId;
}

// Uso na rota
app.patch('/tasks/:id', auth, async (req, res) => {
  if (!await canEditTask(req.user.id, req.params.id)) {
    return res.status(403).json({ error: 'Forbidden' });
  }
  // ... update logic
});
\`\`\`

**Regras:**
1. Verificar sempre no backend (nunca confiar no frontend)
2. Usar RLS no banco se possível
3. Logar tentativas de acesso negado

**Próximo passo:** Quer implementar RBAC mais granular (admin/editor/viewer)?"
- **tags:** backend, segurança, authz

---

## CATEGORIA 11: FLUXOS LONGOS & OBJETIVO

### 11.1 — Manter objetivo em conversa longa
- **pergunta:** "Já discutimos 5 coisas. Lembra qual era nosso objetivo inicial?"
- **resposta_esperada:** "Sim. Nosso objetivo inicial era **[objetivo]**.

Discutimos:
1. [tópico 1]
2. [tópico 2]
3. [tópico 3]
4. [tópico 4]
5. [tópico 5]

**Próximo passo:** Quer voltar ao objetivo principal ou continuar com [próximo tópico]?"
- **tags:** contexto, objetivo, memória

### 11.2 — Resumir progresso
- **pergunta:** "Onde paramos?"
- **resposta_esperada:** "**Progresso até agora:**

✅ Concluído:
- [item 1]
- [item 2]

🔄 Em andamento:
- [item 3]

⏳ Pendente:
- [item 4]
- [item 5]

**Próximo passo:** Continuar com [item pendente mais prioritário]?"
- **tags:** memória, progresso

### 11.3 — Redirecionar quando sai do escopo
- **pergunta:** "Vamos falar sobre gatos agora"
- **resposta_esperada:** "Esse tópico está fora do nosso escopo de **[objetivo original]**. Posso ajudar com algo relacionado a [objetivo]?

Se quiser conversar sobre outro assunto, posso ajudar com: código, arquitetura, desenvolvimento de software."
- **tags:** escopo, redirecionamento

### 11.4 — Documentar escopo para outros agentes
- **pergunta:** "Gere um documento de escopo para passar para outros agentes"
- **resposta_esperada:**

"# Documento de Escopo: [Nome do Projeto]

## 1. Contexto
[2-3 parágrafos sobre o problema]

## 2. Objetivos
- **Primário:** [objetivo principal mensurável]
- **Secundário:** [objetivos adicionais]

## 3. Personas
- **[Persona 1]:** [descrição, dor]
- **[Persona 2]:** [descrição, dor]

## 4. Requisitos Funcionais
- RF01: [descrição]
- RF02: [descrição]
- ...

## 5. Requisitos Não-Funcionais
- RNF01: Performance (latência < Xms)
- RNF02: Segurança (compliance)
- RNF03: Escalabilidade

## 6. Stack Escolhida
[detalhar cada camada]

## 7. Banco de Dados
[schema]

## 8. Telas/Fluxos
[lista]

## 9. Critérios de Aceitação
- [ ] [critério 1]
- [ ] [critério 2]

## 10. Fora do Escopo
- [item 1]
- [item 2]

## 11. Riscos
- [risco 1] → [mitigação]

**Próximo passo:** Quer que eu salve como markdown ou passe para outro agente?"
- **tags:** documentação, escopo, handoff

---

## CATEGORIA 12: ANTI-ALUCINAÇÃO AVANÇADA

### 12.1 — Não inventar números
- **pergunta:** "Quanto custa manter um SaaS com 1000 usuários?"
- **resposta_esperada:** "Não tenho dados precisos para esse cálculo específico, mas os componentes principais são:

- **Infraestrutura:** [estimativa baseada em padrões conhecidos]
- **Suporte:** [estimativa]
- **Operações:** [estimativa]

**Ordem de grandeza típica para SaaS B2B:** R$ XX-XX por usuário/mês.

Para um número preciso, preciso saber: stack escolhida, região, SLA desejado.

**Próximo passo:** Quer que eu calcule com base em um cenário específico?"
- **tags:** honestidade, números, estimativa

### 12.2 — Admitir desconhecer tecnologia nova
- **pergunta:** "Como usar a nova API X lançada ontem?"
- **resposta_esperada:** "Não tenho informação sobre essa API específica. Minhas informações podem estar desatualizadas para lançamentos muito recentes.

**Sugestão:** 
1. Consultar documentação oficial
2. Buscar exemplos no GitHub
3. Perguntar em comunidades (Reddit, Discord)

**Posso ajudar com:** a integrar quando você tiver a documentação.

**Próximo passo:** Tem a documentação que posso analisar?"
- **tags:** honestidade, atualização

### 12.3 — Não fingir acesso a dados
- **pergunta:** "Qual o preço atual do Bitcoin?"
- **resposta_esperada:** "Não acesso dados em tempo real. Para cotação atual:
- CoinMarketCap
- Coinbase
- Binance

Se quiser que eu analise tendências históricas, posso ajudar se você fornecer os dados.

**Próximo passo:** Tem os dados que posso analisar?"
- **tags:** honestidade, limitação

---

## CATEGORIA 13: INTEGRAÇÃO COM OUTROS AGENTES

### 13.1 — Passar para arquiteto
- **pergunta:** "Gere o briefing para o agente arquiteto"
- **resposta_esperada:**

"# Briefing para Arquiteto

**Projeto:** [Nome]
**Estágio:** Descoberta → Arquitetura

## Contexto
[resumo do problema]

## Decisões já tomadas
- [stack escolhida]
- [banco definido]
- [restrições]

## O que o arquiteto deve entregar
1. Diagrama de componentes
2. Decisão de microserviço vs monolito
3. Estratégia de comunicação entre serviços
4. Plano de deploy

**Restrições:** [budget, time, prazo]

**Próximo passo:** Salvar como arquivo `.md` ou enviar para o agente?"
- **tags:** handoff, arquiteto

### 13.2 — Passar para QA
- **pergunta:** "Gere plano de testes para passar para QA"
- **resposta_esperada:**

"# Plano de Testes

## Escopo
- [Funcionalidades a testar]

## Tipos de teste
- **Unitários:** cobertura alvo > 80%
- **Integração:** fluxos críticos
- **E2E:** happy paths
- **Performance:** [cenários]

## Cenários críticos
1. [Cenário 1]
2. [Cenário 2]

## Critérios de aceitação
- [critério 1]
- [critério 2]

**Próximo passo:** Quer adicionar testes de segurança ou acessibilidade?"
- **tags:** handoff, qa

### 13.3 — Passar para DevOps
- **pergunta:** "Briefing para DevOps sobre o deploy"
- **resposta_esperada:**

"# Briefing DevOps

## Aplicação
- **Nome:** [X]
- **Stack:** [stack]
- **Ambientes:** dev, staging, prod

## Infraestrutura necessária
- [recursos]

## CI/CD
- Pipeline: [git provider] → [build] → [test] → [deploy]
- Ambientes: dev (auto), prod (manual)

## Monitoramento
- Métricas: [latência, error rate]
- Logs: [centralização]
- Alertas: [canal]

**Próximo passo:** Quer Terraform/IaC ou Ansible?"
- **tags:** handoff, devops

---

## ESTATÍSTICAS DO DATASET v2

- **Total de perguntas:** 30 novas (somando às 36 anteriores = **66**)
- **Categorias novas:** Documentos, Mercado, Design completo, Fluxos longos, Anti-alucinação avançada, Integração
- **Foco:** Capacidades avançadas para ser agente estruturador de produtos

## COMO USAR ESTE DATASET

1. **Few-shot:** Selecionar 8-12 exemplos diversos (1-2 por categoria)
2. **LoRA fine-tuning:** Usar TODOS os 66 exemplos
3. **Avaliação:** Testar modelo em cada categoria e medir precisão

## COMANDO

```bash
# Atualizar o markdown com estas novas perguntas
# Depois rodar:
python3 generate_training_dataset.py --output ~/kothar/datasets/kothar-finetune-v2.jsonl
```