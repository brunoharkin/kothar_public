/**
 * Auth Service — geração e validação de tokens
 */
import { gerarToken, verificarToken, JWTPayload } from '../utilitarios/jwt.util';

export interface LoginResult {
  token: string;
  expiresAt: string;
  username: string;
}

export function login(username?: string, password?: string): LoginResult {
  if (!username || !password) {
    throw new Error('Usuário e senha são obrigatórios');
  }

  const adminUsername = process.env.ADMIN_USERNAME || 'kothar_admin';
  const adminPassword = process.env.ADMIN_PASSWORD || 'kothar_secure_2026';

  if (username !== adminUsername || password !== adminPassword) {
    throw new Error('Credenciais inválidas');
  }

  const { token, expiresAt } = gerarToken(username);
  return { token, expiresAt, username };
}

export function refresh(username: string): LoginResult {
  const { token, expiresAt } = gerarToken(username);
  return { token, expiresAt, username };
}

export function validarToken(token: string): JWTPayload | null {
  return verificarToken(token);
}
