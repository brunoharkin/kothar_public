/**
 * Auth Service — geração e validação de tokens
 */
import { sessions, AuthSession } from '../utilitarios/session-store';

export interface LoginResult { token: string; session: AuthSession }
export async function login(username: unknown, password: unknown, ip: string): Promise<LoginResult> {
  return sessions().create(username, password, ip);
}
export async function refresh(token: string): Promise<AuthSession | null> {
  // Absolute expiry is preserved; refreshing metadata never extends a stolen session.
  return sessions().read(token);
}
export async function validarToken(token: string): Promise<AuthSession | null> {
  return sessions().read(token);
}
