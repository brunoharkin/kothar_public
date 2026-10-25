import { apiFetch } from '../../seguranca/sessao';

export type Registro = { id: string; revision?: number; [key: string]: unknown };
export interface Fato extends Registro {
  content: string; source: string; observed_at: number; confidence: number;
  expires_at: number | null; category: string;
}
export interface Tarefa extends Registro {
  title: string; status: string; category: string; priority: number; attempts: number;
  max_attempts: number; dependencies: string[]; payload: Record<string, unknown>;
}
export interface Acao extends Registro {
  scope: string; review: string; status: string; payload_hash: string;
  expires_at: number; payload: Record<string, unknown>;
}
export interface Prospecto extends Registro {
  company: string; domain: string; signal: string; source: string; next_step: string;
}
export interface Metricas { tokens: number; calls: number; cost_microunits: number }
export interface Orcamento extends Registro { limits: Metricas; spent: Metricas; reserved: Metricas }
export interface Skill { name: string; description: string; estimated_tokens: number; version: string }
export interface VisaoEvolucao {
  facts: Fato[]; tasks: Tarefa[]; actions: Acao[]; feedback: Registro[];
  prospects: Prospecto[]; evaluations: Registro[]; budget: Orcamento | null;
  skills_metadata: Skill[];
  capabilities: { evaluations: boolean; prospecting: boolean; external_dispatch: boolean };
}
export interface Evidencia { source_url: string; observation: string; observed_at: string }
export interface Sinal { code: string; label: string; limitation: string; evidence: Evidencia }
export interface Perfil {
  business: { name: string; category: string; state: string; website_url?: string };
  signals: Sinal[]; contacts: { email: string; status: string; source_url: string }[];
  coverage: string; expires_at: string;
}

const erros: Record<string, string> = {
  not_found: 'Registro não encontrado. Atualize os dados e tente novamente.',
  stale_revision: 'Esta informação mudou em outra sessão. Atualize antes de corrigir.',
  concurrent_change: 'Outro processo atualizou este registro. Atualize os dados.',
  budget_exceeded: 'O orçamento disponível não cobre esta operação.',
  budget_below_committed_usage: 'O limite deve cobrir o consumo e as reservas existentes.',
  evaluation_executor_unconfigured: 'O modelo de avaliação ainda não foi configurado no servidor.',
  prospecting_disabled: 'A descoberta externa precisa ser habilitada no servidor.',
  prospect_has_no_website: 'Este registro não tem site público para investigar.',
  discovery_expired: 'A descoberta expirou. Faça uma nova busca antes de investigar.',
  profile_expired: 'O perfil expirou. Investigue o site novamente.',
  unsupported_category: 'Segmento não suportado pela fonte de descoberta.',
  dedupe_conflict: 'A chave de execução já foi usada com outros dados.',
  invalid_approval_expiry: 'A validade da aprovação expirou. Gere um novo rascunho.',
  approval_expired: 'Esta aprovação expirou. Gere um novo rascunho.',
  rate_limited: 'Limite temporário atingido. Aguarde antes de tentar novamente.',
};

export class EvolucaoApiError extends Error {
  constructor(public readonly status: number, public readonly code: string, message: string) { super(message); }
}

export async function evolucaoApi<T>(project: string, path = '', method = 'GET', payload?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await apiFetch(`/api/evolucao/${encodeURIComponent(project)}${path}`, {
    method, signal, ...(payload === undefined ? {} : {
      headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    }),
  });
  const data: unknown = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const body = data && typeof data === 'object' ? data as Record<string, unknown> : {};
    const detail = body.detail;
    const code = typeof body.code === 'string' ? body.code : typeof detail === 'string' ? detail : typeof body.error === 'string' ? body.error : '';
    const message = erros[code] || (response.status === 422
      ? 'Confira os campos: algum valor está fora do formato ou limite permitido.'
      : response.status === 403 ? 'Sua sessão não autoriza esta ação.'
      : response.status === 429 ? 'Limite temporário atingido. Aguarde antes de tentar novamente.'
      : 'Não foi possível concluir a operação. Tente novamente.');
    throw new EvolucaoApiError(response.status, code, message);
  }
  return data as T;
}

export const texto = (value: unknown): string => typeof value === 'string' ? value : '';
export const linhas = (value: string): string[] => value.split('\n').map(line => line.trim()).filter(Boolean);
export function urlPublica(value: string): string | undefined {
  try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : undefined; }
  catch { return undefined; }
}
