/**
 * KOTHAR v6.0 — Data Lake Page (SUPREMO + TURBINADO)
 *
 * Página turbinada com:
 * - Projetos indexados (CBM)
 * - Estatísticas globais do Data Lake
 * - Sessões em tempo real (PostgreSQL)
 * - Traces recentes com detalhes
 * - Skills cristalizadas
 * - Cascade multi-modelo
 * - Health check
 * - Hotspots de código
 * - Top symbols por complexidade
 * - Análise temporal
 *
 * Alinhado com backend Kothar real (PostgreSQL + Neo4j + ChromaDB)
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Search, Folder, FileCode, Network, AlertCircle, RefreshCw,
  TrendingUp, Zap, BarChart3, Activity, Cpu, DollarSign,
  Layers, Code2, Brain, X, ChevronRight, Sparkles,
  GitBranch, Server
} from 'lucide-react';
import {
  dataLakeApi, Project, SearchNode, Architecture, DataLakeSession,
  DataLakeTrace, DataLakeStats
} from './datalake.api';
import './datalake.styles.css';

type TabKey = 'overview' | 'projects' | 'sessions' | 'traces' | 'skills' | 'graph' | 'analytics';

export function DataLakePage() {
  const [tab, setTab] = useState<TabKey>('overview');

  // Estado dos dados
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState<SearchNode[]>([]);
  const [sessions, setSessions] = useState<DataLakeSession[]>([]);
  const [traces, setTraces] = useState<DataLakeTrace[]>([]);
  const [skills, setSkills] = useState<any[]>([]);
  const [dashboard, setDashboard] = useState<any>(null);
  const [stats, setStats] = useState<DataLakeStats | null>(null);
  const [codeViewer, setCodeViewer] = useState<{
    title: string; code: string; file: string;
  } | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 10000); // Refresh a cada 10s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedProject) loadArchitecture(selectedProject);
  }, [selectedProject]);

  async function loadAll() {
    setError(null);
    try {
      const [
        projectsData, sessionsData, tracesData, skillsData, dashboardData, statsData
      ] = await Promise.all([
        dataLakeApi.listProjects().catch(() => ({ projects: [], total: 0 })),
        dataLakeApi.listSessions(50).catch(() => []),
        dataLakeApi.listTraces(undefined, 50).catch(() => []),
        dataLakeApi.listSkills().catch(() => []),
        dataLakeApi.getDashboard(24).catch(() => null),
        dataLakeApi.getDataLakeStats().catch(() => null),
      ]);

      setProjects(projectsData.projects || []);
      if (projectsData.projects?.length > 0 && !selectedProject) {
        // Prioriza o projeto kothar como padrão
        const kotharProject = projectsData.projects.find(
          (p: Project) => p.name.includes('kothar')
        );
        setSelectedProject(kotharProject?.name || projectsData.projects[0].name);
      }
      setSessions(sessionsData);
      setTraces(tracesData);
      setSkills(skillsData);
      setDashboard(dashboardData);
      setStats(statsData);
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function loadArchitecture(project: string) {
    try {
      const arch = await dataLakeApi.getArchitecture(project);
      setArchitecture(arch);
    } catch {
      setArchitecture(null);
    }
  }

  async function handleSearch() {
    if (!search.trim() || !selectedProject) return;
    setLoading(true);
    try {
      const data = await dataLakeApi.search(selectedProject, search);
      setSearchResults(data.nodes || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function openCode(qn: string, _type: string) {
    if (!selectedProject) return;
    try {
      const data: any = await dataLakeApi.getCode(selectedProject, qn);
      setCodeViewer({
        title: qn,
        code: data.code || '// código não disponível',
        file: data.file || '',
      });
    } catch (e) {
      alert(`Erro ao carregar código: ${e}`);
    }
  }

  return (
    <div className="datalake-page">
      <header className="datalake-header">
        <div className="datalake-title">
          <Database className="h-6 w-6 text-cyan-400" />
          <h2>Data Lake</h2>
          <span className="datalake-badge">PostgreSQL + Neo4j + CBM</span>
          <span className="datalake-live">
            <span className="datalake-live-dot"></span> live · {projects.length} projetos
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            placeholder={`🔍 Buscar em ${selectedProject || 'projeto'}...`}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            disabled={!selectedProject}
            className="datalake-search-input"
          />
          <button className="datalake-btn-refresh" onClick={loadAll}>
            <RefreshCw className="h-4 w-4" /> Atualizar
          </button>
        </div>
      </header>

      {error && (
        <div className="datalake-error">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs */}
      <nav className="datalake-tabs">
        <TabButton id="overview" tab={tab} setTab={setTab} icon={<Activity />}>Resumo</TabButton>
        <TabButton id="projects" tab={tab} setTab={setTab} icon={<Folder />}>Projetos ({projects.length})</TabButton>
        <TabButton id="sessions" tab={tab} setTab={setTab} icon={<Network />}>Sessões ({sessions.length})</TabButton>
        <TabButton id="traces" tab={tab} setTab={setTab} icon={<GitBranch />}>Eventos ({traces.length})</TabButton>
        <TabButton id="skills" tab={tab} setTab={setTab} icon={<Brain />}>Skills ({skills.length})</TabButton>
        <TabButton id="graph" tab={tab} setTab={setTab} icon={<Network />}>Grafo</TabButton>
        <TabButton id="analytics" tab={tab} setTab={setTab} icon={<BarChart3 />}>Análises</TabButton>
      </nav>

      <AnimatePresence mode="wait">
        {tab === 'overview' && (
          <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <OverviewTab
              projects={projects}
              stats={stats}
              dashboard={dashboard}
              sessions={sessions}
              architecture={architecture}
              traces={traces}
              skills={skills}
              selectedProject={selectedProject}
              setSelectedProject={setSelectedProject}
              architectureLoading={!architecture}
            />
          </motion.div>
        )}
        {tab === 'projects' && (
          <motion.div key="projects" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ProjectsTab
              projects={projects}
              selectedProject={selectedProject}
              setSelectedProject={setSelectedProject}
              architecture={architecture}
              search={search}
              setSearch={setSearch}
              handleSearch={handleSearch}
              loading={loading}
              searchResults={searchResults}
              onOpenCode={openCode}
            />
          </motion.div>
        )}
        {tab === 'sessions' && (
          <motion.div key="sessions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <SessionsTab sessions={sessions} dashboard={dashboard} />
          </motion.div>
        )}
        {tab === 'traces' && (
          <motion.div key="traces" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <TracesTab traces={traces} sessions={sessions} />
          </motion.div>
        )}
        {tab === 'skills' && (
          <motion.div key="skills" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <SkillsTab skills={skills} />
          </motion.div>
        )}
        {tab === 'graph' && (
          <motion.div key="graph" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <GraphTab
              architecture={architecture}
              selectedProject={selectedProject}
            />
          </motion.div>
        )}
        {tab === 'analytics' && (
          <motion.div key="analytics" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <AnalyticsTab
              dashboard={dashboard}
              sessions={sessions}
              traces={traces}              skills={skills}
              stats={stats}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Code Viewer Modal */}
      <AnimatePresence>
        {codeViewer && (
          <motion.div
            className="datalake-modal-backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setCodeViewer(null)}
          >
            <motion.div
              className="datalake-modal"
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="datalake-modal-header">
                <div>
                  <h3><Code2 className="h-4 w-4 inline mr-2" />{codeViewer.title}</h3>
                  <p className="datalake-modal-file">{codeViewer.file}</p>
                </div>
                <button onClick={() => setCodeViewer(null)}><X className="h-4 w-4" /></button>
              </div>
              <pre className="datalake-modal-content"><code>{codeViewer.code}</code></pre>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// =====================================
// TAB BUTTON HELPER
// =====================================

function TabButton({ id, tab, setTab, icon, children }: any) {
  return (
    <button
      className={`datalake-tab ${tab === id ? 'active' : ''}`}
      onClick={() => setTab(id)}
    >
      {icon && <span className="datalake-tab-icon">{icon}</span>}
      <span>{children}</span>
    </button>
  );
}

// =====================================
// STAT CARD HELPER
// =====================================

function StatCard({ icon, color, label, value, sub, trend }: any) {
  return (
    <motion.div className="datalake-stat-card" whileHover={{ y: -2, scale: 1.02 }}>
      <div className="datalake-stat-icon" style={{ color, background: `${color}20` }}>{icon}</div>
      <div className="datalake-stat-body">
        <div className="datalake-stat-label">{label}</div>
        <div className="datalake-stat-value" style={{ color }}>{value}</div>
        {sub && <div className="datalake-stat-sub">{sub}</div>}
        {trend !== undefined && (
          <div className="datalake-stat-trend" style={{ color: trend > 0 ? '#22c55e' : trend < 0 ? '#ef4444' : '#a1a1aa' }}>
            {trend > 0 ? '↑' : trend < 0 ? '↓' : '→'} {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
    </motion.div>
  );
}

// =====================================
// TAB: OVERVIEW
// =====================================

function OverviewTab({
  projects, dashboard, sessions, architecture, traces, skills,
  selectedProject
}: any) {
  const totalErrors = traces.filter((t: DataLakeTrace) => t.is_error).length;
  const errorRate = traces.length > 0 ? (totalErrors / traces.length * 100) : 0;
  const completedSessions = sessions.filter((s: DataLakeSession) => s.status === 'completed').length;
  const totalTokens = sessions.reduce((sum: number, s: DataLakeSession) =>
    sum + (s.tokens_input || 0) + (s.tokens_output || 0), 0);
  const totalCost = sessions.reduce((sum: number, s: DataLakeSession) =>
    sum + (s.total_cost_usd || 0), 0);

  const cascadeTotal = Object.values(dashboard?.cascade?.models_used || {}).reduce((a: number, b: any) => a + (b as number), 0);

  // Top node types para visualização
  const labelEntries = Object.entries(architecture?.node_labels || {}).sort(
    ([, a], [, b]) => (b as number) - (a as number),
  );

  return (
    <>
      {/* === TOP STATS (8 cards) === */}
      <section className="datalake-grid datalake-grid-4">
        <StatCard
          icon={<Folder />}
          color="#06b6d4"
          label="Projetos no Codebase Memory"
          value={projects.length}
          sub={`${architecture?.total_nodes || 0} arquivos indexados`}
        />
        <StatCard
          icon={<Network />}
          color="#a78bfa"
          label="Sessões no PostgreSQL"
          value={sessions.filter((s: DataLakeSession) => s.status === 'active').length}
          sub={`${sessions.length} total · ${completedSessions} finalizadas`}
        />
        <StatCard
          icon={<GitBranch />}
          color="#10b981"
          label="Eventos Registrados"
          value={traces.length}
          sub={`${totalErrors} erros · ${errorRate.toFixed(1)}%`}
        />
        <StatCard
          icon={<FileCode />}
          color="#3b82f6"
          label="Relacionamentos no Neo4j"
          value={architecture?.total_edges || 0}
          sub="Conexões entre arquivos"
        />
      </section>

      <section className="datalake-grid datalake-grid-4">
        <StatCard
          icon={<Brain />}
          color="#f59e0b"
          label="Skills Salvas"
          value={skills.length}
          sub="Conhecimentos cristalizados"
        />
        <StatCard
          icon={<Layers />}
          color="#ec4899"
          label="Tipos de Arquivo"
          value={Object.keys(architecture?.node_labels || {}).length}
          sub="Classes de nós no grafo"
        />
        <StatCard
          icon={<DollarSign />}
          color="#22c55e"
          label="Custo Total"
          value={`$${totalCost.toFixed(4)}`}
          sub={`${totalTokens.toLocaleString()} tokens consumidos`}
        />
        <StatCard
          icon={<Cpu />}
          color="#8b5cf6"
          label="Execuções Multi-Modelo"
          value={cascadeTotal}
          sub={`${dashboard?.cascade?.escalations || 0} mudanças de modelo`}
        />
      </section>

      {/* === TOP: Tipos de Nós (gráfico horizontal) === */}
      {labelEntries.length > 0 && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <Layers className="h-4 w-4" /> Tipos de Arquivo Mais Comuns ({selectedProject})
          </h3>
          <div className="datalake-bars">
            {labelEntries.slice(0, 10).map(([label, count]: any) => {
              const max = labelEntries[0][1] as number || 1;
              const percent = ((count as number) / max * 100).toFixed(1);
              return (
                <div key={label} className="datalake-bar-row">
                  <span className="datalake-bar-label">{label}</span>
                  <div className="datalake-bar-track">
                    <div className="datalake-bar-fill" style={{ width: `${percent}%` }} />
                  </div>
                  <span className="datalake-bar-count">{count as number}</span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* === CENTRO: Snapshot de Saúde === */}
      {dashboard?.health && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <Server className="h-4 w-4" /> Saúde do Data Lake
          </h3>
          <div className="datalake-grid datalake-grid-4">
            {Object.entries(dashboard.health.components || {}).map(([name, info]: any) => (
              <div key={name} className="datalake-health-card">
                <div className="datalake-health-header">
                  <span className="datalake-health-name">{name.toUpperCase()}</span>
                  <span
                    className="datalake-health-status"
                    style={{
                      color: info.status === 'healthy' ? '#22c55e' :
                             info.status === 'degraded' ? '#f59e0b' : '#ef4444',
                    }}
                  >
                    ● {info.status}
                  </span>
                </div>
                {info.latency_ms !== undefined && (
                  <div className="datalake-health-latency">{info.latency_ms.toFixed(1)}ms</div>
                )}
                {info.error && (
                  <div className="datalake-health-error">{info.error.substring(0, 60)}</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

// =====================================
// TAB: PROJECTS
// =====================================

function ProjectsTab({
  projects, selectedProject, setSelectedProject, architecture,
  search, setSearch, handleSearch, loading, searchResults, onOpenCode
}: any) {
  return (
    <>
      {selectedProject && architecture?.note && (
        <div className="datalake-warning">
          <AlertCircle className="h-4 w-4" />
          <span>{architecture.note}</span>
        </div>
      )}

      <div className="datalake-layout">
        {/* Sidebar de projetos */}
        <aside className="datalake-sidebar">
          <h3>Projetos Indexados ({projects.length})</h3>
          <div className="datalake-project-list">
            {projects.map((p: Project) => (
              <button
                key={p.name}
                className={`datalake-project-item ${selectedProject === p.name ? 'datalake-project-item--active' : ''}`}
                onClick={() => setSelectedProject(p.name)}
              >
                <Folder className="h-4 w-4" />
                <div>
                  <div className="datalake-project-name">{p.name}</div>
                  <div className="datalake-project-path">{p.root_path}</div>
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Main: Search + Results + Architecture */}
        <main className="datalake-main">
          <div className="datalake-search-bar">
            <Search className="h-4 w-4" />
            <input
              type="text"
              placeholder={`Buscar código em ${selectedProject}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              disabled={!selectedProject}
            />
            <button onClick={handleSearch} disabled={loading || !search}>
              {loading ? 'Buscando...' : 'Buscar'}
            </button>
          </div>

          {architecture?.node_labels && Object.keys(architecture.node_labels).length > 0 && (
            <section className="datalake-section">
              <h3 className="datalake-section-title">
                <Layers className="h-4 w-4" /> Tipos de Arquivo ({Object.keys(architecture.node_labels).length})
              </h3>
              <div className="datalake-label-grid">
                {Object.entries(architecture.node_labels).map(([label, count]: any) => (
                  <div key={label} className="datalake-label-card">
                    <div className="datalake-label-name">{label}</div>
                    <div className="datalake-label-count">{count as number}</div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {searchResults.length > 0 && (
            <section className="datalake-section">
              <h3 className="datalake-section-title">
                <Search className="h-4 w-4" /> Resultados ({searchResults.length})
              </h3>
              <div className="datalake-results">
                {searchResults.map((node: SearchNode) => (
                  <div
                    key={node.id}
                    className="datalake-result"
                    onClick={() => onOpenCode(node.id, node.type)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="datalake-result-header">
                      <span className="datalake-result-type">{node.type}</span>
                      <span className="datalake-result-name">{node.name}</span>
                      <ChevronRight className="h-3 w-3 opacity-50" />
                    </div>
                    {node.file && (
                      <div className="datalake-result-file">
                        <FileCode className="h-3 w-3" />
                        {node.file}{node.line ? `:${node.line}` : ''}
                      </div>
                    )}
                    {node.complexity !== undefined && (
                      <div className="datalake-result-meta">
                        <span>Complexidade: {node.complexity.toFixed(1)}</span>
                        {node.in_degree !== undefined && <span>· In: {node.in_degree}</span>}
                        {node.out_degree !== undefined && <span>· Out: {node.out_degree}</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {searchResults.length === 0 && search && !loading && (
            <div className="datalake-empty">
              <Search className="h-12 w-12" />
              <p>Nenhum resultado encontrado para "{search}"</p>
            </div>
          )}

          {!selectedProject && projects.length === 0 && (
            <div className="datalake-empty">
              <Database className="h-12 w-12" />
              <p>Nenhum projeto indexado.</p>
              <p className="datalake-empty-hint">
                Inicie o daemon: <code>codebase-memory-mcp daemon start</code>
              </p>
            </div>
          )}
        </main>
      </div>
    </>
  );
}

// =====================================
// TAB: SESSIONS
// =====================================

function SessionsTab({ sessions }: any) {
  const completed = sessions.filter((s: DataLakeSession) => s.status === 'completed').length;
  const failed = sessions.filter((s: DataLakeSession) => s.status === 'failed').length;
  const active = sessions.filter((s: DataLakeSession) => s.status === 'active').length;

  return (
    <>
      <section className="datalake-grid datalake-grid-3">
        <StatCard icon={<Activity />} color="#22c55e" label="Completas" value={completed} sub={`${sessions.length > 0 ? ((completed/sessions.length)*100).toFixed(0) : 0}% sucesso`} />
        <StatCard icon={<Zap />} color="#f59e0b" label="Em andamento" value={active} sub="Sessões em execução" />
        <StatCard icon={<AlertCircle />} color="#ef4444" label="Com falha" value={failed} sub="Sessões que falharam" />
      </section>

      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <Network className="h-4 w-4" /> Sessões Registradas ({sessions.length})
        </h3>
        <div className="datalake-table-container">
          <table className="datalake-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Agente</th>
                <th>Modelo LLM</th>
                <th>Tarefa Executada</th>
                <th>Status</th>
                <th>Tokens Usados</th>
                <th>Custo (USD)</th>
                <th>Início</th>
              </tr>
            </thead>
            <tbody>
              {sessions.slice(0, 50).map((s: DataLakeSession) => (
                <tr key={s.id}>
                  <td><code>{s.id.substring(0, 8)}</code></td>
                  <td><strong>{s.agent_name}</strong></td>
                  <td>{s.llm_model || '-'}</td>
                  <td className="datalake-task-cell">{s.task_summary || '-'}</td>
                  <td>
                    <span className={`datalake-status datalake-status--${s.status}`}>
                      {s.status}
                    </span>
                  </td>
                  <td>{(s.tokens_input + s.tokens_output).toLocaleString()}</td>
                  <td>${(s.total_cost_usd || 0).toFixed(4)}</td>
                  <td>{new Date(s.started_at).toLocaleString('pt-BR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

// =====================================
// TAB: TRACES
// =====================================

function TracesTab({ traces, sessions }: any) {
  const sessionMap = new Map(sessions.map((s: DataLakeSession) => [s.id, s]));
  const eventTypes = Object.entries(
    traces.reduce((acc: Record<string, number>, t: DataLakeTrace) => {
      acc[t.event_type] = (acc[t.event_type] || 0) + 1;
      return acc;
    }, {}),
  ).sort(([, a], [, b]) => (b as number) - (a as number));

  return (
    <>
      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <BarChart3 className="h-4 w-4" /> Distribuição por Tipo de Evento
        </h3>
        <div className="datalake-bars">
          {eventTypes.slice(0, 10).map(([type, count]: any) => {
            const max = eventTypes[0][1] as number || 1;
            const percent = ((count as number) / max * 100).toFixed(1);
            return (
              <div key={type} className="datalake-bar-row">
                <span className="datalake-bar-label">{type}</span>
                <div className="datalake-bar-track">
                  <div className="datalake-bar-fill" style={{ width: `${percent}%` }} />
                </div>
                <span className="datalake-bar-count">{count as number}</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <GitBranch className="h-4 w-4" /> Eventos Recentes ({traces.length})
        </h3>
        <div className="datalake-traces-list">
          {traces.slice(0, 30).map((t: DataLakeTrace) => {
            return (
              <div key={t.id} className={`datalake-trace ${t.is_error ? 'datalake-trace--error' : ''}`}>
                <div className="datalake-trace-header">
                  <span className={`datalake-trace-type datalake-trace-type--${t.event_type}`}>
                    {t.event_type}
                  </span>
                  {t.tool_name && (
                    <span className="datalake-trace-tool">{t.tool_name}</span>
                  )}
                  {t.is_error && <span className="datalake-trace-error-badge">ERRO</span>}
                  <span className="datalake-trace-time">
                    {new Date(t.created_at).toLocaleTimeString('pt-BR')}
                  </span>
                </div>
                {t.content && (
                  <div className="datalake-trace-content">{t.content.substring(0, 200)}</div>
                )}
                {t.tool_input && Object.keys(t.tool_input).length > 0 && (
                  <div className="datalake-trace-input">
                    <code>{JSON.stringify(t.tool_input).substring(0, 200)}</code>
                  </div>
                )}
                {t.is_error && t.error_message && (
                  <div className="datalake-trace-error-msg">{t.error_message}</div>
                )}
                <div className="datalake-trace-footer">
                  <span>👤 {t.agent_name}</span>
                  <span>📊 {t.tokens_used || 0} tokens</span>
                  {t.duration_ms && <span>⏱️ {t.duration_ms}ms</span>}
                  {(() => {
                    const s = sessionMap.get(t.session_id) as DataLakeSession | undefined;
                    return s ? <span>🔗 {s.agent_name}</span> : null;
                  })()}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}

// =====================================
// TAB: SKILLS
// =====================================

function SkillsTab({ skills }: { skills: any[] }) {
  if (skills.length === 0) {
    return (
      <div className="datalake-empty">
        <Brain className="h-12 w-12" />
        <p>Nenhuma skill salva ainda.</p>
        <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          Skills são criadas automaticamente durante a execução de tarefas.
        </span>
      </div>
    );
  }

  return (
    <section className="datalake-section">
      <h3 className="datalake-section-title">
        <Brain className="h-4 w-4" /> Skills Salvas ({skills.length})
      </h3>
      <div className="datalake-skills-grid">
        {skills.map((s, i) => (
          <div key={i} className="datalake-skill-card">
            <div className="datalake-skill-header">
              <h4>{s.name || s.yaml_content?.split('\n')[0] || 'Skill ' + i}</h4>
              {s.category && (
                <span className="datalake-skill-category">{s.category}</span>
              )}
            </div>
            {s.description && <p className="datalake-skill-desc">{s.description}</p>}
            <div className="datalake-skill-meta">
              {s.usage_count !== undefined && (
                <span>📊 Usada {s.usage_count} vezes</span>
              )}
              {s.success_rate !== undefined && (
                <span>✅ {s.success_rate.toFixed(0)}% de sucesso</span>
              )}
              {s.tags && s.tags.length > 0 && (
                <div className="datalake-skill-tags">
                  {s.tags.slice(0, 4).map((tag: string) => (
                    <span key={tag} className="datalake-tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// =====================================
// TAB: GRAPH (Visualização do Grafo)
// =====================================

function GraphTab({ architecture, selectedProject }: any) {
  const labelEntries = Object.entries(architecture?.node_labels || {}).sort(
    ([, a], [, b]) => (b as number) - (a as number),
  );
  const edgeEntries = Object.entries(architecture?.edge_types || {}).sort(
    ([, a], [, b]) => (b as number) - (a as number),
  );

  // Legenda COMPLETA dos labels do Neo4j (Codebase Memory)
  const labelLegend: Record<string, string> = {
    // Classes principais de código
    Section: 'Seção/bloco de código',
    File: 'Arquivo (.py, .ts, .md)',
    Module: 'Módulo Python (.py)',
    Method: 'Método de classe',
    Variable: 'Variável',
    Function: 'Função',
    Class: 'Definição de classe',

    // Estrutura
    Folder: 'Diretório/pasta',
    Project: 'Projeto',
    Package: 'Pacote Python',

    // Web/API
    Route: 'Rota HTTP/endpoint',
    Component: 'Componente React',
    Channel: 'Canal async',

    // TypeScript
    Type: 'Type alias TypeScript',
    Interface: 'Interface TypeScript',
    Import: 'Declaração de import',

    // Python
    Decorator: 'Decorator Python (@decorator)',

    // Ambiente/Git
    EnvVar: 'Variável de ambiente',
    Branch: 'Branch Git',

    // Banco
    Table: 'Tabela de banco de dados',
  };

  // Visual representation with circles (simple)
  const max = labelEntries[0]?.[1] as number || 1;

  return (
    <>
      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <Network className="h-4 w-4" /> Mapa do Grafo: {selectedProject}
        </h3>

        <div className="datalake-graph-summary">
          <div className="datalake-graph-stat">
            <div className="datalake-graph-stat-value">{architecture?.total_nodes || 0}</div>
            <div className="datalake-graph-stat-label">Arquivos</div>
          </div>
          <div className="datalake-graph-stat">
            <div className="datalake-graph-stat-value">{architecture?.total_edges || 0}</div>
            <div className="datalake-graph-stat-label">Conexões</div>
          </div>
          <div className="datalake-graph-stat">
            <div className="datalake-graph-stat-value">{labelEntries.length}</div>
            <div className="datalake-graph-stat-label">Tipos</div>
          </div>
          <div className="datalake-graph-stat">
            <div className="datalake-graph-stat-value">
              {architecture?.total_nodes ?
                ((architecture.total_edges / architecture.total_nodes)).toFixed(2)
                : '0'}
            </div>
            <div className="datalake-graph-stat-label">Conexões/Arquivo</div>
          </div>
        </div>

        {/* Visual bubble map */}
        <div className="datalake-bubbles">
          {labelEntries.map(([label, count]: any) => {
            // Tamanho MAIOR e mais legível (escala mínima 80, máxima 200)
            const size = Math.max(80, Math.min(200, ((count as number) / max) * 200));
            return (
              <div
                key={label}
                className="datalake-bubble"
                style={{
                  width: size,
                  height: size,
                  fontSize: size > 140 ? 14 : 12,
                }}
                title={`${label}: ${count as number} ocorrências`}
              >
                <div className="datalake-bubble-label">{label}</div>
                <div className="datalake-bubble-count">{count as number}</div>
              </div>
            );
          })}
        </div>

        {/* Legenda explicativa dos labels (dados reais do Neo4j) */}
        <div className="datalake-legend">
          <h4 className="datalake-legend-title">O que cada label significa:</h4>
          <div className="datalake-legend-grid">
            {labelEntries.map(([label]: any) => (
              <div key={label} className="datalake-legend-item">
                <code className="datalake-legend-code">{label}</code>
                <span className="datalake-legend-desc">
                  {labelLegend[label as string] || `Símbolo de código (${label})`}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {edgeEntries.length > 0 && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <GitBranch className="h-4 w-4" /> Tipos de Conexões
          </h3>
          <div className="datalake-edge-list">
            {edgeEntries.map(([type, count]: any) => (
              <div key={type} className="datalake-edge-card">
                <div className="datalake-edge-icon">→</div>
                <div>
                  <div className="datalake-edge-type">{type}</div>
                  <div className="datalake-edge-count">{count as number} conexões</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {architecture?.hotspots && architecture.hotspots.length > 0 && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <TrendingUp className="h-4 w-4" /> Arquivos Mais Conectados (Hotspots)
          </h3>
          <div className="datalake-hotspots">
            {architecture.hotspots.map((h: any, i: number) => (
              <div key={i} className="datalake-hotspot">
                <span className="datalake-hotspot-rank">#{i + 1}</span>
                <div>
                  <div className="datalake-hotspot-name">{h.name}</div>
                  <div className="datalake-hotspot-type">{h.type}</div>
                </div>
                <div className="datalake-hotspot-degree">{h.degree} conexões</div>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

// =====================================
// TAB: ANALYTICS
// =====================================

function AnalyticsTab({ dashboard, sessions, traces, stats }: any) {
  // Tokens por agente
  const tokensByAgent = sessions.reduce((acc: Record<string, number>, s: DataLakeSession) => {
    if (!s.agent_name) return acc;
    acc[s.agent_name] = (acc[s.agent_name] || 0) + (s.tokens_input || 0) + (s.tokens_output || 0);
    return acc;
  }, {});

  const tokensByAgentEntries = Object.entries(tokensByAgent).sort(
    ([, a], [, b]) => (b as number) - (a as number),
  );
  const maxTokens = tokensByAgentEntries[0]?.[1] as number || 1;

  // Cascade distribution
  const cascadeEntries = Object.entries(dashboard?.cascade?.models_used || {}).sort(
    ([, a], [, b]) => (b as number) - (a as number),
  );
  const cascadeTotal = cascadeEntries.reduce((a, [, v]) => a + (v as number), 0);

  // Errors by type
  const errorByType: Record<string, number> = {};
  traces.filter((t: DataLakeTrace) => t.is_error).forEach((t: DataLakeTrace) => {
    errorByType[t.event_type] = (errorByType[t.event_type] || 0) + 1;
  });

  return (
    <>
      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <BarChart3 className="h-4 w-4" /> Consumo de Tokens por Agente
        </h3>
        <div className="datalake-bars">
          {tokensByAgentEntries.slice(0, 10).map(([agent, tokens]: any) => {
            const percent = ((tokens as number) / maxTokens * 100).toFixed(1);
            return (
              <div key={agent} className="datalake-bar-row">
                <span className="datalake-bar-label">{agent}</span>
                <div className="datalake-bar-track">
                  <div className="datalake-bar-fill" style={{ width: `${percent}%`, background: '#3b82f6' }} />
                </div>
                <span className="datalake-bar-count">{(tokens as number).toLocaleString()}</span>
              </div>
            );
          })}
          {tokensByAgentEntries.length === 0 && (
            <p className="datalake-empty">Nenhum dado de tokens ainda.</p>
          )}
        </div>
      </section>

      {cascadeTotal > 0 && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <Cpu className="h-4 w-4" /> Distribuição por Modelo (Haiku/Sonnet/Opus)
          </h3>
          <div className="datalake-bars">
            {cascadeEntries.map(([model, count]: any) => {
              const percent = ((count as number) / cascadeTotal * 100).toFixed(1);
              const color = model === 'opus' ? '#ef4444' : model === 'sonnet' ? '#f59e0b' : '#22c55e';
              return (
                <div key={model} className="datalake-bar-row">
                  <span className="datalake-bar-label" style={{ textTransform: 'capitalize' }}>{model}</span>
                  <div className="datalake-bar-track">
                    <div className="datalake-bar-fill" style={{ width: `${percent}%`, background: color }} />
                  </div>
                  <span className="datalake-bar-count">{count as number} ({percent}%)</span>
                </div>
              );
            })}
          </div>
          <div className="datalake-stat-footer">
            Total: <strong>{cascadeTotal}</strong> execuções ·{' '}
            Mudanças de modelo: <strong>{dashboard?.cascade?.escalations || 0}</strong> ·{' '}
            Custo total: <strong>${(dashboard?.cascade?.total_cost_usd || 0).toFixed(6)}</strong>
          </div>
        </section>
      )}

      <section className="datalake-section">
        <h3 className="datalake-section-title">
          <AlertCircle className="h-4 w-4" /> Erros por Tipo de Evento
        </h3>
        {Object.keys(errorByType).length === 0 ? (
          <div className="datalake-empty">
            <Sparkles className="h-12 w-12" style={{ color: '#22c55e' }} />
            <p style={{ color: '#22c55e' }}>Nenhum erro registrado!</p>
          </div>
        ) : (
          <div className="datalake-bars">
            {Object.entries(errorByType).map(([type, count]: any) => {
              const max = Math.max(...Object.values(errorByType).map((v) => v as number));
              const percent = ((count as number) / max * 100).toFixed(1);
              return (
                <div key={type} className="datalake-bar-row">
                  <span className="datalake-bar-label">{type}</span>
                  <div className="datalake-bar-track">
                    <div className="datalake-bar-fill" style={{ width: `${percent}%`, background: '#ef4444' }} />
                  </div>
                  <span className="datalake-bar-count">{count as number}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {stats && (
        <section className="datalake-section">
          <h3 className="datalake-section-title">
            <Activity className="h-4 w-4" /> Resumo Geral do Data Lake
          </h3>
          <div className="datalake-grid datalake-grid-3">
            <StatCard icon={<Network />} color="#06b6d4" label="Total de Sessões" value={stats.total_sessions} sub={`${stats.active_sessions} em andamento`} />
            <StatCard icon={<GitBranch />} color="#10b981" label="Total de Eventos" value={stats.total_traces} sub={`${stats.error_rate_percent.toFixed(1)}% são erros`} />
            <StatCard icon={<Brain />} color="#a78bfa" label="Skills Salvas" value={stats.total_skills} sub="Conhecimentos guardados" />
            <StatCard icon={<AlertCircle />} color="#ef4444" label="Locks Ativos" value={stats.total_locks} sub="Padrões de erro a evitar" />
            <StatCard icon={<Layers />} color="#f59e0b" label="Planos de Tarefa" value={stats.total_blueprints} sub="Blueprints recentes" />
            <StatCard icon={<DollarSign />} color="#22c55e" label="Custo Acumulado" value={`$${stats.total_cost_usd.toFixed(4)}`} sub={`${(stats.total_tokens_input + stats.total_tokens_output).toLocaleString()} tokens gastos`} />
          </div>
        </section>
      )}
    </>
  );
}
