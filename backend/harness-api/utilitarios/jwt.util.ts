/**
 * Utilitários JWT — geração e verificação
 */
// JWT issuance is intentionally disabled: all sessions are revocable server-side.
export interface JWTPayload { sub: string; iat?: number; exp?: number }
export function gerarToken(_identifier: string): never { throw new Error('JWT desativado; use sessão server-side'); }
export function verificarToken(_token: string): null { return null; }
export function extrairToken(_authHeader?: string): null { return null; }
