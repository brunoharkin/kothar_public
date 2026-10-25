import { apiFetch } from '../../seguranca/sessao';
/**
 * Kothar Data Lake API v6.0 SUPREMO (ALINHADO + TURBINADO)
 * Conecta com Codebase Memory MCP + Data Lake (PostgreSQL + Neo4j)
 * + Métricas operacionais do Dashboard
 */

export interface Project {
  name: string;
  root_path: string;
}

export interface SearchNode {
  id: string;
  name: string;
  type: string;
  file?: string;
  line?: number;
  complexity?: number;
  in_degree?: number;
  out_degree?: number;
}

export interface SearchResult {
  nodes: SearchNode[];
  total: number;
  query: string;
  label?: string;
}

export interface SchemaInfo {
  labels: Record<string, number>;
}

export interface Architecture {
  project: string;
  total_nodes: number;
  total_edges: number;
  node_labels: Record<string, number>;
  edge_types?: Record<string, number>;
  hotspots?: Array<{ name: string; type: string; degree: number }>;
  note?: string;
}

// === Data Lake (PostgreSQL) ===
export interface DataLakeSession {
  id: string;
  agent_name: string;
  llm_model: string;
  task_summary: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  tokens_input: number;
  tokens_output: number;
  total_cost_usd: number;
  created_at: string;
}

export interface DataLakeTrace {
  id: string;
  session_id: string;
  sequence: number;
  event_type: string;
  agent_name: string;
  content: string | null;
  tool_name: string | null;
  tool_input: any;
  tool_output: any;
  duration_ms: number | null;
  tokens_used: number;
  tokens_input: number;
  tokens_output: number;
  is_error: boolean;
  error_message: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface DataLakeStats {
  total_sessions: number;
  active_sessions: number;
  total_traces: number;
  total_skills: number;
  total_locks: number;
  total_blueprints: number;
  total_tokens_input: number;
  total_tokens_output: number;
  total_cost_usd: number;
  error_rate_percent: number;
}

const CBM_BASE = '/api/cbm';
const KOTHAR_BASE = '/api';

async function request<T>(url: string): Promise<T> {
  const res = await apiFetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text.substring(0, 100)}`);
  }
  return res.json();
}

export const dataLakeApi = {
  // === CBM (Codebase Memory) ===
  async listProjects(): Promise<{ projects: Project[]; total: number }> {
    return request<{ projects: Project[]; total: number }>(`${CBM_BASE}/projects`);
  },

  async search(project: string, query: string, label?: string): Promise<SearchResult> {
    const url = label
      ? `${CBM_BASE}/search/${project}?q=${encodeURIComponent(query)}&label=${label}`
      : `${CBM_BASE}/search/${project}?q=${encodeURIComponent(query)}`;
    return request<SearchResult>(url);
  },

  async getArchitecture(project: string): Promise<Architecture> {
    return request<Architecture>(`${CBM_BASE}/architecture/${project}`);
  },

  async getCode(project: string, qualifiedName: string): Promise<{
    code: string;
    file: string;
    line_start?: number;
    line_end?: number;
  }> {
    return request(`${CBM_BASE}/code/${project}/${encodeURIComponent(qualifiedName)}`);
  },

  async getSchema(project: string): Promise<SchemaInfo> {
    return request<SchemaInfo>(`${CBM_BASE}/schema/${project}`);
  },

  async traceFunction(project: string, qualifiedName: string): Promise<{
    callers: any[];
    callees: any[];
    impact_level?: string;
  }> {
    return request(`${CBM_BASE}/trace/${project}/${encodeURIComponent(qualifiedName)}`);
  },

  // === Data Lake (PostgreSQL) ===
  async listSessions(limit: number = 50, offset: number = 0, status?: string): Promise<DataLakeSession[]> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (status) params.append('status', status);
    return request<DataLakeSession[]>(`${KOTHAR_BASE}/sessions/?${params}`);
  },

  async getSession(id: string): Promise<DataLakeSession | null> {
    try {
      return await request<DataLakeSession>(`${KOTHAR_BASE}/sessions/${id}`);
    } catch {
      return null;
    }
  },

  async listTraces(sessionId?: string, limit: number = 50): Promise<DataLakeTrace[]> {
    const params = new URLSearchParams({ limit: String(limit) });
    if (sessionId) params.append('session_id', sessionId);
    return request<DataLakeTrace[]>(`${KOTHAR_BASE}/traces/?${params}`);
  },

  async listSkills(): Promise<any[]> {
    return request<any[]>(`${KOTHAR_BASE}/skills/`);
  },

  // === Dashboard operacional ===
  async getDashboard(hours: number = 24): Promise<any> {
    return request(`${KOTHAR_BASE}/dashboard?hours=${hours}`);
  },

  // === Health ===
  async getHealth(): Promise<any> {
    return request(`${KOTHAR_BASE.replace('/api', '')}/health/detailed`);
  },

  // === Aggregate stats do Data Lake ===
  async getDataLakeStats(): Promise<DataLakeStats> {
    // Combina várias chamadas
    const [sessions, dashboard, skills] = await Promise.all([
      this.listSessions(100).catch(() => []),
      this.getDashboard(24).catch(() => null),
      this.listSkills().catch(() => []),
    ]);

    const active = sessions.filter((s) => s.status === 'active').length;
    const totalInput = sessions.reduce((sum, s) => sum + (s.tokens_input || 0), 0);
    const totalOutput = sessions.reduce((sum, s) => sum + (s.tokens_output || 0), 0);
    const totalCost = sessions.reduce((sum, s) => sum + (s.total_cost_usd || 0), 0);

    return {
      total_sessions: sessions.length,
      active_sessions: active,
      total_traces: dashboard?.trace_events_breakdown
        ? Object.values(dashboard.trace_events_breakdown).reduce((a: number, b: any) => a + (b as number), 0)
        : 0,
      total_skills: skills.length,
      total_locks: dashboard?.locks_active || 0,
      total_blueprints: dashboard?.recent_blueprints?.length || 0,
      total_tokens_input: totalInput,
      total_tokens_output: totalOutput,
      total_cost_usd: totalCost,
      error_rate_percent: dashboard?.success_rate_percent
        ? 100 - dashboard.success_rate_percent
        : 0,
    };
  },
};
