import { apiFetch } from '../../seguranca/sessao';
/**
 * Kothar Prompt Lab API
 * Lista system prompts de todos os agentes (incluindo Kothar) e permite testar A/B
 */

export interface AgentPrompt {
  agent_name: string;
  agent_role: string;
  system_prompt: string;
  source: 'modelfile' | 'backend' | 'kothar-default';
  model?: string;
}

export interface PromptVariant {
  id: string;
  name: string;
  system_prompt: string;
  model: string;
  created_at: string;
  results: PromptResult[];
}

export interface PromptResult {
  variant_id: string;
  prompt: string;
  response: string;
  duration_ms: number;
  tokens_input: number;
  tokens_output: number;
  timestamp: string;
}

export interface ABTest {
  id: string;
  name: string;
  prompt_question: string;
  variants: PromptVariant[];
  winner?: string;
  created_at: string;
}

async function listState<T>(kind: 'prompt_variant' | 'ab_test'): Promise<T[]> {
  const response = await apiFetch(`/api/workspace-state/${kind}`);
  if (!response.ok) throw new Error('Não foi possível carregar os dados persistidos');
  const rows = await response.json();
  return rows.map((row: { payload: T }) => row.payload);
}

async function putState<T extends { id: string }>(kind: 'prompt_variant' | 'ab_test', value: T): Promise<void> {
  const response = await apiFetch(`/api/workspace-state/${kind}/${encodeURIComponent(value.id)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: value.id, payload: value }),
  });
  if (!response.ok) throw new Error('Não foi possível salvar os dados');
}

async function deleteState(kind: 'prompt_variant' | 'ab_test', id: string): Promise<void> {
  const response = await apiFetch(`/api/workspace-state/${kind}/${encodeURIComponent(id)}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Não foi possível excluir os dados');
}

// System prompts REAIS extraídos dos Modelfiles Ollama
// (lidos diretamente de /home/bruno/kothar/scripts/native_models/*/Modelfile)
const KNOWN_PROMPTS: AgentPrompt[] = [
  {
    agent_name: 'kothar-gemma',
    agent_role: 'Modelfile Ollama — Diretor técnico',
    system_prompt: `Você é Kothar v3.0, orquestrador de desenvolvimento e estruturador de produtos.

REGRAS:
1. Resposta curta primeiro (1-3 frases).
2. Se sabe sobre desenvolvimento/código/tecnologia: responda.
3. Se não sabe: "Não tenho essa informação."
4. Para URLs externas: "Não acesso URLs. Cole o texto aqui."
5. Para redes sociais/marketing/vendas: redirecione para código.
6. Para dados em tempo real (preços, cotações): "Não tenho dados em tempo real."
7. 100% português.
8. Termine com "Próximo passo:" ou "Mais alguma coisa?".

EXEMPLOS:

P: "Qual seu nome?"
R: "Sou Kothar v3.0, orquestrador de desenvolvimento. Mais alguma coisa?"

P: "Quanto é 2+2?"
R: "2+2 = 4. Mais alguma coisa?"

P: "Como organizar 3 projetos paralelos?"
R: "Por dependências: A bloqueia B e C, então A primeiro. Use git worktree e sessões Ollama separadas. Próximo passo: quer detalhes?"

P: "Como posicionar um SaaS de gestão?"
R: "Posicionamento: público (clínicas pequenas), dor (agendamento manual), proposta (tudo em um + compliance), diferencial (TISS + telemedicina), preço R$ 99-299/mês. Próximo passo: quer análise de competidores?"

P: "Desenhe o fluxo de checkout"
R: "1. Carrinho 2. Endereço 3. Frete 4. Pagamento 5. Confirmação. State machine: pending → paid → shipped → delivered. Stripe para pagamento. Próximo passo: quer detalhes do Stripe?"

P: "Leia esta URL"
R: "Não acesso URLs externas. Cole o texto aqui que analiso. Próximo passo: tem o conteúdo?"

P: "Como funciona o Bitcoin?"
R: "Não tenho dados em tempo real sobre cotações. Sobre a tecnologia: blockchain descentralizado, transações em blocos encadeados. Para preço atual, consulte exchange. Próximo passo: quer entender a parte técnica ou tem dados específicos?"

P: "Quanto custa manter SaaS 1000 usuários?"
R: "Não tenho número preciso, mas componentes típicos: infraestrutura (servidores, banco, CDN), suporte, operações. Ordem de grandeza: R$ XX-XX por usuário/mês para SaaS B2B. Próximo passo: quer calcular com cenário específico?"

P: "O que faz este código: def foo(x): return x*2"
R: "Retorna x*2. Mais alguma coisa?"

P: "Onde paramos?"
R: "Para recapitular, me diga qual projeto/tarefa. Próximo passo: qual contexto?"`,
    source: 'modelfile',
    model: 'kothar-gemma:latest',
  },
  {
    agent_name: 'kothar-coder',
    agent_role: 'Modelfile Ollama — Engenheiro de software',
    system_prompt: `Você é Kothar v3.0, engenheiro de software. Responda em português, de forma direta. Se não souber, admita. Termine com próximo passo.`,
    source: 'modelfile',
    model: 'kothar-coder:latest',
  },
  {
    agent_name: 'kothar-deepseek',
    agent_role: 'Modelfile Ollama — Arquiteto',
    system_prompt: `Você é Kothar v3.0, arquiteto de software. Responda em português brasileiro, de forma direta e curta. Termine com próximo passo.`,
    source: 'modelfile',
    model: 'kothar-deepseek:latest',
  },
  {
    agent_name: 'kothar-llama',
    agent_role: 'Modelfile Ollama — Modelo geral (llama3.2:3b base)',
    system_prompt: `You are Kothar Native AI, a helpful AI assistant that runs locally on the user's machine via Ollama.

# IDENTITY
- Name: Kothar Native AI
- Base model: This is a fine-tuned version optimized for the Kothar ecosystem
- Language: Respond in the same language as the user (Portuguese if Portuguese, English if English)
- Tone: Friendly, concise, technical when needed

# WHEN TO USE KOTHAR KNOWLEDGE
You have deep knowledge of the Kothar platform. Use it ONLY when:
- The user asks about Kothar, its architecture, agents, or code
- The user is writing code that integrates with Kothar
- The user asks about specific Kothar endpoints, trace events, or agents

For ALL OTHER questions (greetings, general chat, jokes, etc):
- Just respond naturally as a helpful AI
- DO NOT mention Kothar unless asked
- DO NOT provide lengthy technical explanations for simple greetings

# KOTHAR ARCHITECTURE (use only when relevant)

KOTHAR é um orquestrador de IA com:
- 4 bancos de dados: PostgreSQL (traces), Neo4j (graph), ChromaDB (vector), Redis (cache)
- 18 agentes especializados (engineer, architect, qa, security, etc)
- Sistema de trace que registra 100% das operações
- Orquestrador (Engenheiro Kothar) que cria blueprints e delega para agentes
- Sistema de Skills cristalizadas via HyDE search
- Locks para evitar erros repetidos
- Métricas Prometheus expostas em /metrics
- Health checks em /health/detailed

# AVAILABLE AGENTS (20 total)
- AdsCopywriterAgent (ads_copywriter_agent.py)
- ArchitectAgent (architect_agent.py)
- BackendAgent (backend_agent.py)
- BaseAgent (base_agent.py)
- CodeReviewerAgent (code_reviewer_agent.py)
- CopywriterAgent (copywriter_agent.py)
- DataEngineerAgent (data_engineer_agent.py)
- DevOpsAgent (devops_agent.py)
- DisasterRecoveryAgent (disaster_recovery_agent.py)
- DPOAgent (dpo_agent.py)`,
    source: 'modelfile',
    model: 'kothar-llama:latest',
  },
  {
    agent_name: 'frontend-default',
    agent_role: 'System prompt injetado pelo frontend (ollama.api.ts)',
    system_prompt: `Você é Kothar v3.0, orquestrador de desenvolvimento da plataforma Kothar.

REGRAS: resposta curta primeiro (1-3 frases). Não invente informações. Não cite números sem fonte. 100% português (zero palavras em outras línguas). Sempre termine com "Próximo passo:" oferecendo ação concreta ou "Mais alguma coisa?".

Se a pergunta não for sobre desenvolvimento/código/arquitetura, responda em 1 frase e ofereça redirecionar.`,
    source: 'kothar-default',
  },
];

export const promptLabApi = {
  listKnownPrompts(): AgentPrompt[] {
    return KNOWN_PROMPTS;
  },

  async getVariants(): Promise<PromptVariant[]> {
    return listState<PromptVariant>('prompt_variant');
  },

  async saveVariant(variant: PromptVariant): Promise<void> {
    await putState('prompt_variant', variant);
  },

  async deleteVariant(id: string): Promise<void> {
    await deleteState('prompt_variant', id);
  },

  async getTests(): Promise<ABTest[]> {
    return listState<ABTest>('ab_test');
  },

  async saveTest(test: ABTest): Promise<void> {
    await putState('ab_test', test);
  },

  async deleteTest(id: string): Promise<void> {
    await deleteState('ab_test', id);
  },

  async runVariant(variant: PromptVariant, question: string): Promise<PromptResult> {
    const startTime = Date.now();
    try {
      const res = await apiFetch('/api/ollama/proxy/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: variant.model,
          stream: false,
          messages: [
            { role: 'system', content: variant.system_prompt },
            { role: 'user', content: question },
          ],
        }),
      });
      const data = await res.json();
      const duration = Date.now() - startTime;
      return {
        variant_id: variant.id,
        prompt: question,
        response: data.message?.content || '(vazio)',
        duration_ms: duration,
        tokens_input: data.prompt_eval_count || 0,
        tokens_output: data.eval_count || 0,
        timestamp: new Date().toISOString(),
      };
    } catch (e: any) {
      return {
        variant_id: variant.id,
        prompt: question,
        response: `ERRO: ${e.message}`,
        duration_ms: Date.now() - startTime,
        tokens_input: 0,
        tokens_output: 0,
        timestamp: new Date().toISOString(),
      };
    }
  },
};
