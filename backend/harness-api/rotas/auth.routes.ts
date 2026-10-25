/**
 * Auth Routes — POST /api/auth/login, POST /api/auth/refresh
 */
import { Router, Request, Response } from 'express';
import * as authService from '../servicos/auth.service';
import { COOKIE_NAME, sessions, AuthSession } from '../utilitarios/session-store';
import { authFailure, sessionCookie } from '../utilitarios/auth.middleware';

const router = Router();
const cookieOptions = { httpOnly: true, secure: true, sameSite: 'strict' as const, path: '/' };
function metadata(session: AuthSession) { return { username: session.username, expiresAt: session.expiresAt, csrfToken: session.csrfToken }; }
router.post('/login', async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body || {};
    const result = await authService.login(username, password, req.socket.remoteAddress || 'unknown');
    const previousToken = sessionCookie(req);
    if (previousToken && previousToken !== result.token) await sessions().revoke(previousToken);
    res.cookie(COOKIE_NAME, result.token, { ...cookieOptions, maxAge: sessions().ttl * 1000 });
    res.setHeader('Cache-Control', 'no-store');
    res.json(metadata(result.session));
  } catch (error) { authFailure(res, error); }
});
router.get('/session', (req: Request, res: Response) => { res.json(metadata(req.authSession!)); });
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const session = await authService.refresh(req.sessionToken!);
    if (!session) return res.status(401).json({ error: 'Não autenticado' });
    res.json(metadata(session));
  } catch (error) { authFailure(res, error); }
});
router.post('/logout', async (req: Request, res: Response) => {
  try {
    await sessions().revoke(req.sessionToken!);
    res.clearCookie(COOKIE_NAME, cookieOptions);
    res.status(204).end();
  } catch (error) { authFailure(res, error); }
});
export default router;
