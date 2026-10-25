import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Gauge,
  Activity,
  Coins,
  AlertCircle,
  Clock,
  TrendingUp,
  Inbox,
  CheckCircle2,
} from 'lucide-react';
import './token-usage.styles.css';
import {
  getAllSnapshots,
  getLedgerSummary,
  getStatus,
  refreshProvider,
  formatNumber,
  formatPercent,
  formatResetsAt,
  type SnapshotResponse,
  type SummaryResponse,
  type StatusResponse,
} from './token-usage.api';

// ===== Helpers =====

const POLL_INTERVAL_MS = 15_000;

type Level = 'healthy' | 'warning' | 'danger' | 'unknown';

function levelFromFraction(f: number): Level {
  if (f >= 0.9) return 'danger';
  if (f >= 0.7) return 'warning';
  return 'healthy';
}

function levelFromStatus(status: string): Level {
  const s = status.toLowerCase();
  if (s === 'healthy' || s === 'ok') return 'healthy';
  if (s === 'degraded' || s === 'stale') return 'warning';
  if (s === 'error' || s === 'failed' || s === 'unavailable') return 'danger';
  return 'unknown';
}

const formatTokens = (n: number) => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toString();
};

const formatRelativeTime = (iso: string | null | undefined) => {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const diffMs = Date.now() - d.getTime();
    const s = Math.floor(diffMs / 1000);
    if (s < 60) return `há ${s}s`;
    const m = Math.floor(s / 60);
    if (m < 60) return `há ${m} min`;
    const h = Math.floor(m / 60);
    if (h < 24) return `há ${h}h`;
    return d.toLocaleString('pt-BR');
  } catch {
    return '—';
  }
};

// ===== Page =====

export function TokenUsagePage() {
  const [snapshots, setSnapshots] = useState<Record<string, SnapshotResponse>>({});
  const [ledger, setLedger] = useState<SummaryResponse | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [providerRefreshing, setProviderRefreshing] = useState<Record<string, boolean>>({});
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setError(null);
    try {
      const [snapshotsData, ledgerData, statusData] = await Promise.all([
        getAllSnapshots(),
        getLedgerSummary(),
        getStatus(),
      ]);
      setSnapshots(snapshotsData || {});
      setLedger(ledgerData);
      setStatus(statusData);
      setLastUpdate(new Date());
    } catch (e: any) {
      console.error('[TokenUsage] fetch error:', e);
      setError(e?.message || 'Falha ao carregar dados');
    } finally {
      setLoading(false);  // turn off spinner even on first error
    }
  }, []);

  // Initial load + setLoading true then off on completion
  useEffect(() => {
    setLoading(true);
    fetchAll();
  }, [fetchAll]);

  // Polling
  useEffect(() => {
    const interval = setInterval(() => {
      // Não muda `loading` no polling — atualização silenciosa
      fetchAll().catch(() => { /* já tratado dentro de fetchAll */ });
    }, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAll]);

  const handleRefreshAll = useCallback(async () => {
    setLoading(true);
    await fetchAll();
  }, [fetchAll]);

  const handleRefreshProvider = useCallback(
    async (providerId: string) => {
      setProviderRefreshing((prev) => ({ ...prev, [providerId]: true }));
      try {
        await refreshProvider(providerId);
        await fetchAll();
      } catch (e) {
        console.error(`[TokenUsage] refresh ${providerId} falhou:`, e);
      } finally {
        setProviderRefreshing((prev) => ({ ...prev, [providerId]: false }));
      }
    },
    [fetchAll],
  );

  // ===== Compute summary cards =====
  // Pick the most-used window across all providers (priority: session > weekly > monthly > others)
  const allWindows = Object.values(snapshots).flatMap((s) => s.windows || []);
  const sessionWin =
    allWindows.find((w) => w.type === 'session') ||
    allWindows.find((w) => w.type === 'sessao') ||
    allWindows.find((w) => w.type === '5h');
  const weeklyWin = allWindows.find((w) => w.type === 'weekly' || w.type === 'week' || w.type === '7d');
  const monthlyWin =
    allWindows.find((w) => w.type === 'monthly' || w.type === 'month') ||
    allWindows.find((w) => w.type === '30d');

  const snapshotCount = Object.keys(snapshots).length;

  // ===== Render =====
  return (
    <div className="tu-page">
      {/* Header */}
      <header className="tu-header">
        <div className="tu-title">
          <Gauge className="tu-stat-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }} />
          <h1>Token Usage</h1>
          <span className="tu-badge">Quota</span>
          {status?.is_running && <span className="tu-badge tu-badge-live">● Live</span>}
        </div>
        <div className="tu-actions">
          {lastUpdate && (
            <span className="tu-last-update">
              <Clock size={12} />
              Atualizado {lastUpdate.toLocaleTimeString('pt-BR')}
            </span>
          )}
          <button
            className="tu-refresh-btn"
            onClick={handleRefreshAll}
            disabled={loading}
            title="Recarregar dados agora"
          >
            <RefreshCw size={14} className={loading ? 'tu-spinning' : ''} />
            {loading ? 'Atualizando…' : 'Atualizar'}
          </button>
        </div>
      </header>

      {error && (
        <div className="tu-error">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* ===== Top stat cards (janelas) ===== */}
      <section className="tu-stats-grid">
        {sessionWin && (
          <WindowStatCard
            label={sessionWin.label || 'Sessão (5h)'}
            window={sessionWin}
            icon={<Activity size={20} />}
          />
        )}
        {weeklyWin && (
          <WindowStatCard
            label={weeklyWin.label || 'Semanal'}
            window={weeklyWin}
            icon={<TrendingUp size={20} />}
          />
        )}
        {monthlyWin && (
          <WindowStatCard
            label={monthlyWin.label || 'Mensal'}
            window={monthlyWin}
            icon={<Coins size={20} />}
          />
        )}
        <div className={`tu-stat-card ${ledger ? 'highlight' : ''}`} style={ledger ? {} : { background: 'rgba(255,255,255,0.05)' }}>
          <div className="tu-stat-icon" style={{ background: 'rgba(167, 139, 250, 0.15)', color: '#a78bfa' }}>
            <Coins size={20} />
          </div>
          <div className="tu-stat-content">
            <div className="tu-stat-label">Tokens hoje (ledger)</div>
            <div className="tu-stat-value">{ledger ? formatTokens(ledger.today.total_tokens) : '—'}</div>
            <div className="tu-stat-meta">
              {ledger ? `${formatNumber(ledger.today.requests)} requests · ${formatTokens(ledger.today.reasoning_tokens)} reasoning` : 'Aguardando dados'}
            </div>
          </div>
        </div>
      </section>

      {/* ===== Provider cards ===== */}
      <section className="tu-providers">
        {snapshotCount === 0 && !loading && (
          <div className="tu-empty">
            <Inbox className="tu-empty-icon" size={32} />
            <div>Nenhum provider registrado ainda.</div>
            <div style={{ fontSize: 12, marginTop: 6 }}>
              O token counter está rodando e aguardando o primeiro snapshot do Claude Code.
            </div>
          </div>
        )}

        {Object.values(snapshots).map((snap) => {
          const level = levelFromStatus(snap.status);
          const isRefreshing = !!providerRefreshing[snap.id];
          return (
            <article key={snap.id} className="tu-provider-card">
              <div className="tu-provider-header">
                <div className="tu-provider-title">
                  <div className="tu-glyph">🔮</div>
                  <div>
                    <div className="tu-provider-name">{snap.name}</div>
                    <div className="tu-provider-id">{snap.id} · fidelity {snap.fidelity}</div>
                  </div>
                </div>
                <div className="tu-provider-actions">
                  <span className={`tu-status-pill ${level}`}>
                    <span className="tu-status-dot" />
                    {snap.status}
                  </span>
                  <button
                    className="tu-mini-btn"
                    onClick={() => handleRefreshProvider(snap.id)}
                    disabled={isRefreshing}
                    title="Forçar refresh deste provider"
                  >
                    <RefreshCw size={12} className={isRefreshing ? 'tu-spinning' : ''} />
                    {isRefreshing ? 'Refresh…' : 'Refresh'}
                  </button>
                </div>
              </div>

              {snap.headline && (
                <div className="tu-headline">{snap.headline}</div>
              )}

              <div className="tu-windows">
                {snap.windows && snap.windows.length > 0 ? (
                  snap.windows.map((w) => {
                    const lvl = levelFromFraction(w.used_fraction);
                    const pct = formatPercent(w.used_fraction, 1);
                    return (
                      <div key={w.type} className="tu-window">
                        <div className="tu-window-row">
                          <div className="tu-window-label">{w.label || w.type}</div>
                          <div className={`tu-window-pct ${lvl}`}>{pct}</div>
                        </div>
                        <div className="tu-progress-bar">
                          <div
                            className={`tu-progress-fill-bar ${lvl}`}
                            style={{ width: `${Math.min(100, w.used_fraction * 100)}%` }}
                          />
                        </div>
                        <div className="tu-window-foot">
                          <span>
                            {formatTokens(w.used)} / {formatTokens(w.limit)}
                          </span>
                          <span>
                            {w.remaining > 0
                              ? `${formatTokens(w.remaining)} restantes`
                              : 'limite atingido'}{' '}
                            · reseta {formatResetsAt(w.resets_at)}
                          </span>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="tu-empty" style={{ background: 'transparent', border: 'none', padding: 24 }}>
                    Nenhuma janela de quota reportada.
                  </div>
                )}

                {snap.ledger_today && (
                  <div style={{ paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', textTransform: 'uppercase', marginBottom: 6 }}>
                      Ledger hoje — {snap.id}
                    </div>
                    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'rgba(255,255,255,0.7)', flexWrap: 'wrap' }}>
                      <span>
                        Input: <strong>{formatTokens(snap.ledger_today.input_tokens)}</strong>
                      </span>
                      <span>
                        Output: <strong>{formatTokens(snap.ledger_today.output_tokens)}</strong>
                      </span>
                      <span>
                        Reasoning: <strong>{formatTokens(snap.ledger_today.reasoning_tokens)}</strong> (
                        {formatPercent(snap.ledger_today.reasoning_share, 0)})
                      </span>
                      <span>
                        Requests: <strong>{formatNumber(snap.ledger_today.requests)}</strong>
                      </span>
                    </div>
                  </div>
                )}

                {snap.context && (snap.context.model || snap.context.instance) && (
                  <div style={{ paddingTop: 10, fontSize: 11, color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>
                    instance=<span style={{ color: '#a78bfa' }}>{snap.context.instance}</span>
                    {snap.context.model && (
                      <> · model=<span style={{ color: '#a78bfa' }}>{snap.context.model}</span></>
                    )}
                    {snap.context.timestamp && (
                      <> · fetched {formatRelativeTime(snap.context.timestamp)}</>
                    )}
                  </div>
                )}

                {snap.error_message && (
                  <div className="tu-error" style={{ marginTop: 10, marginBottom: 0 }}>
                    <AlertCircle size={14} />
                    {snap.error_message}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </section>

      {/* ===== Ledger summary ===== */}
      {ledger && (
        <section className="tu-ledger">
          <div className="tu-ledger-title">
            <CheckCircle2 size={14} />
            Histórico agregado · instância <span style={{ color: '#a78bfa', marginLeft: 4 }}>{ledger.instance}</span> · {ledger.dates_tracked} dias registrados
          </div>
          <div className="tu-ledger-grid">
            <LedgerColumn title="Hoje" t={ledger.today} accent="#f59e0b" />
            <LedgerColumn title="Últimos 7 dias" t={ledger.last_7_days} accent="#3b82f6" />
            <LedgerColumn title="Todos os tempos" t={ledger.all_time} accent="#a78bfa" />
          </div>
        </section>
      )}
    </div>
  );
}

// ===== Subcomponents =====

function WindowStatCard({
  label,
  window: w,
  icon,
}: {
  label: string;
  window: {
    used_fraction: number;
    used: number;
    limit: number;
    remaining: number;
    resets_at: string | null;
  };
  icon: React.ReactNode;
}) {
  const lvl = levelFromFraction(w.used_fraction);
  return (
    <div className={`tu-stat-card ${lvl}`}>
      <div className="tu-stat-icon" style={{ background: 'rgba(255,255,255,0.06)' }}>{icon}</div>
      <div className="tu-stat-content">
        <div className="tu-stat-label">{label}</div>
        <div className="tu-stat-value">{formatPercent(w.used_fraction, 0)}</div>
        <div className="tu-stat-meta">
          {formatTokens(w.used)} / {formatTokens(w.limit)} · reseta {formatResetsAt(w.resets_at)}
        </div>
        <div className="tu-progress">
          <div
            className={`tu-progress-fill ${lvl}`}
            style={{ width: `${Math.min(100, w.used_fraction * 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function LedgerColumn({
  title,
  t,
  accent,
}: {
  title: string;
  t: { total_tokens: number; requests: number; reasoning_tokens: number; reasoning_share: number };
  accent: string;
}) {
  return (
    <div className="tu-ledger-col">
      <div className="tu-ledger-col-label" style={{ color: accent }}>{title}</div>
      <div className="tu-ledger-col-value">{formatTokens(t.total_tokens)}</div>
      <div className="tu-ledger-col-meta">
        {formatNumber(t.requests)} requests ·{' '}
        <span className="accent">{formatTokens(t.reasoning_tokens)} reasoning</span> (
        {formatPercent(t.reasoning_share, 0)})
      </div>
    </div>
  );
}
