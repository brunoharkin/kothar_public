import { aceitarSessao, apiFetch } from '../../seguranca/sessao';
import React, { useState } from 'react';
import { Activity, Lock, User, ChevronRight } from 'lucide-react';
import { motion } from 'framer-motion';
import './LoginPage.styles.css';

interface LoginPageProps {
  onLogin: () => void;
  initialError?: string;
}

export function LoginPage({ onLogin, initialError = '' }: LoginPageProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(initialError);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(response.status === 429 ? 'Muitas tentativas. Aguarde antes de tentar novamente.' : 'Não foi possível autenticar.');
      }

      aceitarSessao(data);
      setPassword('');
      onLogin();
    } catch (err: any) {
      setError(err instanceof Error ? err.message : 'Não foi possível autenticar.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-glass-panel">
        <div className="login-header">
          <div className="app-logo-icon" style={{ margin: '0 auto 1rem' }}>
            <Activity className="h-8 w-8" />
          </div>
          <h1 className="login-title">Kothar v6.0</h1>
          <p className="login-subtitle">Acesso restrito. Área de Comando.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }} 
              animate={{ opacity: 1, y: 0 }} 
              className="login-error"
            >
              {error}
            </motion.div>
          )}

          <div className="input-group">
            <div className="input-icon">
              <User className="h-5 w-5" />
            </div>
            <input
              type="text"
              placeholder="Usuário"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="login-input"
              autoComplete="username"
              required
              maxLength={128}
              autoFocus
            />
          </div>

          <div className="input-group">
            <div className="input-icon">
              <Lock className="h-5 w-5" />
            </div>
            <input
              autoComplete="current-password"
              required
              maxLength={1024}
              type="password"
              placeholder="Senha"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="login-input"
            />
          </div>

          <button 
            type="submit" 
            className="login-button"
            disabled={loading}
          >
            {loading ? 'Autenticando...' : 'Acessar Sistema'}
            {!loading && <ChevronRight className="h-4 w-4 ml-2" />}
          </button>
        </form>
      </div>
    </div>
  );
}
