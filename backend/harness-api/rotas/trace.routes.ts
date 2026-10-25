/**
 * Trace Routes — POST /api/trace, POST /api/trace/batch
 */
import { Router, Request, Response } from 'express';
import * as traceService from '../servicos/trace.service';
import { obterSessao, recuperarSessao, atualizarAgenteSessao } from '../servicos/session.service';

const router = Router();

// Validar payload de trace
function validarTrace(t: any): string | null {
  if (!t) return 'Trace vazio';
  if (!t.session_id) return 'session_id obrigatório';
  if (!t.tool) return 'tool obrigatório';
  if (!t.timestamp) return 'timestamp obrigatório';
  if (t.input === undefined) return 'input obrigatório';
  if (t.output === undefined) return 'output obrigatório';
  if (t.status && !['success', 'error', 'pending'].includes(t.status)) {
    return 'status inválido';
  }
  return null;
}

// Utilitário de Redação de Dados Sensíveis
function redactSensitiveData(text: string): string {
  if (!text) return text;
  let redacted = text;

  // Mascarar Chaves API (Anthropic, OpenAI, etc)
  redacted = redacted.replace(/(sk-(?:ant-api\d{2}-|proj-|)[A-Za-z0-9\-_]{5})[A-Za-z0-9\-_]{15,}/g, '$1***[OCULTO]***');
  
  // Mascarar Bearer Tokens
  redacted = redacted.replace(/(Bearer\s+[A-Za-z0-9\-_]{5})[A-Za-z0-9\-_]{15,}/gi, '$1***[OCULTO]***');

  // Mascarar senhas em geral (password=..., pass: "...")
  redacted = redacted.replace(/(pass(?:word)?\s*[:=]\s*["']?)([^"'\s]{4,})(["']?)/gi, '$1***[OCULTO]***$3');
  
  // Mascarar credenciais em URIs (ex: redis://:senha@host, postgres://user:senha@host)
  redacted = redacted.replace(/(:\/\/[^/:]*:)([^@/]+)(@)/gi, '$1***[OCULTO]***$3');

  return redacted;
}

function applySecurityFilter(t: any): any {
  const inputStr = typeof t.input === 'string' ? t.input : JSON.stringify(t.input);
  let outputStr = typeof t.output === 'string' ? t.output : JSON.stringify(t.output);

  // Se a ferramenta tentar ler arquivos críticos (.env, .pem, .key), mascaramos o output inteiro
  if (t.tool && (t.tool.includes('view_file') || t.tool.includes('Read') || t.tool.includes('Grep') || t.tool.includes('Glob'))) {
    if (/\.(env|pem|key|crt|cert|p8|p12|pkcs)/i.test(inputStr)) {
      outputStr = "[ARQUIVO PROTEGIDO: CONTEÚDO SENSÍVEL OCULTO PELO MAESTRO]";
    }
  }

  return {
    ...t,
    input: redactSensitiveData(inputStr),
    output: redactSensitiveData(outputStr),
  };
}

// POST /api/trace — registrar um trace
router.post('/', async (req: Request, res: Response) => {
  const err = validarTrace(req.body);
  if (err) return res.status(400).json({ error: err });

  if (!(await obterSessao(req.body.session_id))) {
    return res.status(404).json({ error: 'Sessão não encontrada' });
  }

  const safeData = applySecurityFilter(req.body);

  const trace = await traceService.registrarTrace({
    session_id: safeData.session_id,
    timestamp: safeData.timestamp,
    tool: safeData.tool,
    input: safeData.input,
    output: safeData.output,
    reasoning: safeData.reasoning ?? null,
    duration: safeData.duration ?? null,
    input_tokens: safeData.input_tokens ?? null,
    output_tokens: safeData.output_tokens ?? null,
    context_tokens: safeData.context_tokens ?? null,
    status: safeData.status || 'success',
    metadata: safeData.metadata || {},
    event_type: safeData.event_type ?? null,
    agent_name: safeData.agent_name ?? null,
    content: safeData.content ?? null,
    sequence: safeData.sequence ?? null,
    error_message: safeData.error_message ?? null,
  });

  res.json(trace);
});

// POST /api/trace/batch — registrar vários (usado pelo daemon)
router.post('/batch', async (req: Request, res: Response) => {
  const traces = req.body?.traces;
  if (!Array.isArray(traces) || traces.length === 0) {
    return res.status(400).json({ error: 'traces deve ser array não vazio' });
  }

  if (traces.length > 500) {
    return res.status(413).json({ error: 'Batch máximo: 500 traces' });
  }

  for (let i = 0; i < traces.length; i++) {
    const err = validarTrace(traces[i]);
    if (err) return res.status(400).json({ error: `Trace[${i}]: ${err}` });
  }

  for (const t of traces) {
    const sid = t.session_id;
    let agent: 'claude' | 'gemini' = t.agent || (t.tool.toLowerCase().includes('gemini') ? 'gemini' : 'claude');
    
    const sess = await obterSessao(sid);
    if (!sess) {
      await recuperarSessao(sid, agent);
    } else if (sess.agent !== agent && (agent === 'gemini' || agent === 'claude')) {
      await atualizarAgenteSessao(sid, agent);
      sess.agent = agent;
    }
  }

  // Sanitizar e Normalizar
  const normalized = traces.map(t => {
    const safeData = applySecurityFilter(t);
    return {
      session_id: safeData.session_id,
      timestamp: safeData.timestamp,
      tool: safeData.tool,
      input: safeData.input,
      output: safeData.output,
      reasoning: safeData.reasoning ?? null,
      duration: safeData.duration ?? null,
      input_tokens: safeData.input_tokens ?? null,
      output_tokens: safeData.output_tokens ?? null,
      context_tokens: safeData.context_tokens ?? null,
      status: safeData.status || 'success',
    };
  });

  try {
    const result = await traceService.registrarLote(normalized);
    res.json({ count: result.length, traces: result });
  } catch (err: any) {
    console.error('[POST /batch] Erro interno:', err);
    res.status(500).json({ error: 'Erro interno ao inserir no banco', details: err.message });
  }
});

// DELETE /api/trace/:sessionId — limpar traces de uma sessão (sem apagar a sessão)
router.delete('/:sessionId', async (req: Request, res: Response) => {
  const sessionId = req.params.sessionId;
  if (typeof sessionId !== 'string' || !/^[0-9a-f-]{36}$/i.test(sessionId)) {
    return res.status(400).json({ error: 'Identificador inválido' });
  }
  if (!(await obterSessao(sessionId))) {
    return res.status(404).json({ error: 'Sessão não encontrada' });
  }

  const deleted = await traceService.limparTracesSessao(sessionId);
  res.json({ success: true, count: deleted });
});

export default router;
