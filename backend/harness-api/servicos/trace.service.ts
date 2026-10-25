/**
 * Trace Service — registro e consulta de traces
 */
import { getDB } from '../banco/conexao';
import * as crypto from 'crypto';
import { EventEmitter } from 'events';

export interface TraceEntry {
  id: string;
  session_id: string;
  timestamp: string;
  tool: string;
  input: string;
  output: string;
  reasoning: string | null;
  duration: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  context_tokens: number | null;
  status: 'success' | 'error' | 'pending';
  metadata?: any;
  event_type?: string;
  agent_name?: string;
  content?: string;
  sequence?: number;
  error_message?: string;
}

export const traceEvents = new EventEmitter();
traceEvents.setMaxListeners(100);

export async function registrarTrace(trace: Omit<TraceEntry, 'id'>): Promise<TraceEntry> {
  const pool = getDB();
  const id = `tr-${crypto.randomBytes(8).toString('hex')}`;

  await pool.query(`
    INSERT INTO traces (id, session_id, timestamp, tool, input, output, reasoning, duration, input_tokens, output_tokens, context_tokens, status, metadata, event_type, agent_name, content, sequence, error_message)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
  `, [
    id, trace.session_id, trace.timestamp, trace.tool, trace.input, trace.output,
    trace.reasoning ?? null, trace.duration ?? null,
    trace.input_tokens ?? 0, trace.output_tokens ?? 0, trace.context_tokens ?? 0,
    trace.status,
    JSON.stringify(trace.metadata || {}),
    trace.event_type ?? null,
    trace.agent_name ?? null,
    trace.content ?? null,
    trace.sequence ?? null,
    trace.error_message ?? null,
  ]);

  const full: TraceEntry = { id, ...trace };
  traceEvents.emit(`session:${trace.session_id}`, full);
  return full;
}

export async function registrarLote(traces: Array<Omit<TraceEntry, 'id'>>): Promise<TraceEntry[]> {
  const pool = getDB();
  const results: TraceEntry[] = [];

  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    for (const t of traces) {
      const id = `tr-${crypto.randomBytes(8).toString('hex')}`;
      await client.query(`
        INSERT INTO traces (id, session_id, timestamp, tool, input, output, reasoning, duration, input_tokens, output_tokens, context_tokens, status, metadata, event_type, agent_name, content, sequence, error_message)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
      `, [
        id, t.session_id, t.timestamp, t.tool, t.input, t.output,
        t.reasoning ?? null, t.duration ?? null,
        t.input_tokens ?? 0, t.output_tokens ?? 0, t.context_tokens ?? 0,
        t.status,
        JSON.stringify(t.metadata || {}),
        t.event_type ?? null,
        t.agent_name ?? null,
        t.content ?? null,
        t.sequence ?? null,
        t.error_message ?? null,
      ]);
      const full: TraceEntry = { id, ...t };
      results.push(full);
      traceEvents.emit(`session:${t.session_id}`, full);
    }
    await client.query('COMMIT');
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }

  return results;
}

export async function listarTraces(sessionId: string, limit = 500, offset = 0): Promise<TraceEntry[]> {
  const pool = getDB();
  const { rows } = await pool.query(`
    SELECT * FROM traces
    WHERE session_id = $1
    ORDER BY timestamp ASC
    LIMIT $2 OFFSET $3
  `, [sessionId, limit, offset]);
  return rows;
}

export async function limparTracesSessao(sessionId: string): Promise<number> {
  const pool = getDB();
  const { rowCount } = await pool.query('DELETE FROM traces WHERE session_id = $1', [sessionId]);
  return rowCount ?? 0;
}
