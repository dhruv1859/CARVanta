import { useState, useEffect, useCallback, lazy } from 'react';

const API = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8001';

async function api(path: string, opts?: RequestInit) {
  try {
    const r = await fetch(`${API}${path}`, opts);
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

/* ─── Types ────────────────────────────────────────────────────────────── */
type Model = 'gnn' | 'transformer' | 'mlp' | 'vae' | 'lstm';

const MODEL_INFO: Record<Model, { icon: string; name: string; desc: string; color: string }> = {
  gnn: { icon: '🕸️', name: 'Graph Neural Network', desc: 'Protein interaction network target discovery', color: '#8B5CF6' },
  transformer: { icon: '🧬', name: 'Protein Transformer', desc: 'Amino acid sequence viability analysis', color: '#06B6D4' },
  mlp: { icon: '🧠', name: 'Neural Scorer', desc: 'MLP with Monte Carlo dropout uncertainty', color: '#10B981' },
  vae: { icon: '🔬', name: 'Multi-Omics VAE', desc: 'Variational autoencoder for omics integration', color: '#F59E0B' },
  lstm: { icon: '📈', name: 'LSTM Simulator', desc: 'Time-series treatment dynamics prediction', color: '#EF4444' },
};

/* ─── Styles ───────────────────────────────────────────────────────────── */
const S: Record<string, React.CSSProperties> = {
  page: { padding: '2rem', maxWidth: 1400, margin: '0 auto' },
  h1: { fontSize: '2rem', fontWeight: 700, marginBottom: 8, letterSpacing: '-0.03em' },
  subtitle: { color: '#94A3B8', marginBottom: 32, fontSize: '1rem' },
  modelGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16, marginBottom: 32 },
  modelCard: {
    padding: 20, borderRadius: 16, cursor: 'pointer', transition: 'all 0.3s ease',
    border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.03)',
  },
  modelCardActive: {
    padding: 20, borderRadius: 16, cursor: 'pointer', transition: 'all 0.3s ease',
    border: '2px solid', background: 'rgba(255,255,255,0.06)', transform: 'translateY(-2px)',
    boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
  },
  modelIcon: { fontSize: '2rem', marginBottom: 8 },
  modelName: { fontWeight: 600, fontSize: '1.05rem', marginBottom: 4 },
  modelDesc: { fontSize: '0.8rem', color: '#94A3B8' },
  panel: {
    padding: 28, borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)',
    background: 'rgba(255,255,255,0.03)', marginBottom: 24,
  },
  panelTitle: { fontSize: '1.3rem', fontWeight: 600, marginBottom: 16 },
  btn: {
    padding: '10px 24px', borderRadius: 10, border: 'none', fontWeight: 600,
    cursor: 'pointer', fontSize: '0.9rem', transition: 'all 0.2s',
  },
  input: {
    padding: '10px 16px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.06)', color: '#F1F5F9', fontSize: '0.9rem',
    outline: 'none', width: '100%',
  },
  row: { display: 'flex', gap: 12, flexWrap: 'wrap' as const, marginBottom: 16, alignItems: 'end' },
  table: {
    width: '100%', borderCollapse: 'collapse' as const, fontSize: '0.85rem',
  },
  th: {
    textAlign: 'left' as const, padding: '10px 12px', borderBottom: '1px solid rgba(255,255,255,0.1)',
    color: '#94A3B8', fontWeight: 600, fontSize: '0.8rem', textTransform: 'uppercase' as const,
  },
  td: {
    padding: '10px 12px', borderBottom: '1px solid rgba(255,255,255,0.05)',
  },
  badge: {
    display: 'inline-block', padding: '3px 10px', borderRadius: 20, fontSize: '0.75rem', fontWeight: 600,
  },
  insight: {
    padding: 16, borderRadius: 12, background: 'rgba(16,185,129,0.08)',
    border: '1px solid rgba(16,185,129,0.2)', marginTop: 16,
  },
  archBox: {
    padding: 16, borderRadius: 12, background: 'rgba(139,92,246,0.08)',
    border: '1px solid rgba(139,92,246,0.15)', fontFamily: 'monospace', fontSize: '0.8rem',
    marginTop: 12,
  },
  stat: { textAlign: 'center' as const, padding: 16 },
  statVal: { fontSize: '1.8rem', fontWeight: 700 },
  statLabel: { fontSize: '0.75rem', color: '#94A3B8', marginTop: 4 },
  loading: { textAlign: 'center' as const, padding: 40, color: '#94A3B8' },
};

/* ─── Main Component ───────────────────────────────────────────────────── */
export default function DeepLearning() {
  const [active, setActive] = useState<Model>('gnn');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [suiteStatus, setSuiteStatus] = useState<any>(null);

  useEffect(() => { api('/api/v5/deep-learning/status').then(setSuiteStatus); }, []);

  const run = useCallback(async (model: Model) => {
    setLoading(true);
    setData(null);
    let d: any = null;
    const headers = { 'Content-Type': 'application/json' };
    switch (model) {
      case 'gnn':
        d = await api('/api/v5/deep-learning/gnn/predict', { method: 'POST', headers, body: JSON.stringify({ top_k: 15 }) });
        break;
      case 'transformer':
        d = await api('/api/v5/deep-learning/transformer/compare', { method: 'POST', headers, body: JSON.stringify({ targets: ['CD19', 'BCMA', 'HER2', 'MSLN', 'GPC3', 'EGFR', 'DLL3', 'PSMA', 'CD33', 'CD22'] }) });
        break;
      case 'mlp':
        d = await api('/api/v5/deep-learning/mlp/batch', { method: 'POST', headers, body: JSON.stringify({ antigens: ['CD19', 'BCMA', 'HER2', 'MSLN', 'GPC3', 'EGFR', 'DLL3', 'PSMA', 'CD33', 'CD22', 'B7H3', 'GPRC5D'] }) });
        break;
      case 'vae':
        d = await api('/api/v5/deep-learning/vae/analyze', { method: 'POST', headers, body: JSON.stringify({ target: 'CD19', cancer_type: 'DLBCL' }) });
        break;
      case 'lstm':
        d = await api('/api/v5/deep-learning/lstm/simulate', { method: 'POST', headers, body: JSON.stringify({ dose: 1e8, tumor_burden: 50, age: 55, weight: 70, antigen_expression: 0.7, days: 180 }) });
        break;
    }
    setData(d);
    setLoading(false);
  }, []);

  useEffect(() => { run(active); }, [active]);

  const totalParams = suiteStatus?.total_parameters || 0;

  return (
    <div style={S.page}>
      <h1 style={S.h1}>🧪 Deep Learning Suite</h1>
      <p style={S.subtitle}>
        5 neural network architectures for CAR-T therapy research — {totalParams.toLocaleString()} total parameters
      </p>

      {/* Model Selector Cards */}
      <div style={S.modelGrid}>
        {(Object.keys(MODEL_INFO) as Model[]).map(key => {
          const m = MODEL_INFO[key];
          const isActive = active === key;
          return (
            <div key={key}
              style={{ ...(isActive ? S.modelCardActive : S.modelCard), borderColor: isActive ? m.color : undefined }}
              onClick={() => setActive(key)}>
              <div style={S.modelIcon}>{m.icon}</div>
              <div style={{ ...S.modelName, color: isActive ? m.color : '#F1F5F9' }}>{m.name}</div>
              <div style={S.modelDesc}>{m.desc}</div>
              {suiteStatus?.models && (
                <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#64748B' }}>
                  {suiteStatus.models.find((x: any) => x.name === m.name)?.parameters?.toLocaleString() || '?'} params
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Results Panel */}
      <div style={S.panel}>
        <div style={{ ...S.panelTitle, color: MODEL_INFO[active].color }}>
          {MODEL_INFO[active].icon} {MODEL_INFO[active].name} — Results
        </div>

        {loading && <div style={S.loading}>⏳ Running neural network inference...</div>}

        {!loading && data && active === 'gnn' && <GNNResults data={data} />}
        {!loading && data && active === 'transformer' && <TransformerResults data={data} />}
        {!loading && data && active === 'mlp' && <MLPResults data={data} />}
        {!loading && data && active === 'vae' && <VAEResults data={data} />}
        {!loading && data && active === 'lstm' && <LSTMResults data={data} />}

        {data?.ai_insight && (
          <div style={S.insight}>
            <div style={{ fontWeight: 600, marginBottom: 8, color: '#10B981' }}>
              🤖 AI Interpretation {data.ai_insight_source === 'llm' ? '(LLM)' : ''}
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.6 }}
              dangerouslySetInnerHTML={{ __html: data.ai_insight.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── GNN Results ──────────────────────────────────────────────────────── */
function GNNResults({ data }: { data: any }) {
  if (!data?.predictions) return null;
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#8B5CF6' }}>{data.graph_stats?.nodes}</div><div style={S.statLabel}>Nodes</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#8B5CF6' }}>{data.graph_stats?.edges}</div><div style={S.statLabel}>Edges</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#8B5CF6' }}>{data.graph_stats?.avg_degree}</div><div style={S.statLabel}>Avg Degree</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#8B5CF6' }}>{data.architecture?.parameters?.toLocaleString()}</div><div style={S.statLabel}>Parameters</div></div>
      </div>
      <div style={S.archBox}>Architecture: 3-Layer Message-Passing GNN → {data.architecture?.hidden_dim}-dim → Node Classification</div>
      <table style={{ ...S.table, marginTop: 16 }}>
        <thead><tr><th style={S.th}>Rank</th><th style={S.th}>Target</th><th style={S.th}>GNN Score</th><th style={S.th}>Expression</th><th style={S.th}>Safety</th><th style={S.th}>Efficacy</th><th style={S.th}>Novelty</th></tr></thead>
        <tbody>
          {data.predictions.map((p: any) => (
            <tr key={p.target}>
              <td style={S.td}>#{p.rank}</td>
              <td style={{ ...S.td, fontWeight: 600 }}>{p.target}</td>
              <td style={S.td}><span style={{ ...S.badge, background: p.gnn_viability_score > 0.6 ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)', color: p.gnn_viability_score > 0.6 ? '#10B981' : '#F59E0B' }}>{p.gnn_viability_score.toFixed(3)}</span></td>
              <td style={S.td}>{p.sub_scores.expression_signal.toFixed(3)}</td>
              <td style={S.td}>{p.sub_scores.safety_profile.toFixed(3)}</td>
              <td style={S.td}>{p.sub_scores.efficacy_potential.toFixed(3)}</td>
              <td style={S.td}>{p.sub_scores.novelty_index.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/* ─── Transformer Results ──────────────────────────────────────────────── */
function TransformerResults({ data }: { data: any }) {
  if (!data?.comparisons) return null;
  return (
    <>
      <div style={S.archBox}>Architecture: 2-Layer Transformer Encoder, 4 Attention Heads, 64-dim Embeddings, GELU Activation</div>
      <table style={{ ...S.table, marginTop: 16 }}>
        <thead><tr><th style={S.th}>Target</th><th style={S.th}>Composite</th><th style={S.th}>Binding</th><th style={S.th}>Surface</th><th style={S.th}>Immunogen.</th><th style={S.th}>Stability</th><th style={S.th}>Manufact.</th><th style={S.th}>Seq Len</th></tr></thead>
        <tbody>
          {data.comparisons.map((c: any) => (
            <tr key={c.target}>
              <td style={{ ...S.td, fontWeight: 600 }}>{c.target}</td>
              <td style={S.td}><span style={{ ...S.badge, background: 'rgba(6,182,212,0.15)', color: '#06B6D4' }}>{c.composite_score.toFixed(3)}</span></td>
              <td style={S.td}>{c.predictions.binding_affinity.toFixed(3)}</td>
              <td style={S.td}>{c.predictions.surface_accessibility.toFixed(3)}</td>
              <td style={S.td}>{c.predictions.immunogenicity.toFixed(3)}</td>
              <td style={S.td}>{c.predictions.stability.toFixed(3)}</td>
              <td style={S.td}>{c.predictions.manufacturability.toFixed(3)}</td>
              <td style={S.td}>{c.sequence_length}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/* ─── MLP Results ──────────────────────────────────────────────────────── */
function MLPResults({ data }: { data: any }) {
  if (!data?.rankings) return null;
  return (
    <>
      <div style={S.archBox}>Architecture: 12 → 64 → 32 → 16 → 3-head (CVS + Tier + Confidence), MC Dropout Uncertainty</div>
      <table style={{ ...S.table, marginTop: 16 }}>
        <thead><tr><th style={S.th}>#</th><th style={S.th}>Antigen</th><th style={S.th}>CVS Score</th><th style={S.th}>Tier</th><th style={S.th}>Uncertainty</th><th style={S.th}>Confidence</th></tr></thead>
        <tbody>
          {data.rankings.map((r: any, i: number) => (
            <tr key={r.antigen}>
              <td style={S.td}>{i + 1}</td>
              <td style={{ ...S.td, fontWeight: 600 }}>{r.antigen}</td>
              <td style={S.td}><span style={{ ...S.badge, background: 'rgba(16,185,129,0.15)', color: '#10B981' }}>{r.cvs_score.toFixed(3)}</span></td>
              <td style={{ ...S.td, fontSize: '0.8rem' }}>{r.tier}</td>
              <td style={S.td}>{r.uncertainty.toFixed(4)}</td>
              <td style={S.td}><span style={{ ...S.badge, background: r.confidence === 'high' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)', color: r.confidence === 'high' ? '#10B981' : '#F59E0B' }}>{r.confidence}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

/* ─── VAE Results ──────────────────────────────────────────────────────── */
function VAEResults({ data }: { data: any }) {
  if (!data?.latent_representation) return null;
  return (
    <>
      <div style={S.archBox}>Architecture: Encoder (92→128→64→16) | Latent (μ, σ²) | Decoder (16→64→128→92)</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 16 }}>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#F59E0B' }}>{data.integration_score?.toFixed(3)}</div><div style={S.statLabel}>Integration Score</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#F59E0B' }}>{data.losses?.reconstruction?.toFixed(4)}</div><div style={S.statLabel}>Recon Loss</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#F59E0B' }}>{data.losses?.kl_divergence?.toFixed(4)}</div><div style={S.statLabel}>KL Divergence</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: data.anomaly_detection?.is_anomalous ? '#EF4444' : '#10B981' }}>{data.anomaly_detection?.anomaly_score?.toFixed(2)}</div><div style={S.statLabel}>Anomaly Score</div></div>
      </div>
      <div style={{ marginTop: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Reconstruction Quality by Omics Layer</div>
        {data.reconstruction_quality && Object.entries(data.reconstruction_quality).map(([k, v]: [string, any]) => (
          <div key={k} style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 8, fontSize: '0.85rem' }}>
            <span style={{ width: 140, fontWeight: 500, textTransform: 'capitalize' }}>{k}</span>
            <div style={{ flex: 1, height: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: `${Math.max(0, v.correlation * 100)}%`, height: '100%', background: '#F59E0B', borderRadius: 4 }} />
            </div>
            <span style={{ width: 60, textAlign: 'right', color: '#94A3B8' }}>{(v.correlation * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Latent Space (16-dim z-vector)</div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {data.latent_representation?.z_vector?.map((v: number, i: number) => (
            <span key={i} style={{ ...S.badge, background: v > 0 ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', color: v > 0 ? '#10B981' : '#EF4444', fontSize: '0.7rem' }}>
              z{i}: {v.toFixed(2)}
            </span>
          ))}
        </div>
      </div>
    </>
  );
}

/* ─── LSTM Results ─────────────────────────────────────────────────────── */
function LSTMResults({ data }: { data: any }) {
  if (!data?.timeline) return null;
  const t = data.timeline;
  return (
    <>
      <div style={S.archBox}>Architecture: 2-Layer Stacked LSTM, Hidden=32, Input=6 features/step, Output=4 variables</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginTop: 16 }}>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#EF4444' }}>{data.outcome?.response?.split(' ')[0]}</div><div style={S.statLabel}>{data.outcome?.response}</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#EF4444' }}>Day {data.key_events?.peak_car_t?.day}</div><div style={S.statLabel}>Peak CAR-T</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#EF4444' }}>{data.outcome?.final_tumor_pct}%</div><div style={S.statLabel}>Final Tumor</div></div>
        <div style={S.stat}><div style={{ ...S.statVal, color: '#EF4444' }}>{data.outcome?.final_health?.toFixed(3)}</div><div style={S.statLabel}>Health Score</div></div>
      </div>
      <div style={{ marginTop: 20, fontSize: '0.85rem' }}>
        <div style={{ fontWeight: 600, marginBottom: 8 }}>Treatment Timeline ({t.days?.length} data points, {data.architecture?.sequence_length} days)</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 12 }}>
          <div><strong>CAR-T Cell Expansion</strong>
            <div style={{ display: 'flex', gap: 2, height: 60, alignItems: 'flex-end', marginTop: 8 }}>
              {t.car_t_cells?.slice(0, 40).map((v: number, i: number) => {
                const max = Math.max(...t.car_t_cells);
                return <div key={i} style={{ flex: 1, height: `${(v / max) * 100}%`, background: '#EF4444', borderRadius: 1, minHeight: 1 }} />;
              })}
            </div>
          </div>
          <div><strong>Tumor Volume</strong>
            <div style={{ display: 'flex', gap: 2, height: 60, alignItems: 'flex-end', marginTop: 8 }}>
              {t.tumor_volume_pct?.slice(0, 40).map((v: number, i: number) => (
                <div key={i} style={{ flex: 1, height: `${v}%`, background: '#F59E0B', borderRadius: 1, minHeight: 1 }} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
