/**
 * KOTHAR v6.0 — Metrics Page
 * Dashboard de métricas, RAG analytics e health checks
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity, AlertTriangle, CheckCircle2, Database, HardDrive,
  Server, Timer, XCircle, Brain, Zap, Clock, TrendingUp,
  TrendingDown, Minus, RefreshCw, Eye, MemoryStick
} from 'lucide-react';
import {
  getDashboard,
  type DashboardData,
} from './metrics.api';
import './metrics.styles.css';

export function MetricsPage() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchAll = async () => {
    setLoading(true);
    try {
      const data = await getDashboard(24).catch(() => null);
      setDashboard(data);
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}h ${m}m ${s}s`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#22c55e';
      case 'degraded': return '#eab308';
      case 'unhealthy': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle2 className="status-icon healthy" size={16} />;
      case 'degraded': return <AlertTriangle className="status-icon degraded" size={16} />;
      case 'unhealthy': return <XCircle className="status-icon unhealthy" size={16} />;
      default: return <Minus className="status-icon" size={16} />;
    }
  };

  const getTrendIcon = (value: number, threshold: number = 0) => {
    if (value > threshold) return <TrendingUp className="trend-up" size={14} />;
    if (value < threshold) return <TrendingDown className="trend-down" size={14} />;
    return <Minus className="trend-neutral" size={14} />;
  };

  return (
    <div className="metrics-page">
      {/* Header */}
      <div className="metrics-header">
        <div className="metrics-title">
          <Activity size={24} />
          <h1>Observability Hub</h1>
          <span className="badge">Live</span>
        </div>
        <div className="metrics-actions">
          <span className="last-update">
            <Clock size={14} />
            Atualizado: {lastUpdate.toLocaleTimeString()}
          </span>
          <button className="refresh-btn" onClick={fetchAll} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spinning' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="metrics-grid">
        {/* Uptime */}
        <motion.div className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <div className="stat-icon"><Timer /></div>
          <div className="stat-content">
            <span className="stat-label">Uptime</span>
            <span className="stat-value">{dashboard ? formatUptime(dashboard.uptime_seconds) : '--'}</span>
          </div>
        </motion.div>

        {/* Sessions */}
        <motion.div className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <div className="stat-icon"><Server /></div>
          <div className="stat-content">
            <span className="stat-label">Sessões</span>
            <span className="stat-value">
              {dashboard?.active_sessions || 0}
              <span className="stat-detail">/ {dashboard?.total_sessions_period || 0} total</span>
            </span>
          </div>
        </motion.div>

        {/* RAG Hit Rate */}
        <motion.div className="stat-card highlight" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <div className="stat-icon"><Brain /></div>
          <div className="stat-content">
            <span className="stat-label">RAG Hit Rate</span>
            <span className="stat-value">
              {dashboard ? `${dashboard.rag.hit_rate_percent.toFixed(1)}%` : '--'}
              {dashboard && getTrendIcon(dashboard.rag.hit_rate_percent / 100, 0.7)}
            </span>
          </div>
        </motion.div>

        {/* RAG Hits/Misses */}
        <motion.div className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <div className="stat-icon"><Zap /></div>
          <div className="stat-content">
            <span className="stat-label">RAG Performance</span>
            <span className="stat-value">
              <span className="text-green">{dashboard?.rag.total_hits || 0} hits</span>
              <span className="stat-divider">/</span>
              <span className="text-red">{dashboard?.rag.total_misses || 0} misses</span>
            </span>
          </div>
        </motion.div>

        {/* Health Status */}
        <motion.div className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <div className="stat-icon">
            {dashboard?.health ? getStatusIcon(dashboard.health.status) : <Minus />}
          </div>
          <div className="stat-content">
            <span className="stat-label">System Health</span>
            <span className="stat-value" style={{ color: dashboard?.health ? getStatusColor(dashboard.health.status) : undefined }}>
              {dashboard?.health.status || 'unknown'}
            </span>
          </div>
        </motion.div>

        {/* Trace Events */}
        <motion.div className="stat-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
          <div className="stat-icon"><Activity /></div>
          <div className="stat-content">
            <span className="stat-label">Trace Events</span>
            <span className="stat-value">
              {Object.values(dashboard?.trace_events || {}).reduce((a, b) => a + b, 0)}
            </span>
          </div>
        </motion.div>
      </div>

      {/* Two Column Layout */}
      <div className="metrics-columns">
        {/* RAG Analytics */}
        <motion.div className="metrics-panel" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
          <div className="panel-header">
            <Brain size={20} />
            <h2>RAG Analytics</h2>
          </div>
          <div className="panel-content">
            {dashboard ? (
              <>
                {/* Hit Rate Bar */}
                <div className="metric-row">
                  <span className="metric-label">Hit Rate</span>
                  <div className="metric-bar-container">
                    <div
                      className="metric-bar hit"
                      style={{ width: `${dashboard.rag.hit_rate_percent}%` }}
                    />
                  </div>
                  <span className="metric-value">{dashboard.rag.hit_rate_percent.toFixed(1)}%</span>
                </div>

                {/* By Type */}
                <div className="metric-section-title">Por Tipo de Query</div>
                {Object.entries(dashboard.rag.hits_by_type).map(([type, hits]) => (
                  <div key={type} className="metric-row">
                    <span className="metric-label">{type}</span>
                    <div className="metric-mini-bar">
                      <div
                        className="metric-bar hit"
                        style={{ width: `${(hits / Math.max(dashboard.rag.total_hits, 1)) * 100}%` }}
                      />
                    </div>
                    <span className="metric-value">
                      <span className="text-green">{hits}</span>
                    </span>
                  </div>
                ))}

                {/* No data message */}
                {Object.keys(dashboard.rag.hits_by_type).length === 0 && (
                  <div className="no-data">
                    <Eye size={32} />
                    <p>Aguardando dados de RAG...</p>
                    <span>Execute queries para ver métricas</span>
                  </div>
                )}
              </>
            ) : (
              <div className="loading-state">
                <RefreshCw className="spinning" size={24} />
                <span>Carregando métricas RAG...</span>
              </div>
            )}
          </div>
        </motion.div>

        {/* Health Checks */}
        <motion.div className="metrics-panel" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
          <div className="panel-header">
            <HardDrive size={20} />
            <h2>Component Health</h2>
          </div>
          <div className="panel-content">
            {dashboard?.health ? (
              <>
                {/* Overall Status */}
                <div className="health-summary">
                  {getStatusIcon(dashboard.health.status)}
                  <span>Status: <strong>{dashboard.health.status}</strong></span>
                  <span className="health-checked">
                    Verificado: {new Date(dashboard.health.checked_at).toLocaleTimeString()}
                  </span>
                </div>

                {/* Components */}
                <div className="component-list">
                  {Object.entries(dashboard.health.components).map(([name, comp]) => (
                    <div key={name} className={`component-row ${comp.status}`}>
                      <div className="component-info">
                        {name === 'postgres' && <Database size={16} />}
                        {name === 'redis' && <MemoryStick size={16} />}
                        {name === 'chromadb' && <HardDrive size={16} />}
                        {name === 'neo4j' && <Database size={16} />}
                        {name === 'api' && <Server size={16} />}
                        <span className="component-name">{name}</span>
                      </div>
                      <div className="component-metrics">
                        {getStatusIcon(comp.status)}
                        <span className="latency">{(comp.latency_ms || 0).toFixed(1)}ms</span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="loading-state">
                <RefreshCw className="spinning" size={24} />
                <span>Carregando health checks...</span>
              </div>
            )}
          </div>
        </motion.div>
      </div>

      {/* Trace Events Breakdown */}
      <motion.div className="metrics-panel full-width" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <div className="panel-header">
          <Activity size={20} />
          <h2>Trace Events Breakdown</h2>
        </div>
        <div className="panel-content">
          {dashboard?.trace_events_breakdown && Object.keys(dashboard.trace_events_breakdown).length > 0 ? (
            <div className="events-grid">
              {Object.entries(dashboard.trace_events_breakdown)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .map(([eventType, count]) => (
                  <div key={eventType} className="event-chip">
                    <span className="event-type">{eventType}</span>
                    <span className="event-count">{count as number}</span>
                  </div>
                ))}
            </div>
          ) : (
            <div className="no-data">
              <Activity size={32} />
              <p>Nenhum evento de trace ainda</p>
              <span>Execute comandos para ver eventos</span>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
