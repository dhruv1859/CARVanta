import React, { useState, useCallback } from 'react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8001';

/* ═══════════════════════════════════════════════════════════════════════════════
   Types
   ═══════════════════════════════════════════════════════════════════════════════ */
interface Mutation {
  gene: string; variant: string; type: string; vaf: number;
  tier: number; clinical_significance: string; car_t_impact: string; evidence_level: string;
}
interface CNV { gene: string; alteration: string; copy_number: number; car_t_impact: string; }
interface Signature { name: string; classification: string; score: number; prognosis: string; car_t_relevance: string; }
interface ResistancePathway {
  pathway: string; risk_score: number; risk_level: string;
  mechanism: string; monitoring: string; mitigation: string[];
}
interface MRDData {
  trajectory: number[]; nadir_value: number; nadir_day: number;
  final_mrd: number; is_mrd_negative: boolean; mrd_negative_day: number | null;
  relapse_detected: boolean; relapse_day: number | null;
  monitoring_recommendations: string[];
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Interactive Chart with Hover Tooltips
   ═══════════════════════════════════════════════════════════════════════════════ */
function InteractiveChart({ data, color, label, unit, maxOverride }: {
  data: number[]; color: string; label: string; unit?: string; maxOverride?: number;
}) {
  const [hover, setHover] = useState<{ x: number; y: number; val: number; day: number } | null>(null);
  if (!data || data.length === 0) return null;

  const w = 640, h = 180, padL = 55, padR = 20, padT = 20, padB = 35;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;
  const max = maxOverride || Math.max(...data, 0.001);
  const min = 0;

  const points = data.map((v, i) => ({
    x: padL + (i / Math.max(data.length - 1, 1)) * chartW,
    y: padT + chartH - ((v - min) / (max - min || 1)) * chartH,
    val: v,
    day: i,
  }));

  const polyline = points.map(p => `${p.x},${p.y}`).join(' ');
  const area = `${padL},${padT + chartH} ${polyline} ${padL + chartW},${padT + chartH}`;

  // Y-axis tick values
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    val: min + f * (max - min),
    y: padT + chartH - f * chartH,
  }));

  // X-axis ticks (5 evenly spaced)
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map(f => ({
    day: Math.round(f * (data.length - 1)),
    x: padL + f * chartW,
  }));

  return (
    <div style={{ position: 'relative', marginBottom: 12 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary, #e2e8f0)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block' }} />
        {label}
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: 'auto', cursor: 'crosshair' }}
        onMouseMove={e => {
          const rect = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
          const mx = ((e.clientX - rect.left) / rect.width) * w;
          const idx = Math.round(((mx - padL) / chartW) * (data.length - 1));
          if (idx >= 0 && idx < data.length) {
            setHover({ x: points[idx].x, y: points[idx].y, val: data[idx], day: idx });
          }
        }}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id={`fill-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {yTicks.map((t, i) => (
          <g key={`y-${i}`}>
            <line x1={padL} y1={t.y} x2={padL + chartW} y2={t.y} stroke="var(--border-color, rgba(148,163,184,0.1))" strokeWidth="0.5" />
            <text x={padL - 8} y={t.y + 4} textAnchor="end" fill="var(--text-muted, #64748b)" fontSize="9">{t.val >= 1000 ? `${(t.val/1000).toFixed(1)}k` : t.val >= 1 ? t.val.toFixed(1) : t.val.toFixed(3)}</text>
          </g>
        ))}
        {xTicks.map((t, i) => (
          <text key={`x-${i}`} x={t.x} y={h - 5} textAnchor="middle" fill="var(--text-muted, #64748b)" fontSize="9">Day {t.day}</text>
        ))}

        {/* Area fill */}
        <polygon points={area} fill={`url(#fill-${color.replace('#', '')})`} />

        {/* Line */}
        <polyline points={polyline} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

        {/* Data dots */}
        {points.filter((_, i) => i % Math.max(1, Math.floor(data.length / 12)) === 0 || i === data.length - 1).map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r="3" fill={color} stroke="var(--bg-card, #1e293b)" strokeWidth="1.5" />
        ))}

        {/* Hover crosshair + tooltip */}
        {hover && (
          <>
            <line x1={hover.x} y1={padT} x2={hover.x} y2={padT + chartH} stroke={color} strokeWidth="1" strokeDasharray="3,3" opacity="0.6" />
            <circle cx={hover.x} cy={hover.y} r="5" fill={color} stroke="#fff" strokeWidth="2" />
            <rect x={hover.x - 45} y={hover.y - 32} width="90" height="22" rx="6" fill="var(--bg-tooltip, rgba(15,23,42,0.92))" />
            <text x={hover.x} y={hover.y - 17} textAnchor="middle" fill="#fff" fontSize="10" fontWeight="600">
              Day {hover.day}: {hover.val >= 1 ? hover.val.toFixed(1) : hover.val.toExponential(2)}{unit ? ` ${unit}` : ''}
            </text>
          </>
        )}

        {/* Axes */}
        <line x1={padL} y1={padT} x2={padL} y2={padT + chartH} stroke="var(--border-color, rgba(148,163,184,0.15))" strokeWidth="1" />
        <line x1={padL} y1={padT + chartH} x2={padL + chartW} y2={padT + chartH} stroke="var(--border-color, rgba(148,163,184,0.15))" strokeWidth="1" />
      </svg>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   MRD Chart with hover + threshold line
   ═══════════════════════════════════════════════════════════════════════════════ */
function MRDChart({ data }: { data: MRDData }) {
  const [hover, setHover] = useState<{ x: number; y: number; val: number; day: number } | null>(null);
  const traj = data.trajectory;
  const w = 700, h = 280, padL = 60, padR = 30, padT = 25, padB = 35;
  const chartW = w - padL - padR;
  const chartH = h - padT - padB;
  const maxLog = Math.log10(Math.max(...traj, 1));
  const minLog = -4;
  const range = maxLog - minLog || 1;

  const toY = (v: number) => padT + chartH - ((Math.log10(Math.max(v, 0.0001)) - minLog) / range) * chartH;

  const points = traj.map((v, i) => ({
    x: padL + (i / Math.max(traj.length - 1, 1)) * chartW,
    y: Math.max(padT, Math.min(padT + chartH, toY(v))),
    val: v, day: i,
  }));

  const polyline = points.map(p => `${p.x},${p.y}`).join(' ');
  const threshY = toY(0.01);

  return (
    <div>
      <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', cursor: 'crosshair' }}
        onMouseMove={e => {
          const rect = (e.target as SVGElement).closest('svg')!.getBoundingClientRect();
          const mx = ((e.clientX - rect.left) / rect.width) * w;
          const idx = Math.round(((mx - padL) / chartW) * (traj.length - 1));
          if (idx >= 0 && idx < traj.length) setHover({ x: points[idx].x, y: points[idx].y, val: traj[idx], day: idx });
        }}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          <linearGradient id="mrd-grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid */}
        {[-4, -3, -2, -1, 0].filter(v => v <= maxLog).map(v => {
          const y = padT + chartH - ((v - minLog) / range) * chartH;
          return (
            <g key={v}>
              <line x1={padL} y1={y} x2={padL + chartW} y2={y} stroke="var(--border-color, rgba(148,163,184,0.1))" strokeWidth="0.5" />
              <text x={padL - 8} y={y + 4} textAnchor="end" fill="var(--text-muted, #64748b)" fontSize="9">10^{v}</text>
            </g>
          );
        })}

        {/* MRD negativity threshold */}
        <line x1={padL} y1={threshY} x2={padL + chartW} y2={threshY} stroke="#10b981" strokeWidth="1.5" strokeDasharray="6,4" />
        <text x={padL + chartW + 4} y={threshY + 4} fill="#10b981" fontSize="10" fontWeight="600">MRD⁻</text>

        {/* Area + Line */}
        <polygon points={`${padL},${padT + chartH} ${polyline} ${padL + chartW},${padT + chartH}`} fill="url(#mrd-grad)" />
        <polyline points={polyline} fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />

        {/* Relapse marker */}
        {data.relapse_detected && data.relapse_day && (
          <>
            <line x1={points[data.relapse_day]?.x} y1={padT} x2={points[data.relapse_day]?.x} y2={padT + chartH} stroke="#ef4444" strokeWidth="1.5" strokeDasharray="4,3" />
            <text x={points[data.relapse_day]?.x} y={padT - 5} textAnchor="middle" fill="#ef4444" fontSize="10" fontWeight="700">⚠ Relapse</text>
          </>
        )}

        {/* Hover */}
        {hover && (
          <>
            <line x1={hover.x} y1={padT} x2={hover.x} y2={padT + chartH} stroke="#06b6d4" strokeWidth="1" strokeDasharray="3,3" opacity="0.6" />
            <circle cx={hover.x} cy={hover.y} r="5" fill="#06b6d4" stroke="#fff" strokeWidth="2" />
            <rect x={hover.x - 55} y={hover.y - 32} width="110" height="22" rx="6" fill="var(--bg-tooltip, rgba(15,23,42,0.92))" />
            <text x={hover.x} y={hover.y - 17} textAnchor="middle" fill="#fff" fontSize="10" fontWeight="600">
              Day {hover.day}: {hover.val.toExponential(2)}
            </text>
          </>
        )}

        <line x1={padL} y1={padT} x2={padL} y2={padT + chartH} stroke="var(--border-color, rgba(148,163,184,0.15))" />
        <line x1={padL} y1={padT + chartH} x2={padL + chartW} y2={padT + chartH} stroke="var(--border-color, rgba(148,163,184,0.15))" />
        <text x={w / 2} y={h - 2} textAnchor="middle" fill="var(--text-muted, #64748b)" fontSize="10">Days Post-Infusion</text>
        <text x={12} y={h / 2} textAnchor="middle" fill="var(--text-muted, #64748b)" fontSize="10" transform={`rotate(-90 12 ${h / 2})`}>MRD Level (log₁₀)</text>
      </svg>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════════
   Style Constants
   ═══════════════════════════════════════════════════════════════════════════════ */
const S = {
  page: { maxWidth: 1200, margin: '0 auto', padding: 20, fontFamily: "'Inter', system-ui, sans-serif" } as React.CSSProperties,
  header: { marginBottom: 24, textAlign: 'center' as const },
  h1: { fontSize: 28, fontWeight: 800, margin: '0 0 6px', background: 'linear-gradient(135deg, #818cf8, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' },
  subtitle: { fontSize: 14, color: 'var(--text-muted, #94a3b8)', margin: 0 },
  tabs: { display: 'flex', gap: 4, marginBottom: 24, background: 'var(--bg-card, rgba(30,41,59,0.6))', border: '1px solid var(--border-color, rgba(148,163,184,0.12))', borderRadius: 14, padding: 5 } as React.CSSProperties,
  tab: (active: boolean) => ({
    flex: 1, padding: '12px 16px', border: 'none', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s',
    background: active ? 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.15))' : 'transparent',
    color: active ? 'var(--text-accent, #a5b4fc)' : 'var(--text-muted, #94a3b8)',
    boxShadow: active ? '0 2px 8px rgba(99,102,241,0.15)' : 'none',
  }) as React.CSSProperties,
  card: { background: 'var(--bg-card, rgba(30,41,59,0.6))', border: '1px solid var(--border-color, rgba(148,163,184,0.12))', borderRadius: 14, padding: 20, marginBottom: 16, backdropFilter: 'blur(12px)' } as React.CSSProperties,
  sectionTitle: { fontSize: 16, fontWeight: 700, color: 'var(--text-primary, #f1f5f9)', margin: '0 0 14px', paddingBottom: 10, borderBottom: '1px solid var(--border-color, rgba(148,163,184,0.1))', display: 'flex', alignItems: 'center', gap: 8 } as React.CSSProperties,
  statGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 16 } as React.CSSProperties,
  stat: (accent: string) => ({
    background: `linear-gradient(135deg, ${accent}10, ${accent}05)`, border: `1px solid ${accent}25`, borderRadius: 12, padding: '14px 12px', textAlign: 'center' as const, transition: 'transform 0.2s, box-shadow 0.2s',
  }) as React.CSSProperties,
  statValue: { fontSize: 22, fontWeight: 800, color: 'var(--text-primary, #f1f5f9)', display: 'block' },
  statLabel: { fontSize: 10, fontWeight: 600, color: 'var(--text-muted, #94a3b8)', textTransform: 'uppercase' as const, letterSpacing: '0.05em', marginTop: 4, display: 'block' },
  formRow: { display: 'flex', gap: 12, alignItems: 'flex-end', flexWrap: 'wrap' as const, marginBottom: 16 },
  field: { display: 'flex', flexDirection: 'column' as const, gap: 6, flex: '1 1 160px' },
  label: { fontSize: 11, fontWeight: 700, color: 'var(--text-muted, #94a3b8)', textTransform: 'uppercase' as const, letterSpacing: '0.05em' },
  input: { background: 'var(--bg-input, rgba(15,23,42,0.6))', border: '1px solid var(--border-color, rgba(148,163,184,0.15))', color: 'var(--text-primary, #f1f5f9)', padding: '10px 12px', borderRadius: 8, fontSize: 14 },
  btn: { background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: 10, fontSize: 13, fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s', boxShadow: '0 4px 12px rgba(99,102,241,0.3)' },
  error: { background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#f87171', padding: '12px 18px', borderRadius: 10, fontSize: 13, fontWeight: 500, marginBottom: 16 },
  table: { width: '100%', borderCollapse: 'collapse' as const, fontSize: 13 },
  th: { textAlign: 'left' as const, padding: '10px 12px', fontSize: 10, fontWeight: 700, color: 'var(--text-muted, #94a3b8)', textTransform: 'uppercase' as const, letterSpacing: '0.05em', borderBottom: '2px solid var(--border-color, rgba(148,163,184,0.15))' },
  td: { padding: '10px 12px', borderBottom: '1px solid var(--border-color, rgba(148,163,184,0.06))', color: 'var(--text-primary, #e2e8f0)' },
  badge: (color: string) => ({ fontSize: 11, padding: '3px 10px', borderRadius: 20, fontWeight: 700, background: `${color}18`, color, border: `1px solid ${color}30` }),
  progressBar: { height: 8, borderRadius: 4, background: 'var(--bg-input, rgba(148,163,184,0.1))', overflow: 'hidden' as const, marginTop: 6, marginBottom: 6 },
  progressFill: (pct: number, color: string) => ({ height: '100%', width: `${pct}%`, borderRadius: 4, background: `linear-gradient(90deg, ${color}, ${color}cc)`, transition: 'width 0.6s ease' }),
};

/* ═══════════════════════════════════════════════════════════════════════════════
   Color helpers
   ═══════════════════════════════════════════════════════════════════════════════ */
const impactColor = (impact: string) => {
  if (impact.includes('unfavorable') || impact === 'highly_unfavorable') return '#ef4444';
  if (impact.includes('favorable')) return '#10b981';
  if (impact === 'neutral') return '#f59e0b';
  return '#94a3b8';
};
const riskColor = (level: string) => {
  if (level === 'high') return '#ef4444';
  if (level === 'moderate') return '#f59e0b';
  if (level === 'low') return '#10b981';
  return '#94a3b8';
};
const tierColor = (tier: number) => ['', '#ef4444', '#f59e0b', '#06b6d4', '#94a3b8'][tier] || '#94a3b8';

/* ═══════════════════════════════════════════════════════════════════════════════
   Main Component
   ═══════════════════════════════════════════════════════════════════════════════ */
export default function GenomicProfiler() {
  const [activeTab, setActiveTab] = useState<'profile' | 'resistance' | 'mrd'>('profile');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [cancerType, setCancerType] = useState('DLBCL');
  const [patientAge, setPatientAge] = useState(55);
  const [profileData, setProfileData] = useState<any>(null);

  const [targetAntigen, setTargetAntigen] = useState('CD19');
  const [resistanceData, setResistanceData] = useState<any>(null);

  const [mrdDays, setMrdDays] = useState(180);
  const [treatmentResponse, setTreatmentResponse] = useState('CR');
  const [genomicRisk, setGenomicRisk] = useState('standard');
  const [mrdData, setMrdData] = useState<MRDData | null>(null);

  const fetchProfile = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/api/v5/twin/genomic-profile`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cancer_type: cancerType, patient_age: patientAge }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setProfileData(await res.json());
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  }, [cancerType, patientAge]);

  const fetchResistance = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/api/v5/twin/resistance-analysis`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cancer_type: cancerType, target_antigen: targetAntigen, mutations: profileData?.mutations || null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setResistanceData(await res.json());
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  }, [cancerType, targetAntigen, profileData]);

  const fetchMRD = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/api/v5/twin/mrd-trajectory`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: mrdDays, cancer_type: cancerType, treatment_response: treatmentResponse, genomic_risk: genomicRisk }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setMrdData(await res.json());
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  }, [mrdDays, cancerType, treatmentResponse, genomicRisk]);

  return (
    <div style={S.page}>
      {/* Header */}
      <div style={S.header}>
        <h1 style={S.h1}>🧬 Genomic Profiler</h1>
        <p style={S.subtitle}>Comprehensive genomic analysis • Resistance prediction • MRD monitoring</p>
      </div>

      {/* Tabs */}
      <div style={S.tabs}>
        {(['profile', 'resistance', 'mrd'] as const).map(tab => (
          <button key={tab} style={S.tab(activeTab === tab)} onClick={() => setActiveTab(tab)}>
            {tab === 'profile' ? '🔬 Genomic Profile' : tab === 'resistance' ? '🛡️ Resistance Analysis' : '📈 MRD Trajectory'}
          </button>
        ))}
      </div>

      {error && <div style={S.error}>⚠️ {error}</div>}

      {/* ═══ TAB 1: GENOMIC PROFILE ═══════════════════════════════════════════ */}
      {activeTab === 'profile' && (
        <>
          <div style={S.card}>
            <div style={S.formRow}>
              <div style={S.field}>
                <label style={S.label}>Cancer Type</label>
                <select style={S.input} value={cancerType} onChange={e => setCancerType(e.target.value)}>
                  <option value="DLBCL">DLBCL</option><option value="ALL">ALL</option>
                  <option value="MCL">MCL</option><option value="Multiple Myeloma">Multiple Myeloma</option>
                  <option value="FL">Follicular Lymphoma</option><option value="CLL">CLL</option>
                </select>
              </div>
              <div style={S.field}>
                <label style={S.label}>Patient Age</label>
                <input style={S.input} type="number" value={patientAge} onChange={e => setPatientAge(+e.target.value)} min={1} max={100} />
              </div>
              <button style={{ ...S.btn, opacity: loading ? 0.7 : 1 }} onClick={fetchProfile} disabled={loading}>
                {loading ? '⏳ Analyzing Genome...' : '🧬 Generate Genomic Profile'}
              </button>
            </div>
          </div>

          {profileData && (
            <>
              {/* Summary Stats */}
              <div style={S.statGrid}>
                <div style={S.stat('#818cf8')}><span style={S.statValue}>{profileData.tumor_mutational_burden}</span><span style={S.statLabel}>TMB (mut/Mb)</span><span style={{ fontSize: 10, color: '#818cf8' }}>{profileData.tmb_category}</span></div>
                <div style={S.stat('#06b6d4')}><span style={S.statValue}>{profileData.msi_status}</span><span style={S.statLabel}>MSI Status</span></div>
                <div style={S.stat('#f59e0b')}><span style={S.statValue}>{profileData.pd_l1_expression}%</span><span style={S.statLabel}>PD-L1 Expression</span></div>
                <div style={S.stat('#10b981')}><span style={S.statValue}>{profileData.immune_phenotype}</span><span style={S.statLabel}>Immune Phenotype</span></div>
                <div style={S.stat('#f97316')}><span style={S.statValue}>{profileData.total_mutations_detected}</span><span style={S.statLabel}>Total Mutations</span><span style={{ fontSize: 10, color: '#ef4444' }}>Tier 1: {profileData.tier1_mutations}</span></div>
              </div>

              {/* Molecular Subtype */}
              {profileData.molecular_subtype?.subtype && (
                <div style={S.card}>
                  <h3 style={S.sectionTitle}>🧫 Molecular Subtype</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-primary, #f1f5f9)' }}>{profileData.molecular_subtype.subtype}</span>
                    <span style={S.badge(profileData.molecular_subtype.prognosis === 'favorable' ? '#10b981' : '#ef4444')}>
                      {profileData.molecular_subtype.prognosis}
                    </span>
                    <span style={{ fontSize: 13, color: 'var(--text-muted, #94a3b8)' }}>{profileData.molecular_subtype.classification}</span>
                  </div>
                </div>
              )}

              {/* Double-Hit */}
              {profileData.double_hit_assessment && (
                <div style={{ ...S.card, borderColor: profileData.double_hit_assessment.status?.includes('Double') ? 'rgba(239,68,68,0.3)' : undefined }}>
                  <h3 style={S.sectionTitle}>⚠️ Double-Hit Assessment</h3>
                  <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary, #f1f5f9)' }}>{profileData.double_hit_assessment.status}</span>
                    <span style={S.badge(impactColor(profileData.double_hit_assessment.car_t_impact || ''))}>{profileData.double_hit_assessment.car_t_impact}</span>
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-muted, #94a3b8)', lineHeight: 1.6, margin: 0 }}>{profileData.double_hit_assessment.recommendation}</p>
                </div>
              )}

              {/* Mutations Table */}
              <div style={S.card}>
                <h3 style={S.sectionTitle}>🔬 Somatic Mutations ({profileData.mutations.length})</h3>
                {profileData.mutations.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={S.table}>
                      <thead>
                        <tr>
                          <th style={S.th}>Gene</th><th style={S.th}>Variant</th><th style={S.th}>Type</th>
                          <th style={S.th}>VAF</th><th style={S.th}>Tier</th><th style={S.th}>CAR-T Impact</th><th style={S.th}>Evidence</th>
                        </tr>
                      </thead>
                      <tbody>
                        {profileData.mutations.map((m: Mutation, i: number) => (
                          <tr key={i} style={{ transition: 'background 0.15s' }} onMouseEnter={e => (e.currentTarget.style.background = 'rgba(99,102,241,0.05)')} onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                            <td style={{ ...S.td, fontWeight: 700 }}>{m.gene}</td>
                            <td style={{ ...S.td, fontFamily: 'monospace', fontSize: 12 }}>{m.variant}</td>
                            <td style={S.td}>{m.type}</td>
                            <td style={S.td}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <div style={{ ...S.progressBar, width: 50, height: 5 }}>
                                  <div style={S.progressFill(m.vaf * 100, '#818cf8')} />
                                </div>
                                {(m.vaf * 100).toFixed(1)}%
                              </div>
                            </td>
                            <td style={S.td}><span style={S.badge(tierColor(m.tier))}>Tier {m.tier}</span></td>
                            <td style={S.td}><span style={{ color: impactColor(m.car_t_impact), fontWeight: 600 }}>{m.car_t_impact}</span></td>
                            <td style={S.td}><span style={{ fontSize: 11, color: 'var(--text-muted, #94a3b8)' }}>{m.evidence_level}</span></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : <p style={{ color: 'var(--text-muted)', padding: 20, textAlign: 'center' }}>No mutations detected</p>}
              </div>

              {/* CNV */}
              {profileData.copy_number_variations?.length > 0 && (
                <div style={S.card}>
                  <h3 style={S.sectionTitle}>📊 Copy Number Variations</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={S.table}>
                      <thead><tr><th style={S.th}>Gene</th><th style={S.th}>Alteration</th><th style={S.th}>Copy #</th><th style={S.th}>Impact</th></tr></thead>
                      <tbody>
                        {profileData.copy_number_variations.map((c: CNV, i: number) => (
                          <tr key={i}><td style={{ ...S.td, fontWeight: 700 }}>{c.gene}</td><td style={S.td}>{c.alteration}</td><td style={S.td}>{c.copy_number}</td><td style={S.td}><span style={{ color: impactColor(c.car_t_impact), fontWeight: 600 }}>{c.car_t_impact}</span></td></tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Expression Signatures */}
              <div style={S.card}>
                <h3 style={S.sectionTitle}>📈 Expression Signatures</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 12 }}>
                  {profileData.expression_signatures?.map((s: Signature, i: number) => {
                    const pc = s.prognosis === 'favorable' ? '#10b981' : s.prognosis === 'unfavorable' ? '#ef4444' : '#f59e0b';
                    return (
                      <div key={i} style={{ background: `${pc}08`, border: `1px solid ${pc}20`, borderRadius: 10, padding: 14 }}>
                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary, #f1f5f9)', marginBottom: 6 }}>{s.name}</div>
                        <div style={S.progressBar}><div style={S.progressFill(s.score * 100, pc)} /></div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                          <span style={{ fontSize: 11, color: 'var(--text-muted, #94a3b8)' }}>{s.classification}</span>
                          <span style={S.badge(pc)}>{s.prognosis}</span>
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted, #94a3b8)', marginTop: 8, lineHeight: 1.5 }}>{s.car_t_relevance}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Actionable Findings */}
              {profileData.actionable_findings?.length > 0 && (
                <div style={{ ...S.card, borderColor: 'rgba(245,158,11,0.3)' }}>
                  <h3 style={S.sectionTitle}>⚡ Actionable Findings</h3>
                  {profileData.actionable_findings.map((f: any, i: number) => (
                    <div key={i} style={{ padding: '12px 14px', borderRadius: 8, background: 'rgba(245,158,11,0.06)', marginBottom: 8, borderLeft: `3px solid ${tierColor(f.tier)}` }}>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary, #f1f5f9)', marginBottom: 4 }}>{f.gene} ({f.variant}) <span style={S.badge(tierColor(f.tier))}>Tier {f.tier}</span></div>
                      <p style={{ fontSize: 13, color: 'var(--text-muted, #94a3b8)', margin: 0, lineHeight: 1.6 }}>{f.recommendation}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Resistance Risk */}
              {profileData.resistance_risk && (
                <div style={S.card}>
                  <h3 style={S.sectionTitle}>🛡️ Resistance Risk Overview</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 10 }}>
                    <span style={{ fontSize: 28, fontWeight: 800, color: riskColor(profileData.resistance_risk.risk_level) }}>{(profileData.resistance_risk.overall_risk * 100).toFixed(0)}%</span>
                    <span style={S.badge(riskColor(profileData.resistance_risk.risk_level))}>{profileData.resistance_risk.risk_level} risk</span>
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>PFS modifier: {profileData.resistance_risk.predicted_pfs_modifier}×</span>
                  </div>
                  <div style={S.progressBar}><div style={S.progressFill(profileData.resistance_risk.overall_risk * 100, riskColor(profileData.resistance_risk.risk_level))} /></div>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* ═══ TAB 2: RESISTANCE ANALYSIS ═══════════════════════════════════════ */}
      {activeTab === 'resistance' && (
        <>
          <div style={S.card}>
            <div style={S.formRow}>
              <div style={S.field}>
                <label style={S.label}>Target Antigen</label>
                <select style={S.input} value={targetAntigen} onChange={e => setTargetAntigen(e.target.value)}>
                  <option value="CD19">CD19</option><option value="CD22">CD22</option><option value="BCMA">BCMA</option><option value="CD20">CD20</option>
                </select>
              </div>
              <button style={{ ...S.btn, opacity: loading ? 0.7 : 1 }} onClick={fetchResistance} disabled={loading}>
                {loading ? '⏳ Analyzing...' : '🛡️ Analyze Resistance Mechanisms'}
              </button>
            </div>
          </div>

          {resistanceData && (
            <>
              <div style={S.statGrid}>
                <div style={S.stat(riskColor(resistanceData.overall_risk_level))}>
                  <span style={{ ...S.statValue, color: riskColor(resistanceData.overall_risk_level) }}>{(resistanceData.overall_resistance_risk * 100).toFixed(0)}%</span>
                  <span style={S.statLabel}>Overall Risk</span>
                  <span style={S.badge(riskColor(resistanceData.overall_risk_level))}>{resistanceData.overall_risk_level}</span>
                </div>
                <div style={S.stat('#818cf8')}>
                  <span style={S.statValue}>{resistanceData.highest_risk_pathway}</span>
                  <span style={S.statLabel}>Highest Risk Pathway</span>
                </div>
              </div>

              <div style={S.card}>
                <h3 style={S.sectionTitle}>🔬 Resistance Pathways</h3>
                <div style={{ display: 'grid', gap: 12 }}>
                  {resistanceData.resistance_pathways?.map((p: ResistancePathway, i: number) => (
                    <div key={i} style={{ padding: 16, borderRadius: 12, border: `1px solid ${riskColor(p.risk_level)}25`, background: `${riskColor(p.risk_level)}06` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary, #f1f5f9)' }}>{p.pathway}</span>
                        <span style={S.badge(riskColor(p.risk_level))}>{p.risk_level.toUpperCase()} — {(p.risk_score * 100).toFixed(0)}%</span>
                      </div>
                      <div style={S.progressBar}><div style={S.progressFill(p.risk_score * 100, riskColor(p.risk_level))} /></div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10, fontSize: 12, color: 'var(--text-muted, #94a3b8)', lineHeight: 1.6 }}>
                        <div><strong style={{ color: 'var(--text-primary, #e2e8f0)' }}>Mechanism:</strong> {p.mechanism}</div>
                        <div><strong style={{ color: 'var(--text-primary, #e2e8f0)' }}>Monitoring:</strong> {p.monitoring}</div>
                      </div>
                      {p.mitigation?.length > 0 && (
                        <div style={{ marginTop: 8, padding: '8px 12px', borderRadius: 8, background: 'rgba(16,185,129,0.06)' }}>
                          <strong style={{ fontSize: 11, color: '#10b981' }}>Mitigation:</strong>
                          <ul style={{ margin: '4px 0 0', paddingLeft: 18, fontSize: 12, color: 'var(--text-muted, #94a3b8)' }}>
                            {p.mitigation.map((m, j) => <li key={j}>{m}</li>)}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {resistanceData.recommended_strategy && (
                <div style={{ ...S.card, borderColor: 'rgba(99,102,241,0.3)' }}>
                  <h3 style={S.sectionTitle}>💡 Recommended Strategy</h3>
                  <p style={{ fontSize: 14, color: 'var(--text-primary, #e2e8f0)', lineHeight: 1.8, margin: 0 }}>{resistanceData.recommended_strategy}</p>
                </div>
              )}
            </>
          )}
        </>
      )}

      {/* ═══ TAB 3: MRD TRAJECTORY ════════════════════════════════════════════ */}
      {activeTab === 'mrd' && (
        <>
          <div style={S.card}>
            <div style={S.formRow}>
              <div style={S.field}>
                <label style={S.label}>Simulation Days</label>
                <input style={S.input} type="number" value={mrdDays} onChange={e => setMrdDays(+e.target.value)} min={30} max={365} />
              </div>
              <div style={S.field}>
                <label style={S.label}>Treatment Response</label>
                <select style={S.input} value={treatmentResponse} onChange={e => setTreatmentResponse(e.target.value)}>
                  <option value="CR">Complete Response</option><option value="PR">Partial Response</option>
                  <option value="SD">Stable Disease</option><option value="PD">Progressive Disease</option>
                </select>
              </div>
              <div style={S.field}>
                <label style={S.label}>Genomic Risk</label>
                <select style={S.input} value={genomicRisk} onChange={e => setGenomicRisk(e.target.value)}>
                  <option value="standard">Standard</option><option value="intermediate">Intermediate</option>
                  <option value="high">High</option><option value="very_high">Very High</option>
                </select>
              </div>
              <button style={{ ...S.btn, opacity: loading ? 0.7 : 1 }} onClick={fetchMRD} disabled={loading}>
                {loading ? '⏳ Simulating...' : '📈 Simulate MRD Trajectory'}
              </button>
            </div>
          </div>

          {mrdData && (
            <>
              {/* MRD Summary Stats */}
              <div style={S.statGrid}>
                <div style={S.stat('#06b6d4')}><span style={S.statValue}>{mrdData.nadir_value.toExponential(2)}</span><span style={S.statLabel}>Nadir MRD Value</span></div>
                <div style={S.stat('#818cf8')}><span style={S.statValue}>Day {mrdData.nadir_day}</span><span style={S.statLabel}>Nadir Day</span></div>
                <div style={S.stat(mrdData.is_mrd_negative ? '#10b981' : '#ef4444')}>
                  <span style={{ ...S.statValue, color: mrdData.is_mrd_negative ? '#10b981' : '#ef4444' }}>{mrdData.is_mrd_negative ? '✅ NEGATIVE' : '⚠️ POSITIVE'}</span>
                  <span style={S.statLabel}>Final MRD Status</span>
                </div>
                {mrdData.mrd_negative_day && <div style={S.stat('#10b981')}><span style={S.statValue}>Day {mrdData.mrd_negative_day}</span><span style={S.statLabel}>MRD⁻ Achieved</span></div>}
                {mrdData.relapse_detected && <div style={S.stat('#ef4444')}><span style={{ ...S.statValue, color: '#ef4444' }}>Day {mrdData.relapse_day}</span><span style={S.statLabel}>⚠ Relapse Detected</span></div>}
                <div style={S.stat('#f59e0b')}><span style={S.statValue}>{mrdData.final_mrd.toExponential(2)}</span><span style={S.statLabel}>Final MRD Level</span></div>
              </div>

              {/* Interactive MRD Chart */}
              <div style={S.card}>
                <h3 style={S.sectionTitle}>📈 MRD Trajectory (Hover for Details)</h3>
                <MRDChart data={mrdData} />
              </div>

              {/* Monitoring Recommendations */}
              {mrdData.monitoring_recommendations?.length > 0 && (
                <div style={S.card}>
                  <h3 style={S.sectionTitle}>📋 Monitoring Recommendations</h3>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {mrdData.monitoring_recommendations.map((rec, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '10px 14px', borderRadius: 8, background: 'rgba(6,182,212,0.05)', border: '1px solid rgba(6,182,212,0.1)' }}>
                        <span style={{ fontSize: 16 }}>{'📌'}</span>
                        <span style={{ fontSize: 13, color: 'var(--text-primary, #e2e8f0)', lineHeight: 1.6 }}>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
