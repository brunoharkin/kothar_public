import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Workflow, Code, Shield, Database, Briefcase, Brain, Search, Play } from 'lucide-react';
import { agentsApi, AgentInfo } from './agents.api';
import './agents.styles.css';

const CATEGORY_ICONS = {
  engineering: Code,
  security: Shield,
  data: Database,
  business: Briefcase,
  analysis: Brain,
};

const CATEGORY_COLORS = {
  engineering: '#60a5fa',
  security: '#f87171',
  data: '#34d399',
  business: '#fbbf24',
  analysis: '#a78bfa',
};

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<AgentInfo | null>(null);

  useEffect(() => {
    agentsApi.list().then(setAgents);
  }, []);

  const filtered = agents.filter((a) => {
    const matchesCategory = filter === 'all' || a.category === filter;
    const matchesSearch =
      !search ||
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.role.toLowerCase().includes(search.toLowerCase()) ||
      a.capabilities.some((c) => c.toLowerCase().includes(search.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const categories = Array.from(new Set(agents.map((a) => a.category)));

  return (
    <div className="agents-page">
      <header className="agents-header">
        <div className="agents-title">
          <Workflow className="h-6 w-6 text-blue-400" />
          <h2>Agents</h2>
          <span className="agents-badge">{agents.length} specialists</span>
        </div>
        <div className="agents-controls">
          <div className="agents-search">
            <Search className="h-4 w-4" />
            <input
              type="text"
              placeholder="Buscar agente..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Filtros por categoria */}
      <div className="agents-filters">
        <button
          className={`agents-filter ${filter === 'all' ? 'agents-filter--active' : ''}`}
          onClick={() => setFilter('all')}
        >
          Todos ({agents.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            className={`agents-filter ${filter === cat ? 'agents-filter--active' : ''}`}
            onClick={() => setFilter(cat)}
            style={{ borderColor: filter === cat ? CATEGORY_COLORS[cat] : undefined }}
          >
            {cat} ({agents.filter((a) => a.category === cat).length})
          </button>
        ))}
      </div>

      {/* Grid de agentes */}
      <div className="agents-grid">
        {filtered.map((agent, i) => {
          const Icon = CATEGORY_ICONS[agent.category];
          const color = CATEGORY_COLORS[agent.category];
          return (
            <motion.div
              key={agent.name}
              className="agent-card"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.02 }}
              onClick={() => setSelected(agent)}
              style={{ borderLeft: `3px solid ${color}` }}
            >
              <div className="agent-card-header">
                <div className="agent-card-icon" style={{ color }}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="agent-card-name">{agent.name}</div>
                  <div className="agent-card-role">{agent.role}</div>
                </div>
              </div>
              <p className="agent-card-desc">{agent.description}</p>
              <div className="agent-card-tags">
                {agent.capabilities.slice(0, 3).map((cap) => (
                  <span key={cap} className="agent-tag">
                    {cap}
                  </span>
                ))}
                {agent.capabilities.length > 3 && (
                  <span className="agent-tag agent-tag--more">+{agent.capabilities.length - 3}</span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <p className="agents-empty">Nenhum agente encontrado com esses filtros.</p>
      )}

      {/* Modal de detalhes */}
      {selected && (
        <div className="agent-modal" onClick={() => setSelected(null)}>
          <div className="agent-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="agent-modal-header" style={{ borderLeft: `3px solid ${CATEGORY_COLORS[selected.category]}` }}>
              <div>
                <h3>{selected.role}</h3>
                <code>{selected.name}</code>
              </div>
              <button onClick={() => setSelected(null)}>✕</button>
            </div>
            <p className="agent-modal-desc">{selected.description}</p>
            <h4>Capacidades</h4>
            <ul>
              {selected.capabilities.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
            <h4>Casos de uso típicos</h4>
            <ul>
              {selected.typical_use_cases.map((u) => (
                <li key={u}>{u}</li>
              ))}
            </ul>
            <button
              className="agent-modal-test"
              onClick={async () => {
                try {
                  await agentsApi.startOrchestrator(
                    `Testar ${selected.role}: ${selected.typical_use_cases[0]}`
                  );
                  alert('Sessão de teste criada! Vá para /trace para acompanhar.');
                } catch (e: any) {
                  alert(`Erro: ${e.message}`);
                }
              }}
            >
              <Play className="h-4 w-4" /> Testar este agente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
