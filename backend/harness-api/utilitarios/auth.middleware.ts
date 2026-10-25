/**
 * Auth Middleware — valida JWT em todas as rotas /api/*
 */
import { Request, Response, NextFunction } from 'express';
import { AuthSession, AuthError, COOKIE_NAME, equalToken, sessions } from './session-store';

declare global { namespace Express { interface Request { user?: { sub: string }; authSession?: AuthSession; sessionToken?: string } } }

export function allowedOrigins(): string[] {
  const origins = (process.env.CORS_ORIGIN || '').split(',').map(x => x.trim()).filter(Boolean);
  if (!origins.length || origins.some(x => { try { return new URL(x).origin !== x || !x.startsWith('https://'); } catch { return true; } })) throw new Error('CORS_ORIGIN deve conter origens HTTPS explícitas');
  return origins;
}
export function sessionCookie(req: Request): string {
  const values = (req.headers.cookie || '').split(';').map(x => x.trim()).filter(x => x.startsWith(COOKIE_NAME + '='));
  return values.length === 1 ? values[0].slice(COOKIE_NAME.length + 1) : '';
}
export function authFailure(res: Response, error: unknown): void {
  const status = error instanceof AuthError ? error.status : 503;
  if (status === 429) res.setHeader('Retry-After', '900');
  res.status(status).json({ error: error instanceof AuthError ? error.message : 'Autenticação indisponível' });
}
export async function publicRateLimit(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    // Never trust arbitrary X-Forwarded-For. Express trust proxy remains disabled.
    await sessions().limit('api-ip', req.socket.remoteAddress || 'unknown', 300, 60);
    next();
  } catch (error) { authFailure(res, error); }
}
export async function authMiddleware(req: Request, res: Response, next: NextFunction): Promise<void> {
  try {
    const mutating = !['GET', 'HEAD', 'OPTIONS'].includes(req.method);
    if (mutating && !allowedOrigins().includes(req.get('origin') || '')) throw new AuthError(403, 'Origem não autorizada');
    if (req.path === '/health' || (req.path === '/auth/login' && req.method === 'POST')) { next(); return; }
    const token = sessionCookie(req);
    const session = await sessions().read(token);
    if (!session) throw new AuthError(401, 'Não autenticado');
    if (mutating && !equalToken(req.get('X-CSRF-Token') || '', session.csrfToken)) throw new AuthError(403, 'CSRF inválido');
    req.user = { sub: session.username };
    req.authSession = session;
    req.sessionToken = token;
    res.setHeader('Cache-Control', 'no-store');
    next();
  } catch (error) { authFailure(res, error); }
}
