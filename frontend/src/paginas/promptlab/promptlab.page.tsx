import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  FlaskConical, Bot, Plus, Trash2, Play, Copy, Edit2, Save, X,
  Sparkles, ChevronDown, ChevronUp, Clock, Zap, Trophy
} from 'lucide-react';
import { promptLabApi, AgentPrompt, PromptVariant } from './promptlab.api';
import './promptlab.styles.css';

const AVAILABLE_MODELS = [
  'kothar-llama3:latest',
  'kothar-coder:latest',
  'kothar-deepseek:latest',
  'llama3.2:3b',
  'qwen2.5-coder:1.5b',
  'deepseek-r1:1.5b',
];

export function PromptLabPage() {
  const [knownPrompts, setKnownPrompts] = useState<AgentPrompt[]>([]);
  const [variants, setVariants] = useState<PromptVariant[]>([]);
  const [activeTab, setActiveTab] = useState<'known' | 'variants' | 'abtest'>('known');
  const [expandedPrompt, setExpandedPrompt] = useState<string | null>(null);
  const [editingVariant, setEditingVariant] = useState<PromptVariant | null>(null);
  const [testQuestion, setTestQuestion] = useState('');
  const [running, setRunning] = useState(false);

  useEffect(() => {
    setKnownPrompts(promptLabApi.listKnownPrompts());
    setVariants(promptLabApi.getVariants());
  }, []);

  // Fallback defensivo — se knownPrompts vier vazio, lista fallback
  const safeKnownPrompts = Array.isArray(knownPrompts) ? knownPrompts : [];

  const persistVariants = (next: PromptVariant[]) => {
    setVariants(next);
    next.forEach((v) => promptLabApi.saveVariant(v));
  };

  const createNewVariant = (fromPrompt?: AgentPrompt) => {
    const newVariant: PromptVariant = {
      id: `v_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      name: fromPrompt ? `Variante de ${fromPrompt.agent_name}` : 'Nova variante',
      system_prompt: fromPrompt?.system_prompt || '',
      model: fromPrompt?.model || 'kothar-gemma:latest',
      created_at: new Date().toISOString(),
      results: [],
    };
    setEditingVariant(newVariant);
  };

  const saveVariant = (v: PromptVariant) => {
    const next = [...variants.filter((x) => x.id !== v.id), v];
    persistVariants(next);
    setEditingVariant(null);
  };

  const deleteVariant = (id: string) => {
    const next = variants.filter((v) => v.id !== id);
    persistVariants(next);
    promptLabApi.deleteVariant(id);
  };

  const runVariant = async (variant: PromptVariant) => {
    if (!testQuestion.trim()) {
      alert('Digite uma pergunta para testar');
      return;
    }
    setRunning(true);
    const result = await promptLabApi.runVariant(variant, testQuestion);
    const updated: PromptVariant = {
      ...variant,
      results: [result, ...variant.results].slice(0, 20), // mantém últimos 20
    };
    saveVariant(updated);
    setRunning(false);
  };

  const runAllVariants = async () => {
    if (!testQuestion.trim()) {
      alert('Digite uma pergunta para testar');
      return;
    }
    setRunning(true);
    const updated = [...variants];
    for (let i = 0; i < updated.length; i++) {
      const result = await promptLabApi.runVariant(updated[i], testQuestion);
      updated[i] = {
        ...updated[i],
        results: [result, ...updated[i].results].slice(0, 20),
      };
    }
    persistVariants(updated);
    setRunning(false);
  };

  return (
    <div className="promptlab-page">
      <header className="promptlab-header">
        <div className="promptlab-title">
          <FlaskConical className="h-6 w-6 text-emerald-400" />
          <h2>Prompt Lab</h2>
          <span className="promptlab-badge">A/B Testing</span>
        </div>
        <button
          className="promptlab-btn-primary"
          onClick={() => createNewVariant()}
        >
          <Plus className="h-4 w-4" /> Nova variante
        </button>
      </header>

      <div className="promptlab-tabs">
        <button
          className={`promptlab-tab ${activeTab === 'known' ? 'promptlab-tab--active' : ''}`}
          onClick={() => setActiveTab('known')}
        >
          <Bot className="h-4 w-4" /> Prompts Conhecidos
        </button>
        <button
          className={`promptlab-tab ${activeTab === 'variants' ? 'promptlab-tab--active' : ''}`}
          onClick={() => setActiveTab('variants')}
        >
          <Sparkles className="h-4 w-4" /> Minhas Variantes ({variants.length})
        </button>
        <button
          className={`promptlab-tab ${activeTab === 'abtest' ? 'promptlab-tab--active' : ''}`}
          onClick={() => setActiveTab('abtest')}
        >
          <Trophy className="h-4 w-4" /> A/B Test
        </button>
      </div>

      {/* TAB: Prompts Conhecidos */}
      {activeTab === 'known' && (
        <section className="promptlab-section">
          <p className="promptlab-intro">
            System prompts oficiais usados pelos agentes. Clique para ver completo ou duplique como variante para editar.
          </p>
          <div className="promptlab-known-list">
            {safeKnownPrompts.map((p) => (
              <motion.div
                key={p.agent_name}
                className="promptlab-known-card"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="promptlab-known-header">
                  <div className="promptlab-known-info">
                    <div className="promptlab-known-name">
                      <Bot className="h-4 w-4" />
                      {p.agent_name}
                    </div>
                    <div className="promptlab-known-role">{p.agent_role}</div>
                    <div className="promptlab-known-source">
                      <span className={`promptlab-source-badge promptlab-source-badge--${p.source}`}>
                        {p.source}
                      </span>
                      {p.model && <span className="promptlab-known-model">{p.model}</span>}
                    </div>
                  </div>
                  <div className="promptlab-known-actions">
                    <button onClick={() => setExpandedPrompt(expandedPrompt === p.agent_name ? null : p.agent_name)}>
                      {expandedPrompt === p.agent_name ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                    <button onClick={() => createNewVariant(p)} title="Duplicar como variante">
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                {expandedPrompt === p.agent_name && (
                  <pre className="promptlab-known-content">{p.system_prompt}</pre>
                )}
              </motion.div>
            ))}
          </div>
        </section>
      )}

      {/* TAB: Variantes */}
      {activeTab === 'variants' && (
        <section className="promptlab-section">
          <div className="promptlab-test-bar">
            <input
              type="text"
              placeholder="Pergunta para testar todas as variantes (ex: 'Como organizar 3 projetos paralelos?')"
              value={testQuestion}
              onChange={(e) => setTestQuestion(e.target.value)}
            />
            <button
              className="promptlab-btn-run-all"
              onClick={runAllVariants}
              disabled={running || variants.length === 0}
            >
              {running ? 'Rodando...' : <><Play className="h-4 w-4" /> Testar todas</>}
            </button>
          </div>

          {variants.length === 0 && (
            <p className="promptlab-empty">
              Nenhuma variante ainda. Clique em "Nova variante" ou duplique um prompt conhecido.
            </p>
          )}

          <div className="promptlab-variants-list">
            {variants.map((v) => (
              <motion.div
                key={v.id}
                className="promptlab-variant-card"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="promptlab-variant-header">
                  <div>
                    <input
                      className="promptlab-variant-name"
                      value={v.name}
                      onChange={(e) => {
                        const next = variants.map((x) => x.id === v.id ? { ...x, name: e.target.value } : x);
                        setVariants(next);
                      }}
                      onBlur={() => persistVariants(variants)}
                    />
                    <div className="promptlab-variant-meta">
                      <span className="promptlab-variant-model">{v.model}</span>
                      <span>•</span>
                      <span>{v.results.length} testes</span>
                    </div>
                  </div>
                  <div className="promptlab-variant-actions">
                    <button onClick={() => runVariant(v)} disabled={running} title="Testar">
                      <Play className="h-4 w-4" />
                    </button>
                    <button onClick={() => setEditingVariant(v)} title="Editar">
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button onClick={() => deleteVariant(v.id)} title="Excluir">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <details className="promptlab-variant-prompt">
                  <summary>Ver system prompt</summary>
                  <pre>{v.system_prompt}</pre>
                </details>

                {v.results.length > 0 && (
                  <div className="promptlab-results">
                    <div className="promptlab-results-title">Último resultado:</div>
                    <div className="promptlab-result">
                      <div className="promptlab-result-meta">
                        <span title="Duração"><Clock className="h-3 w-3" /> {(v.results[0].duration_ms / 1000).toFixed(1)}s</span>
                        <span title="Tokens"><Zap className="h-3 w-3" /> {v.results[0].tokens_input}↓ {v.results[0].tokens_output}↑</span>
                      </div>
                      <div className="promptlab-result-content">{v.results[0].response}</div>
                    </div>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </section>
      )}

      {/* TAB: A/B Test */}
      {activeTab === 'abtest' && (
        <section className="promptlab-section">
          <p className="promptlab-intro">
            Compare variantes lado-a-lado com a mesma pergunta para descobrir qual prompt gera melhor resultado.
          </p>

          {variants.length < 2 ? (
            <p className="promptlab-empty">
              Crie pelo menos 2 variantes para rodar um A/B test.
            </p>
          ) : (
            <>
              <div className="promptlab-test-bar">
                <input
                  type="text"
                  placeholder="Pergunta para A/B test..."
                  value={testQuestion}
                  onChange={(e) => setTestQuestion(e.target.value)}
                />
                <button
                  className="promptlab-btn-run-all"
                  onClick={runAllVariants}
                  disabled={running}
                >
                  {running ? 'Rodando...' : <><Play className="h-4 w-4" /> Rodar A/B test</>}
                </button>
              </div>

              <div className="promptlab-ab-comparison">
                {variants.map((v) => (
                  <div key={v.id} className="promptlab-ab-col">
                    <div className="promptlab-ab-header">
                      <h4>{v.name}</h4>
                      <span className="promptlab-ab-model">{v.model}</span>
                    </div>
                    {v.results[0] ? (
                      <>
                        <div className="promptlab-ab-metrics">
                          <div className="promptlab-ab-metric">
                            <Clock className="h-4 w-4" />
                            <span>{(v.results[0].duration_ms / 1000).toFixed(1)}s</span>
                          </div>
                          <div className="promptlab-ab-metric">
                            <Zap className="h-4 w-4" />
                            <span>{v.results[0].tokens_output} tok</span>
                          </div>
                          <div className="promptlab-ab-metric">
                            <span>📏 {v.results[0].response.length} chars</span>
                          </div>
                        </div>
                        <div className="promptlab-ab-response">{v.results[0].response}</div>
                      </>
                    ) : (
                      <div className="promptlab-ab-empty">Sem resultado ainda</div>
                    )}
                  </div>
                ))}
              </div>

              {variants.length >= 2 && variants.every((v) => v.results.length > 0) && (
                <div className="promptlab-winner">
                  <Trophy className="h-5 w-5" />
                  <div>
                    <strong>Recomendação:</strong>{' '}
                    {(() => {
                      const fastest = variants.reduce((a, b) =>
                        (a.results[0]?.duration_ms || Infinity) < (b.results[0]?.duration_ms || Infinity) ? a : b
                      );
                      return `${fastest.name} respondeu mais rápido (${(fastest.results[0].duration_ms / 1000).toFixed(1)}s). Para resposta mais curta, compare tokens_output.`;
                    })()}
                  </div>
                </div>
              )}
            </>
          )}
        </section>
      )}

      {/* Modal de edição de variante */}
      {editingVariant && (
        <div className="promptlab-modal" onClick={() => setEditingVariant(null)}>
          <div className="promptlab-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="promptlab-modal-header">
              <h3>Editar variante</h3>
              <button onClick={() => setEditingVariant(null)}><X className="h-4 w-4" /></button>
            </div>
            <label>Nome</label>
            <input
              type="text"
              value={editingVariant.name}
              onChange={(e) => setEditingVariant({ ...editingVariant, name: e.target.value })}
            />
            <label>Modelo</label>
            <select
              value={editingVariant.model}
              onChange={(e) => setEditingVariant({ ...editingVariant, model: e.target.value })}
            >
              {AVAILABLE_MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <label>System Prompt</label>
            <textarea
              value={editingVariant.system_prompt}
              onChange={(e) => setEditingVariant({ ...editingVariant, system_prompt: e.target.value })}
              rows={20}
            />
            <div className="promptlab-modal-actions">
              <button onClick={() => setEditingVariant(null)}>Cancelar</button>
              <button className="promptlab-btn-primary" onClick={() => saveVariant(editingVariant)}>
                <Save className="h-4 w-4" /> Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
