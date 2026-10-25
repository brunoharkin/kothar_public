/** Cookie HttpOnly é a única credencial; CSRF fica apenas na página atual. */
export interface Sessao { username: string; expiresAt: string; csrfToken: string }
let csrfToken: string | null = null;

export function aceitarSessao(value: unknown): Sessao {
  const session = value as Partial<Sessao> | null;
  if (!session || typeof session.username !== 'string' ||
      typeof session.expiresAt !== 'string' || typeof session.csrfToken !== 'string' ||
      !session.csrfToken || !(Date.parse(session.expiresAt) > Date.now())) {
    throw new Error('Resposta de sessão inválida');
  }
  csrfToken = session.csrfToken;
  return session as Sessao;
}

export function limparSessao(): void {
  csrfToken = null;
  window.dispatchEvent(new Event('kothar:session-ended'));
}

export async function apiFetch(input: string | URL, options: RequestInit = {}): Promise<Response> {
  const url = new URL(String(input), window.location.origin);
  if (url.origin !== window.location.origin) throw new Error('API deve usar a mesma origem');
  const method = (options.method || 'GET').toUpperCase();
  const headers = new Headers(options.headers);
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && url.pathname !== '/api/auth/login') {
    if (!csrfToken) throw new Error('Sessão não validada; entre novamente');
    headers.set('X-CSRF-Token', csrfToken);
  }
  const response = await fetch(url, { ...options, method, headers, credentials: 'same-origin', cache: 'no-store' });
  if (response.status === 401 && url.pathname !== '/api/auth/login') limparSessao();
  return response;
}

export async function verificarSessao(): Promise<boolean> {
  const response = await apiFetch('/api/auth/session');
  if (response.status === 401) return false;
  if (!response.ok) throw new Error('Não foi possível verificar a sessão');
  aceitarSessao(await response.json());
  return true;
}

export async function encerrarSessao(): Promise<void> {
  const response = await apiFetch('/api/auth/logout', { method: 'POST' });
  if (!response.ok && response.status !== 401) throw new Error('Não foi possível encerrar a sessão');
  limparSessao();
}
