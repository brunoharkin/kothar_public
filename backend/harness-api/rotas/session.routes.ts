/**
 * Session Routes — CRUD + SSE stream
 */
import { Router, Request, Response } from 'express';
import * as sessionService from '../servicos/session.service';
import { listarTraces, traceEvents } from '../servicos/trace.service';
import fs from 'fs';
import path from 'path';

const router = Router();

function routeId(req: Request): string {
  const value = req.params.id;
  if (typeof value !== 'string' || !/^[0-9a-f-]{36}$/i.test(value)) {
    throw new Error('Identificador inválido');
  }
  return value;
}

// POST /api/session — criar nova sessão
router.post('/', async (req: Request, res: Response) => {
  try {
    const { name, agent, sub_agent } = req.body;
    const session = await sessionService.criarSessao(name, agent, sub_agent);
    res.json(session);
  } catch (e: any) {
    res.status(400).json({ error: e.message });
  }
});

// GET /api/session — listar todas
router.get('/', async (req: Request, res: Response) => {
  const sessions = await sessionService.listarSessoes();
  res.json(sessions);
});

// GET /api/session/:id — detalhes
router.get('/:id', async (req: Request, res: Response) => {
  const session = await sessionService.obterSessao(routeId(req));
  if (!session) return res.status(404).json({ error: 'Sessão não encontrada' });
  res.json(session);
});

// PUT /api/session/:id — encerrar
router.put('/:id', async (req: Request, res: Response) => {
  const session = await sessionService.encerrarSessao(routeId(req));
  if (!session) return res.status(404).json({ error: 'Sessão não encontrada ou já encerrada' });
  res.json(session);
});

// DELETE /api/session/:id — excluir permanentemente (CASCADE remove traces)
router.delete('/:id', async (req: Request, res: Response) => {
  const id = routeId(req);
  const ok = await sessionService.deletarSessao(id);
  if (!ok) return res.status(404).json({ error: 'Sessão não encontrada' });
  res.json({ deleted: true, id });
});

// GET /api/session/:id/traces — listar traces (paginado)
router.get('/:id/traces', async (req: Request, res: Response) => {
  const id = routeId(req);
  const session = await sessionService.obterSessao(id);
  if (!session) return res.status(404).json({ error: 'Sessão não encontrada' });

  const limit = parseInt((req.query.limit as string) || '500', 10);
  const offset = parseInt((req.query.offset as string) || '0', 10);
  const traces = await listarTraces(id, limit, offset);
  res.json(traces);
});

// GET /api/session/:id/traces/stream — SSE live
router.get('/:id/traces/stream', async (req: Request, res: Response) => {
  const id = routeId(req);
  const session = await sessionService.obterSessao(id);
  if (!session) return res.status(404).json({ error: 'Sessão não encontrada' });

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();

  // Enviar evento inicial de keepalive
  const keepalive = setInterval(() => {
    res.write(`: keepalive\n\n`);
  }, 15000);

  // Listener para novos traces dessa sessão
  const onTrace = (trace: any) => {
    res.write(`event: trace\ndata: ${JSON.stringify(trace)}\n\n`);
  };

  traceEvents.on(`session:${id}`, onTrace);

  // Cleanup no disconnect
  req.on('close', () => {
    clearInterval(keepalive);
    traceEvents.off(`session:${id}`, onTrace);
    res.end();
  });
});

// POST /api/session/:id/report — gerar relatório Markdown
router.post('/:id/report', async (req: Request, res: Response) => {
  try {
    const id = routeId(req);
    const session = await sessionService.obterSessao(id);
    if (!session) return res.status(404).json({ error: 'Sessão não encontrada' });

    const traces = await listarTraces(id, 10000, 0);
    
    let md = `# Relatório de Sessão: ${session.name || session.id}\n\n`;
    md += `- **Agente**: ${session.agent}\n`;
    if (session.sub_agent) md += `- **Sub-agente**: ${session.sub_agent}\n`;
    md += `- **Início**: ${session.started_at || new Date().toISOString()}\n`;
    md += `- **Status**: ${session.status}\n\n`;
    md += `## Histórico de Traces (${traces.length})\n\n`;

    traces.forEach((t, i) => {
      const type = t.tool || t.event_type || 'Event';
      md += `### [${i + 1}] ${type} - ${new Date(t.timestamp).toLocaleTimeString('pt-BR')}\n\n`;
      
      let inputStr = '';
      if (t.input) inputStr = typeof t.input === 'string' ? t.input : JSON.stringify(t.input, null, 2);
      else if (t.content) inputStr = t.content;

      if (inputStr) {
        md += `**Input/Contexto**:\n\`\`\`\n${inputStr}\n\`\`\`\n\n`;
      }
      
      let outputStr = '';
      if (t.output) outputStr = typeof t.output === 'string' ? t.output : JSON.stringify(t.output, null, 2);
      
      if (outputStr) {
         md += `**Output/Resultado**:\n\`\`\`\n${outputStr}\n\`\`\`\n\n`;
      }
      md += `---\n\n`;
    });

    const cofreDir = '/home/bruno/kothar/Cofre/sessoes';
    if (!fs.existsSync(cofreDir)) {
      fs.mkdirSync(cofreDir, { recursive: true });
    }
    const safeName = (session.name || session.id).replace(/[^a-z0-9]/gi, '_').toLowerCase();
    const filePath = path.join(cofreDir, `${safeName}_${session.id.slice(0, 8)}.md`);
    
    fs.writeFileSync(filePath, md, 'utf-8');

    res.json({ success: true, path: filePath });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
