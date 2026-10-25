import { apiFetch } from '../../seguranca/sessao';
/**
 * Kothar Trace API v6.0 SUPREMO (ALINHADO + TURBINADO)
 *
 * Funcionalidades:
 * - Listagem de traces por sessão
 * - Detecção de sub-agentes e modelos usados
 * - Tracking de erros com contexto (onde/quando/qual)
 * - Tokens categorizados (nunca "outros" - sempre classificado)
 * - Reportar falso positivo (marca para re-treino)
 */

export interface ApiTraceEntry {
  id: string;
  session_id: string;
  timestamp: string;
  tool: string;
  tool_name?: string;
  tool_input?: any;
  tool_output?: any;
  event_type?: string;
  agent_name?: string;
  subagent_type?: string;
  parent_tool_use_id?: string;
  input: string;
  output: string;
  raw_tool_input?: any;
  raw_tool_output?: any;
  reasoning: string | null;
  duration: number | null;
  tokens_used: number | null;
  tokens_input?: number | null;
  tokens_output?: number | null;
  context_tokens: number | null;
  token_type?: string;
  status: 'success' | 'error' | 'pending';
  is_error?: boolean;
  error_message?: string;
  metadata?: any;
}

export interface ApiSession {
  id: string;
  name: string;
  agent: string;
  sub_agent?: string | null;
  started_at: string;
  ended_at: string | null;
  status: 'active' | 'completed' | 'failed';
  trace_count?: number;
  tokens_input?: number;
  tokens_output?: number;
  tokens_total?: number;
}

// Categorias REAIS de tokens (nunca genérico "outros")
export type TokenCategory =
  | 'system_prompt'      // System prompt injetado
  | 'user_input'         // Mensagem do usuário
  | 'rag_context'        // Contexto RAG injetado
  | 'memory_history'     // Histórico de conversa
  | 'tool_result'        // Resultado de ferramenta
  | 'assistant_response' // Resposta do modelo
  | 'cascade_overhead'   // Overhead do sistema multi-modelo
  | 'error_recovery';    // Tokens usados em retry/recuperação

export interface TokenUsageByCategory {
  system_prompt: number;
  user_input: number;
  rag_context: number;
  memory_history: number;
  tool_result: number;
  assistant_response: number;
  cascade_overhead: number;
  error_recovery: number;
}

// Erro marcado pelo usuário (para re-treino)
export interface MarkedError {
  id: string;
  trace_id: string;
  session_id: string;
  error_type: 'falso_positivo' | 'falso_negativo' | 'bug_real' | 'outros';
  description: string;
  what_was_wrong: string;  // O que estava errado
  what_was_expected: string; // O que deveria ter feito
  where_in_code?: string;    // Onde no código (file:line)
  which_model?: string;      // Qual modelo cometeu
  which_agent?: string;      // Qual agente cometeu
  marked_by: string;
  marked_at: string;
  resolved: boolean;
}

const API_BASE = '/api';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  const res = await apiFetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export { verificarSessao as login, encerrarSessao as logout } from '../../seguranca/sessao';


export async function listSessions(): Promise<ApiSession[]> {
  const data: any[] = await request('/sessions/');
  return data.map(s => ({
    id: s.id,
    name: s.task_summary || 'Sessão Kothar v4',
    agent: s.agent_name || 'kothar',
    sub_agent: s.llm_model,
    started_at: s.created_at || new Date().toISOString(),
    ended_at: s.ended_at || null,
    status: s.status || 'active',
    trace_count: 0,
    tokens_input: s.tokens_input || 0,
    tokens_output: s.tokens_output || 0,
    tokens_total: (s.tokens_input || 0) + (s.tokens_output || 0),
  }));
}

export async function getSession(id: string): Promise<ApiSession> {
  const s: any = await request(`/sessions/${id}`);
  return {
    id: s.id,
    name: s.task_summary || 'Sessão Kothar v4',
    agent: s.agent_name || 'kothar',
    sub_agent: s.llm_model,
    started_at: s.created_at,
    ended_at: s.ended_at || null,
    status: s.status || 'active',
  };
}

export async function deleteSession(id: string): Promise<{ deleted: boolean; id: string }> {
  try {
    await request(`/sessions/${id}`, { method: 'DELETE' });
    return { deleted: true, id };
  } catch {
    return { deleted: false, id };
  }
}

export async function generateSessionReport(id: string): Promise<{ success: boolean }> {
  try {
    await request(`/sessions/${id}/complete`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'completed' })
    });
    return { success: true };
  } catch (e: any) {
    throw new Error(e.message);
  }
}

export async function clearSessionTraces(id: string): Promise<{ success: boolean; count: number }> {
  try {
    await request(`/traces/?session_id=${id}`, { method: 'DELETE' });
    return { success: true, count: 0 };
  } catch {
    return { success: false, count: 0 };
  }
}

// =========================================================
// SISTEMA DE MARCAÇÃO DE ERROS (REPORTAR FALSO POSITIVO)
// =========================================================

let markedErrorsCache: MarkedError[] = [];

export async function loadMarkedErrors(): Promise<MarkedError[]> {
  const response = await apiFetch(`${API_BASE}/workspace-state/marked_error`);
  if (!response.ok) throw new Error('Não foi possível carregar os erros marcados');
  const rows = await response.json();
  markedErrorsCache = rows.map((row: { payload: MarkedError }) => row.payload);
  return markedErrorsCache;
}

async function persistMarkedError(error: MarkedError): Promise<void> {
  const response = await apiFetch(`${API_BASE}/workspace-state/marked_error/${encodeURIComponent(error.id)}`, {
    method: 'PUT', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: error.id, payload: error }),
  });
  if (!response.ok) throw new Error('Não foi possível persistir o erro marcado');
}

/**
 * Marca um trace como erro que o usuário identificou.
 * Isso permite ao agente saber COMO errou para não repetir.
 */
export function markTraceAsError(
  traceId: string,
  sessionId: string,
  details: {
    error_type: MarkedError['error_type'];
    description: string;
    what_was_wrong: string;
    what_was_expected: string;
    where_in_code?: string;
    which_model?: string;
    which_agent?: string;
  }
): MarkedError {
  const error: MarkedError = {
    id: `err_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    trace_id: traceId,
    session_id: sessionId,
    error_type: details.error_type,
    description: details.description,
    what_was_wrong: details.what_was_wrong,
    what_was_expected: details.what_was_expected,
    where_in_code: details.where_in_code,
    which_model: details.which_model,
    which_agent: details.which_agent,
    marked_by: 'bruno',
    marked_at: new Date().toISOString(),
    resolved: false,
  };

  markedErrorsCache = [...markedErrorsCache.filter((item) => item.id !== error.id), error];

  // PostgreSQL é a autoridade; o cache acima serve apenas à renderização atual.
  persistMarkedError(error).catch(() => {});
  syncErrorToBackend(error).catch(() => {});

  return error;
}

/**
 * Lista todos os erros marcados pelo usuário
 */
export function getMarkedErrors(sessionId?: string): MarkedError[] {
  return sessionId ? markedErrorsCache.filter(e => e.session_id === sessionId) : [...markedErrorsCache];
}

/**
 * Conta erros por tipo em uma sessão
 */
export function countErrorsByType(sessionId: string): Record<string, number> {
  const errors = getMarkedErrors(sessionId);
  const counts: Record<string, number> = {
    falso_positivo: 0,
    falso_negativo: 0,
    bug_real: 0,
    outros: 0,
  };
  errors.forEach(e => {
    counts[e.error_type] = (counts[e.error_type] || 0) + 1;
  });
  return counts;
}

/**
 * Envia erro para o backend (locks aprendidos)
 */
async function syncErrorToBackend(error: MarkedError): Promise<void> {
  try {
    await request('/inspector/chromadb/collections').catch(() => null);

    // Salva como lock no Neo4j/PostgreSQL via endpoint dedicado
    await apiFetch(`${API_BASE}/locks/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pattern: error.what_was_wrong.substring(0, 200),
        description: error.description,
        alternative: error.what_was_expected,
        where: error.where_in_code,
        model: error.which_model,
        agent: error.which_agent,
        trace_id: error.trace_id,
        session_id: error.session_id,
        error_type: error.error_type,
        marked_at: error.marked_at,
      }),
    }).catch(() => null);
  } catch {}
}

// =========================================================
// CLASSIFICAÇÃO DE TOKENS (SEMPRE ESPECÍFICO, NUNCA "OUTROS")
// =========================================================

/**
 * Classifica tokens por CATEGORIA REAL (não "outros").
 * Cada token é rastreado por onde foi gasto.
 */
export function classifyTokensByCategory(
  traces: ApiTraceEntry[]
): TokenUsageByCategory {
  const result: TokenUsageByCategory = {
    system_prompt: 0,
    user_input: 0,
    rag_context: 0,
    memory_history: 0,
    tool_result: 0,
    assistant_response: 0,
    cascade_overhead: 0,
    error_recovery: 0,
  };

  traces.forEach(t => {
    const tokens = t.tokens_input || 0;
    const tokensOut = t.tokens_output || 0;
    const total = tokens + tokensOut;

    if (total === 0) return;

    // Mapear pelo tipo de evento/tool
    if (t.event_type === 'user_message' || t.tool === 'Chat:User') {
      result.user_input += total;
    } else if (t.event_type === 'rag_preload' || t.tool_input?.rag_chunks) {
      result.rag_context += total;
    } else if (t.event_type === 'memory_load' || t.tool_input?.memory_context) {
      result.memory_history += total;
    } else if (t.event_type === 'tool_result' || t.event_type === 'tool_call') {
      result.tool_result += total;
    } else if (t.event_type === 'thinking' || t.tool === 'Claude:thinking') {
      result.assistant_response += total; // thinking é parte da resposta
    } else if (t.event_type === 'assistant_response' || t.tool === 'Chat:Agent') {
      result.assistant_response += total;
    } else if (t.event_type === 'cascade_step' || t.metadata?.cascade) {
      result.cascade_overhead += total;
    } else if (t.event_type === 'error_retry' || (t.is_error && t.metadata?.retry_count > 0)) {
      result.error_recovery += total;
    } else if (t.event_type === 'session_start' || t.metadata?.system_prompt) {
      result.system_prompt += total;
    } else {
      // Se não classificou, distribui entre assistant_response
      // (nunca "outros" - sempre conta em uma categoria real)
      result.assistant_response += total;
    }
  });

  return result;
}

/**
 * Calcula distribuição percentual
 */
export function getTokenDistribution(byCategory: TokenUsageByCategory) {
  const total = Object.values(byCategory).reduce((a, b) => a + b, 0);
  if (total === 0) return [];

  return Object.entries(byCategory)
    .map(([cat, value]) => ({
      category: cat,
      value,
      percent: (value / total) * 100,
    }))
    .filter((x) => x.value > 0)
    .sort((a, b) => b.value - a.value);
}

// =========================================================
// SUB-AGENTES E MODELOS
// =========================================================

export interface SubAgentInfo {
  id: string;
  parent_trace_id: string;
  type: string;
  description: string;
  started_at: string;
  ended_at?: string;
  total_traces: number;
  tokens_used: number;
  model_used?: string;
  status: 'running' | 'completed' | 'failed';
}

/**
 * Extrai lista de sub-agentes de uma lista de traces
 */
export function extractSubAgents(traces: ApiTraceEntry[]): SubAgentInfo[] {
  const subagents = new Map<string, SubAgentInfo>();

  traces.forEach((t) => {
    // Detecta sub-agente por: tipo de evento OU campo subagent_type OU metadata.is_subagent_message
    const isSubagent = t.event_type === 'subagent_spawn' ||
                      t.subagent_type ||
                      t.metadata?.is_subagent_message === true ||
                      t.metadata?.is_subagent === true;

    if (isSubagent) {
      const id = t.parent_tool_use_id || t.id;
      if (!subagents.has(id)) {
        subagents.set(id, {
          id,
          parent_trace_id: t.parent_tool_use_id || t.metadata?.parent_tool_use_id || '',
          type: t.subagent_type || t.tool_input?.subagent_type || t.tool_input?.subagent_name || t.metadata?.subagent_type || 'subagent',
          description: t.tool_input?.description || t.input?.substring(0, 200) || t.metadata?.description || '',
          started_at: t.timestamp,
          total_traces: 0,
          tokens_used: 0,
          model_used: t.tool_input?.model || t.metadata?.model || t.metadata?.cascade_model,
          status: 'running',
        });
      }
    }

    // Contar traces e tokens por sub-agente
    if (t.parent_tool_use_id && subagents.has(t.parent_tool_use_id)) {
      const sa = subagents.get(t.parent_tool_use_id)!;
      sa.total_traces += 1;
      sa.tokens_used += (t.tokens_input || 0) + (t.tokens_output || 0);
    }
  });

  return Array.from(subagents.values());
}

// =========================================================
// HELPERS DE EXTRAÇÃO
// =========================================================

function extractMainText(obj: any): string {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  return String(
    obj.text ?? obj.content ?? obj.message ?? obj.msg ?? obj.thinking ?? obj.result ?? ''
  );
}

function extractSubagentSummary(obj: any): string {
  if (!obj || typeof obj !== 'object') return '';
  const parts: string[] = [];
  if (obj.subagent_type) parts.push(`🤖 ${obj.subagent_type}`);
  if (obj.subagent_name) parts.push(String(obj.subagent_name));
  if (obj.description) parts.push(`📋 ${obj.description}`);
  if (obj.task) parts.push(`\n${String(obj.task).slice(0, 1000)}`);
  return parts.join('\n');
}

function extractToolSummary(obj: any): string {
  if (!obj || typeof obj !== 'object') return '';
  const parts: string[] = [];
  if (obj.command) parts.push(`⚡ ${String(obj.command).slice(0, 500)}`);
  if (obj.file_path || obj.path) parts.push(`📄 ${obj.file_path ?? obj.path}`);
  if (obj.pattern) parts.push(`🔍 ${obj.pattern}`);
  if (obj.query) parts.push(`🔍 ${obj.query}`);
  if (obj.url) parts.push(`🌐 ${obj.url}`);
  return parts.join(' | ');
}

function extractInputString(t: any): string {
  if (!t.tool_input) return t.content ?? '';
  if (typeof t.tool_input === 'string') return t.tool_input;
  if (t.event_type === 'user_message' || t.tool_name === 'Chat:User') {
    return String(t.tool_input?.prompt ?? t.tool_input?.text ?? '');
  }
  if (t.event_type?.includes('subagent') || t.tool_name === 'Agent') {
    return extractSubagentSummary(t.tool_input);
  }
  const toolSummary = extractToolSummary(t.tool_input);
  if (toolSummary) return toolSummary;
  return extractMainText(t.tool_input);
}

function extractOutputString(t: any): string {
  if (!t.tool_output) return '';
  if (typeof t.tool_output === 'string') return t.tool_output;
  return extractMainText(t.tool_output);
}

export async function listTraces(
  sessionId: string,
  options?: { limit?: number; offset?: number }
): Promise<ApiTraceEntry[]> {
  const limit = options?.limit ?? 5000;
  const offset = options?.offset ?? 0;
  const data: any[] = await request(
    `/traces/?session_id=${sessionId}&limit=${limit}&offset=${offset}`
  );
  const reversed = [...data].reverse();

  return reversed.map(t => {
    let toolName = t.tool_name || t.event_type || 'event';
    if (t.event_type === 'user_message') toolName = 'Chat:User';
    else if (t.event_type === 'subagent_spawn') toolName = 'Agent:SubagentSpawn';
    else if (t.event_type === 'subagent_complete') toolName = 'Agent:SubagentComplete';

    return {
      id: t.id,
      session_id: t.session_id,
      timestamp: t.created_at,
      tool: toolName,
      tool_name: t.tool_name,
      input: extractInputString(t),
      output: extractOutputString(t),
      raw_tool_input: t.tool_input,
      raw_tool_output: t.tool_output,
      reasoning: t.tool_input?.thinking ?? null,
      duration: t.duration_ms,
      tokens_used: t.tokens_used ?? t.metadata?.tokens_used ?? 0,
      tokens_input: t.tokens_input ?? t.metadata?.tokens_in ?? 0,
      tokens_output: t.tokens_output ?? t.metadata?.tokens_out ?? 0,
      context_tokens: t.metadata?.context_tokens ?? 0,
      token_type: t.metadata?.token_type ?? 'execution',
      agent_name: t.agent_name,
      subagent_type: t.tool_input?.subagent_type ?? t.tool_input?.subagent_name,
      event_type: t.event_type,
      status: t.is_error ? 'error' : 'success',
      is_error: t.is_error,
      error_message: t.error_message,
      metadata: t.metadata,
      parent_tool_use_id: t.metadata?.parent_tool_use_id,
    };
  });
}

export function subscribeToTraces(
  sessionId: string,
  onTrace: (trace: ApiTraceEntry) => void,
  onError?: (err: Error) => void
): () => void {
  let aborted = false;
  let seenIds = new Set<string>();

  async function poll() {
    if (aborted) return;
    try {
      const traces = await listTraces(sessionId);
      for (const t of traces) {
        if (!seenIds.has(t.id)) {
          seenIds.add(t.id);
          onTrace(t);
        }
      }
    } catch (e: any) {
      onError?.(e);
    }
    if (!aborted) setTimeout(poll, 2000);
  }

  poll();
  return () => { aborted = true; };
}
