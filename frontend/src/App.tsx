/**
 * KOTHAR v6.0 — App Shell
 * Layout principal com sidebar premium, glassmorphism e navegação moderna
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity, Brain, ChevronRight, Database, Network,
  Search, Server, Workflow, BarChart3, FlaskConical, Gauge
} from 'lucide-react';
import { TracePage } from './paginas/trace/trace.page';
import { ControleDeTemperaturaPage } from './paginas/trace/controle_de_temperatura.page';
import { GraphPage } from './paginas/graph/graph.page';
import { MetricsPage } from './paginas/metrics/metrics.page';
import { OllamaChatPage } from './paginas/ollama/ollama.page';
import { MemoryInspectorPage } from './paginas/memory/memory.page';
import { AgentsPage } from './paginas/agents/agents.page';
import { DataLakePage } from './paginas/datalake/datalake.page';
import { PromptLabPage } from './paginas/promptlab/promptlab.page';
import { TokenUsagePage } from './paginas/token-usage/token-usage.page';
import { LoginPage } from './paginas/login/LoginPage';
import { Flame } from 'lucide-react';
import './App.styles.css';

type PageId = 'trace' | 'graph' | 'metrics' | 'ollama' | 'memory' | 'agents' | 'datalake' | 'promptlab' | 'temperature' | 'tokenusage';

interface NavItem {
  id: PageId;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  color: string;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: 'Observabilidade',
    items: [
      {
        id: 'trace',
        label: 'Traces',
        description: 'Timeline de eventos',
        icon: Activity,
        badge: 'Live',
        color: '#3b82f6',
      },
      {
        id: 'metrics',
        label: 'Métricas',
        description: 'RAG, Health, Prometheus',
        icon: BarChart3,
        badge: 'New',
        color: '#8b5cf6',
      },
      {
        id: 'temperature',
        label: 'Temperatura',
        description: 'Heatmaps e UX',
        icon: Flame,
        badge: 'Hot',
        color: '#f97316',
      },
      {
        id: 'graph',
        label: 'Code Graph 3D',
        description: 'Visualização do código',
        icon: Network,
        color: '#22c55e',
      },
      {
        id: 'ollama',
        label: 'Local AI',
        description: 'Chat via Headless GPU',
        icon: Brain,
        badge: 'Beta',
        color: '#f43f5e',
      },
    ],
  },
];

export function App() {
  const validPages: PageId[] = ['trace', 'graph', 'metrics', 'ollama', 'memory', 'agents', 'datalake', 'promptlab', 'temperature', 'tokenusage'];
  const [activePage, setActivePage] = useState<PageId>(() => {
    const hash = window.location.hash.replace('#', '');
    return (validPages.includes(hash as PageId) ? hash as PageId : 'trace');
  });
  const [hoveredItem, setHoveredItem] = useState<PageId | null>(null);
  
  // Auth state
  const [token, setToken] = useState<string | null>(localStorage.getItem('kothar_token'));

  const handleLogin = (newToken: string) => {
    localStorage.setItem('kothar_token', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('kothar_token');
    setToken(null);
  };

  React.useEffect(() => {
    window.location.hash = activePage;
  }, [activePage]);

  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (validPages.includes(hash as PageId)) {
        setActivePage(hash as PageId);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      {/* Sidebar Premium */}
      <aside className="app-sidebar">
        {/* Logo Header */}
        <div className="app-sidebar-header">
          <div className="app-logo">
            <div className="app-logo-icon">
              <Activity className="h-5 w-5" />
            </div>
            <div className="app-logo-text">
              <span className="app-logo-name">Kothar</span>
              <span className="app-logo-version">v6.0</span>
            </div>
          </div>
        </div>

        {/* Search hint */}
        <div className="app-search-hint">
          <Search className="h-3.5 w-3.5" />
          <span>Buscar...</span>
          <kbd>⌘K</kbd>
        </div>

        {/* Navigation */}
        <nav className="app-nav">
          {navGroups.map((group, groupIndex) => (
            <div key={group.title} className="app-nav-group">
              <div className="app-nav-group-title">{group.title}</div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                const isHovered = hoveredItem === item.id;

                return (
                  <motion.button
                    key={item.id}
                    className={`app-nav-item ${isActive ? 'app-nav-item--active' : ''}`}
                    onClick={() => setActivePage(item.id)}
                    onMouseEnter={() => setHoveredItem(item.id)}
                    onMouseLeave={() => setHoveredItem(null)}
                    style={{
                      '--item-color': item.color,
                    } as React.CSSProperties}
                    whileHover={{ x: 4 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {/* Active indicator bar */}
                    {isActive && (
                      <motion.div
                        layoutId="nav-active-indicator"
                        className="app-nav-item-indicator"
                        style={{ background: item.color }}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                      />
                    )}

                    {/* Icon container */}
                    <div
                      className="app-nav-item-icon"
                      style={{
                        background: isActive ? `${item.color}20` : isHovered ? `${item.color}15` : 'transparent',
                        borderColor: isActive ? `${item.color}40` : 'transparent',
                        color: isActive ? item.color : isHovered ? item.color : '#8b8b94',
                      }}
                    >
                      <Icon className="h-4 w-4" />
                    </div>

                    {/* Content */}
                    <div className="app-nav-item-content">
                      <div className="app-nav-item-label-row">
                        <span className="app-nav-item-label">{item.label}</span>
                        {item.badge && (
                          <span
                            className="app-nav-item-badge"
                            style={{
                              background: `${item.color}25`,
                              color: item.color,
                              borderColor: `${item.color}40`,
                            }}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <span className="app-nav-item-description">{item.description}</span>
                    </div>

                    {/* Arrow */}
                    <ChevronRight
                      className={`app-nav-item-arrow ${isHovered || isActive ? 'app-nav-item-arrow--visible' : ''}`}
                      style={{ color: isActive ? item.color : undefined }}
                    />
                  </motion.button>
                );
              })}
            </div>
          ))}

          {/* Ferramentas Avançadas */}
          <div className="app-nav-group">
            <div className="app-nav-group-title">Ferramentas</div>
            <div
              className={`app-nav-item ${activePage === 'memory' ? 'app-nav-item--active' : ''}`}
              onClick={() => setActivePage('memory')}
              onMouseEnter={() => setHoveredItem('memory')}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="app-nav-item-icon" style={{ color: '#a78bfa' }}>
                <Brain className="h-4 w-4" />
              </div>
              <div className="app-nav-item-content">
                <div className="app-nav-item-label-row">
                  <span className="app-nav-item-label">Memory Inspector</span>
                </div>
                <span className="app-nav-item-description">RAG & Vault</span>
              </div>
            </div>
            <div
              className={`app-nav-item ${activePage === 'agents' ? 'app-nav-item--active' : ''}`}
              onClick={() => setActivePage('agents')}
              onMouseEnter={() => setHoveredItem('agents')}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="app-nav-item-icon" style={{ color: '#60a5fa' }}>
                <Workflow className="h-4 w-4" />
              </div>
              <div className="app-nav-item-content">
                <div className="app-nav-item-label-row">
                  <span className="app-nav-item-label">Agents</span>
                  <span className="app-nav-item-badge">20</span>
                </div>
                <span className="app-nav-item-description">Specialists</span>
              </div>
            </div>
            <div
              className={`app-nav-item ${activePage === 'datalake' ? 'app-nav-item--active' : ''}`}
              onClick={() => setActivePage('datalake')}
              onMouseEnter={() => setHoveredItem('datalake')}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="app-nav-item-icon" style={{ color: '#22d3ee' }}>
                <Database className="h-4 w-4" />
              </div>
              <div className="app-nav-item-content">
                <div className="app-nav-item-label-row">
                  <span className="app-nav-item-label">Data Lake</span>
                </div>
                <span className="app-nav-item-description">Postgres + Neo4j</span>
              </div>
            </div>
            <div
              className={`app-nav-item ${activePage === 'promptlab' ? 'app-nav-item--active' : ''}`}
              onClick={() => setActivePage('promptlab')}
              onMouseEnter={() => setHoveredItem('promptlab')}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="app-nav-item-icon" style={{ color: '#10b981' }}>
                <FlaskConical className="h-4 w-4" />
              </div>
              <div className="app-nav-item-content">
                <div className="app-nav-item-label-row">
                  <span className="app-nav-item-label">Prompt Lab</span>
                  <span className="app-nav-item-badge">A/B</span>
                </div>
                <span className="app-nav-item-description">Teste system prompts</span>
              </div>
            </div>
            <div
              className={`app-nav-item ${activePage === 'tokenusage' ? 'app-nav-item--active' : ''}`}
              onClick={() => setActivePage('tokenusage')}
              onMouseEnter={() => setHoveredItem('tokenusage')}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="app-nav-item-icon" style={{ color: '#f59e0b' }}>
                <Gauge className="h-4 w-4" />
              </div>
              <div className="app-nav-item-content">
                <div className="app-nav-item-label-row">
                  <span className="app-nav-item-label">Token Usage</span>
                  <span className="app-nav-item-badge">New</span>
                </div>
                <span className="app-nav-item-description">Cotas Claude Code</span>
              </div>
            </div>
          </div>
        </nav>

        {/* Footer com status */}
        <div className="app-sidebar-footer">
          <div className="app-status-card" onClick={handleLogout} style={{ cursor: 'pointer' }} title="Clique para sair">
            <div className="app-status-row">
              <div className="app-status-indicator">
                <span className="app-status-dot" />
                <span>Sistema Ativo (Sair)</span>
              </div>
              <span className="app-status-time">100ms</span>
            </div>
            <div className="app-status-meta">
              <Server className="h-3 w-3" />
              <span>kothar-api:8080</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="app-main">
        <AnimatePresence mode="wait">
          <motion.div
            key={activePage}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="app-page"
          >
            {activePage === 'trace' && <TracePage />}
            {activePage === 'graph' && <GraphPage />}
            {activePage === 'metrics' && <MetricsPage />}
            {activePage === 'ollama' && <OllamaChatPage />}
            {activePage === 'memory' && <MemoryInspectorPage />}
            {activePage === 'agents' && <AgentsPage />}
            {activePage === 'datalake' && <DataLakePage />}
            {activePage === 'promptlab' && <PromptLabPage />}
            {activePage === 'temperature' && <ControleDeTemperaturaPage />}
            {activePage === 'tokenusage' && <TokenUsagePage />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    minHeight: '100vh',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    backgroundColor: '#0d1117',
    color: '#c9d1d9',
  },
};

export default App;
