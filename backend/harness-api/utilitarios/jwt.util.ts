/**
 * Utilitários JWT — geração e verificação
 */
import * as jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-change-me-in-production-32chars';
const JWT_EXPIRES_IN = parseInt(process.env.JWT_EXPIRES_IN || '2592000', 10); // 30 dias

export interface JWTPayload {
  sub: string; // identifier
  iat?: number;
  exp?: number;
}

export function gerarToken(identifier: string): { token: string; expiresAt: string } {
  const payload: JWTPayload = { sub: identifier };
  const token = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });

  const expiresAt = new Date(Date.now() + JWT_EXPIRES_IN * 1000).toISOString();
  return { token, expiresAt };
}

export function verificarToken(token: string): JWTPayload | null {
  try {
    const payload = jwt.verify(token, JWT_SECRET) as JWTPayload;
    return payload;
  } catch (e) {
    return null;
  }
}

export function extrairToken(authHeader?: string): string | null {
  if (!authHeader) return null;
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0].toLowerCase() !== 'bearer') return null;
  return parts[1];
}
