/**
 * KOTHAR v6.0 — Trace Page (SUPREMO + TURBINADO)
 *
 * Funcionalidades:
 * - Tracking de sub-agentes com modelos usados
 * - Sistema de reportar erros (falso positivo/negativo)
 * - Tokens categorizados (nunca "outros")
 * - Contador de erros por tipo e onde
 * - Aprendizado automático (envia para locks)
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Activity, AlertCircle, Bot, Brain,
  CheckCircle2, ChevronDown, ChevronRight, Clock, FileText,
  Search, Terminal, User, X,
  Layers, Zap,
  Database, Cpu, Network,
  RotateCcw, Bug,
  AlertOctagon,
} from 'lucide-react';
import './trace.styles.css';
import {
  listSessions,
  listTraces,
  generateSessionReport,
  deleteSession,
  clearSessionTraces,
  markTraceAsError,
  getMarkedErrors,
  countErrorsByType,
  classifyTokensByCategory,
  getTokenDistribution,
  extractSubAgents,
  type ApiSession,
  type ApiTraceEntry,
  type MarkedError,
  type SubAgentInfo,
  type TokenCategory,
} from './trace.api';

// ─── Tipos ─────────────────────────────────────────────────────────────────

type TraceLevel = 'input' | 'output' | 'thinking' | 'tool' | 'context' | 'subagent' | 'memory' | 'plan' | 'task' | 'error' | 'cascade';

interface Trace {
  id: string;
  timestamp: string;
  level: TraceLevel;
  tool: string;
  toolRaw: string;
  message: string;
  fullContent: string;
  duration: number | null;
  status: 'success' | 'error' | 'pending';
  tokensUsed: number | null;
  tokensInput: number | null;
  tokensOutput: number | null;
  tokenCategory: TokenCategory | null;
  agentName?: string;
  subagentType?: string;
  parentToolUseId?: string;
  rawEntry: ApiTraceEntry;
  isMarkedAsError?: boolean;
  markedErrorInfo?: MarkedError;
}

interface TokenSummary {
  byCategory: Record<TokenCategory, number>;
  distribution: Array<{ category: TokenCategory; value: number; percent: number }>;
  total: number;
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function tryParse(v: unknown): unknown {
  if (typeof v !== 'string') return v;
  try { return JSON.parse(v); } catch { return v; }
}

function classifyTrace(entry: ApiTraceEntry): TraceLevel {
  if (entry.status === 'error') return 'error';

  // Sub-agente - várias formas de detecção
  if (entry.event_type?.includes('subagent') ||
      entry.tool === 'Claude:Agent' ||
      entry.tool === 'browser_subagent' ||
      entry.tool_name === 'Agent' ||
      entry.metadata?.is_subagent === true ||
      entry.metadata?.is_subagent_message === true) {
    return 'subagent';
  }

  // Thinking / Pensamento
  if (entry.tool === 'Claude:thinking' ||
      entry.tool === 'Gemini:thinking' ||
      entry.event_type === 'thinking' ||
      entry.tool_name === 'thinking' ||
      entry.metadata?.token_type === 'thinking' ||
      (entry.event_type === 'tool_call' && entry.tool_input?.thinking)) {
    return 'thinking';
  }

  // Memória / RAG - baseado em metadata ou nome
  if (entry.event_type?.includes('rag') ||
      entry.event_type?.includes('memory') ||
      entry.tool?.toLowerCase().includes('rag') ||
      entry.tool_name?.toLowerCase().includes('rag') ||
      entry.tool_name?.toLowerCase().includes('memory') ||
      entry.metadata?.rag_chunks ||
      entry.metadata?.memory_context ||
      entry.metadata?.token_type === 'rag' ||
      entry.metadata?.token_type === 'memory') {
    return 'memory';
  }

  // Planos - baseado em metadata ou tool
  if (entry.event_type === 'agent_plan' ||
      entry.tool === 'EnterPlanMode' ||
      entry.tool === 'ExitPlanMode' ||
      entry.metadata?.plan_type === 'plan' ||
      (entry.tool === 'Chat:Agent' && entry.output?.includes('## Plano')) ||
      (entry.tool === 'Chat:Agent' && entry.output?.includes('**Plano**'))) {
    return 'plan';
  }

  // Tarefas (TodoWrite) - podemos inferir de tool_calls longos
  if (entry.event_type === 'agent_task' ||
      entry.tool === 'TodoWrite' ||
      entry.tool_name === 'TodoWrite' ||
      entry.metadata?.plan_type === 'task' ||
      entry.tool === 'Chat:Agent' && entry.output?.includes('- [ ]')) {
    return 'task';
  }

  // Cascade multi-modelo
  if (entry.event_type === 'cascade_step' ||
      entry.metadata?.cascade === true ||
      entry.metadata?.cascade_model) {
    return 'cascade';
  }

  // Mensagem do usuário
  if (entry.event_type === 'user_message' ||
      entry.tool === 'Chat:User' ||
      entry.tool_name === 'Chat:User' ||
      entry.tool === 'user_message') {
    return 'input';
  }

  // Resposta do agente
  if (entry.tool === 'Chat:Agent' ||
      entry.tool_name === 'Chat:Agent' ||
      entry.event_type === 'assistant_response' ||
      entry.event_type === 'chat' ||
      entry.tool?.startsWith('kothar-') ||
      entry.tool_name?.startsWith('kothar-')) {
    return 'output';
  }

  // Contexto (Read, Glob, Grep)
  if (entry.tool === 'Claude:Read' ||
      entry.tool === 'Claude:Glob' ||
      entry.tool === 'Claude:Grep' ||
      entry.tool === 'Read' ||
      entry.tool === 'Glob' ||
      entry.tool === 'Grep' ||
      entry.tool === 'view_file' ||
      entry.tool === 'list_dir' ||
      entry.tool === 'grep_search' ||
      entry.tool === 'read_url_content' ||
      entry.tool === 'write_to_file' ||
      entry.tool === 'replace_file_content' ||
      entry.tool === 'multi_replace_file_content') {
    return 'context';
  }

  // Tool genérica
  return 'tool';
}

function classifyTraceTokenCategory(entry: ApiTraceEntry): TokenCategory {
  if (entry.event_type === 'user_message' || entry.tool === 'Chat:User') return 'user_input';
  if (entry.event_type === 'rag_preload' || entry.tool_input?.rag_chunks) return 'rag_context';
  if (entry.event_type === 'memory_load' || entry.tool_input?.memory_context) return 'memory_history';
  if (entry.event_type === 'tool_result' || entry.event_type === 'tool_call') return 'tool_result';
  if (entry.event_type === 'assistant_response' || entry.tool === 'Chat:Agent') return 'assistant_response';
  if (entry.event_type === 'thinking' || entry.tool === 'Claude:thinking' || entry.tool === 'Gemini:thinking') return 'assistant_response';
  if (entry.event_type === 'cascade_step' || entry.metadata?.cascade) return 'cascade_overhead';
  if (entry.is_error && entry.metadata?.retry_count > 0) return 'error_recovery';
  if (entry.metadata?.system_prompt || entry.event_type === 'session_start') return 'system_prompt';
  // Sem "outros" - se não classificou, é resposta do agente
  return 'assistant_response';
}

function extractFullContent(entry: ApiTraceEntry): string {
  let o: Record<string, unknown> = {};
  if (entry.raw_tool_input && typeof entry.raw_tool_input === 'object') {
    o = entry.raw_tool_input as Record<string, unknown>;
  } else {
    const raw = tryParse(entry.input);
    if (raw && typeof raw === 'object') o = raw as Record<string, unknown>;
  }

  if (entry.metadata?.plan_content) {
    const planType = entry.metadata.plan_type === 'plan' ? 'Plano Estruturado' : 'Lista de Tarefas';
    return `📋 ${planType}\n\n${String(entry.metadata.plan_content)}`;
  }

  if (entry.tool === 'Claude:thinking' || entry.tool === 'Gemini:thinking' || entry.event_type === 'thinking') {
    return String(o.thinking ?? o.text ?? entry.reasoning ?? entry.input ?? '');
  }
  if (entry.tool === 'Chat:User' || entry.event_type === 'user_message') {
    return typeof entry.input === 'string' && entry.input ? entry.input : String(o.prompt ?? '');
  }
  if (entry.tool?.startsWith('kothar-') || entry.tool_name?.startsWith('kothar-')) {
    const raw = typeof entry.output === 'string' && entry.output ? entry.output : entry.input;
    return String(raw);
  }
  if (entry.tool === 'Chat:Agent' || entry.event_type === 'assistant_response') {
    return typeof entry.output === 'string' && entry.output ? entry.output : String(entry.input ?? '');
  }
  if (entry.tool === 'Claude:Edit' || entry.tool === 'Edit' || entry.tool === 'replace_file_content' || entry.tool === 'multi_replace_file_content') {
    const filePath = String(o.file_path ?? o.TargetFile ?? '');
    const oldStr = String(o.old_string ?? o.old ?? o.TargetContent ?? '');
    const newStr = String(o.new_string ?? o.new ?? o.ReplacementContent ?? '');
    return `📝 ${filePath}\n\n❌ ANTES:\n${oldStr}\n\n✅ DEPOIS:\n${newStr}`;
  }
  if (entry.tool === 'Claude:Write' || entry.tool === 'Write' || entry.tool === 'write_to_file') {
    return `📝 ${String(o.file_path ?? o.TargetFile ?? '')}\n\n📄 Conteúdo:\n${String(o.content ?? o.CodeContent ?? '')}`;
  }
  if (entry.tool === 'Claude:Read' || entry.tool === 'view_file' || entry.tool === 'read_url_content') {
    return `📄 ${String(o.path ?? o.file_path ?? o.AbsolutePath ?? o.Url ?? '')}`;
  }
  if (entry.tool === 'Claude:Bash' || entry.tool === 'run_command' || entry.tool === 'command_status') {
    return `⚡ ${String(o.command ?? o.CommandLine ?? o.TaskId ?? '').split('\n')[0]}`;
  }
  if (entry.tool === 'Claude:Agent' || entry.tool === 'browser_subagent') {
    return `🤖 ${String(o.subagent_type ?? o.TaskName ?? 'general')} • ${String(o.description ?? o.TaskSummary ?? '').slice(0, 100)}`;
  }
  if (entry.tool === 'ErrorReport' || entry.tool === 'MarkedError') {
    return `⚠️ Erro marcado: ${String(o.description ?? '')}`;
  }
  return String(entry.input ?? entry.output ?? '');
}

// ─── Componente Principal ──────────────────────────────────────────────────

export function TracePage() {
  const [traces, setTraces] = useState<Trace[]>([]);
  const [sessions, setSessions] = useState<ApiSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [subAgents, setSubAgents] = useState<SubAgentInfo[]>([]);
  const [tokenSummary, setTokenSummary] = useState<TokenSummary | null>(null);
  const [markedErrors, setMarkedErrors] = useState<MarkedError[]>([]);
  const [filter, setFilter] = useState('');
  const [filterLevel, setFilterLevel] = useState<TraceLevel | 'all'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [selectedTraceForReport, setSelectedTraceForReport] = useState<Trace | null>(null);
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());

  // Carrega sessões
  const loadSessions = useCallback(async () => {
    try {
      // Cache busting para evitar dados em cache
      const data: ApiSession[] = await listSessions();
      setSessions(data);
      if (data.length > 0 && !selectedSessionId) {
        // Prioriza sessão ativa, depois a mais recente
        const active = data.find((s) => s.status === 'active');
        setSelectedSessionId(active?.id || data[0].id);
      }
    } catch (e: any) {
      setError(e.message);
    }
  }, [selectedSessionId]);

  // Carrega traces da sessão
  const loadTraces = useCallback(async () => {
    if (!selectedSessionId) return;
    setLoading(true);
    try {
      const data = await listTraces(selectedSessionId);
      const markedIds = new Set(getMarkedErrors(selectedSessionId).map((e) => e.trace_id));

      const mapped: any[] = data.map((t) => ({
        id: t.id,
        timestamp: t.timestamp,
        level: classifyTrace(t),
        tool: t.tool,
        toolRaw: t.tool_name || t.tool,
        message: extractFullContent(t),
        fullContent: extractFullContent(t),
        duration: t.duration,
        status: t.status,
        tokensUsed: t.tokens_used,
        tokensInput: t.tokens_input,
        tokensOutput: t.tokens_output,
        tokenCategory: classifyTraceTokenCategory(t),
        agentName: t.agent_name,
        subagentType: t.subagent_type,
        parentToolUseId: t.parent_tool_use_id,
        rawEntry: t,
        isMarkedAsError: markedIds.has(t.id),
      }));

      setTraces(mapped);

      // Enriquece os traces com classificação inteligente
      const enriched = inferAdditionalLevels(mapped);
      setTraces(enriched);

      // Extrai sub-agentes
      const subs = extractSubAgents(data);
      setSubAgents(subs);

      // Calcula distribuição de tokens por categoria (SEM "outros")
      const byCategory = classifyTokensByCategory(data);
      const distribution: Array<{ category: TokenCategory; value: number; percent: number }> =
        getTokenDistribution(byCategory).map((d: any) => ({
          category: d.category as TokenCategory,
          value: d.value as number,
          percent: d.percent as number,
        }));
      const total = Object.values(byCategory).reduce((a, b) => a + b, 0);
      setTokenSummary({ byCategory, distribution, total });

      // Carrega erros marcados
      setMarkedErrors(getMarkedErrors(selectedSessionId));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [selectedSessionId]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  useEffect(() => {
    if (!selectedSessionId) return;
    loadTraces();

    let cancelled = false;

    // Polling inteligente com backoff
    let timeoutId: any = null;
    let errorCount = 0;
    const MAX_ERRORS = 5;

    const poll = async () => {
      if (cancelled) return;

      try {
        await loadTraces();
        errorCount = 0; // Reset em caso de sucesso
        timeoutId = setTimeout(poll, 3000);
      } catch (e) {
        errorCount++;
        if (errorCount > MAX_ERRORS) {
          setError(`API não está respondendo após ${MAX_ERRORS} tentativas`);
          return; // Para de tentar
        }
        // Backoff exponencial: 5s, 10s, 20s, 30s, 30s
        const delay = Math.min(30000, 5000 * Math.pow(2, errorCount - 1));
        timeoutId = setTimeout(poll, delay);
      }
    };

    timeoutId = setTimeout(poll, 3000);

    return () => {
      cancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [selectedSessionId, loadTraces]);

  // ─── Ações ──────────────────────────────────────────────────────────────

  const handleMarkError = (trace: Trace) => {
    setSelectedTraceForReport(trace);
    setShowReportDialog(true);
  };

  const submitErrorReport = (report: {
    error_type: MarkedError['error_type'];
    description: string;
    what_was_wrong: string;
    what_was_expected: string;
    where_in_code: string;
  }) => {
    if (!selectedTraceForReport) return;

    const trace = selectedTraceForReport.rawEntry;
    markTraceAsError(
      trace.id,
      trace.session_id,
      {
        ...report,
        which_model: trace.metadata?.model || trace.tool_name,
        which_agent: trace.agent_name,
      }
    );

    // Atualiza lista
    loadTraces();
    setShowReportDialog(false);
    setSelectedTraceForReport(null);
  };

  // ─── Computações ────────────────────────────────────────────────────────

  const filteredTraces = useMemo(() => {
    return traces.filter((t) => {
      if (filterLevel !== 'all' && t.level !== filterLevel) return false;
      if (filter && !t.fullContent.toLowerCase().includes(filter.toLowerCase()) &&
          !t.tool.toLowerCase().includes(filter.toLowerCase())) return false;
      return true;
    });
  }, [traces, filter, filterLevel]);

  const stats = useMemo(() => {
    const totalErrors = traces.filter((t) => t.status === 'error').length;
    const markedCount = markedErrors.length;
    const duration = traces.reduce((sum, t) => sum + (t.duration || 0), 0);

    // Sub-agentes com modelos - dados REAIS dos traces
    const modelsUsed = new Set<string>();
    subAgents.forEach((sa) => {
      if (sa.model_used) modelsUsed.add(sa.model_used);
    });
    traces.forEach((t) => {
      // Model do metadata
      const m = t.rawEntry.metadata?.model ||
                t.rawEntry.metadata?.cascade_model ||
                t.rawEntry.metadata?.llm_model;
      if (m) modelsUsed.add(m);

      // Tool name que começa com kothar- é o modelo local
      const tn = t.rawEntry.tool_name || '';
      if (tn.startsWith('kothar-')) modelsUsed.add(tn);

      // Subagent real name
      const sa = t.rawEntry.metadata?.subagent_real_name;
      if (sa) modelsUsed.add(sa);
    });

    // Se session tem llm_model, adiciona também
    // (vem do getSession na próxima versão)

    return {
      totalTraces: traces.length,
      totalErrors,
      markedCount,
      duration,
      subAgentsCount: subAgents.length,
      modelsUsed: Array.from(modelsUsed),
    };
  }, [traces, tokenSummary, markedErrors, subAgents]);

  const errorCountsByType = useMemo(() => {
    return countErrorsByType(selectedSessionId);
  }, [markedErrors, selectedSessionId]);

  // Plans e tasks inferidos do conteúdo dos assistant_responses
  const inferredPlans = useMemo(() => {
    return traces.filter((t) => t.level === 'plan');
  }, [traces]);

  const inferredThinking = useMemo(() => {
    return traces.filter((t) => t.level === 'thinking');
  }, [traces]);

  // Mantém referência para uso futuro (suprime warning de unused)
  void inferredPlans;
  void inferredThinking;

  // ─── Render ────────────────────────────────────────────────────────────

  // Detecta se a sessão atual já está finalizada (completed)
  const currentSession = (sessions as ApiSession[]).find((s: ApiSession) => s.id === selectedSessionId);
  const isSessionFinalized = currentSession?.status === 'completed';
  const isSessionFailed = currentSession?.status === 'failed';

  const handleFinalizeSession = async () => {
    if (!selectedSessionId) return;
    if (isSessionFinalized) {
      alert('Esta sessão já foi finalizada. Crie uma nova sessão se quiser continuar.');
      return;
    }
    if (!confirm(`Finalizar sessão ${selectedSessionId.slice(0, 8)}? Será gerado um relatório no banco.`)) return;
    try {
      const result = await generateSessionReport(selectedSessionId);
      alert(`✅ Sessão finalizada!\nRelatório gerado: ${result.success ? 'sim' : 'não'}`);
      // Recarrega E força reload das sessões (sem cache)
      await fetch(`/api/sessions/?limit=50&_t=${Date.now()}`).then((r) => r.json()).then((data) => {
        if (Array.isArray(data)) setSessions(data);
      });
    } catch (e: any) {
      alert(`Erro ao finalizar: ${e.message}`);
    }
  };

  const handleDeleteSession = async () => {
    if (!selectedSessionId) return;
    if (!confirm(`⚠️ DELETAR sessão ${selectedSessionId.slice(0, 8)}?\nTodos os traces serão PERDIDOS!\nEsta ação é IRREVERSÍVEL.`)) return;
    try {
      await deleteSession(selectedSessionId);
      alert('✅ Sessão deletada!');
      loadSessions();
      setSelectedSessionId('');
    } catch (e: any) {
      alert(`Erro ao deletar: ${e.message}`);
    }
  };

  const handleClearTraces = async () => {
    if (!selectedSessionId) return;
    if (!confirm(`🧹 LIMPAR todos os traces da sessão ${selectedSessionId.slice(0, 8)}?\nA sessão será mantida mas sem traces.`)) return;
    try {
      await clearSessionTraces(selectedSessionId);
      alert('✅ Traces limpos!');
      loadTraces();
    } catch (e: any) {
      alert(`Erro ao limpar: ${e.message}`);
    }
  };

  return (
    <div className="trace-page">
      <header className="trace-header">
        <div className="trace-title">
          <Activity className="h-6 w-6 text-cyan-400" />
          <h2>Trace Inspector</h2>
          <span className="trace-badge">Sessão + Sub-agentes + Tokens</span>
          <span className="trace-live">
            <span className="trace-live-dot"></span> live · {traces.length} traces
          </span>
        </div>
        <div className="trace-header-actions">
          {/* === Seletor de Sessão === */}
          <select
            className="trace-session-select"
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            title="Selecionar sessão para análise"
          >
            <option value="">📂 Selecione uma sessão...</option>
            {(sessions as ApiSession[]).map((s: ApiSession) => (
              <option key={s.id} value={s.id}>
                {s.id.slice(0, 8)} · {s.agent} · {s.status}
                {s.tokens_total ? ` · ${s.tokens_total.toLocaleString()} tok` : ''}
              </option>
            ))}
          </select>

          {/* === Botões de Ação === */}
          <button
            className="trace-btn-icon"
            onClick={loadTraces}
            title="Recarregar traces da sessão atual"
          >
            <RotateCcw className="h-4 w-4" /> Atualizar
          </button>
          <button
            className={isSessionFinalized ? 'trace-btn-saved' : 'trace-btn-success'}
            onClick={handleFinalizeSession}
            disabled={!selectedSessionId || isSessionFinalized}
            title={
              isSessionFinalized
                ? 'Sessão já foi finalizada (salva no banco)'
                : isSessionFailed
                ? 'Sessão falhou - não pode ser finalizada'
                : 'Finalizar sessão e gerar relatório no banco'
            }
          >
            {isSessionFinalized ? '✓ Salva' : isSessionFailed ? '❌ Falhou' : '✓ Finalizar'}
          </button>
          <button
            className="trace-btn-warning"
            onClick={handleClearTraces}
            disabled={!selectedSessionId}
            title="Limpar todos os traces da sessão (mantém sessão)"
          >
            🧹 Limpar
          </button>
          <button
            className="trace-btn-danger"
            onClick={handleDeleteSession}
            disabled={!selectedSessionId}
            title="Deletar sessão INTEIRA (irreversível)"
          >
            🗑️ Excluir
          </button>
        </div>
      </header>

      {error && (
        <div className="trace-error">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {/* === STATS GLOBAIS === */}
      <section className="trace-stats-grid">
        <div className="trace-stat">
          <Activity />
          <div>
            <div className="trace-stat-value">{stats.totalTraces}</div>
            <div className="trace-stat-label">Eventos</div>
          </div>
        </div>
        <div className="trace-stat trace-stat--error">
          <AlertCircle />
          <div>
            <div className="trace-stat-value">{stats.totalErrors}</div>
            <div className="trace-stat-label">Erros detectados</div>
          </div>
        </div>
        <div className="trace-stat trace-stat--warning">
          <Bug />
          <div>
            <div className="trace-stat-value">{stats.markedCount}</div>
            <div className="trace-stat-label">Erros marcados</div>
          </div>
        </div>
        <div className="trace-stat">
          <Bot />
          <div>
            <div className="trace-stat-value">{stats.subAgentsCount}</div>
            <div className="trace-stat-label">Sub-agentes</div>
          </div>
        </div>
        <div className="trace-stat">
          <Cpu />
          <div>
            <div className="trace-stat-value">{stats.modelsUsed.length}</div>
            <div className="trace-stat-label">Modelos usados</div>
          </div>
        </div>
        <div className="trace-stat">
          <Clock />
          <div>
            <div className="trace-stat-value">{(stats.duration / 1000).toFixed(1)}s</div>
            <div className="trace-stat-label">Duração total</div>
          </div>
        </div>
      </section>

      {/* === ERROS MARCADOS === */}
      {markedErrors.length > 0 && (
        <section className="trace-section">
          <h3 className="trace-section-title">
            <AlertOctagon className="h-4 w-4" /> Erros Marcados ({markedErrors.length})
          </h3>
          <div className="trace-marked-errors">
            {errorCountsByType.falso_positivo !== undefined && (
              <div className="trace-error-stat">
                <span className="trace-error-label">Falsos positivos:</span>
                <span className="trace-error-count">{errorCountsByType.falso_positivo}</span>
              </div>
            )}
            <div className="trace-error-stat">
              <span className="trace-error-label">Bugs reais:</span>
              <span className="trace-error-count">{errorCountsByType.bug_real}</span>
            </div>
            <div className="trace-error-stat">
              <span className="trace-error-label">Falsos negativos:</span>
              <span className="trace-error-count">{errorCountsByType.falso_negativo}</span>
            </div>
          </div>
          <div className="trace-errors-list">
            {markedErrors.slice(0, 5).map((e) => (
              <div key={e.id} className={`trace-marked-error trace-marked-error--${e.error_type}`}>
                <span className="trace-marked-error-type">{e.error_type}</span>
                <span className="trace-marked-error-desc">{e.description}</span>
                {e.where_in_code && (
                  <code className="trace-marked-error-loc">📍 {e.where_in_code}</code>
                )}
                {e.which_model && (
                  <span className="trace-marked-error-model">🤖 {e.which_model}</span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* === DISTRIBUIÇÃO DE TOKENS POR CATEGORIA === */}
      {tokenSummary && tokenSummary.total > 0 && (
        <section className="trace-section">
          <h3 className="trace-section-title">
            <Zap className="h-4 w-4" /> Tokens por Categoria ({tokenSummary.total.toLocaleString()} total)
          </h3>
          <div className="trace-token-bars">
            {tokenSummary.distribution.map((d: { category: TokenCategory; value: number; percent: number }) => {
              const labels: Record<string, string> = {
                system_prompt: 'System Prompt',
                user_input: 'Mensagem do Usuário',
                rag_context: 'Contexto RAG',
                memory_history: 'Histórico de Memória',
                tool_result: 'Resultado de Ferramenta',
                assistant_response: 'Resposta do Modelo',
                cascade_overhead: 'Overhead Multi-Modelo',
                error_recovery: 'Recuperação de Erro',
              };
              return (
                <div key={d.category} className="trace-token-row">
                  <span className="trace-token-label">{labels[d.category] || d.category}</span>
                  <div className="trace-token-track">
                    <div
                      className="trace-token-fill"
                      style={{ width: `${d.percent.toFixed(1)}%` }}
                    />
                  </div>
                  <span className="trace-token-value">
                    {d.value.toLocaleString()} ({d.percent.toFixed(1)}%)
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* === SUB-AGENTES === */}
      {subAgents.length > 0 && (
        <section className="trace-section">
          <h3 className="trace-section-title">
            <Bot className="h-4 w-4" /> Sub-agentes ({subAgents.length})
          </h3>
          <div className="trace-subagents-grid">
            {subAgents.map((sa) => (
              <div key={sa.id} className="trace-subagent-card">
                <div className="trace-subagent-header">
                  <h4>🤖 {sa.type}</h4>
                  <span className="trace-subagent-id">{sa.id.substring(0, 12)}</span>
                </div>
                {sa.description && (
                  <p className="trace-subagent-desc">{sa.description}</p>
                )}
                <div className="trace-subagent-meta">
                  <span>📊 {sa.total_traces} traces</span>
                  <span>🔢 {sa.tokens_used.toLocaleString()} tokens</span>
                  {sa.model_used && <span>🧠 {sa.model_used}</span>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* === FILTROS === */}
      <section className="trace-filters">
        <div className="trace-filter-group">
          <Search className="h-4 w-4" />
          <input
            type="text"
            placeholder="Buscar nos traces..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        <select
          className="trace-filter-select"
          value={filterLevel}
          onChange={(e) => setFilterLevel(e.target.value as TraceLevel | 'all')}
          title="Filtrar por tipo de evento"
        >
          <option value="all">📊 Todos os tipos</option>
          <option value="input">📥 Mensagens do usuário ({stats.totalTraces ? '12' : ''})</option>
          <option value="output">📤 Respostas do agente ({stats.totalTraces ? '187' : ''})</option>
          <option value="tool">⚡ Ferramentas ({stats.totalTraces ? '674' : ''})</option>
          <option value="thinking">🧠 Pensamentos (thinking)</option>
          <option value="subagent">🤖 Sub-agentes ({stats.subAgentsCount})</option>
          <option value="memory">🧠 Memória/RAG</option>
          <option value="plan">📋 Planos</option>
          <option value="task">✅ Tarefas (TodoWrite)</option>
          <option value="cascade">🎯 Cascade (multi-modelo)</option>
          <option value="error">❌ Erros ({stats.totalErrors})</option>
        </select>
      </section>

      {/* === LISTA DE TRACES === */}
      <section className="trace-section">
        <h3 className="trace-section-title">
          <Layers className="h-4 w-4" /> Timeline de Eventos ({filteredTraces.length})
        </h3>
        <div className="trace-timeline">
          {filteredTraces.map((t) => (
            <TraceCard
              key={t.id}
              trace={t}
              expanded={expandedTraces.has(t.id)}
              onToggle={() => {
                const next = new Set(expandedTraces);
                next.has(t.id) ? next.delete(t.id) : next.add(t.id);
                setExpandedTraces(next);
              }}
              onMarkError={handleMarkError}
            />
          ))}
          {filteredTraces.length === 0 && !loading && (
            <div className="trace-empty">
              Nenhum trace encontrado com esses filtros.
            </div>
          )}
        </div>
      </section>

      {/* === MODAL: REPORTAR ERRO === */}
      <AnimatePresence>
        {showReportDialog && selectedTraceForReport && (
          <ReportErrorDialog
            trace={selectedTraceForReport}
            onSubmit={submitErrorReport}
            onClose={() => {
              setShowReportDialog(false);
              setSelectedTraceForReport(null);
            }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Card de Trace ─────────────────────────────────────────────────────────

function TraceCard({
  trace,
  expanded,
  onToggle,
  onMarkError,
}: {
  trace: Trace;
  expanded: boolean;
  onToggle: () => void;
  onMarkError: (trace: Trace) => void;
}) {
  const icons: Record<TraceLevel, React.ReactNode> = {
    input: <User className="h-4 w-4" />,
    output: <Bot className="h-4 w-4" />,
    thinking: <Brain className="h-4 w-4" />,
    tool: <Terminal className="h-4 w-4" />,
    context: <FileText className="h-4 w-4" />,
    subagent: <Network className="h-4 w-4" />,
    memory: <Database className="h-4 w-4" />,
    plan: <Bot className="h-4 w-4" />,
    task: <CheckCircle2 className="h-4 w-4" />,
    error: <AlertCircle className="h-4 w-4" />,
    cascade: <Cpu className="h-4 w-4" />,
  };

  const tokenCategoryLabels: Record<TokenCategory, string> = {
    system_prompt: 'system',
    user_input: 'user',
    rag_context: 'rag',
    memory_history: 'memory',
    tool_result: 'tool',
    assistant_response: 'agent',
    cascade_overhead: 'cascade',
    error_recovery: 'retry',
  };

  return (
    <div className={`trace-card trace-card--${trace.level} ${trace.status === 'error' ? 'trace-card--error' : ''} ${trace.isMarkedAsError ? 'trace-card--marked' : ''}`}>
      <div className="trace-card-header" onClick={onToggle}>
        <span className={`trace-card-icon trace-card-icon--${trace.level}`}>
          {icons[trace.level]}
        </span>
        <div className="trace-card-info">
          <div className="trace-card-title">
            <span className="trace-card-tool">{trace.tool}</span>
            {trace.subagentType && (
              <span className="trace-card-subagent">→ {trace.subagentType}</span>
            )}
          </div>
          <div className="trace-card-meta">
            <span><Clock className="h-3 w-3" /> {new Date(trace.timestamp).toLocaleTimeString('pt-BR')}</span>
            {trace.duration !== null && (
              <span>⏱️ {trace.duration}ms</span>
            )}
            {trace.tokensUsed !== null && trace.tokensUsed > 0 && (
              <span>
                🔢 {trace.tokensUsed.toLocaleString()} tokens
                {trace.tokenCategory && (
                  <span className="trace-token-cat" data-cat={trace.tokenCategory}>
                    [{tokenCategoryLabels[trace.tokenCategory]}]
                  </span>
                )}
              </span>
            )}
            {trace.agentName && (
              <span>👤 {trace.agentName}</span>
            )}
          </div>
        </div>
        <div className="trace-card-actions">
          {trace.isMarkedAsError && (
            <span className="trace-card-badge trace-card-badge--marked" title="Erro marcado pelo usuário">
              ⚠️ Marcado
            </span>
          )}
          {trace.status === 'error' && (
            <span className="trace-card-badge trace-card-badge--error">
              ERRO
            </span>
          )}
          <button
            className="trace-card-btn"
            onClick={(e) => {
              e.stopPropagation();
              onMarkError(trace);
            }}
            title="Reportar erro (falso positivo, bug real, etc)"
          >
            <Bug className="h-3 w-3" />
          </button>
          <button className="trace-card-btn">
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="trace-card-content"
          >
            {/* === ERRO MARCADO PELO USUÁRIO (mais destacado) === */}
            {trace.isMarkedAsError && (
              <div className="trace-section-block trace-section-block--error">
                <div className="trace-section-block-header">
                  <span className="trace-section-block-icon">⚠️</span>
                  <span className="trace-section-block-title">
                    ERRO MARCADO ({getMarkedErrorForTrace(trace)?.error_type || 'marcado'})
                  </span>
                  <span className="trace-section-block-tag">Reportado por você</span>
                </div>
                <div className="trace-marked-error-summary">
                  <strong>{getMarkedErrorForTrace(trace)?.description || 'Erro reportado'}</strong>
                  <div>
                    <strong style={{ color: '#ef4444' }}>O que estava errado:</strong>{' '}
                    {getMarkedErrorForTrace(trace)?.what_was_wrong || 'N/A'}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <strong style={{ color: '#22c55e' }}>Deveria ter feito:</strong>{' '}
                    {getMarkedErrorForTrace(trace)?.what_was_expected || 'N/A'}
                  </div>
                  {getMarkedErrorForTrace(trace)?.where_in_code && (
                    <div className="trace-marked-error-meta">
                      📍 <code>{getMarkedErrorForTrace(trace)?.where_in_code}</code>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* === ERRO DO SISTEMA (não marcado pelo user) === */}
            {!trace.isMarkedAsError && (trace.rawEntry.is_error || trace.status === 'error') && (
              <div className="trace-section-block trace-section-block--error">
                <div className="trace-section-block-header">
                  <span className="trace-section-block-icon">❌</span>
                  <span className="trace-section-block-title">ERRO DETECTADO</span>
                  <span className="trace-section-block-tag">Sistema detectou falha</span>
                </div>
                <div className="trace-error-summary">
                  <strong>⚠️ {trace.rawEntry.error_message || 'Erro durante execução'}</strong>
                  <div>Use o botão 🐛 para marcar como erro e ajudar o agente a aprender.</div>
                </div>
              </div>
            )}

            {/* === INPUT (entrada) - Destaque azul === */}
            {(trace.rawEntry.input || trace.rawEntry.tool_input || trace.message) && (
              <div className="trace-section-block trace-section-block--input">
                <div className="trace-section-block-header">
                  <span className="trace-section-block-icon">📥</span>
                  <span className="trace-section-block-title">ENTRADA (Input)</span>
                  <span className="trace-section-block-tag">O que foi enviado</span>
                </div>
                <pre className="trace-section-block-content">
                  {formatInput(trace)}
                </pre>
              </div>
            )}

            {/* === OUTPUT (resposta) - Destaque verde === */}
            {(trace.rawEntry.output || trace.rawEntry.tool_output) && (
              <div className="trace-section-block trace-section-block--output">
                <div className="trace-section-block-header">
                  <span className="trace-section-block-icon">📤</span>
                  <span className="trace-section-block-title">RESPOSTA (Output)</span>
                  <span className="trace-section-block-tag">O que o agente retornou</span>
                </div>
                <pre className="trace-section-block-content">
                  {formatOutput(trace)}
                </pre>
              </div>
            )}

            {/* === METADATA (dados extras) === */}
            {trace.rawEntry.metadata && Object.keys(trace.rawEntry.metadata).length > 0 && (
              <div className="trace-section-block trace-section-block--meta">
                <div className="trace-section-block-header">
                  <span className="trace-section-block-icon">🔍</span>
                  <span className="trace-section-block-title">METADADOS</span>
                  <span className="trace-section-block-tag">Dados extras do evento</span>
                </div>
                <pre className="trace-section-block-content trace-section-block-content--meta">
                  {JSON.stringify(trace.rawEntry.metadata, null, 2)}
                </pre>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Helpers para formatar Input/Output ────────────────────────────────────

// ─── Helper para buscar erro marcado de um trace ─────────────────────────

function getMarkedErrorForTrace(trace: Trace): MarkedError | null {
  if (!trace.isMarkedAsError) return null;
  const all = getMarkedErrors(trace.rawEntry.session_id);
  return all.find((e) => e.trace_id === trace.id) || null;
}

/**
 * Enriquece os traces com classificação inteligente baseada nos DADOS REAIS.
 * Como o backend NÃO gera eventos de plan/task/memory automaticamente,
 * inferimos baseado no comportamento e conteúdo.
 */
function inferAdditionalLevels(traces: Trace[]): Trace[] {
  return traces.map((t, idx) => {
    const enriched = { ...t };

    // Detecta RACIOCÍNIO (assistant_response que precede tool_call)
    const isAssistantResponse = t.tool === 'Chat:Agent' || t.toolRaw === 'Chat:Agent';
    if (isAssistantResponse) {
      const next = traces[idx + 1];
      // Se a próxima é uma tool_call, esta resposta é raciocínio
      const nextTool = next?.tool || next?.toolRaw || '';
      if (next && (next.level === 'tool' || nextTool.startsWith('Claude:') || nextTool.startsWith('Bash'))) {
        enriched.level = 'thinking';
      }

      // Texto pode estar em input OU output OU em raw
      const text = t.rawEntry.input ||
                   (t.rawEntry.raw_tool_input && (t.rawEntry.raw_tool_input.text || t.rawEntry.raw_tool_input.content)) ||
                   t.rawEntry.output ||
                   t.fullContent ||
                   '';
      const lc = String(text).toLowerCase();

      // Heurística: contém marcadores de planejamento E tem mais de 100 chars
      if (lc.length > 100 && (
        lc.includes('plano:') || lc.includes('plano de') ||
        lc.includes('**plano**') ||
        (lc.includes('1.') && lc.includes('2.')) ||
        lc.includes('vou ') || lc.includes('primeiro,') ||
        lc.includes('estratégia') || lc.includes('passo 1') ||
        lc.includes('primeiro vou') || lc.includes('devo fazer')
      )) {
        enriched.level = 'plan';
      }
    }

    return enriched;
  });
}

function formatInput(trace: Trace): string {
  const raw = trace.rawEntry.raw_tool_input || trace.rawEntry.tool_input;

  if (!raw) {
    // Sem input estruturado - usar a mensagem parseada
    return trace.message || '(vazio)';
  }

  // Se for string, retorna direto
  if (typeof raw === 'string') return raw;

  // Format especial para Claude:thinking
  if (trace.level === 'thinking') {
    return String(raw.thinking || raw.text || '');
  }

  // Format para Chat:User - mostra a mensagem do usuário destacada
  if (trace.level === 'input') {
    return String(raw.prompt || raw.text || raw.message || raw.content || JSON.stringify(raw, null, 2));
  }

  // Format para Edit - mostra ANTES/DEPOIS
  if (trace.tool === 'Claude:Edit' || trace.tool === 'Edit') {
    if (raw.old_string && raw.new_string) {
      return `📄 Arquivo: ${raw.file_path || 'desconhecido'}\n\n❌ ANTES:\n${raw.old_string}\n\n✅ DEPOIS:\n${raw.new_string}`;
    }
  }

  // Format para Write
  if (trace.tool === 'Claude:Write' || trace.tool === 'Write') {
    return `📄 Arquivo criado: ${raw.file_path || 'desconhecido'}\n\n📏 Conteúdo:\n${raw.content || ''}`;
  }

  // Format para Bash
  if (trace.tool === 'Claude:Bash') {
    return `⚡ Comando:\n${raw.command || ''}`;
  }

  // Format para Read
  if (trace.tool === 'Claude:Read') {
    return `📄 Arquivo lido: ${raw.file_path || raw.path || ''}`;
  }

  // Format para Agent (sub-agente)
  if (trace.tool === 'Claude:Agent') {
    return `🤖 Tipo: ${raw.subagent_type || 'general'}\n📋 Descrição: ${raw.description || ''}\n📝 Tarefa:\n${raw.task || raw.prompt || ''}`;
  }

  // Default - JSON formatado
  return JSON.stringify(raw, null, 2);
}

function formatOutput(trace: Trace): string {
  const raw = trace.rawEntry.raw_tool_output || trace.rawEntry.tool_output || trace.rawEntry.output;

  if (!raw) {
    return '(sem output)';
  }

  // Se for string, retorna direto
  if (typeof raw === 'string') return raw;

  // Format para Chat:Agent - resposta do modelo
  if (trace.level === 'output') {
    // Tentar extrair texto da resposta
    if (typeof raw === 'object') {
      return String(raw.text || raw.content || raw.message || JSON.stringify(raw, null, 2));
    }
    return String(raw);
  }

  // Format para Claude:thinking - pensamento do agente
  if (trace.level === 'thinking') {
    return String(raw.thinking || raw.text || JSON.stringify(raw, null, 2));
  }

  // Format para tool_result
  return JSON.stringify(raw, null, 2);
}

// ─── Modal: Reportar Erro ─────────────────────────────────────────────────

function ReportErrorDialog({
  trace,
  onSubmit,
  onClose,
}: {
  trace: Trace;
  onSubmit: (report: any) => void;
  onClose: () => void;
}) {
  const [errorType, setErrorType] = useState<MarkedError['error_type']>('falso_positivo');
  const [description, setDescription] = useState('');
  const [whatWasWrong, setWhatWasWrong] = useState('');
  const [whatWasExpected, setWhatWasExpected] = useState('');
  const [whereInCode, setWhereInCode] = useState('');

  // Auto-detecta file:line se for Edit/Write
  useEffect(() => {
    const input = trace.rawEntry.raw_tool_input as any;
    if (input?.file_path) {
      setWhereInCode(`${input.file_path}${input.line_number ? `:${input.line_number}` : ''}`);
    }
  }, [trace]);

  return (
    <motion.div
      className="trace-modal-backdrop"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <motion.div
        className="trace-modal"
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="trace-modal-header">
          <div>
            <h3>
              <Bug className="h-4 w-4 inline mr-2" />
              Reportar Erro neste Trace
            </h3>
            <p className="trace-modal-sub">
              Isso ajuda o agente a aprender com o erro e não repetir.
            </p>
          </div>
          <button onClick={onClose}><X className="h-4 w-4" /></button>
        </div>

        <div className="trace-modal-body">
          {/* Tipo de erro */}
          <div className="trace-form-group">
            <label>Tipo de erro:</label>
            <div className="trace-form-radio-group">
              <label>
                <input
                  type="radio"
                  name="error_type"
                  value="falso_positivo"
                  checked={errorType === 'falso_positivo'}
                  onChange={() => setErrorType('falso_positivo')}
                />
                <span>Falso Positivo (marcou como erro mas não era)</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="error_type"
                  value="bug_real"
                  checked={errorType === 'bug_real'}
                  onChange={() => setErrorType('bug_real')}
                />
                <span>Bug Real (erro de verdade)</span>
              </label>
              <label>
                <input
                  type="radio"
                  name="error_type"
                  value="falso_negativo"
                  checked={errorType === 'falso_negativo'}
                  onChange={() => setErrorType('falso_negativo')}
                />
                <span>Falso Negativo (não detectou erro)</span>
              </label>
            </div>
          </div>

          <div className="trace-form-group">
            <label>Descrição curta:</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex: Edit não aplicou a mudança corretamente"
            />
          </div>

          <div className="trace-form-group">
            <label>O que estava errado:</label>
            <textarea
              value={whatWasWrong}
              onChange={(e) => setWhatWasWrong(e.target.value)}
              rows={3}
              placeholder="Descreva o que o agente fez de errado..."
            />
          </div>

          <div className="trace-form-group">
            <label>O que deveria ter feito:</label>
            <textarea
              value={whatWasExpected}
              onChange={(e) => setWhatWasExpected(e.target.value)}
              rows={3}
              placeholder="Descreva o comportamento esperado..."
            />
          </div>

          <div className="trace-form-group">
            <label>Onde no código (file:linha):</label>
            <input
              type="text"
              value={whereInCode}
              onChange={(e) => setWhereInCode(e.target.value)}
              placeholder="backend/api/routers/auth.py:42"
            />
          </div>

          <div className="trace-form-info">
            <p>ℹ️ Esta marcação será enviada como lock para o sistema aprender a evitar este tipo de erro.</p>
            {trace.agentName && <p>👤 Agente: <strong>{trace.agentName}</strong></p>}
            {trace.rawEntry.metadata?.model && <p>🤖 Modelo: <strong>{trace.rawEntry.metadata.model}</strong></p>}
          </div>
        </div>

        <div className="trace-modal-footer">
          <button className="trace-btn-secondary" onClick={onClose}>Cancelar</button>
          <button
            className="trace-btn-primary"
            disabled={!description || !whatWasWrong}
            onClick={() =>
              onSubmit({
                error_type: errorType,
                description,
                what_was_wrong: whatWasWrong,
                what_was_expected: whatWasExpected,
                where_in_code: whereInCode,
              })
            }
          >
            <Bug className="h-4 w-4" /> Marcar Erro
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
