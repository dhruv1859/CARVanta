import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import api from '../api/client';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Types                                                                 */
/* ═══════════════════════════════════════════════════════════════════════ */

interface DiffusionResult {
    seed_nodes: string[];
    top_heated_nodes: { node: string; heat: number }[];
    total_heat: number;
}
interface RWRResult {
    seed_node: string;
    top_related_nodes: { node: string; proximity: number }[];
}
interface SIRResult {
    timeline_sample: { step: number; S: number; I: number; R: number }[];
    infection_probability: Record<string, number>;
    total_ever_infected: number;
    avg_final_recovered_pct: number;
}
interface InfluenceResult {
    seed_set: string[];
    estimated_spread: number;
    spread_fraction: number;
}
interface MotifCensus {
    summary: Record<string, number>;
    details: Record<string, any>;
}
interface GraphNode {
    id: string; name: string; group: string; layer: string;
    val: number; score?: number;
}

type SubTab = 'heat' | 'rwr' | 'sir' | 'influence' | 'motifs' | 'triangles' | 'cliques' | 'hubs';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Styles                                                                */
/* ═══════════════════════════════════════════════════════════════════════ */

const colors = {
    bg: '#0a0a0f', card: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)',
    accent1: '#4ECDC4', accent2: '#FF6B6B', accent3: '#45B7D1', accent4: '#FFEAA7',
    accent5: '#DDA0DD', accent6: '#96CEB4', text: '#e2e8f0', muted: '#64748b',
};

const baseCard: React.CSSProperties = {
    background: colors.card, border: `1px solid ${colors.border}`,
    borderRadius: 14, padding: 20, marginBottom: 16,
};

const baseBtn = (active: boolean, color: string): React.CSSProperties => ({
    background: active ? `${color}22` : 'transparent',
    border: `1px solid ${active ? color : 'rgba(255,255,255,0.1)'}`,
    borderRadius: 10, padding: '8px 16px', color: active ? color : colors.muted,
    cursor: 'pointer', fontSize: 12, fontWeight: active ? 700 : 400,
    transition: 'all 0.2s',
});

const statBox = (color: string): React.CSSProperties => ({
    background: `${color}0a`, border: `1px solid ${color}25`,
    borderRadius: 12, padding: '16px 14px', textAlign: 'center',
});

/* ═══════════════════════════════════════════════════════════════════════ */
/* Reusable Components                                                   */
/* ═══════════════════════════════════════════════════════════════════════ */

const StatCard = ({ label, value, sub, color = colors.accent1 }: { label: string; value: string | number; sub?: string; color?: string }) => (
    <div style={statBox(color)}>
        <div style={{ fontSize: 10, color: colors.muted, textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
        <div style={{ fontSize: 24, fontWeight: 800, color, marginTop: 4, fontFamily: 'monospace' }}>{value}</div>
        {sub && <div style={{ fontSize: 10, color: colors.muted, marginTop: 4 }}>{sub}</div>}
    </div>
);

const Badge = ({ text, color }: { text: string; color: string }) => (
    <span style={{ background: `${color}22`, color, padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600 }}>{text}</span>
);

const BarChart = ({ data, valueKey, labelKey, color = colors.accent1, maxWidth = 300 }: {
    data: any[]; valueKey: string; labelKey: string; color?: string; maxWidth?: number;
}) => {
    const maxVal = Math.max(...data.map(d => d[valueKey] || 0), 0.001);
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {data.map((d, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                    <span style={{ width: 140, color: colors.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {(d[labelKey] || '').replace(/^(antigen_|disease_|pathway_|family_|domain_)/, '')}
                    </span>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 4, height: 16, overflow: 'hidden' }}>
                        <div style={{ width: `${(d[valueKey] / maxVal) * 100}%`, height: '100%', background: `linear-gradient(90deg, ${color}88, ${color})`, borderRadius: 4, transition: 'width 0.5s ease' }} />
                    </div>
                    <span style={{ width: 60, textAlign: 'right', color, fontFamily: 'monospace', fontSize: 10 }}>
                        {typeof d[valueKey] === 'number' ? d[valueKey].toFixed(4) : d[valueKey]}
                    </span>
                </div>
            ))}
        </div>
    );
};

const TimelineChart = ({ data, keys, colors: lineColors }: {
    data: any[]; keys: string[]; colors: string[];
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || data.length === 0) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const W = canvas.width = 500;
        const H = canvas.height = 200;
        const maxVal = Math.max(...data.flatMap(d => keys.map(k => d[k] || 0)));
        const stepW = W / Math.max(data.length - 1, 1);

        ctx.fillStyle = '#0a0a0f';
        ctx.fillRect(0, 0, W, H);

        // Grid
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        for (let y = 0; y <= H; y += H / 4) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

        keys.forEach((key, ki) => {
            ctx.beginPath();
            ctx.strokeStyle = lineColors[ki] || '#fff';
            ctx.lineWidth = 2;
            data.forEach((d, i) => {
                const x = i * stepW;
                const y = H - ((d[key] || 0) / maxVal) * H * 0.9 - H * 0.05;
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();
        });

        // Legend
        ctx.font = '10px Inter, sans-serif';
        keys.forEach((key, ki) => {
            ctx.fillStyle = lineColors[ki];
            ctx.fillRect(10, 10 + ki * 18, 12, 12);
            ctx.fillStyle = '#ccc';
            ctx.fillText(key, 28, 20 + ki * 18);
        });
    }, [data, keys, lineColors]);

    return <canvas ref={canvasRef} style={{ width: '100%', maxWidth: 500, height: 200, borderRadius: 10, border: `1px solid ${colors.border}` }} />;
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Main Component                                                        */
/* ═══════════════════════════════════════════════════════════════════════ */

export default function NeuralBridgeAdvanced() {
    /* State */
    const [subTab, setSubTab] = useState<SubTab>('heat');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    /* Diffusion */
    const [heatSeeds, setHeatSeeds] = useState('antigen_CD19');
    const [heatSteps, setHeatSteps] = useState(10);
    const [heatRate, setHeatRate] = useState(0.3);
    const [heatResult, setHeatResult] = useState<DiffusionResult | null>(null);

    /* RWR */
    const [rwrSeed, setRwrSeed] = useState('antigen_CD19');
    const [rwrRestart, setRwrRestart] = useState(0.15);
    const [rwrResult, setRwrResult] = useState<RWRResult | null>(null);

    /* SIR */
    const [sirInfected, setSirInfected] = useState('antigen_CD19');
    const [sirInfRate, setSirInfRate] = useState(0.3);
    const [sirRecRate, setSirRecRate] = useState(0.1);
    const [sirResult, setSirResult] = useState<SIRResult | null>(null);

    /* Influence */
    const [infK, setInfK] = useState(5);
    const [infResult, setInfResult] = useState<InfluenceResult | null>(null);

    /* Motifs */
    const [motifCensus, setMotifCensus] = useState<MotifCensus | null>(null);
    const [triangles, setTriangles] = useState<any>(null);
    const [cliques, setCliques] = useState<any>(null);
    const [hubSpokes, setHubSpokes] = useState<any>(null);

    /* API calls */
    const call = async (fn: () => Promise<void>) => {
        setLoading(true); setError('');
        try { await fn(); } catch (e: any) { setError(e.message || 'Request failed'); }
        finally { setLoading(false); }
    };

    const runHeat = () => call(async () => {
        const r = await api.get('/api/v5/bridge/diffusion/heat', { params: { seeds: heatSeeds, steps: heatSteps, rate: heatRate } });
        setHeatResult(r.data);
    });

    const runRWR = () => call(async () => {
        const r = await api.get(`/api/v5/bridge/diffusion/rwr/${rwrSeed}`, { params: { restart_prob: rwrRestart } });
        setRwrResult(r.data);
    });

    const runSIR = () => call(async () => {
        const r = await api.get('/api/v5/bridge/diffusion/sir', { params: { infected: sirInfected, infection_rate: sirInfRate, recovery_rate: sirRecRate } });
        setSirResult(r.data);
    });

    const runInfluence = () => call(async () => {
        const r = await api.get('/api/v5/bridge/diffusion/influence-max', { params: { k: infK } });
        setInfResult(r.data);
    });

    const runMotifCensus = () => call(async () => {
        const r = await api.get('/api/v5/bridge/motifs/census');
        setMotifCensus(r.data);
    });

    const runTriangles = () => call(async () => {
        const r = await api.get('/api/v5/bridge/motifs/triangles');
        setTriangles(r.data);
    });

    const runCliques = () => call(async () => {
        const r = await api.get('/api/v5/bridge/motifs/cliques');
        setCliques(r.data);
    });

    const runHubs = () => call(async () => {
        const r = await api.get('/api/v5/bridge/motifs/hubs');
        setHubSpokes(r.data);
    });

    /* Tab definitions */
    const tabs: { id: SubTab; label: string; icon: string; color: string }[] = [
        { id: 'heat', label: 'Heat Diffusion', icon: '🔥', color: colors.accent2 },
        { id: 'rwr', label: 'Random Walk', icon: '🚶', color: colors.accent1 },
        { id: 'sir', label: 'SIR Model', icon: '🦠', color: colors.accent4 },
        { id: 'influence', label: 'Influence Max', icon: '💥', color: colors.accent5 },
        { id: 'motifs', label: 'Motif Census', icon: '🔺', color: colors.accent6 },
        { id: 'triangles', label: 'Triangles', icon: '△', color: colors.accent3 },
        { id: 'cliques', label: 'Cliques', icon: '⬡', color: colors.accent1 },
        { id: 'hubs', label: 'Hub-Spokes', icon: '☀️', color: colors.accent4 },
    ];

    /* ── Input Row helper ─────────────────────────────────────────── */
    const InputRow = ({ children }: { children: React.ReactNode }) => (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16, alignItems: 'flex-end' }}>{children}</div>
    );

    const InputField = ({ label, value, onChange, type = 'text', width = 180 }: { label: string; value: any; onChange: (v: any) => void; type?: string; width?: number }) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 10, color: colors.muted, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</label>
            <input type={type} value={value}
                onChange={e => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${colors.border}`, borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13, width, outline: 'none' }}
            />
        </div>
    );

    const RunBtn = ({ onClick, label, color = colors.accent1 }: { onClick: () => void; label: string; color?: string }) => (
        <button onClick={onClick} disabled={loading}
            style={{ background: `linear-gradient(135deg, ${color}, ${color}cc)`, color: '#000', border: 'none', borderRadius: 10, padding: '10px 24px', fontWeight: 700, cursor: loading ? 'wait' : 'pointer', fontSize: 13, opacity: loading ? 0.6 : 1, alignSelf: 'flex-end' }}>
            {loading ? '⏳ Running...' : label}
        </button>
    );

    /* ── Tab content renderers ─────────────────────────────────────── */

    const renderHeat = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent2, fontSize: 16, margin: '0 0 8px' }}>🔥 Heat Diffusion Simulation</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Simulate how a signal (drug target, mutation) propagates through the knowledge graph via heat diffusion.</p>
                <InputRow>
                    <InputField label="Seed Nodes (comma-sep)" value={heatSeeds} onChange={setHeatSeeds} width={280} />
                    <InputField label="Time Steps" value={heatSteps} onChange={setHeatSteps} type="number" width={90} />
                    <InputField label="Diffusion Rate" value={heatRate} onChange={setHeatRate} type="number" width={110} />
                    <RunBtn onClick={runHeat} label="Run Diffusion" color={colors.accent2} />
                </InputRow>
            </div>
            {heatResult && (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 16 }}>
                        <StatCard label="Seed Nodes" value={heatResult.seed_nodes.length} color={colors.accent2} />
                        <StatCard label="Heated Nodes" value={heatResult.top_heated_nodes.length} color={colors.accent1} />
                        <StatCard label="Total Heat" value={heatResult.total_heat.toFixed(3)} color={colors.accent4} />
                    </div>
                    <div style={baseCard}>
                        <h4 style={{ color: colors.accent2, fontSize: 14, margin: '0 0 12px' }}>Top Heated Nodes</h4>
                        <BarChart data={heatResult.top_heated_nodes} valueKey="heat" labelKey="node" color={colors.accent2} />
                    </div>
                </>
            )}
        </>
    );

    const renderRWR = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent1, fontSize: 16, margin: '0 0 8px' }}>🚶 Random Walk with Restart</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Personalised PageRank — find functionally close nodes even if topologically distant.</p>
                <InputRow>
                    <InputField label="Seed Node" value={rwrSeed} onChange={setRwrSeed} width={220} />
                    <InputField label="Restart Prob" value={rwrRestart} onChange={setRwrRestart} type="number" width={110} />
                    <RunBtn onClick={runRWR} label="Run RWR" color={colors.accent1} />
                </InputRow>
            </div>
            {rwrResult && (
                <div style={baseCard}>
                    <h4 style={{ color: colors.accent1, fontSize: 14, margin: '0 0 4px' }}>Closest Nodes to <span style={{ color: '#fff' }}>{rwrResult.seed_node}</span></h4>
                    <p style={{ color: colors.muted, fontSize: 11, marginBottom: 12 }}>Ranked by personalised PageRank proximity</p>
                    <BarChart data={rwrResult.top_related_nodes} valueKey="proximity" labelKey="node" color={colors.accent1} />
                </div>
            )}
        </>
    );

    const renderSIR = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent4, fontSize: 16, margin: '0 0 8px' }}>🦠 SIR Epidemic Simulation</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Model how mutations or resistance signals propagate through the network.</p>
                <InputRow>
                    <InputField label="Initially Infected" value={sirInfected} onChange={setSirInfected} width={220} />
                    <InputField label="Infection Rate" value={sirInfRate} onChange={setSirInfRate} type="number" width={110} />
                    <InputField label="Recovery Rate" value={sirRecRate} onChange={setSirRecRate} type="number" width={110} />
                    <RunBtn onClick={runSIR} label="Run SIR" color={colors.accent4} />
                </InputRow>
            </div>
            {sirResult && (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 16 }}>
                        <StatCard label="Total Infected" value={sirResult.total_ever_infected} color={colors.accent2} />
                        <StatCard label="Final Recovered %" value={`${sirResult.avg_final_recovered_pct}%`} color={colors.accent6} />
                    </div>
                    {sirResult.timeline_sample.length > 0 && (
                        <div style={baseCard}>
                            <h4 style={{ color: colors.accent4, fontSize: 14, margin: '0 0 12px' }}>SIR Timeline</h4>
                            <TimelineChart data={sirResult.timeline_sample} keys={['S', 'I', 'R']} colors={[colors.accent3, colors.accent2, colors.accent6]} />
                        </div>
                    )}
                    <div style={baseCard}>
                        <h4 style={{ color: colors.accent4, fontSize: 14, margin: '0 0 12px' }}>Top Infection Probabilities</h4>
                        <BarChart
                            data={Object.entries(sirResult.infection_probability).slice(0, 15).map(([node, prob]) => ({ node, prob }))}
                            valueKey="prob" labelKey="node" color={colors.accent2}
                        />
                    </div>
                </>
            )}
        </>
    );

    const renderInfluence = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent5, fontSize: 16, margin: '0 0 8px' }}>💥 Influence Maximization</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Find the k most influential nodes — optimal combination therapy targets.</p>
                <InputRow>
                    <InputField label="k (seed set size)" value={infK} onChange={setInfK} type="number" width={110} />
                    <RunBtn onClick={runInfluence} label="Find Top-k" color={colors.accent5} />
                </InputRow>
            </div>
            {infResult && (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 16 }}>
                        <StatCard label="Seed Set Size" value={infResult.seed_set.length} color={colors.accent5} />
                        <StatCard label="Expected Spread" value={infResult.estimated_spread.toFixed(1)} color={colors.accent1} />
                        <StatCard label="Spread Fraction" value={`${(infResult.spread_fraction * 100).toFixed(1)}%`} color={colors.accent4} />
                    </div>
                    <div style={baseCard}>
                        <h4 style={{ color: colors.accent5, fontSize: 14, margin: '0 0 12px' }}>Optimal Seed Set</h4>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                            {infResult.seed_set.map((s, i) => (
                                <div key={i} style={{ background: `${colors.accent5}15`, border: `1px solid ${colors.accent5}30`, borderRadius: 10, padding: '8px 14px', fontSize: 12, color: colors.accent5, fontWeight: 600 }}>
                                    #{i + 1} {s.replace(/^(antigen_|disease_|pathway_)/, '')}
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </>
    );

    const renderMotifCensus = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent6, fontSize: 16, margin: '0 0 8px' }}>🔺 Full Motif Census</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Detect recurring structural patterns: triangles, cliques, feed-forward loops, hubs, diamonds, chains.</p>
                <RunBtn onClick={runMotifCensus} label="Run Census" color={colors.accent6} />
            </div>
            {motifCensus && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
                    {Object.entries(motifCensus.summary).map(([k, v]) => (
                        <StatCard key={k} label={k.replace(/_/g, ' ')} value={v} color={colors.accent6} />
                    ))}
                </div>
            )}
        </>
    );

    const renderTriangles = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent3, fontSize: 16, margin: '0 0 8px' }}>△ Triangle Detection</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Find tightly coupled 3-node functional modules (A—B—C, all connected).</p>
                <RunBtn onClick={runTriangles} label="Find Triangles" color={colors.accent3} />
            </div>
            {triangles && (
                <div style={baseCard}>
                    <h4 style={{ color: colors.accent3, fontSize: 14, margin: '0 0 12px' }}>Found {triangles.total_triangles} triangles</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
                        {triangles.triangles?.slice(0, 12).map((t: any, i: number) => (
                            <div key={i} style={{ background: `${colors.accent3}08`, border: `1px solid ${colors.accent3}20`, borderRadius: 10, padding: 12 }}>
                                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                    {t.names.map((n: string, j: number) => (
                                        <React.Fragment key={j}>
                                            <Badge text={n || t.nodes[j].split('_').pop()} color={colors.accent3} />
                                            {j < 2 && <span style={{ color: colors.muted, fontSize: 10 }}>—</span>}
                                        </React.Fragment>
                                    ))}
                                </div>
                                <div style={{ fontSize: 10, color: colors.muted, marginTop: 6 }}>
                                    Groups: {t.groups?.join(' · ')}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );

    const renderCliques = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent1, fontSize: 16, margin: '0 0 8px' }}>⬡ Clique Detection</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Find fully connected subgraphs using Bron–Kerbosch algorithm.</p>
                <RunBtn onClick={runCliques} label="Find Cliques" color={colors.accent1} />
            </div>
            {cliques && (
                <div style={baseCard}>
                    <h4 style={{ color: colors.accent1, fontSize: 14, margin: '0 0 12px' }}>Found {cliques.total_cliques} cliques</h4>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {cliques.cliques?.slice(0, 10).map((c: any, i: number) => (
                            <div key={i} style={{ background: `${colors.accent1}08`, border: `1px solid ${colors.accent1}20`, borderRadius: 10, padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                    {c.names?.map((n: string, j: number) => <Badge key={j} text={n || c.nodes[j]} color={colors.accent1} />)}
                                </div>
                                <span style={{ fontSize: 11, color: colors.muted }}>size {c.size}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );

    const renderHubs = () => (
        <>
            <div style={baseCard}>
                <h3 style={{ color: colors.accent4, fontSize: 16, margin: '0 0 8px' }}>☀️ Hub-Spoke Patterns</h3>
                <p style={{ color: colors.muted, fontSize: 12, marginBottom: 16 }}>Find star-topology hubs with high degree but sparse spoke interconnection.</p>
                <RunBtn onClick={runHubs} label="Find Hubs" color={colors.accent4} />
            </div>
            {hubSpokes && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {hubSpokes.hub_spokes?.slice(0, 10).map((h: any, i: number) => (
                        <div key={i} style={{ ...baseCard, borderLeft: `3px solid ${colors.accent4}`, marginBottom: 0 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <div>
                                    <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>{h.hub_name || h.hub_id}</span>
                                    <Badge text={h.group} color={colors.accent3} />
                                </div>
                                <span style={{ color: colors.accent4, fontFamily: 'monospace', fontSize: 13 }}>deg={h.degree}</span>
                            </div>
                            <div style={{ display: 'flex', gap: 16, fontSize: 11, color: colors.muted }}>
                                <span>Star Score: <span style={{ color: colors.accent4 }}>{h.star_score}</span></span>
                                <span>Spoke Density: {h.spoke_density}</span>
                                <span>Groups: {Object.entries(h.spoke_groups || {}).map(([g, c]: any) => `${g}(${c})`).join(', ')}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );

    const TAB_RENDER: Record<SubTab, () => React.ReactNode> = {
        heat: renderHeat, rwr: renderRWR, sir: renderSIR, influence: renderInfluence,
        motifs: renderMotifCensus, triangles: renderTriangles, cliques: renderCliques, hubs: renderHubs,
    };

    /* ── Main Render ──────────────────────────────────────────────── */
    return (
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24, fontFamily: 'Inter, system-ui, sans-serif' }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, margin: '0 0 4px', background: 'linear-gradient(135deg, #4ECDC4, #FF6B6B, #DDA0DD)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Neural Bridge — Advanced Analytics
            </h1>
            <p style={{ color: colors.muted, fontSize: 13, marginBottom: 20 }}>Diffusion, influence propagation, and structural motif detection</p>

            {/* Tab bar */}
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 20 }}>
                {tabs.map(t => (
                    <button key={t.id} onClick={() => setSubTab(t.id)} style={baseBtn(subTab === t.id, t.color)}>
                        {t.icon} {t.label}
                    </button>
                ))}
            </div>

            {error && <div style={{ background: 'rgba(255,107,107,0.1)', border: '1px solid rgba(255,107,107,0.3)', borderRadius: 10, padding: '10px 16px', marginBottom: 16, color: '#FF6B6B', fontSize: 13 }}>⚠️ {error}</div>}

            {TAB_RENDER[subTab]?.()}
        </div>
    );
}
