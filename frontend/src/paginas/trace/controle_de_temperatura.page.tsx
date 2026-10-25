import { apiFetch } from '../../seguranca/sessao';
import { useState, useEffect, useRef } from 'react';
import { Flame, RefreshCw, Layers, Users, MousePointer2, Move } from 'lucide-react';
import './trace.styles.css';

interface HeatmapPoint {
  x: number;
  y: number;
  value: number;
  type: string;
}

interface HeatmapSession {
  session_id: string;
  count: number;
  started_at: string;
  last_activity: string;
}

// Formatar tempo em formato legível (ex: 1m 30s)
const formatDuration = (start: string, end: string) => {
  const diffMs = new Date(end).getTime() - new Date(start).getTime();
  if (diffMs < 1000) return '0s'; // Instantâneo ou só um evento
  const seconds = Math.floor((diffMs / 1000) % 60);
  const minutes = Math.floor((diffMs / (1000 * 60)) % 60);
  const hours = Math.floor((diffMs / (1000 * 60 * 60)) % 24);
  
  const parts = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
  return parts.join(' ');
};

export function ControleDeTemperaturaPage() {
  const [projectId, setProjectId] = useState('novo-site-ugarit');
  
  const projectUrls: Record<string, string> = {
    'novo-site-ugarit': 'http://localhost:3001',
    'chronodesk': 'http://localhost:3000',
    'crm-Sophia': 'http://localhost:2785',
    'Orby.ia': 'http://localhost:5440'
  };
  
  const [points, setPoints] = useState<HeatmapPoint[]>([]);
  const [sessions, setSessions] = useState<HeatmapSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [iframeHeight, setIframeHeight] = useState<number | null>(null);
  const [iframeScrollY, setIframeScrollY] = useState(0);
  const [zoom, setZoom] = useState<number>(0.8);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  const fetchSessions = async () => {
    try {
      const res = await apiFetch(`/api/heatmaps/sessions/${projectId}`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (e) {
      console.error("Erro ao carregar sessões", e);
    }
  };

  const fetchHeatmap = async () => {
    setLoading(true);
    setError(null);
    try {
      const url = `/api/heatmaps/data/${projectId}${selectedSession ? `?sessionId=${selectedSession}` : ''}`;
      const res = await apiFetch(url);
      if (!res.ok) throw new Error('Falha ao buscar dados');
      const data = await res.json();
      setPoints(data.points || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSelectedSession(null);
    fetchSessions();
    fetchHeatmap();
  }, [projectId]);

  useEffect(() => {
    fetchHeatmap();
  }, [selectedSession]);

  // Sincronia Automática
  useEffect(() => {
    const interval = setInterval(() => {
      fetchSessions();
      fetchHeatmap();
    }, 3000); // 3 segundos
    return () => clearInterval(interval);
  }, [projectId, selectedSession]);

  useEffect(() => {
    const handleMessage = (e: MessageEvent) => {
      if (e.data && e.data.type === 'HEATMAP_HEIGHT') {
        setIframeHeight(e.data.height);
      }
      if (e.data && e.data.type === 'SCROLL_UPDATE') {
        setIframeScrollY(e.data.scrollY);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  
  const clicksCount = points.filter(p => p.type === 'click').length;
  const movesCount = points.filter(p => p.type === 'move' || p.type === 'scroll').length;

  return (
    <div className="trace-page-container" data-content-height={iframeHeight ?? undefined}>
      {error && <p role="alert">{error}</p>}
      <header className="trace-header">
        <div className="trace-header-title">
          <Flame className="h-6 w-6 text-orange-500" />
          <h1>Heatmap Analytics</h1>
          <span className="trace-header-badge">Enterprise Edition</span>
        </div>
        <div className="trace-header-actions" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.05)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
            <span style={{ fontSize: '0.75rem', color: '#8b8b94' }}>Zoom</span>
            <input type="range" className="trace-zoom-slider" min="0.2" max="1.5" step="0.1" value={zoom} onChange={(e) => setZoom(Number(e.target.value))} />
            <span style={{ fontSize: '0.75rem', color: '#c9d1d9', minWidth: '3ch' }}>{Math.round(zoom * 100)}%</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(34, 197, 94, 0.1)', padding: '0.35rem 0.75rem', borderRadius: '100px', border: '1px solid rgba(34, 197, 94, 0.3)' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 8px #22c55e', animation: 'pulse 2s infinite' }} />
            <span style={{ fontSize: '0.75rem', color: '#4ade80', fontWeight: 600 }}>Sync Ativa</span>
          </div>
        </div>
      </header>

      <div className="trace-content" style={{ display: 'flex', gap: '1rem', height: 'calc(100vh - 100px)' }}>
        {/* COLUNA ESQUERDA: PROJETOS */}
        <aside style={{ width: '220px', background: 'rgba(20,20,25,0.8)', backdropFilter: 'blur(10px)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ color: '#8b8b94', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers className="w-4 h-4" /> Projetos
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, flex: 1 }}>
            {['novo-site-ugarit', 'crm-Sophia', 'chronodesk', 'Orby.ia'].map(proj => (
              <li key={proj} style={{ marginBottom: '0.5rem' }}>
                <button
                  style={{
                    width: '100%', textAlign: 'left', padding: '0.75rem', fontSize: '0.875rem',
                    background: proj === projectId ? 'linear-gradient(90deg, rgba(249, 115, 22, 0.15) 0%, transparent 100%)' : 'transparent',
                    color: proj === projectId ? '#f97316' : '#a1a1aa',
                    border: 'none', borderLeft: proj === projectId ? '2px solid #f97316' : '2px solid transparent',
                    borderRadius: '0 4px 4px 0', cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onClick={() => setProjectId(proj)}
                >
                  {proj}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* COLUNA CENTRAL: MAPA DE CALOR */}
        <main 
          style={{ flex: 1, background: '#0a0a0c', borderRadius: '8px', position: 'relative', overflow: 'auto', border: '1px solid rgba(255,255,255,0.05)', boxShadow: 'inset 0 0 50px rgba(0,0,0,0.5)' }}
        >
          {/* Zoom Wrapper (controla o tamanho real do scroll) */}
          <div style={{ width: `${1920 * zoom}px`, height: `${1080 * zoom}px`, position: 'relative', margin: '2rem auto' }}>
            {/* Inner Scaled Container (Fixed Desktop Size) */}
            <div style={{ 
              position: 'absolute', 
              top: 0, left: 0, 
              width: '1920px', 
              height: '1080px',
              transform: `scale(${zoom})`,
              transformOrigin: 'top left',
              transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              overflow: 'hidden',
              boxShadow: '0 0 30px rgba(0,0,0,0.8)',
              borderRadius: '8px'
            }}>
            {/* Iframe Preview */}
            {projectUrls[projectId] && (
              <iframe
                ref={iframeRef}
                src={projectUrls[projectId]}
                style={{
                  position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none',
                  opacity: 0.6, pointerEvents: 'auto', filter: 'grayscale(20%) brightness(0.6)'
                }}
                title="Site Preview"
              />
            )}

            {loading && <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#f97316', zIndex: 50 }}><RefreshCw className="w-8 h-8 animate-spin" /></div>}
            {!loading && points.length === 0 && <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: '#52525b', zIndex: 50 }}>Nenhuma interação detectada</div>}
            
            {/* Heatmap Renderer (Overlay Sincronizado) */}
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 20, pointerEvents: 'none', transform: `translateY(-${iframeScrollY}px)` }}>
              {points.map((p, i) => {
                const isClick = p.type === 'click';
                return (
                  <div
                    key={i}
                    style={{
                      position: 'absolute',
                      left: p.x,
                      top: p.y,
                      width: isClick ? '90px' : '120px',
                      height: isClick ? '90px' : '120px',
                      background: isClick 
                        ? 'radial-gradient(circle, rgba(239,68,68,0.7) 0%, rgba(249,115,22,0.4) 40%, rgba(0,0,0,0) 70%)' 
                        : 'radial-gradient(circle, rgba(59,130,246,0.3) 0%, rgba(139,92,246,0.15) 40%, rgba(0,0,0,0) 70%)',
                      borderRadius: '50%',
                      filter: 'blur(8px)',
                      transform: 'translate(-50%, -50%) scale(1.5)',
                      pointerEvents: 'none',
                      mixBlendMode: 'screen'
                    }}
                  />
                );
              })}
            </div>
          </div>
          </div>
          
          {/* Overlay Status Box */}
          <div style={{ position: 'absolute', bottom: '1.5rem', left: '50%', transform: 'translateX(-50%)', background: 'rgba(20,20,25,0.85)', backdropFilter: 'blur(12px)', padding: '0.75rem 1.5rem', borderRadius: '100px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', gap: '1.5rem', boxShadow: '0 10px 30px rgba(0,0,0,0.5)', zIndex: 100 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ef4444' }}>
              <MousePointer2 className="w-4 h-4" />
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{clicksCount} Clicks</span>
            </div>
            <div style={{ width: '1px', height: '16px', background: 'rgba(255,255,255,0.1)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#3b82f6' }}>
              <Move className="w-4 h-4" />
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{movesCount} Moves</span>
            </div>
          </div>
        </main>

        {/* COLUNA DIREITA: SESSÕES */}
        <aside style={{ width: '280px', background: 'rgba(20,20,25,0.8)', backdropFilter: 'blur(10px)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ color: '#8b8b94', fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Users className="w-4 h-4" /> Sessões
            </h3>
            {selectedSession && (
              <button onClick={() => setSelectedSession(null)} style={{ background: 'transparent', border: 'none', color: '#f97316', fontSize: '0.75rem', cursor: 'pointer' }}>Limpar Filtro</button>
            )}
          </div>
          
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.25rem' }} className="sessions-list">
            <button
              onClick={() => setSelectedSession(null)}
              style={{
                width: '100%', padding: '1rem', marginBottom: '0.5rem', borderRadius: '6px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
                background: selectedSession === null ? 'rgba(249,115,22,0.1)' : 'rgba(255,255,255,0.02)',
                border: selectedSession === null ? '1px solid rgba(249,115,22,0.3)' : '1px solid transparent',
              }}
            >
              <div style={{ color: selectedSession === null ? '#f97316' : '#e4e4e7', fontSize: '0.875rem', fontWeight: 600 }}>Visão Global (Todas)</div>
              <div style={{ color: '#71717a', fontSize: '0.75rem', marginTop: '0.25rem' }}>Mapa de densidade combinado</div>
            </button>

            {sessions.map((sess, idx) => {
              const duration = formatDuration(sess.started_at, sess.last_activity);
              return (
              <button
                key={sess.session_id}
                onClick={() => setSelectedSession(sess.session_id)}
                style={{
                  width: '100%', padding: '0.75rem', marginBottom: '0.5rem', borderRadius: '6px', cursor: 'pointer', textAlign: 'left', transition: 'all 0.2s',
                  background: selectedSession === sess.session_id ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                  border: selectedSession === sess.session_id ? '1px solid rgba(255,255,255,0.2)' : '1px solid transparent',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ color: '#e4e4e7', fontSize: '0.875rem', fontFamily: 'monospace' }}>
                    User #{sess.session_id.split('_')[1] || idx}
                  </div>
                  <div style={{ background: 'rgba(249,115,22,0.2)', color: '#f97316', padding: '0.1rem 0.4rem', borderRadius: '100px', fontSize: '0.65rem', fontWeight: 'bold' }}>
                    {sess.count} pts
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem' }}>
                  <div style={{ color: '#71717a', fontSize: '0.7rem' }}>
                    {new Date(sess.started_at).toLocaleString('pt-BR')}
                  </div>
                  <div style={{ color: '#a1a1aa', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '0.25rem', background: 'rgba(255,255,255,0.05)', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                    ⏱️ {duration}
                  </div>
                </div>
              </button>
            )})}
            
            {sessions.length === 0 && !loading && (
              <div style={{ color: '#52525b', fontSize: '0.875rem', textAlign: 'center', padding: '2rem 0' }}>
                Nenhuma sessão capturada ainda.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
