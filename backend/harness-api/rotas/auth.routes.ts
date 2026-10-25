/**
 * Auth Routes — POST /api/auth/login, POST /api/auth/refresh
 */
import { Router, Request, Response } from 'express';
import * as authService from '../servicos/auth.service';

const router = Router();

router.post('/login', (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;
    const result = authService.login(username, password);
    res.json(result);
  } catch (e: any) {
    res.status(400).json({ error: e.message });
  }
});

router.post('/refresh', (req: Request, res: Response) => {
  try {
    if (!req.user?.sub) {
      return res.status(401).json({ error: 'Não autenticado' });
    }
    const result = authService.refresh(req.user.sub);
    res.json(result);
  } catch (e: any) {
    res.status(400).json({ error: e.message });
  }
});

export default router;
