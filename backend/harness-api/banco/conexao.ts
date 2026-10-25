/**
 * Conexão PostgreSQL pool + migration runner
 */
import { Pool } from 'pg';
import * as fs from 'fs';
import * as path from 'path';

let poolInstance: Pool | null = null;

export async function initDB(): Promise<void> {
  if (!poolInstance) {
    const required = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME'] as const;
    for (const name of required) {
      if (!process.env[name]) throw new Error(`Configuração obrigatória ausente: ${name}`);
    }
    const port = Number(process.env.DB_PORT || '5432');
    if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('DB_PORT inválida');
    poolInstance = new Pool({
      host: process.env.DB_HOST,
      port,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
    });

    await runMigrations(poolInstance);
  }
}

export function getDB(): Pool {
  if (!poolInstance) {
    throw new Error('Database not initialized. Call initDB first.');
  }
  return poolInstance;
}

async function runMigrations(pool: Pool) {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS _migrations (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        applied_at TIMESTAMP NOT NULL
      );
    `);

    const migrationsDir = path.join(__dirname, 'migrations');
    if (!fs.existsSync(migrationsDir)) return;

    const files = fs.readdirSync(migrationsDir)
      .filter((f) => f.endsWith('.sql'))
      .sort();

    const { rows } = await client.query('SELECT name FROM _migrations');
    const applied = new Set(rows.map((r: any) => r.name));

    for (const file of files) {
      if (applied.has(file)) continue;

      let sql = fs.readFileSync(path.join(migrationsDir, file), 'utf8');
      
      // Adapt SQLite specifics to PostgreSQL
      // Replace TEXT PRIMARY KEY with TEXT PRIMARY KEY (already compatible)
      // Check constraints syntax is generally compatible.
      // But let's let the raw SQL run.
      
      try {
        await client.query('BEGIN');
        await client.query(sql);
        await client.query('INSERT INTO _migrations (name, applied_at) VALUES ($1, $2)', [
          file,
          new Date().toISOString()
        ]);
        await client.query('COMMIT');
        console.log(`[migrations] Aplicada: ${file}`);
      } catch (err) {
        await client.query('ROLLBACK');
        console.error(`[migrations] Falha ao aplicar ${file}`);
        throw err;
      }
    }
  } finally {
    client.release();
  }
}

export async function closeDB() {
  if (poolInstance) {
    await poolInstance.end();
    poolInstance = null;
  }
}
