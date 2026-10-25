/**
 * Session Service — CRUD de sessões
 */
import { getDB } from '../banco/conexao';
import * as crypto from 'crypto';

export type AgentType = 'kothar' | 'claude' | 'gemini' | 'kothar-legacy' | 'kothar-1.0';

export interface Session {
  id: string;
  name: string;
  agent: AgentType;
  sub_agent?: string | null;
  started_at: string;
  ended_at: string | null;
  status: 'active' | 'completed';
  trace_count?: number;
}

export async function criarSessao(name: string, agent: AgentType, sub_agent?: string): Promise<Session> {
  if (!['kothar', 'claude', 'gemini', 'kothar-legacy', 'kothar-1.0'].includes(agent)) {
    throw new Error(`Agent inválido: ${agent}`);
  }

  const pool = getDB();
  const id = `sess-${crypto.randomBytes(8).toString('hex')}-${Date.now()}`;
  const startedAt = new Date().toISOString();
  const subAgentValue = sub_agent || null;

  await pool.query(`
    INSERT INTO sessions (id, name, agent, sub_agent, started_at, status)
    VALUES ($1, $2, $3, $4, $5, 'active')
  `, [id, name, agent, subAgentValue, startedAt]);

  return {
    id,
    name,
    agent,
    sub_agent: subAgentValue,
    started_at: startedAt,
    ended_at: null,
    status: 'active',
  };
}

export async function listarSessoes(): Promise<Session[]> {
  const pool = getDB();
  const { rows } = await pool.query(`
    SELECT s.*, COUNT(t.id) as trace_count
    FROM sessions s
    LEFT JOIN traces t ON t.session_id = s.id
    GROUP BY s.id
    ORDER BY s.started_at DESC
  `);
  return rows;
}

export async function obterSessao(id: string): Promise<Session | null> {
  const pool = getDB();
  const { rows } = await pool.query(`
    SELECT s.*, COUNT(t.id) as trace_count
    FROM sessions s
    LEFT JOIN traces t ON t.session_id = s.id
    WHERE s.id = $1
    GROUP BY s.id
  `, [id]);
  return rows[0] || null;
}

export async function encerrarSessao(id: string): Promise<Session | null> {
  const pool = getDB();
  const endedAt = new Date().toISOString();
  const { rowCount } = await pool.query(`
    UPDATE sessions
    SET ended_at = $1, status = 'completed'
    WHERE id = $2 AND status = 'active'
  `, [endedAt, id]);

  if (rowCount === 0) return null;
  return await obterSessao(id);
}

export async function deletarSessao(id: string): Promise<boolean> {
  const pool = getDB();
  const { rowCount } = await pool.query('DELETE FROM sessions WHERE id = $1', [id]);
  return (rowCount ?? 0) > 0;
}

export async function recuperarSessao(id: string, agent: AgentType, sub_agent?: string): Promise<Session> {
  const existing = await obterSessao(id);
  if (existing) return existing;

  const pool = getDB();
  const name = `kothar-recovered-${Math.floor(Date.now() / 1000)}`;
  const startedAt = new Date().toISOString();
  const subAgentValue = sub_agent || null;
  
  await pool.query(`
    INSERT INTO sessions (id, name, agent, sub_agent, started_at, status)
    VALUES ($1, $2, $3, $4, $5, 'active')
  `, [id, name, agent, subAgentValue, startedAt]);

  return {
    id,
    name,
    agent,
    sub_agent: subAgentValue,
    started_at: startedAt,
    ended_at: null,
    status: 'active',
  };
}

export async function atualizarAgenteSessao(id: string, agent: AgentType, sub_agent?: string): Promise<void> {
  const pool = getDB();
  await pool.query(`
    UPDATE sessions SET agent = $1, sub_agent = $2 WHERE id = $3
  `, [agent, sub_agent || null, id]);
}
