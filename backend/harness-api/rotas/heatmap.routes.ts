import { Router } from 'express';
import { getDB } from '../banco/conexao';

const router = Router();

// Rota pública para receber eventos do heatmap (CORS deve permitir as origens corretas no app)
router.post('/track', async (req, res) => {
  const { projectId, url, x, y, type, sessionId } = req.body;

  if (!projectId || !url || typeof x !== 'number' || typeof y !== 'number' || !type) {
    return res.status(400).json({ error: 'Parâmetros inválidos' });
  }

  try {
    const pool = getDB();
    await pool.query(
      'INSERT INTO heatmaps (project_id, url, x, y, type, session_id) VALUES ($1, $2, $3, $4, $5, $6)',
      [projectId, url, x, y, type, sessionId || 'anonymous']
    );
    res.status(200).json({ success: true });
  } catch (err) {
    console.error('[Heatmap Track Error]', err);
    res.status(500).json({ error: 'Erro ao salvar dado de heatmap' });
  }
});

// Nova rota para listar sessões distintas de um projeto
router.get('/sessions/:projectId', async (req, res) => {
  const { projectId } = req.params;
  try {
    const pool = getDB();
    const query = `
      SELECT session_id, count(*) as count, min(created_at) as started_at, max(created_at) as last_activity
      FROM heatmaps 
      WHERE project_id = $1 AND session_id IS NOT NULL 
      GROUP BY session_id 
      ORDER BY started_at DESC
    `;
    const { rows } = await pool.query(query, [projectId]);
    res.status(200).json({ sessions: rows });
  } catch (err) {
    console.error('[Heatmap Sessions Error]', err);
    res.status(500).json({ error: 'Erro ao buscar sessões' });
  }
});

// Rota para buscar dados de heatmap, permitindo filtrar por session_id
router.get('/data/:projectId', async (req, res) => {
  const { projectId } = req.params;
  const { url, sessionId } = req.query;

  try {
    const pool = getDB();
    let query = 'SELECT x, y, type FROM heatmaps WHERE project_id = $1';
    const params: any[] = [projectId];

    if (url) {
      params.push(url);
      query += ` AND url = $${params.length}`;
    }

    if (sessionId) {
      params.push(sessionId);
      query += ` AND session_id = $${params.length}`;
    }

    const { rows } = await pool.query(query, params);
    res.status(200).json({ points: rows });
  } catch (err) {
    console.error('[Heatmap Data Error]', err);
    res.status(500).json({ error: 'Erro ao buscar dados de heatmap' });
  }
});

export default router;
