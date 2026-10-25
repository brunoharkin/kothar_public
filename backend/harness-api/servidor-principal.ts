/**
 * KOTHAR v3.0 — Trace Backend
 * Servidor principal Express
 */
import * as dotenv from 'dotenv';
import * as path from 'path';

// Carregar .env da raiz do backend
dotenv.config({ path: path.join(__dirname, '.env') });

import express from 'express';
import cors from 'cors';
import { initDB } from './banco/conexao';
import { allowedOrigins, authMiddleware, publicRateLimit } from './utilitarios/auth.middleware';
import { initAuth } from './utilitarios/session-store';
import authRoutes from './rotas/auth.routes';
import sessionRoutes from './rotas/session.routes';
import traceRoutes from './rotas/trace.routes';
import heatmapRoutes from './rotas/heatmap.routes';

const app = express();
const PORT = parseInt(process.env.PORT || '3000', 10);
const CORS_ORIGIN = allowedOrigins();

const corsOptions = {
  origin: CORS_ORIGIN,
  credentials: true,
};

app.disable('x-powered-by');
app.use(express.json({ limit: '1mb' }));
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Cache-Control', 'no-store');
  next();
});

app.use(cors(corsOptions));
app.use(publicRateLimit);

// Health check (público)
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'kothar-trace-backend', timestamp: new Date().toISOString() });
});

// Rotas públicas já definidas acima

// Auth middleware em todas as rotas /api/* (abaixo daqui) exceto as de cima
app.use('/api', authMiddleware);

// Rotas
app.use('/api/auth', authRoutes);
app.use('/api/session', sessionRoutes);
app.use('/api/trace', traceRoutes);
app.use('/api/heatmaps', heatmapRoutes);

// 404
app.use((req, res) => {
  res.status(404).json({ error: 'Rota não encontrada', path: req.path });
});

// Error handler
app.use((err: unknown, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('[error] falha interna');
  res.status(500).json({ error: 'Erro interno do servidor' });
});

// Inicializar DB e iniciar servidor
Promise.all([initDB(), initAuth()]).then(() => {
  const server = app.listen(PORT, () => {
    console.log('Kothar Trace Backend iniciado');
  });

  // Graceful shutdown
  process.on('SIGTERM', () => {
    console.log('SIGTERM recebido, encerrando...');
    server.close(() => process.exit(0));
  });

  process.on('SIGINT', () => {
    console.log('\\nSIGINT recebido, encerrando...');
    server.close(() => process.exit(0));
  });
}).catch(err => {
  console.error('Erro fatal ao inicializar banco de dados:', err);
  process.exit(1);
});
