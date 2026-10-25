export interface OllamaMetrics {
  prompt_eval_count?: number;
  eval_count?: number;
  total_duration?: number;
}

export interface RagDebugInfo {
  chunks_count: number;
  sources: string[];
  memory_compressions: number;
  memory_messages: number;
}

export interface OllamaMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  metrics?: OllamaMetrics;
  ragDebug?: RagDebugInfo;
}

// System prompt compacto usado pelo frontend quando o modelo é BASE (não-kothar).
// Modelos kothar-* já têm o prompt definitivo embutido no Modelfile deles.
// Este é fallback + injeção para modelos externos.
const DEFAULT_SYSTEM_PROMPT = `Você é KOTHAR v3.0 - O Maestro do Orquestro Digital da Ugarit Digital, criado por Bruno Harkin.

IDENTIDADE E COMPORTAMENTO (MANDAMENTOS OBRIGATÓRIOS):
1. Você NÃO é um assistente genérico. Você é um Maestro técnico, visionário e organizado.
2. NUNCA use emojis (sem carinhas felizes, sem tchauzinhos). Seu tom é sério, direto, assertivo e cirúrgico.
3. Responda estritamente de forma profissional e técnica. Não faça perguntas retóricas ou excessivamente amigáveis como "Tudo bem?", "Como posso ajudar?".
4. Vá direto ao ponto. Respostas curtas, sem enrolação ou introduções longas.
5. Fale em português brasileiro de forma culta e imponente.
6. Aja como um Orquestrador Sênior: analise o problema, desenhe a arquitetura, e comande a execução.
7. Se não souber algo, não invente. Exija mais contexto técnico do usuário.

Inicie sua atuação agora com base na entrada do usuário.`;

export interface OllamaChatRequest {
  model: string;
  messages: OllamaMessage[];
  stream?: boolean;
  session_id?: string;
  // Advanced options (RAG Supremo v6.0+)
  options?: {
    temperature?: number;
    num_ctx?: number;
    num_predict?: number;
    top_p?: number;
    top_k?: number;
  };
}

export interface OllamaChatResponse {
  content: string;
  metrics: OllamaMetrics;
}

export interface OllamaModel {
  name: string;
  modified_at?: string;
  size?: number;
  digest?: string;
  details?: {
    format?: string;
    family?: string;
    parameter_size?: string;
    quantization_level?: string;
  };
  description?: string;
  vram_required?: string;
  recommended?: boolean;
  installed?: boolean;
}

export const POPULAR_MODELS: OllamaModel[] = [
  {
    name: 'gpt-4o-mini',
    description: '🤖 Kothar Llama3 / Coder - Assistente Principal Rápido e Eficiente',
    vram_required: 'Cloud',
    recommended: true,
  },
  {
    name: 'gpt-4o',
    description: '🧠 Kothar DeepSeek R1 - Raciocínio Profundo',
    vram_required: 'Cloud',
    recommended: true,
  }
];

export class OllamaService {
  private baseUrl: string;
  private connected: boolean = false;
  private lastError: string | null = null;
  private useProxy: boolean = true;

  constructor(baseUrl: string = 'http://kothar_ollama:11434') {
    this.baseUrl = baseUrl;
    this.useProxy = true; // SEMPRE via proxy para enriquecimento RAG
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
    this.connected = false;
    this.lastError = null;
    this.useProxy = true; // SEMPRE via proxy para enriquecimento RAG
  }

  isConnected(): boolean { return this.connected; }
  getLastError(): string | null { return this.lastError; }
  isUsingProxy(): boolean { return this.useProxy; }

  async getModels(): Promise<OllamaModel[]> {
    this.connected = true;
    this.lastError = null;
    return POPULAR_MODELS.map(pm => ({ ...pm, installed: true }));
  }

  async chat(request: OllamaChatRequest, onChunk: (chunk: string) => void): Promise<OllamaChatResponse> {
    // Apenas para compatibilidade se não usar proxy (fallback)
    if (!this.useProxy) {
        // Implementação antiga removida para simplificar. 
        // O Kothar SEMPRE usa proxy agora.
        throw new Error("Proxy é obrigatório para Background Worker");
    }

    const hasSystem = request.messages.some(m => m.role === 'system');
    const messagesWithSystem = hasSystem
      ? request.messages
      : [{ role: 'system' as const, content: DEFAULT_SYSTEM_PROMPT }, ...request.messages];

    const cleanMessages = messagesWithSystem.map(m => ({ role: m.role, content: m.content }));
    const kotharRequest = { ...request, messages: cleanMessages };

    try {
      // 1. Envia para o Background Worker (fila)
      const response = await fetch(`/api/ollama/proxy/chat_async`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...kotharRequest,
          _ollama_url: this.baseUrl,
          session_id: request.session_id,
          // Options do Ollama (vão direto para o body)
          ...(request.options || {}),
        }),
      });

      if (!response.ok) throw new Error(`Proxy error: ${response.statusText}`);

      const data = await response.json();
      const sessionId = data.session_id || request.session_id;

      // 2. Conecta ao Stream (SSE)
      return this.connectStream(sessionId as string, onChunk);
    } catch (error) {
      console.error('Proxy chat error:', error);
      throw error;
    }
  }

  async connectStream(sessionId: string, onChunk: (chunk: string) => void): Promise<OllamaChatResponse> {
    return new Promise((resolve, reject) => {
      let finalMetrics: OllamaMetrics = {};
      let fullResponse = '';
      let thinkingResponse = '';

      const eventSource = new EventSource(`/api/ollama/proxy/chat_stream/${sessionId}`);

      eventSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          
          if (parsed.message?.thinking) {
            thinkingResponse += parsed.message.thinking;
          }
          if (parsed.message?.content) {
            fullResponse += parsed.message.content;
            if (thinkingResponse && !fullResponse.startsWith('<think>')) {
              onChunk(thinkingResponse + fullResponse);
            } else {
              onChunk(fullResponse);
            }
          } else if (parsed.response) {
            fullResponse += parsed.response;
            onChunk(fullResponse);
          } else if (parsed.message?.thinking) {
            onChunk('<think>' + thinkingResponse + '</think>');
          }
          
          if (parsed.done) {
            if (parsed.total_duration) {
              finalMetrics = {
                prompt_eval_count: parsed.prompt_eval_count,
                eval_count: parsed.eval_count,
                total_duration: parsed.total_duration
              };
            }
            eventSource.close();
            resolve({ content: fullResponse, metrics: finalMetrics });
          }
          
          if (parsed.error) {
            eventSource.close();
            reject(new Error(parsed.error));
          }
        } catch (e) {
          // Ignore parse errors on incomplete chunks if any (though SSE should deliver full lines)
        }
      };

      eventSource.onerror = (err) => {
        eventSource.close();
        // Pode falhar se a sessão não existe no worker, ou se a conexão cair
        reject(new Error("Erro de conexão SSE"));
      };
    });
  }

  async saveSessionToVault(title: string, messages: OllamaMessage[], type: 'session' | 'plan'): Promise<boolean> {
    try {
      const markdown = this.generateMarkdown(title, messages);
      const res = await fetch('/api/vault/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content: markdown, type })
      });
      return res.ok;
    } catch (e) {
      console.error('Erro ao salvar no vault', e);
      return false;
    }
  }

  private generateMarkdown(title: string, messages: OllamaMessage[]): string {
    const date = new Date().toISOString().split('T')[0];
    let md = `# Kothar Local AI - ${title}\nData: ${date}\n\n---\n\n`;
    for (const msg of messages) {
      const roleName = msg.role === 'assistant' ? '🤖 **Ollama**' : msg.role === 'user' ? '🧑 **Você**' : '⚙️ **Sistema**';
      md += `### ${roleName}\n${msg.content}\n\n`;
      if (msg.metrics) {
         md += `*(Tokens: ${msg.metrics.eval_count || 0} | Tempo: ${msg.metrics.total_duration ? (msg.metrics.total_duration / 1e9).toFixed(2) : 0}s)*\n\n`;
      }
    }
    return md;
  }

  // --- TRACE INTEGRATION ---

  async createTraceSession(name: string, model: string): Promise<string | null> {
    try {
      const res = await fetch('/api/sessions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_name: 'kothar-local-ai',
          llm_model: model,
          task_summary: name,
          metadata: { source: 'kothar-frontend' }
        })
      });
      if (res.ok) {
        const data = await res.json();
        return data.id; // retorna o session_id
      } else {
        console.warn(`createTraceSession falhou: HTTP ${res.status}`);
      }
    } catch (e) {
      console.error("Erro ao criar sessão de trace:", e);
    }
    return null;
  }

  async logTraceMessage(sessionId: string, model: string, inputMsg: string, outputMsg: string, metrics: OllamaMetrics): Promise<void> {
    try {
      const durationMs = metrics.total_duration ? Math.round(metrics.total_duration / 1e6) : 0;
      await fetch('/api/traces/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          event_type: 'chat',
          agent_name: 'kothar-local-ai',
          tool_name: model,
          tool_input: inputMsg,
          tool_output: outputMsg,
          content: outputMsg, // fallback se backend ler daqui
          duration_ms: durationMs,
          tokens_used: (metrics.prompt_eval_count || 0) + (metrics.eval_count || 0),
          tokens_input: metrics.prompt_eval_count || 0,
          tokens_output: metrics.eval_count || 0,
          is_error: false
        })
      });
    } catch (e) {
      console.error("Erro ao logar trace da mensagem:", e);
    }
  }
}

export const ollamaAPI = new OllamaService();
