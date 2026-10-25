/**
 * KOTHAR v6.0 — Metrics API Client (ATUALIZADO)
 * Agora usa endpoint unificado /api/dashboard
 */

interface MetricsData {
  uptime_seconds: number;
  sessions: {
    started: number;
    completed: number;
    failed: number;
  };
  trace_events: Record<string, number>;
  agents_executed: Record<string, number>;
}

interface RAGMetrics {
  total_hits: number;
  total_misses: number;
  hit_rate: number;
  by_type: Record<string, { hits: number; misses: number }>;
}

interface ComponentHealth {
  component: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms: number;
  message: string;
  details: Record<string, any>;
  checked_at: string;
}

interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, ComponentHealth>;
  checked_at: string;
}

export interface DashboardData {
  uptime_seconds: number;
  sessions: any;
  rag: {
    total_hits: number;
    total_misses: number;
    total_requests: number;
    hit_rate_percent: number;
    cache_hits: number;
    hits_by_type: Record<string, number>;
    misses_by_type: Record<string, number>;
  };
  active_sessions: number;
  recent_sessions: Array<{
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
    metadata: Record<string, any>;
  }>;
  total_sessions_period: number;
  sessions_by_status: Record<string, number>;
  sessions_by_agent: Record<string, number>;
  token_usage: {
    input: number;
    output: number;
    total: number;
    total_cost_usd: number;
  };
  trace_events: Record<string, number>;
  trace_events_breakdown: Record<string, number>;
  trace_events_by_agent: Record<string, number>;
  errors_count: number;
  success_rate_percent: number;
  skills_total: number;
  locks_active: number;
  recent_blueprints: any[];
  cascade: {
    total_executions: number;
    models_used: Record<string, number>;
    distribution: Record<string, { count: number; percent: number }>;
    escalations: number;
    escalations_by_path: Record<string, number>;
    tokens_by_model: Record<string, number>;
    cost_by_model: Record<string, number>;
    total_cost_usd: number;
    escalation_rate_percent: number;
    uptime_seconds: number;
  };
  avg_latency_ms: number;
  throughput_per_min: number;
  health: HealthCheck;
  period_hours: number;
  generated_at: string;
}

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ===== MÉTODO PRINCIPAL =====
export async function getDashboard(hours: number = 24): Promise<DashboardData> {
  return fetchJSON<DashboardData>(`/api/dashboard?hours=${hours}`);
}

// ===== Métodos legados (mantidos para compatibilidade) =====
export async function getMetrics(): Promise<MetricsData> {
  return fetchJSON<MetricsData>('/metrics/json');
}

export async function getRAGMetrics(): Promise<RAGMetrics> {
  return fetchJSON<RAGMetrics>('/metrics/rag');
}

export async function getHealthCheck(): Promise<HealthCheck> {
  return fetchJSON<HealthCheck>('/health/detailed');
}

// (DashboardData já exportado acima)
export {
  type MetricsData,
  type RAGMetrics,
  type HealthCheck,
  type ComponentHealth,
};
