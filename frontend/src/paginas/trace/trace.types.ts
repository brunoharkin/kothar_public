/**
 * KOTHAR v3.0 — Trace Types
 * Tipos para a página de análise de traces
 */

export interface TraceEntry {
  id: string;
  timestamp: string;
  tool: string;
  input: unknown;
  output: unknown;
  duration?: number;
  status: 'success' | 'error' | 'pending';
}

export interface TraceFilter {
  tool?: string;
  status?: TraceEntry['status'];
  dateFrom?: string;
  dateTo?: string;
}

export interface TraceView {
  mode: 'chat' | 'table';
  selectedEntry?: TraceEntry;
}
