const assert = require('node:assert/strict');
const { scryptSync } = require('node:crypto');
const test = require('node:test');
const { AuthError, SessionStore } = require('../dist/utilitarios/session-store.js');

class Store {
  constructor() { this.data = new Map(); this.counters = new Map(); }
  async get(key) { return this.data.get(key) || null; }
  async set(key, value) { this.data.set(key, value); }
  async del(key) { this.data.delete(key); }
  async eval(_script, { keys, arguments: args }) {
    const count = (this.counters.get(keys[0]) || 0) + 1;
    this.counters.set(keys[0], count);
    return count > Number(args[0]) ? 0 : 1;
  }
}

function fixture(ttl = 300) {
  const salt = 'aa'.repeat(16);
  const password = 'synthetic-passphrase';
  const encoded = scryptSync(password, Buffer.from(salt, 'hex'), 64,
    { N: 16384, r: 8, p: 1 }).toString('hex');
  return { password, store: new Store(), sessions: new SessionStore(new Store(), 'admin', `${salt}:${encoded}`, ttl) };
}

test('creates, reads and revokes opaque server-side sessions', async () => {
  const salt = 'aa'.repeat(16), password = 'synthetic-passphrase';
  const encoded = scryptSync(password, Buffer.from(salt, 'hex'), 64,
    { N: 16384, r: 8, p: 1 }).toString('hex');
  const store = new Store();
  const sessions = new SessionStore(store, 'admin', `${salt}:${encoded}`, 300);
  const created = await sessions.create('admin', password, '127.0.0.1');
  assert.match(created.token, /^[a-f0-9]{64}$/);
  assert.equal((await sessions.read(created.token)).username, 'admin');
  await sessions.revoke(created.token);
  assert.equal(await sessions.read(created.token), null);
});

test('rejects invalid password and applies shared limits', async () => {
  const salt = 'bb'.repeat(16), encoded = scryptSync('right', Buffer.from(salt, 'hex'), 64,
    { N: 16384, r: 8, p: 1 }).toString('hex');
  const sessions = new SessionStore(new Store(), 'admin', `${salt}:${encoded}`, 300);
  await assert.rejects(sessions.create('admin', 'wrong', 'one'), (error) => error instanceof AuthError && error.status === 401);
  for (let index = 0; index < 4; index += 1) {
    await assert.rejects(sessions.create('admin', 'wrong', 'limited'));
  }
  await assert.rejects(sessions.create('admin', 'wrong', 'limited'),
    (error) => error instanceof AuthError && error.status === 429);
});

test('configuration refuses missing credentials and unsafe TTL', () => {
  const store = new Store();
  assert.throws(() => new SessionStore(store, '', '', 300));
  assert.throws(() => new SessionStore(store, 'admin', `${'aa'.repeat(16)}:${'bb'.repeat(64)}`, 0));
});
