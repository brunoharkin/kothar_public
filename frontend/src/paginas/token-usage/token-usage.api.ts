import { apiFetch } from '../../seguranca/sessao';
/**
 * KOTHAR — Token Usage API Client
 * Consome endpoints REST do backend/token_counter
 * Docs do backend: backend/token_counter/api.py
 */

export interface TotalsResponse {
  requests: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  reasoning_tokens: number;
  reasoning_share: number;
}

export interface WindowResponse {
  type: string;               // "session" | "weekly" | "monthly" | etc.
  used_fraction: number;      // 0.0 - 1.0
  used: number;               // tokens usados no ciclo
  limit: number;              // tokens permitidos no ciclo
  remaining: number;
  resets_at: string | null;
  label: string | null;
}

export interface ContextResponse {
  timestamp: string | null;
  instance: string | null;
  model: string | null;
}

export interface SnapshotResponse {
  id: string;                 // ex: "claude-cli"
  name: string;               // ex: "Claude Code CLI"
  fidelity: string;           // "exact" | "approximate" | "estimated" | etc.
  status: string;             // "healthy" | "degraded" | "error" | etc.
  windows: WindowResponse[];
  headline: string | null;    // frase amigável do estado atual
  context: ContextResponse | null;
  ledger_today: TotalsResponse | null;
  error_message: string | null;
}

export interface SummaryResponse {
  instance: string;
  today: TotalsResponse;
  last_7_days: TotalsResponse;
  all_time: TotalsResponse;
  dates_tracked: number;
}

export interface ProviderStatusEntry {
  status?: string;
  last_fetch?: string | null;
  error?: string | null;
  // qualquer outra coisa retornada pelo store
  [key: string]: any;
}

export interface StatusResponse {
  is_running: boolean;
  providers: Record<string, ProviderStatusEntry>;
}

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await apiFetch(url, init);
  if (!res.ok) throw new Error(`HTTP ${res.status} em ${url}`);
  return res.json();
}

export async function getAllSnapshots(): Promise<Record<string, SnapshotResponse>> {
  return fetchJSON<Record<string, SnapshotResponse>>('/api/usage/snapshots');
}

export async function getSnapshot(providerId: string): Promise<SnapshotResponse> {
  return fetchJSON<SnapshotResponse>(
    `/api/usage/snapshot/${encodeURIComponent(providerId)}`,
  );
}

export async function getLedgerSummary(instance = 'default'): Promise<SummaryResponse> {
  return fetchJSON<SummaryResponse>(
    `/api/usage/ledger?instance=${encodeURIComponent(instance)}`,
  );
}

export async function getStatus(): Promise<StatusResponse> {
  return fetchJSON<StatusResponse>('/api/usage/status');
}

export async function refreshAll(): Promise<{ refreshed: string[] }> {
  return fetchJSON<{ refreshed: string[] }>('/api/usage/refresh', {
    method: 'POST',
  });
}

export async function refreshProvider(
  providerId: string,
): Promise<{ refreshed: string; snapshot: any }> {
  return fetchJSON<{ refreshed: string; snapshot: any }>(
    '/api/usage/refresh',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_id: providerId }),
    },
  );
}

/* ===== Helpers de formatação ===== */

export function formatNumber(n: number): string {
  return n.toLocaleString('pt-BR');
}

export function formatPercent(fraction: number, digits = 1): string {
  const pct = Math.max(0, Math.min(1, fraction)) * 100;
  return `${pct.toFixed(digits)}%`;
}

export function formatResetsAt(iso: string | null): string {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '—';
  }
}
