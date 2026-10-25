import { apiFetch } from '../../seguranca/sessao';
/**
 * Kothar Memory Inspector API v6.0 SUPREMO (ALINHADO)
 * Mapeamento completo do cofre, RAG em tempo real, análise avançada
 * 100% alinhado com os endpoints reais do backend Kothar
 */

// =====================================================
// INTERFACES ALINHADAS COM SCHEMA REAL
// =====================================================

// Schema real de /api/rag-metrics/rag/json
export interface RAGMetrics {
  total_hits: number;
  total_misses: number;
  total_requests: number;
  hit_rate_percent: number;
  cache_hits: number;
  hits_by_type: Record<string, number>;
  misses_by_type: Record<string, number>;
  uptime_seconds: number;
}

// Schema real de /api/rag-tracker/recent
export interface RAGQuery {
  session_id?: string;
  query: string;
  chunks_count: number;
  sources: string[];
  timestamp: number | string; // API pode retornar ISO string ou timestamp
  is_hit: boolean;
}

// Schema real de /api/rag-tracker/sessions/{id}
export interface RAGSessionDetail {
  queries: RAGQuery[];
  total_queries: number;
  total_hits: number;
  total_chunks: number;
}

export interface RAGSession {
  session_id: string;
  total_queries: number;
  total_hits: number;
  hit_rate: number;
  total_chunks: number;
  last_active: number | string;
  recent_queries?: RAGQuery[];
}

// Schema real de /api/rag-tracker/stats
export interface RAGGlobalStats {
  total_queries: number;
  total_hits: number;
  total_misses: number;
  total_chunks_retrieved: number;
  active_sessions: number;
  hit_rate: number;
}

// === VAULT INSPECTOR ===
export interface VaultCategory {
  category: string;
  path: string;
  files: number;
  md_files: number;
  size_bytes: number;
  size_kb: number;
}

export interface VaultFile {
  name: string;
  path: string;
  category: string;
  size_bytes: number;
  size_kb: number;
}

export interface VaultStats {
  categories: VaultCategory[];
  total_files: number;
  total_md: number;
  total_size_bytes: number;
  total_size_kb: number;
  top_files: VaultFile[];
}

// === CHROMADB ===
export interface ChromaCollection {
  name: string;
  count: number;
  categories?: string[];
  sample_metadata?: any;
  error?: string;
}

export interface ChromaSample {
  id: string;
  metadata: any;
  content_preview: string;
  content_length: number;
}

// === RAG ANALYSIS ===
export interface TopSource {
  name: string;
  count: number;
}

export interface TopKeyword {
  word: string;
  count: number;
}

export interface ChunksStats {
  avg: number;
  max: number;
  min: number;
  histogram: Record<string, number>;
}

export interface RAGAnalysis {
  total_queries_analyzed: number;
  top_sources: TopSource[];
  top_keywords: TopKeyword[];
  chunks_stats: ChunksStats;
  time_distribution: Record<string, number>;
}

// === BLUEPRINT (schema real) ===
export interface BlueprintStep {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'done';
  agent: string;
  result?: any;
}

export interface Blueprint {
  id: string;
  session_id: string;
  title: string;
  description: string;
  steps: BlueprintStep[];
  status: string;
  assigned_agent?: string;
}

// === DASHBOARD (para integrar métricas operacionais) ===
export interface DashboardData {
  uptime_seconds: number;
  active_sessions: number;
  total_sessions_period: number;
  sessions_by_status: Record<string, number>;
  sessions_by_agent: Record<string, number>;
  token_usage: { input: number; output: number; total: number; total_cost_usd: number };
  trace_events_breakdown: Record<string, number>;
  trace_events_by_agent: Record<string, number>;
  errors_count: number;
  success_rate_percent: number;
  skills_total: number;
  locks_active: number;
  cascade: {
    total_executions: number;
    models_used: Record<string, number>;
    distribution: Record<string, { count: number; percent: number }>;
    escalations: number;
    escalations_by_path?: Record<string, number>;
    tokens_by_model: Record<string, number>;
    cost_by_model: Record<string, number>;
    total_cost_usd: number;
    escalation_rate_percent?: number;
  };
  avg_latency_ms: number;
  throughput_per_min: number;
  recent_sessions: Array<{
    id: string;
    agent_name: string;
    task_summary: string;
    status: string;
    started_at: string;
    duration_seconds: number | null;
    tokens_input: number;
    tokens_output: number;
    total_cost_usd: number;
  }>;
  health: {
    overall: string;
    components: Record<string, { status: string; error?: string; latency_ms?: number }>;
  };
}

// =====================================================
// API CLIENT
// =====================================================

const BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await apiFetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text.substring(0, 100)}`);
  }
  return res.json();
}

export const memoryApi = {
  // === RAG Metrics ===
  async getRAGMetrics(): Promise<RAGMetrics> {
    return request<RAGMetrics>('/rag-metrics/rag/json');
  },

  // === RAG Tracker ===
  async getGlobalStats(): Promise<RAGGlobalStats> {
    return request<RAGGlobalStats>('/rag-tracker/stats');
  },
  async listRAGSessions(): Promise<{ sessions: any[]; total: number }> {
    try {
      const response: any = await request<any>('/rag-tracker/sessions');
      // API pode retornar array direto OU { sessions: [], total: 0 }
      if (Array.isArray(response)) {
        return { sessions: response, total: response.length };
      }
      return {
        sessions: response?.sessions || [],
        total: response?.total || 0,
      };
    } catch {
      return { sessions: [], total: 0 };
    }
  },
  async getRAGSessionDetail(sessionId: string): Promise<RAGSessionDetail> {
    return request<RAGSessionDetail>(`/rag-tracker/sessions/${sessionId}`);
  },
  async getRecentRAGQueries(limit: number = 20): Promise<{ queries: RAGQuery[] }> {
    return request<{ queries: RAGQuery[] }>(`/rag-tracker/recent?limit=${limit}`);
  },

  // === Sessions reais do orquestrador ===
  async getActiveSessions(): Promise<{ sessions: RAGSession[]; total: number }> {
    return request<{ sessions: RAGSession[]; total: number }>('/inspector/sessions/active');
  },

  // === Blueprint (do orquestrador real) ===
  async getBlueprint(sessionId: string): Promise<Blueprint | null> {
    try {
      const data = await request<{ session_id: string; context: any; progress: string; progress_pct: number; blueprint_id: string; current_step: any }>(
        `/orchestrate/${sessionId}/status`
      );
      // Converte o formato do orquestrador para o formato Blueprint
      return {
        id: data.blueprint_id || sessionId,
        session_id: sessionId,
        title: data.context?.tarefa_atual || `Sessão ${sessionId.substring(0, 8)}`,
        description: data.context?.tarefa_atual || '',
        status: data.progress || 'active',
        steps: data.current_step ? [{
          id: 0,
          title: data.current_step.title || 'Em progresso',
          description: data.current_step.description || '',
          status: 'in_progress',
          agent: data.current_step.agent || 'unknown',
        }] : [],
      };
    } catch {
      return null;
    }
  },

  // === Vault Inspector ===
  async getVaultStats(): Promise<VaultStats> {
    return request<VaultStats>('/inspector/vault/stats');
  },
  async getVaultTree(maxDepth: number = 3): Promise<any> {
    return request<any>(`/inspector/vault/tree?max_depth=${maxDepth}`);
  },
  async readVaultFile(path: string, maxLines: number = 200): Promise<any> {
    return request<any>(`/inspector/vault/file?path=${encodeURIComponent(path)}&max_lines=${maxLines}`);
  },

  // === ChromaDB ===
  async getChromaCollections(): Promise<{ collections: ChromaCollection[]; total_collections: number; total_documents: number }> {
    return request<any>('/inspector/chromadb/collections');
  },
  async getChromaSample(name: string, limit: number = 5): Promise<any> {
    return request<any>(`/inspector/chromadb/collection/${name}/sample?limit=${limit}`);
  },

  // === RAG Analysis ===
  async getRAGAnalysis(): Promise<RAGAnalysis> {
    return request<RAGAnalysis>('/inspector/rag/analysis');
  },

  // === Dashboard unificado (para métricas operacionais) ===
  async getDashboard(hours: number = 24): Promise<DashboardData> {
    return request<DashboardData>(`/dashboard?hours=${hours}`);
  },

  // === Sessions reais do PostgreSQL ===
  async getSessionsFromDB(limit: number = 10, status?: string): Promise<any[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status) params.append('status', status);
    return request<any[]>(`/sessions/?${params}`);
  },

  // === Sessions ativas do orquestrador (alias) ===
  async getOrchestrateActiveSessions(): Promise<any[]> {
    return request<any[]>('/inspector/sessions/active');
  },
};

// Re-export Blueprint types
export type { BlueprintStep as BlueprintStepType };
