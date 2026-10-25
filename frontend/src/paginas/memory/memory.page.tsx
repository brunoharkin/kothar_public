/**
 * KOTHAR v6.0 — Memory Inspector Page (ALINHADO COM SISTEMA REAL)
 * Lê dados reais dos endpoints do Kothar:
 * - /api/rag-metrics/rag/json (métricas RAG)
 * - /api/rag-tracker/* (queries recentes)
 * - /api/inspector/vault/* (Cofre)
 * - /api/inspector/chromadb/* (ChromaDB)
 * - /api/inspector/rag/analysis (Análise)
 * - /api/dashboard (métricas operacionais integradas)
 */

import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, Database, FileText, Activity, AlertCircle, RefreshCw, Sparkles,
  Clock, Zap, FolderTree, Search, BarChart3, Network, TrendingUp,
  Eye, X, Layers, Hash, Cpu, DollarSign, Activity as Pulse
} from 'lucide-react';
import {
  memoryApi,
  RAGQuery,
  RAGSession,
  RAGGlobalStats,
  VaultStats,
  ChromaCollection,
  RAGAnalysis,
  VaultCategory,
  VaultFile,
  DashboardData,
} from './memory.api';
import './memory.styles.css';

type TabKey = 'overview' | 'vault' | 'chromadb' | 'sessions' | 'analysis' | 'operations';

export function MemoryInspectorPage() {
  const [tab, setTab] = useState<TabKey>('overview');

  // Dados de RAG (Prometheus)
  const [metrics, setMetrics] = useState<any>(null);

  // Dados do RAG Tracker (tempo real)
  const [globalStats, setGlobalStats] = useState<RAGGlobalStats | null>(null);
  const [recentQueries, setRecentQueries] = useState<RAGQuery[]>([]);

  // Dados do Vault
  const [vaultStats, setVaultStats] = useState<VaultStats | null>(null);

  // Dados do ChromaDB
  const [chromaCollections, setChromaCollections] = useState<ChromaCollection[]>([]);

  // Análise RAG
  const [ragAnalysis, setRagAnalysis] = useState<RAGAnalysis | null>(null);

  // Sessions ativas (do orquestrador)
  const [activeSessions, setActiveSessions] = useState<RAGSession[]>([]);

  // Dashboard integrado
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [fileViewer, setFileViewer] = useState<{
    path: string; content: string; name: string; lines: number;
  } | null>(null);
  const [chromaSample, setChromaSample] = useState<{
    name: string; docs: any[]; total: number;
  } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 5000);
    return () => clearInterval(interval);
  }, []);

  async function loadAll() {
    setError(null);
    try {
      // Carrega tudo em paralelo (9 chamadas)
      const [
        m, stats, recent, vault,
        chroma, analysis, activeSess, dash
      ] = await Promise.all([
        memoryApi.getRAGMetrics().catch(() => null),
        memoryApi.getGlobalStats().catch(() => null),
        memoryApi.getRecentRAGQueries(15).catch(() => ({ queries: [] })),
        memoryApi.getVaultStats().catch(() => null),
        memoryApi.getChromaCollections().catch(() => ({ collections: [], total_collections: 0, total_documents: 0 })),
        memoryApi.getRAGAnalysis().catch(() => null),
        memoryApi.getOrchestrateActiveSessions().catch(() => []),
        memoryApi.getDashboard(24).catch(() => null),
      ]);

      setMetrics(m);
      setGlobalStats(stats);
      setRecentQueries((recent as any)?.queries || []);
      setVaultStats(vault);
      setChromaCollections((chroma as any)?.collections || []);
      setRagAnalysis(analysis);
      // activeSess pode ser array direto OU objeto com sessions
      const sessArray = Array.isArray(activeSess)
        ? activeSess
        : ((activeSess as any)?.sessions || []);
      setActiveSessions(sessArray);
      setDashboard(dash);
    } catch (e: any) {
      setError(e.message || 'Erro ao carregar');
    } finally {
      setLoading(false);
    }
  }

  async function openFile(path: string) {
    try {
      const data = await memoryApi.readVaultFile(path, 100);
      if (data.error) {
        alert(`Erro: ${data.error}`);
        return;
      }
      setFileViewer({
        path: data.path,
        content: data.content,
        name: data.name,
        lines: data.total_lines,
      });
    } catch (e: any) {
      alert(`Erro ao ler: ${e.message}`);
    }
  }

  async function openChromaSample(name: string) {
    try {
      const data = await memoryApi.getChromaSample(name, 5);
      if (data.error) {
        alert(`Erro: ${data.error}`);
        return;
      }
      setChromaSample({ name, docs: data.sample, total: data.total });
    } catch (e: any) {
      alert(`Erro ao ler Chroma: ${e.message}`);
    }
  }

  // Filtragem
  const filteredQueries = useMemo(() => {
    if (!searchQuery) return recentQueries;
    const q = searchQuery.toLowerCase();
    return recentQueries.filter(
      (qq) => qq.query?.toLowerCase().includes(q) ||
        qq.sources?.some((s) => s?.toLowerCase().includes(q))
    );
  }, [recentQueries, searchQuery]);

  const filteredCollections = useMemo(() => {
    if (!searchQuery) return chromaCollections;
    const q = searchQuery.toLowerCase();
    return chromaCollections.filter(
      (c) => c.name?.toLowerCase().includes(q) ||
        (c.categories || []).some((cat) => cat?.toLowerCase().includes(q))
    );
  }, [chromaCollections, searchQuery]);

  if (loading && !metrics && !dashboard) {
    return (
      <div className="memory-page">
        <div className="memory-loading">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <p>Mapeando memória do sistema...</p>
        </div>
      </div>
    );
  }

  // ===== Variáveis derivadas dos dados REAIS =====
  // Métricas RAG (Prometheus)
  const hitRate = (metrics?.hit_rate_percent ?? 0) / 100;
  const total = metrics?.total_requests ?? 0;
  const hits = metrics?.total_hits ?? 0;
  const misses = metrics?.total_misses ?? 0;
  const cacheHits = metrics?.cache_hits ?? 0;

  // RAG Tracker (tempo real)
  const trackerTotal = globalStats?.total_queries ?? 0;
  const trackerHits = globalStats?.total_hits ?? 0;
  const trackerMisses = globalStats?.total_misses ?? 0;
  const trackerHitRate = globalStats?.hit_rate ?? 0;
  const activeRAGSessions = globalStats?.active_sessions ?? 0;

  return (
    <div className="memory-page">
      <header className="memory-header">
        <div className="memory-title">
          <Brain className="h-6 w-6 text-purple-400" />
          <h2>Memory Inspector</h2>
          <span className="memory-badge">RAG & Vault</span>
          <span className="memory-live-badge">
            <span className="memory-live-dot"></span> live · {activeRAGSessions} sessões RAG
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input
            type="text"
            placeholder="🔍 Buscar..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="memory-search"
          />
          <button className="memory-btn-refresh" onClick={loadAll}>
            <RefreshCw className="h-4 w-4" /> Atualizar
          </button>
        </div>
      </header>

      {error && (
        <div className="memory-error">
          <AlertCircle className="h-5 w-5" />
          <p>{error}</p>
        </div>
      )}

      {/* Tabs */}
      <nav className="memory-tabs">
        <button className={`memory-tab ${tab === 'overview' ? 'active' : ''}`} onClick={() => setTab('overview')}>
          <Activity className="h-4 w-4" /> Visão Geral
        </button>
        <button className={`memory-tab ${tab === 'vault' ? 'active' : ''}`} onClick={() => setTab('vault')}>
          <FolderTree className="h-4 w-4" /> Cofre ({vaultStats?.total_files ?? 0})
        </button>
        <button className={`memory-tab ${tab === 'chromadb' ? 'active' : ''}`} onClick={() => setTab('chromadb')}>
          <Database className="h-4 w-4" /> ChromaDB ({chromaCollections.length})
        </button>
        <button className={`memory-tab ${tab === 'sessions' ? 'active' : ''}`} onClick={() => setTab('sessions')}>
          <Network className="h-4 w-4" /> Sessões ({activeSessions.length})
        </button>
        <button className={`memory-tab ${tab === 'analysis' ? 'active' : ''}`} onClick={() => setTab('analysis')}>
          <BarChart3 className="h-4 w-4" /> Análise
        </button>
        <button className={`memory-tab ${tab === 'operations' ? 'active' : ''}`} onClick={() => setTab('operations')}>
          <Cpu className="h-4 w-4" /> Operações
        </button>
      </nav>

      <AnimatePresence mode="wait">
        {tab === 'overview' && (
          <motion.div key="overview" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <OverviewTab
              metrics={metrics}
              globalStats={globalStats}
              hitRate={hitRate} total={total} hits={hits} misses={misses} cacheHits={cacheHits}
              trackerTotal={trackerTotal} trackerHits={trackerHits}
              trackerMisses={trackerMisses} trackerHitRate={trackerHitRate}
              recentQueries={filteredQueries}
              vaultStats={vaultStats}
              chromaCollections={chromaCollections}
              dashboard={dashboard}
            />
          </motion.div>
        )}
        {tab === 'vault' && (
          <motion.div key="vault" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <VaultTab
              vaultStats={vaultStats}
              onOpenFile={openFile}
            />
          </motion.div>
        )}
        {tab === 'chromadb' && (
          <motion.div key="chromadb" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ChromaDBTab
              collections={filteredCollections}
              totalDocs={chromaCollections.reduce((s, c) => s + (c.count || 0), 0)}
              onOpenSample={openChromaSample}
            />
          </motion.div>
        )}
        {tab === 'sessions' && (
          <motion.div key="sessions" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <SessionsTab sessions={activeSessions} />
          </motion.div>
        )}
        {tab === 'analysis' && (
          <motion.div key="analysis" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <AnalysisTab analysis={ragAnalysis} />
          </motion.div>
        )}
        {tab === 'operations' && (
          <motion.div key="operations" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <OperationsTab dashboard={dashboard} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* File Viewer Modal */}
      <AnimatePresence>
        {fileViewer && (
          <motion.div
            className="memory-modal-backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setFileViewer(null)}
          >
            <motion.div
              className="memory-modal"
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="memory-modal-header">
                <div>
                  <h3><FileText className="h-4 w-4 inline mr-2" />{fileViewer.name}</h3>
                  <p className="memory-modal-path">{fileViewer.path}</p>
                  <p className="memory-modal-meta">{fileViewer.lines} linhas</p>
                </div>
                <button onClick={() => setFileViewer(null)}><X className="h-4 w-4" /></button>
              </div>
              <pre className="memory-modal-content"><code>{fileViewer.content}</code></pre>
            </motion.div>
          </motion.div>
        )}
        {chromaSample && (
          <motion.div
            className="memory-modal-backdrop"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setChromaSample(null)}
          >
            <motion.div
              className="memory-modal"
              initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="memory-modal-header">
                <div>
                  <h3><Database className="h-4 w-4 inline mr-2" />{chromaSample.name}</h3>
                  <p className="memory-modal-path">Sample de {chromaSample.docs.length} docs (total: {chromaSample.total})</p>
                </div>
                <button onClick={() => setChromaSample(null)}><X className="h-4 w-4" /></button>
              </div>
              <div className="memory-modal-list">
                {chromaSample.docs.map((doc: any, i: number) => (
                  <div key={i} className="memory-chroma-doc">
                    <div className="memory-chroma-doc-header">
                      <code className="memory-chroma-doc-id">{doc.id}</code>
                      <span className="memory-chroma-doc-len">{doc.content_length} chars</span>
                    </div>
                    {doc.metadata && (
                      <div className="memory-chroma-doc-meta">
                        {Object.entries(doc.metadata).slice(0, 4).map(([k, v]) => (
                          <span key={k} className="memory-meta-chip">
                            <strong>{k}:</strong> {String(v).slice(0, 50)}
                          </span>
                        ))}
                      </div>
                    )}
                    <pre className="memory-chroma-doc-content">{doc.content_preview}</pre>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// =====================================
// SUB-COMPONENTES POR ABA
// =====================================

function OverviewTab({
  metrics, globalStats,
  hitRate, total, hits, misses, cacheHits,
  trackerTotal, trackerHits, trackerMisses, trackerHitRate,
  recentQueries, chromaCollections, dashboard,
}: any) {
  return (
    <>
      {/* === CARD 1: Métricas RAG Prometheus === */}
      <section className="memory-section">
        <h3 className="memory-section-title">
          <Zap className="h-4 w-4" /> RAG Prometheus (Acumulado desde boot)
        </h3>
        <div className="memory-grid memory-grid-4">
          <StatCard
            icon={<Activity />}
            color="#a78bfa"
            label="Hit Rate"
            value={`${(hitRate * 100).toFixed(1)}%`}
            sub={`${hits} hits / ${misses} misses`}
          />
          <StatCard
            icon={<BarChart3 />}
            color="#34d399"
            label="Total Requests"
            value={total}
            sub="Queries totais"
          />
          <StatCard
            icon={<Sparkles />}
            color="#fbbf24"
            label="Cache Hits"
            value={cacheHits}
            sub="Hits via cache"
          />
          <StatCard
            icon={<Database />}
            color="#60a5fa"
            label="Docs Indexados"
            value={chromaCollections.reduce((s: number, c: any) => s + (c.count || 0), 0)}
            sub={`${chromaCollections.length} collections`}
          />
        </div>
      </section>

      {/* === CARD 2: RAG Tracker (tempo real) === */}
      <section className="memory-section">
        <h3 className="memory-section-title">
          <TrendingUp className="h-4 w-4" /> RAG Tracker (Tempo Real)
        </h3>
        <div className="memory-grid memory-grid-3">
          <StatCard
            icon={<BarChart3 />}
            color="#10b981"
            label="Queries (Tracker)"
            value={trackerTotal}
            sub={`${trackerHits} hits / ${trackerMisses} misses`}
          />
          <StatCard
            icon={<TrendingUp />}
            color="#22d3ee"
            label="Hit Rate Real"
            value={`${(trackerHitRate * 100).toFixed(1)}%`}
            sub={`${globalStats?.total_chunks_retrieved ?? 0} chunks injetados`}
          />
          <StatCard
            icon={<Network />}
            color="#f472b6"
            label="Sessões Ativas"
            value={globalStats?.active_sessions ?? 0}
            sub="com RAG ativo"
          />
        </div>
      </section>

      {/* === CARD 3: Por Tipo de Query === */}
      {metrics?.hits_by_type && Object.keys(metrics.hits_by_type).length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title">
            <BarChart3 className="h-4 w-4" /> Por Tipo de Query (Prometheus)
          </h3>
          <div className="memory-by-type">
            {Object.entries(metrics.hits_by_type).map(([type, hitCount]: any) => {
              const missCount = metrics.misses_by_type?.[type] || 0;
              const t = hitCount + missCount;
              const rate = t > 0 ? hitCount / t : 0;
              return (
                <div key={type} className="memory-by-type-row">
                  <span className="memory-by-type-label">{type}</span>
                  <div className="memory-by-type-bar">
                    <div
                      className="memory-by-type-fill"
                      style={{ width: `${rate * 100}%` }}
                    />
                  </div>
                  <span className="memory-by-type-value">{(rate * 100).toFixed(0)}%</span>
                  <span className="memory-by-type-count">({hitCount}/{t})</span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* === CARD 4: Queries recentes === */}
      <section className="memory-section">
        <div className="memory-section-header">
          <h3 className="memory-section-title">
            <Activity className="h-4 w-4" /> Últimas Queries RAG
          </h3>
          <span className="memory-count">{recentQueries.length} queries</span>
        </div>
        <div className="memory-queries">
          {recentQueries.length === 0 ? (
            <p className="memory-empty">
              Nenhuma query registrada ainda. Use o chat para gerar queries RAG.
            </p>
          ) : (
            recentQueries.map((q: RAGQuery, i: number) => {
              const ts = typeof q.timestamp === 'string'
                ? new Date(q.timestamp).toLocaleTimeString('pt-BR')
                : new Date((q.timestamp || 0) * 1000).toLocaleTimeString('pt-BR');
              return (
                <div key={i} className="memory-query-row">
                  <div className="memory-query-time">{ts}</div>
                  <div className="memory-query-text">
                    <span className={`memory-query-badge ${q.is_hit ? 'hit' : 'miss'}`}>
                      {q.is_hit ? `✓ ${q.chunks_count} chunks` : '✗ miss'}
                    </span>
                    <div className="memory-query-q">{q.query}</div>
                  </div>
                  {q.sources && q.sources.length > 0 && (
                    <div className="memory-query-sources">
                      {q.sources.slice(0, 5).map((s, j) => (
                        <span key={j} className="memory-source-chip">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </section>

      {/* === CARD 5: Operations Snapshot === */}
      {dashboard && (
        <section className="memory-section">
          <h3 className="memory-section-title">
            <Cpu className="h-4 w-4" /> Snapshot Operacional (24h)
          </h3>
          <div className="memory-grid memory-grid-4">
            <StatCard
              icon={<Clock />}
              color="#8b5cf6"
              label="Avg Latency"
              value={`${dashboard.avg_latency_ms?.toFixed(1) ?? 0}ms`}
              sub="Latência média"
            />
            <StatCard
              icon={<TrendingUp />}
              color="#f59e0b"
              label="Throughput"
              value={`${dashboard.throughput_per_min?.toFixed(1) ?? 0}/min`}
              sub="Traces por minuto"
            />
            <StatCard
              icon={<DollarSign />}
              color="#22c55e"
              label="Custo Total"
              value={`$${(dashboard.token_usage?.total_cost_usd ?? 0).toFixed(4)}`}
              sub={`${dashboard.token_usage?.total ?? 0} tokens`}
            />
            <StatCard
              icon={<Pulse />}
              color={dashboard.success_rate_percent > 95 ? "#22c55e" : "#ef4444"}
              label="Success Rate"
              value={`${dashboard.success_rate_percent ?? 100}%`}
              sub={`${dashboard.errors_count ?? 0} erros`}
            />
          </div>
        </section>
      )}
    </>
  );
}

function StatCard({ icon, color, label, value, sub }: any) {
  return (
    <motion.div className="memory-card" whileHover={{ y: -2 }}>
      <div className="memory-card-icon" style={{ color, background: `${color}20` }}>{icon}</div>
      <div className="memory-card-content">
        <div className="memory-card-label">{label}</div>
        <div className="memory-card-value">{value}</div>
        <div className="memory-card-sub">{sub}</div>
      </div>
    </motion.div>
  );
}

function VaultTab({ vaultStats, onOpenFile }: any) {
  if (!vaultStats) {
    return <div className="memory-empty">Carregando cofre...</div>;
  }

  const maxSize = Math.max(...vaultStats.categories.map((c: VaultCategory) => c.size_bytes || 0), 1);

  return (
    <>
      <section className="memory-grid memory-grid-4">
        <StatCard icon={<FolderTree />} color="#10b981" label="Total Arquivos" value={vaultStats.total_files} sub={`${vaultStats.total_md} markdown`} />
        <StatCard icon={<Database />} color="#3b82f6" label="Tamanho Total" value={`${(vaultStats.total_size_kb || 0).toFixed(1)} KB`} sub="Disco ocupado" />
        <StatCard icon={<Layers />} color="#a78bfa" label="Categorias" value={vaultStats.categories.length} sub="Pastas ativas" />
        <StatCard icon={<FileText />} color="#f59e0b" label="Maior Arquivo" value={
          vaultStats.top_files?.[0] ? `${vaultStats.top_files[0].size_kb} KB` : '-'
        } sub={vaultStats.top_files?.[0]?.name?.slice(0, 30) || ''} />
      </section>

      {/* Categorias com barra de tamanho */}
      <section className="memory-section">
        <h3 className="memory-section-title"><FolderTree className="h-4 w-4" /> Categorias do Cofre</h3>
        <div className="memory-vault-categories">
          {vaultStats.categories.map((cat: VaultCategory) => (
            <div key={cat.category} className="memory-vault-cat">
              <div className="memory-vault-cat-header">
                <span className="memory-vault-cat-name">{cat.category}</span>
                <span className="memory-vault-cat-stats">
                  {cat.files} arq · {cat.md_files} md · {cat.size_kb} KB
                </span>
              </div>
              <div className="memory-vault-bar">
                <div className="memory-vault-bar-fill" style={{ width: `${((cat.size_bytes || 0) / maxSize) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Top arquivos por tamanho */}
      {vaultStats.top_files?.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title"><BarChart3 className="h-4 w-4" /> Top Arquivos por Tamanho</h3>
          <div className="memory-vault-files">
            {vaultStats.top_files.map((f: VaultFile) => (
              <div key={f.path} className="memory-vault-file" onClick={() => onOpenFile(f.path)}>
                <div className="memory-vault-file-info">
                  <span className="memory-vault-file-name">{f.name}</span>
                  <span className="memory-vault-file-cat">{f.category}</span>
                </div>
                <div className="memory-vault-file-size">
                  <div className="memory-vault-file-bar">
                    <div
                      className="memory-vault-file-bar-fill"
                      style={{ width: `${((f.size_bytes || 0) / (vaultStats.top_files[0]?.size_bytes || 1)) * 100}%` }}
                    />
                  </div>
                  <span>{f.size_kb} KB</span>
                </div>
                <button className="memory-btn-icon" title="Abrir">
                  <Eye className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function ChromaDBTab({ collections, totalDocs, onOpenSample }: any) {
  if (!collections || collections.length === 0) {
    return (
      <div className="memory-empty">
        <Database className="h-8 w-8 mb-2 opacity-50" />
        <p>Nenhuma collection ChromaDB encontrada.</p>
        <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          Verifique se o ChromaDB está rodando e indexado.
        </span>
      </div>
    );
  }

  return (
    <>
      <section className="memory-grid memory-grid-3">
        <StatCard icon={<Database />} color="#3b82f6" label="Total Collections" value={collections.length} sub="No ChromaDB" />
        <StatCard icon={<FileText />} color="#10b981" label="Total Documentos" value={totalDocs} sub="Chunks indexados" />
        <StatCard icon={<TrendingUp />} color="#a78bfa" label="Média por Collection" value={Math.round(totalDocs / collections.length)} sub="Chunks" />
      </section>

      <section className="memory-section">
        <h3 className="memory-section-title"><Database className="h-4 w-4" /> Collections ChromaDB</h3>
        <div className="memory-chroma-grid">
          {collections.map((col: ChromaCollection) => (
            <motion.div
              key={col.name}
              className="memory-chroma-card"
              whileHover={{ scale: 1.01 }}
              onClick={() => onOpenSample(col.name)}
            >
              <div className="memory-chroma-card-header">
                <h4><Database className="h-4 w-4 inline mr-2" />{col.name}</h4>
                <span className="memory-chroma-count">{(col.count || 0).toLocaleString()} docs</span>
              </div>
              {col.categories && col.categories.length > 0 && (
                <div className="memory-chroma-categories">
                  {col.categories.slice(0, 6).map((c) => (
                    <span key={c} className="memory-cat-chip">{c}</span>
                  ))}
                </div>
              )}
              {col.error && (
                <p className="memory-chroma-error">⚠ {col.error}</p>
              )}
              <div className="memory-chroma-card-footer">
                <span className="memory-chroma-click">clique para ver sample →</span>
              </div>
            </motion.div>
          ))}
        </div>
      </section>
    </>
  );
}

function SessionsTab({ sessions }: { sessions: any[] }) {
  return (
    <section className="memory-section">
      <h3 className="memory-section-title">
        <Network className="h-4 w-4" /> Sessões com RAG Ativo ({sessions.length})
      </h3>
      {sessions.length === 0 ? (
        <div className="memory-empty">
          <Network className="h-8 w-8 mb-2 opacity-50" />
          <p>Nenhuma sessão com RAG no momento.</p>
          <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
            Inicie uma sessão no chat para gerar queries RAG.
          </span>
        </div>
      ) : (
        <div className="memory-sessions-list">
          {sessions.map((s: any) => (
            <div key={s.session_id} className="memory-session-card">
              <div className="memory-session-header">
                <code className="memory-session-id">
                  {s.session_id?.substring(0, 16) || 'unknown'}...
                </code>
                {s.hit_rate !== undefined && (
                  <span className={`memory-session-rate ${s.hit_rate > 0.5 ? 'high' : 'low'}`}>
                    {(s.hit_rate * 100).toFixed(0)}% hit
                  </span>
                )}
              </div>
              <div className="memory-session-stats">
                <span><Hash className="h-3 w-3" /> {s.total_queries || 0} queries</span>
                <span><FileText className="h-3 w-3" /> {s.total_chunks || 0} chunks</span>
                {s.last_active && (
                  <span>
                    <Clock className="h-3 w-3" />
                    {' '}{typeof s.last_active === 'string'
                      ? new Date(s.last_active).toLocaleTimeString('pt-BR')
                      : new Date((s.last_active || 0) * 1000).toLocaleTimeString('pt-BR')}
                  </span>
                )}
              </div>
              {s.recent_queries && s.recent_queries.length > 0 && (
                <div className="memory-session-queries">
                  {s.recent_queries.map((q: any, i: number) => (
                    <div key={i} className="memory-session-q">
                      <span className={`memory-mini-badge ${q.is_hit ? 'hit' : 'miss'}`}>
                        {q.is_hit ? '✓' : '✗'}
                      </span>
                      <span className="memory-session-q-text">{(q.query || '').slice(0, 80)}</span>
                      <span className="memory-session-q-time">
                        {typeof q.timestamp === 'string'
                          ? new Date(q.timestamp).toLocaleTimeString('pt-BR')
                          : new Date((q.timestamp || 0) * 1000).toLocaleTimeString('pt-BR')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function AnalysisTab({ analysis }: { analysis: RAGAnalysis | null }) {
  if (!analysis) {
    return (
      <div className="memory-empty">
        <BarChart3 className="h-8 w-8 mb-2 opacity-50" />
        <p>Sem dados de análise ainda.</p>
        <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          Execute queries RAG para gerar análise.
        </span>
      </div>
    );
  }

  const hasData = analysis.total_queries_analyzed > 0;
  const maxSource = analysis.top_sources?.[0]?.count ?? 1;
  const maxWord = analysis.top_keywords?.[0]?.count ?? 1;
  const histogramEntries = Object.entries(analysis.chunks_stats?.histogram || {});
  const maxBucket = Math.max(...histogramEntries.map(([, v]) => v as number), 1);
  const timeEntries = Object.entries(analysis.time_distribution || {});
  const maxTime = Math.max(...timeEntries.map(([, v]) => v as number), 1);

  if (!hasData) {
    return (
      <div className="memory-empty">
        <BarChart3 className="h-8 w-8 mb-2 opacity-50" />
        <p>0 queries analisadas ainda.</p>
        <span style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
          Aguardando atividade RAG para gerar análise estatística.
        </span>
      </div>
    );
  }

  return (
    <>
      <section className="memory-grid memory-grid-3">
        <StatCard icon={<Hash />} color="#3b82f6" label="Queries Analisadas" value={analysis.total_queries_analyzed} sub="Últimas 200" />
        <StatCard icon={<FileText />} color="#10b981" label="Chunks Médio/Query" value={analysis.chunks_stats.avg} sub={`Max: ${analysis.chunks_stats.max}`} />
        <StatCard icon={<BarChart3 />} color="#a78bfa" label="Top Source" value={analysis.top_sources?.[0]?.name?.slice(0, 20) ?? '-'} sub={`${analysis.top_sources?.[0]?.count ?? 0} hits`} />
      </section>

      {analysis.top_sources?.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title"><TrendingUp className="h-4 w-4" /> Top Sources (mais consultados)</h3>
          <div className="memory-analysis-list">
            {analysis.top_sources.map((s, i) => (
              <div key={i} className="memory-analysis-row">
                <span className="memory-analysis-rank">#{i + 1}</span>
                <span className="memory-analysis-name" title={s.name}>{s.name}</span>
                <div className="memory-analysis-bar">
                  <div className="memory-analysis-fill" style={{ width: `${(s.count / maxSource) * 100}%` }} />
                </div>
                <span className="memory-analysis-count">{s.count}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {analysis.top_keywords?.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title"><Search className="h-4 w-4" /> Top Keywords nas Queries</h3>
          <div className="memory-keywords-cloud">
            {analysis.top_keywords.map((k) => (
              <span
                key={k.word}
                className="memory-keyword"
                style={{ fontSize: `${0.85 + (k.count / maxWord) * 1.2}em` }}
              >
                {k.word} <span className="memory-keyword-count">{k.count}</span>
              </span>
            ))}
          </div>
        </section>
      )}

      {histogramEntries.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title"><BarChart3 className="h-4 w-4" /> Distribuição de Chunks por Query</h3>
          <div className="memory-histogram">
            {histogramEntries.map(([bucket, count]) => (
              <div key={bucket} className="memory-histogram-bar">
                <div className="memory-histogram-fill" style={{ height: `${((count as number) / maxBucket) * 100}%` }} />
                <span className="memory-histogram-label">{bucket}</span>
                <span className="memory-histogram-count">{count as number}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {timeEntries.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title"><Clock className="h-4 w-4" /> Distribuição por Hora</h3>
          <div className="memory-time-dist">
            {timeEntries.map(([hour, count]) => (
              <div key={hour} className="memory-time-row">
                <span className="memory-time-hour">{hour}</span>
                <div className="memory-time-bar">
                  <div className="memory-time-fill" style={{ width: `${(count as number / maxTime) * 100}%` }} />
                </div>
                <span className="memory-time-count">{count as number}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}

function OperationsTab({ dashboard }: { dashboard: DashboardData | null }) {
  if (!dashboard) {
    return <div className="memory-empty">Carregando dados operacionais...</div>;
  }

  const cascadeTotal = Object.values(dashboard.cascade?.models_used || {}).reduce((a, b) => a + b, 0);
  const maxModelTokens = Math.max(...Object.values(dashboard.cascade?.tokens_by_model || {}), 1);

  return (
    <>
      {/* Top Stats */}
      <section className="memory-grid memory-grid-4">
        <StatCard icon={<Clock />} color="#8b5cf6" label="Avg Latency" value={`${dashboard.avg_latency_ms?.toFixed(1) ?? 0}ms`} sub="Últimas 24h" />
        <StatCard icon={<TrendingUp />} color="#f59e0b" label="Throughput" value={`${dashboard.throughput_per_min?.toFixed(1) ?? 0}/min`} sub="Traces/min" />
        <StatCard icon={<DollarSign />} color="#22c55e" label="Custo Total" value={`$${(dashboard.token_usage?.total_cost_usd ?? 0).toFixed(4)}`} sub={`${dashboard.token_usage?.total ?? 0} tokens`} />
        <StatCard
          icon={<Pulse />}
          color={dashboard.success_rate_percent > 95 ? "#22c55e" : "#ef4444"}
          label="Success Rate"
          value={`${dashboard.success_rate_percent ?? 100}%`}
          sub={`${dashboard.errors_count ?? 0} erros (24h)`}
        />
      </section>

      {/* Cascade Multi-Modelo */}
      {cascadeTotal > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title">
            <Cpu className="h-4 w-4" /> Cascade Multi-Modelo
          </h3>
          <div className="memory-grid memory-grid-2">
            <div className="memory-card">
              <h4 style={{ margin: '0 0 12px', fontSize: 14 }}>Distribuição de Modelos</h4>
              {Object.entries(dashboard.cascade?.models_used || {}).map(([model, count]) => {
                const percent = ((count as number) / cascadeTotal * 100).toFixed(1);
                const color = model === 'opus' ? '#ef4444' : model === 'sonnet' ? '#f59e0b' : '#22c55e';
                return (
                  <div key={model} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{model}</span>
                      <span style={{ color: '#a1a1aa' }}>{percent}% ({count})</span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: '#27272a', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${percent}%`, height: '100%', background: color, transition: 'width 0.3s' }} />
                    </div>
                  </div>
                );
              })}
              <div style={{ marginTop: 12, fontSize: 12, color: '#a1a1aa' }}>
                Escalações: <strong>{dashboard.cascade?.escalations || 0}</strong> ({dashboard.cascade?.escalation_rate_percent?.toFixed(1) || 0}%)
              </div>
            </div>

            <div className="memory-card">
              <h4 style={{ margin: '0 0 12px', fontSize: 14 }}>Tokens por Modelo</h4>
              {Object.entries(dashboard.cascade?.tokens_by_model || {}).map(([model, tokens]) => {
                const cost = dashboard.cascade?.cost_by_model?.[model] || 0;
                return (
                  <div key={model} style={{ marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{model}</span>
                      <span>{(tokens as number).toLocaleString()} tokens · <strong>${(cost as number).toFixed(6)}</strong></span>
                    </div>
                    <div style={{ width: '100%', height: 6, background: '#27272a', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        width: `${((tokens as number) / maxModelTokens) * 100}%`,
                        height: '100%',
                        background: model === 'opus' ? '#ef4444' : model === 'sonnet' ? '#f59e0b' : '#22c55e',
                        transition: 'width 0.3s',
                      }} />
                    </div>
                  </div>
                );
              })}
              <div style={{ marginTop: 12, padding: 10, background: '#0a0a0b', borderRadius: 6 }}>
                <div style={{ fontSize: 12, color: '#a1a1aa' }}>Custo Total Estimado</div>
                <div style={{ fontSize: 18, fontWeight: 700 }}>
                  ${(dashboard.cascade?.total_cost_usd || 0).toFixed(6)}
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Sessions ativas recentes */}
      {dashboard.recent_sessions && dashboard.recent_sessions.length > 0 && (
        <section className="memory-section">
          <h3 className="memory-section-title">
            <Network className="h-4 w-4" /> Sessões Recentes
          </h3>
          <div className="memory-queries">
            {dashboard.recent_sessions.slice(0, 10).map((s) => (
              <div key={s.id} className="memory-query-row">
                <div className="memory-query-time">
                  {s.started_at ? new Date(s.started_at).toLocaleTimeString('pt-BR') : '-'}
                </div>
                <div className="memory-query-text">
                  <span className={`memory-query-badge ${s.status === 'active' ? 'hit' : 'miss'}`}>
                    {s.status}
                  </span>
                  <div className="memory-query-q">
                    {s.task_summary || '(sem descrição)'}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#a1a1aa', marginTop: 4 }}>
                  <span>👤 {s.agent_name}</span>
                  <span>📊 {s.tokens_input + s.tokens_output} tokens</span>
                  <span>⏱️ {s.duration_seconds ? `${Math.round(s.duration_seconds)}s` : 'running'}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Health Check */}
      {dashboard.health && (
        <section className="memory-section">
          <h3 className="memory-section-title">
            <Pulse className="h-4 w-4" /> Health Check
          </h3>
          <div className="memory-grid memory-grid-4">
            {Object.entries(dashboard.health.components || {}).map(([name, info]: any) => (
              <div key={name} className="memory-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, fontWeight: 600, textTransform: 'capitalize' }}>{name}</span>
                  <span style={{
                    color: info.status === 'healthy' ? '#22c55e' : info.status === 'degraded' ? '#f59e0b' : '#ef4444',
                    fontWeight: 700,
                    fontSize: 11,
                  }}>● {info.status}</span>
                </div>
                {info.latency_ms !== undefined && (
                  <div style={{ fontSize: 11, color: '#a1a1aa', marginTop: 4 }}>
                    {info.latency_ms.toFixed(1)}ms
                  </div>
                )}
                {info.error && (
                  <div style={{ fontSize: 10, color: '#ef4444', marginTop: 4 }}>
                    {info.error.substring(0, 50)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
