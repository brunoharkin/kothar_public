import { createClient } from 'redis';
import { createHash, randomBytes, scrypt, timingSafeEqual } from 'crypto';

export const COOKIE_NAME = '__Host-kothar_session';
export const digest = (value: string): string => createHash('sha256').update(value).digest('hex');
export interface AuthSession { username: string; csrfToken: string; expiresAt: string; credentialVersion: string }
export interface Store {
  get(key: string): Promise<string | null>;
  set(key: string, value: string, options: { EX: number }): Promise<unknown>;
  del(key: string): Promise<unknown>;
  eval(script: string, options: { keys: string[]; arguments: string[] }): Promise<unknown>;
}
export class AuthError extends Error { constructor(public status: number, message: string) { super(message); } }
export const LIMIT_SCRIPT = `local n = redis.call('INCR', KEYS[1]); if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end; if n > tonumber(ARGV[1]) then return 0 end; return 1`;
export class SessionStore {
  readonly ttl: number;
  readonly version: string;
  constructor(private store: Store, private username: string, private passwordHash: string, ttl = 86400) {
    if (!username || !/^[a-f0-9]{32,128}:[a-f0-9]{128}$/.test(passwordHash)) throw new Error('Credenciais administrativas não configuradas');
    if (!Number.isInteger(ttl) || ttl < 300 || ttl > 86400) throw new Error('TTL de sessão inválido');
    this.ttl = ttl;
    this.version = digest(username + '\0' + passwordHash);
  }
  async limit(scope: string, identifier: string, max: number, seconds: number): Promise<void> {
    const allowed = await this.store.eval(LIMIT_SCRIPT, { keys: [`kothar:auth:limit:${scope}:${digest(identifier)}`], arguments: [String(max), String(seconds)] });
    if (Number(allowed) !== 1) throw new AuthError(429, 'Limite de tentativas excedido');
  }
  async create(username: unknown, password: unknown, ip: string): Promise<{ token: string; session: AuthSession }> {
    await this.limit('login-ip', ip, 5, 900);
    if (typeof username !== 'string' || typeof password !== 'string' || username.length < 1 || username.length > 128 || password.length < 1 || password.length > 1024) throw new AuthError(400, 'Credenciais inválidas');
    await this.limit('login-account', username.normalize('NFKC').toLowerCase(), 5, 900);
    const [salt, encoded] = this.passwordHash.split(':');
    const derived = await new Promise<Buffer>((resolve, reject) => scrypt(password, Buffer.from(salt, 'hex'), 64, { N: 16384, r: 8, p: 1 }, (err, key) => err ? reject(err) : resolve(key)));
    const valid = timingSafeEqual(derived, Buffer.from(encoded, 'hex'));
    if (!valid || username !== this.username) throw new AuthError(401, 'Credenciais inválidas');
    const token = randomBytes(32).toString('hex');
    const session: AuthSession = { username, csrfToken: randomBytes(32).toString('hex'), expiresAt: new Date(Date.now() + this.ttl * 1000).toISOString(), credentialVersion: this.version };
    await this.store.set(this.key(token), JSON.stringify(session), { EX: this.ttl });
    return { token, session };
  }
  key(token: string): string { return `kothar:auth:session:${digest(token)}`; }
  async read(token: string): Promise<AuthSession | null> {
    if (!/^[a-f0-9]{64}$/.test(token)) return null;
    const data = await this.store.get(this.key(token));
    if (!data) return null;
    const session: AuthSession = JSON.parse(data);
    if (session.username !== this.username || session.credentialVersion !== this.version || !/^[a-f0-9]{64}$/.test(session.csrfToken) || !Number.isFinite(Date.parse(session.expiresAt)) || Date.parse(session.expiresAt) <= Date.now()) return null;
    return session;
  }
  async revoke(token: string): Promise<void> { if (/^[a-f0-9]{64}$/.test(token)) await this.store.del(this.key(token)); }
}
let instance: SessionStore | undefined;
export async function initAuth(): Promise<void> {
  const url = process.env.AUTH_REDIS_URL || process.env.REDIS_URL;
  if (!url || !/^rediss?:\/\//.test(url)) throw new Error('Redis de autenticação obrigatório');
  const client = createClient({ url, disableOfflineQueue: true, socket: { connectTimeout: 3000, reconnectStrategy: false } });
  client.on('error', () => console.error('[auth] Redis indisponível'));
  const candidate = new SessionStore(client as unknown as Store, process.env.ADMIN_USERNAME || '', process.env.ADMIN_PASSWORD_SCRYPT || '', Number(process.env.AUTH_SESSION_TTL_SECONDS || '86400'));
  await client.connect();
  await client.ping();
  instance = candidate;
}
export function sessions(): SessionStore { if (!instance) throw new AuthError(503, 'Autenticação indisponível'); return instance; }
export function equalToken(a: string, b: string): boolean { return /^[a-f0-9]{64}$/.test(a) && /^[a-f0-9]{64}$/.test(b) && timingSafeEqual(Buffer.from(a), Buffer.from(b)); }
