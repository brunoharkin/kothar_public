/**
 * Auth Middleware — valida JWT em todas as rotas /api/*
 */
import { Request, Response, NextFunction } from 'express';
import { extrairToken, verificarToken } from '../utilitarios/jwt.util';

declare global {
  namespace Express {
    interface Request {
      user?: { sub: string };
    }
  }
}

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  // Pular health check e rotas de auth (já que auth é montado depois)
  // Quando app.use('/api', authMiddleware) é aplicado, req.path relativo é:
  //  /health, /auth/login, /auth/refresh, /session, /trace, etc.
  if (req.path === '/health' || req.path.startsWith('/auth/')) {
    return next();
  }

  const token = extrairToken(req.headers.authorization);
  if (!token) {
    return res.status(401).json({ error: 'Token ausente' });
  }

  const payload = verificarToken(token);
  if (!payload) {
    return res.status(401).json({ error: 'Token inválido ou expirado' });
  }

  req.user = { sub: payload.sub };
  next();
}
