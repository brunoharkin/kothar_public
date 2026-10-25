const { Pool } = require('pg');
const fs = require('fs');

const pool = new Pool({
  host: 'localhost',
  port: 5444,
  user: 'kothar',
  password: process.env.POSTGRES_PASSWORD || '',
  database: 'traces',
});

async function run() {
  const sql = fs.readFileSync('./banco/migrations/002_metadata.sql', 'utf8');
  await pool.query(sql);
  console.log('Migration 002 aplicada com sucesso');

  // Verificar
  const result = await pool.query(`
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'traces'
    ORDER BY ordinal_position
  `);
  console.log('\nColunas da tabela traces:');
  for (const row of result.rows) {
    console.log(`  ${row.column_name}: ${row.data_type}`);
  }

  await pool.end();
}
run().catch(e => { console.error(e); process.exit(1); });
