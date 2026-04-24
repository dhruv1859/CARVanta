import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import api from '../api/client';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Types                                                                 */
/* ═══════════════════════════════════════════════════════════════════════ */

interface GraphSummary {
    total_nodes: number;
    total_edges: number;
    groups: Record<string, number>;
    layers: Record<string, number>;
    edge_types: Record<string, number>;
}
interface TopologyData {
    radius: number;
    diameter: number;
    centre_nodes: string[];
    periphery_nodes: string[];
    sample_size: number;
}
interface ClusteringSummary {
    global_average: number;
    transitivity: number;
    top_clustered_nodes: { node: string; cc: number }[];
}
interface ComponentData {
    n_components: number;
    largest_component_size: number;
    component_sizes: number[];
}
interface RichClubData {
    [k: string]: number;
}
interface TriadData {
    open_triads: number;
    closed_triads: number;
    closure_rate: number;
}
interface SmallWorldData {
    sigma: number;
    is_small_world: boolean;
    cc_real: number;
    cc_random: number;
    apl_real: number;
    apl_random: number;
}
interface CentralityEntry {
    node: string;
    score: number;
}

type DashTab = 'overview' | 'centrality' | 'topology' | 'structure' | 'distribution';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Colours & Styles                                                      */
/* ═══════════════════════════════════════════════════════════════════════ */

const C = {
    bg: '#0a0a0f', card: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)',
    text: '#e2e8f0', muted: '#64748b',
    a1: '#4ECDC4', a2: '#FF6B6B', a3: '#45B7D1', a4: '#FFEAA7', a5: '#DDA0DD', a6: '#96CEB4',
};
const GC: Record<string, string> = {
    Disease: '#FF6B6B', Pathway: '#4ECDC4', Antigen: '#45B7D1',
    GeneFamily: '#96CEB4', ProteinDomain: '#DDA0DD',
};

const cardS: React.CSSProperties = { background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 20, marginBottom: 16 };
const statS = (c: string): React.CSSProperties => ({ background: `${c}0a`, border: `1px solid ${c}25`, borderRadius: 12, padding: '16px 14px', textAlign: 'center' });

/* ═══════════════════════════════════════════════════════════════════════ */
/* Reusable pieces                                                       */
/* ═══════════════════════════════════════════════════════════════════════ */

const Stat = ({ l, v, sub, c = C.a1 }: { l: string; v: string | number; sub?: string; c?: string }) => (
    <div style={statS(c)}>
        <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 1 }}>{l}</div>
        <div style={{ fontSize: 24, fontWeight: 800, color: c, marginTop: 4, fontFamily: 'monospace' }}>{v}</div>
        {sub && <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>{sub}</div>}
    </div>
);

const Badge = ({ t, c }: { t: string; c: string }) => (
    <span style={{ background: `${c}22`, color: c, padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600 }}>{t}</span>
);

const PieChart = ({ data, colors: pieColors, size = 160 }: {
    data: { label: string; value: number }[];
    colors: string[];
    size?: number;
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || data.length === 0) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const S = canvas.width = canvas.height = size * 2;
        const cx = S / 2, cy = S / 2, r = S * 0.38;
        const total = data.reduce((s, d) => s + d.value, 0);
        if (total === 0) return;

        ctx.clearRect(0, 0, S, S);
        let angle = -Math.PI / 2;
        data.forEach((d, i) => {
            const sliceAngle = (d.value / total) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, r, angle, angle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = pieColors[i % pieColors.length];
            ctx.fill();
            angle += sliceAngle;
        });

        // Centre hole
        ctx.beginPath(); ctx.arc(cx, cy, r * 0.55, 0, Math.PI * 2);
        ctx.fillStyle = '#0a0a0f'; ctx.fill();
        // Total
        ctx.fillStyle = '#fff'; ctx.font = `bold ${S * 0.1}px monospace`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(total.toLocaleString(), cx, cy);
        ctx.fillStyle = C.muted; ctx.font = `${S * 0.05}px Inter, sans-serif`;
        ctx.fillText('total', cx, cy + S * 0.08);
    }, [data, pieColors, size]);

    return (
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <canvas ref={canvasRef} style={{ width: size, height: size }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {data.map((d, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                        <span style={{ width: 10, height: 10, borderRadius: 3, background: pieColors[i % pieColors.length] }} />
                        <span style={{ color: C.muted }}>{d.label}</span>
                        <span style={{ color: '#fff', fontWeight: 600, marginLeft: 'auto' }}>{d.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

const HorizBar = ({ items, color = C.a1 }: { items: { label: string; value: number }[]; color?: string }) => {
    const maxV = Math.max(...items.map(i => i.value), 0.001);
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {items.map((d, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                    <span style={{ width: 130, color: C.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {d.label.replace(/^(antigen_|disease_|pathway_|family_|domain_)/, '')}
                    </span>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 4, height: 16, overflow: 'hidden' }}>
                        <div style={{ width: `${(d.value / maxV) * 100}%`, height: '100%', background: `linear-gradient(90deg, ${color}88, ${color})`, borderRadius: 4, transition: 'width 0.4s' }} />
                    </div>
                    <span style={{ width: 55, textAlign: 'right', color, fontFamily: 'monospace', fontSize: 10 }}>
                        {d.value < 1 ? d.value.toFixed(5) : d.value.toLocaleString()}
                    </span>
                </div>
            ))}
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Main Component                                                        */
/* ═══════════════════════════════════════════════════════════════════════ */

export default function NeuralBridgeDashboard() {
    const [tab, setTab] = useState<DashTab>('overview');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [summary, setSummary] = useState<GraphSummary | null>(null);
    const [topology, setTopology] = useState<TopologyData | null>(null);
    const [clustering, setClustering] = useState<ClusteringSummary | null>(null);
    const [components, setComponents] = useState<ComponentData | null>(null);
    const [richClub, setRichClub] = useState<RichClubData | null>(null);
    const [triads, setTriads] = useState<TriadData | null>(null);
    const [smallWorld, setSmallWorld] = useState<SmallWorldData | null>(null);

    const [centralityMetric, setCentralityMetric] = useState('pagerank');
    const [centralityData, setCentralityData] = useState<CentralityEntry[]>([]);
    const [hitsData, setHitsData] = useState<any>(null);

    const call = async (fn: () => Promise<void>) => {
        setLoading(true); setError('');
        try { await fn(); } catch (e: any) { setError(e.message); } finally { setLoading(false); }
    };

    /* Load summary on mount */
    useEffect(() => {
        call(async () => {
            const r = await api.get('/api/v5/bridge/summary');
            setSummary(r.data);
        });
    }, []);

    const loadTopology = () => call(async () => {
        const r = await api.get('/api/v5/bridge/topology');
        setTopology(r.data);
    });

    const loadClustering = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/clustering');
        setClustering(r.data);
    });

    const loadComponents = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/components');
        setComponents(r.data);
    });

    const loadRichClub = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/rich-club');
        setRichClub(r.data?.rich_club || {});
    });

    const loadTriads = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/triads');
        setTriads(r.data);
    });

    const loadSmallWorld = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/small-world');
        setSmallWorld(r.data);
    });

    const loadCentrality = (metric: string) => call(async () => {
        setCentralityMetric(metric);
        const r = await api.get(`/api/v5/bridge/analytics/centrality/${metric}`, { params: { top_n: 20 } });
        setCentralityData(r.data?.top_nodes || []);
    });

    const loadHITS = () => call(async () => {
        const r = await api.get('/api/v5/bridge/analytics/hits');
        setHitsData(r.data);
    });

    /* Tab defs */
    const tabs: { id: DashTab; label: string; icon: string }[] = [
        { id: 'overview', label: 'Overview', icon: '📊' },
        { id: 'centrality', label: 'Centrality', icon: '🎯' },
        { id: 'topology', label: 'Topology', icon: '🌐' },
        { id: 'structure', label: 'Structure', icon: '🧩' },
        { id: 'distribution', label: 'Distributions', icon: '📈' },
    ];

    /* ── Render ────────────────────────────────────────────────────── */
    return (
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24, fontFamily: 'Inter, system-ui, sans-serif' }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, margin: '0 0 4px', background: 'linear-gradient(135deg, #6366f1, #4ECDC4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Graph Analytics Dashboard
            </h1>
            <p style={{ color: C.muted, fontSize: 13, marginBottom: 20 }}>Comprehensive network metrics: centrality, topology, clustering, motifs</p>

            {/* Tab bar */}
            <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
                {tabs.map(t => (
                    <button key={t.id} onClick={() => setTab(t.id)} style={{
                        background: tab === t.id ? `${C.a1}15` : 'transparent', border: `1px solid ${tab === t.id ? C.a1 : 'rgba(255,255,255,0.1)'}`,
                        borderRadius: 10, padding: '8px 16px', color: tab === t.id ? C.a1 : C.muted,
                        cursor: 'pointer', fontSize: 12, fontWeight: tab === t.id ? 700 : 400, transition: 'all 0.2s',
                    }}>{t.icon} {t.label}</button>
                ))}
            </div>

            {error && <div style={{ background: 'rgba(255,107,107,0.1)', border: '1px solid rgba(255,107,107,0.3)', borderRadius: 10, padding: '10px 16px', marginBottom: 16, color: C.a2, fontSize: 13 }}>⚠️ {error}</div>}

            {/* OVERVIEW */}
            {tab === 'overview' && summary && (
                <>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 14, marginBottom: 20 }}>
                        <Stat l="Total Nodes" v={summary.total_nodes.toLocaleString()} c={C.a1} />
                        <Stat l="Total Edges" v={summary.total_edges.toLocaleString()} c={C.a3} />
                        <Stat l="Node Groups" v={Object.keys(summary.groups).length} c={C.a4} />
                        <Stat l="Edge Types" v={Object.keys(summary.edge_types).length} c={C.a5} />
                        <Stat l="Layers" v={Object.keys(summary.layers).length} c={C.a6} />
                        <Stat l="Density" v={(2 * summary.total_edges / Math.max(summary.total_nodes * (summary.total_nodes - 1), 1)).toFixed(4)} c={C.a2} />
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <div style={cardS}>
                            <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Node Distribution</h4>
                            <PieChart
                                data={Object.entries(summary.groups).map(([l, v]) => ({ label: l, value: v }))}
                                colors={Object.keys(summary.groups).map(g => GC[g] || '#888')}
                            />
                        </div>
                        <div style={cardS}>
                            <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Edge Types</h4>
                            <HorizBar
                                items={Object.entries(summary.edge_types).map(([l, v]) => ({ label: l.replace(/_/g, ' '), value: v })).sort((a, b) => b.value - a.value)}
                                color={C.a3}
                            />
                        </div>
                    </div>
                </>
            )}

            {/* CENTRALITY */}
            {tab === 'centrality' && (
                <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                        {['degree', 'betweenness', 'closeness', 'pagerank', 'eigenvector'].map(m => (
                            <button key={m} onClick={() => loadCentrality(m)} style={{
                                background: centralityMetric === m ? `${C.a3}22` : 'transparent',
                                border: `1px solid ${centralityMetric === m ? C.a3 : 'rgba(255,255,255,0.1)'}`,
                                borderRadius: 8, padding: '7px 14px', color: centralityMetric === m ? C.a3 : C.muted,
                                cursor: 'pointer', fontSize: 12, fontWeight: centralityMetric === m ? 700 : 400,
                            }}>{m}</button>
                        ))}
                        <button onClick={loadHITS} style={{
                            background: hitsData ? `${C.a5}22` : 'transparent',
                            border: `1px solid ${hitsData ? C.a5 : 'rgba(255,255,255,0.1)'}`,
                            borderRadius: 8, padding: '7px 14px', color: hitsData ? C.a5 : C.muted,
                            cursor: 'pointer', fontSize: 12,
                        }}>HITS</button>
                    </div>
                    {centralityData.length > 0 && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a3, fontSize: 14, margin: '0 0 12px' }}>Top 20 by {centralityMetric}</h4>
                            <HorizBar items={centralityData.map(d => ({ label: d.node, value: d.score }))} color={C.a3} />
                        </div>
                    )}
                    {hitsData && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            <div style={cardS}>
                                <h4 style={{ color: C.a5, fontSize: 14, margin: '0 0 12px' }}>Top Hubs</h4>
                                <HorizBar items={hitsData.top_hubs?.map((h: any) => ({ label: h.node, value: h.score })) || []} color={C.a5} />
                            </div>
                            <div style={cardS}>
                                <h4 style={{ color: C.a4, fontSize: 14, margin: '0 0 12px' }}>Top Authorities</h4>
                                <HorizBar items={hitsData.top_authorities?.map((a: any) => ({ label: a.node, value: a.score })) || []} color={C.a4} />
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* TOPOLOGY */}
            {tab === 'topology' && (
                <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                        <button onClick={loadTopology} disabled={loading} style={{ background: `linear-gradient(135deg, ${C.a1}, ${C.a3})`, color: '#000', border: 'none', borderRadius: 10, padding: '10px 24px', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Compute Topology</button>
                        <button onClick={loadSmallWorld} disabled={loading} style={{ background: `linear-gradient(135deg, ${C.a4}, ${C.a2})`, color: '#000', border: 'none', borderRadius: 10, padding: '10px 24px', fontWeight: 700, cursor: 'pointer', fontSize: 13 }}>Small-World Test</button>
                    </div>
                    {topology && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 14, marginBottom: 16 }}>
                            <Stat l="Radius" v={topology.radius} c={C.a1} />
                            <Stat l="Diameter" v={topology.diameter} c={C.a2} />
                            <Stat l="Sample Size" v={topology.sample_size} c={C.a6} />
                        </div>
                    )}
                    {topology && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                            <div style={cardS}>
                                <h4 style={{ color: C.a1, fontSize: 14, margin: '0 0 12px' }}>Centre Nodes</h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{topology.centre_nodes.map((n, i) => <Badge key={i} t={n.replace(/^(antigen_|disease_|pathway_)/, '')} c={C.a1} />)}</div>
                            </div>
                            <div style={cardS}>
                                <h4 style={{ color: C.a2, fontSize: 14, margin: '0 0 12px' }}>Periphery Nodes</h4>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>{topology.periphery_nodes.map((n, i) => <Badge key={i} t={n.replace(/^(antigen_|disease_|pathway_)/, '')} c={C.a2} />)}</div>
                            </div>
                        </div>
                    )}
                    {smallWorld && (
                        <div style={{ ...cardS, marginTop: 16 }}>
                            <h4 style={{ color: C.a4, fontSize: 14, margin: '0 0 12px' }}>Small-World Analysis</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10 }}>
                                <Stat l="σ Coefficient" v={smallWorld.sigma?.toFixed(3) || '—'} c={C.a4} sub={smallWorld.is_small_world ? '✓ Small-world' : '✗ Not small-world'} />
                                <Stat l="CC (Real)" v={smallWorld.cc_real?.toFixed(4) || '—'} c={C.a1} />
                                <Stat l="CC (Random)" v={smallWorld.cc_random?.toFixed(4) || '—'} c={C.muted} />
                                <Stat l="APL (Real)" v={smallWorld.apl_real?.toFixed(2) || '—'} c={C.a3} />
                                <Stat l="APL (Random)" v={smallWorld.apl_random?.toFixed(2) || '—'} c={C.muted} />
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* STRUCTURE */}
            {tab === 'structure' && (
                <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
                        <button onClick={loadClustering} disabled={loading} style={{ background: `${C.a6}22`, border: `1px solid ${C.a6}`, borderRadius: 8, padding: '8px 16px', color: C.a6, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Clustering</button>
                        <button onClick={loadComponents} disabled={loading} style={{ background: `${C.a3}22`, border: `1px solid ${C.a3}`, borderRadius: 8, padding: '8px 16px', color: C.a3, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Components</button>
                        <button onClick={loadTriads} disabled={loading} style={{ background: `${C.a4}22`, border: `1px solid ${C.a4}`, borderRadius: 8, padding: '8px 16px', color: C.a4, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Triads</button>
                        <button onClick={loadRichClub} disabled={loading} style={{ background: `${C.a5}22`, border: `1px solid ${C.a5}`, borderRadius: 8, padding: '8px 16px', color: C.a5, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>Rich-Club</button>
                    </div>
                    {clustering && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a6, fontSize: 14, margin: '0 0 12px' }}>Clustering Coefficients</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
                                <Stat l="Global Avg" v={clustering.global_average?.toFixed(4) || '—'} c={C.a6} />
                                <Stat l="Transitivity" v={clustering.transitivity?.toFixed(4) || '—'} c={C.a1} />
                                <Stat l="Top CC Nodes" v={clustering.top_clustered_nodes?.length || 0} c={C.a3} />
                            </div>
                            {clustering.top_clustered_nodes && (
                                <HorizBar items={clustering.top_clustered_nodes.map(d => ({ label: d.node, value: d.cc }))} color={C.a6} />
                            )}
                        </div>
                    )}
                    {components && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a3, fontSize: 14, margin: '0 0 12px' }}>Connected Components</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                                <Stat l="Components" v={components.n_components} c={C.a3} />
                                <Stat l="Largest Size" v={components.largest_component_size} c={C.a1} />
                                <Stat l="Isolated" v={components.component_sizes?.filter(s => s === 1).length || 0} c={C.a2} />
                            </div>
                        </div>
                    )}
                    {triads && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a4, fontSize: 14, margin: '0 0 12px' }}>Triad Census</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                                <Stat l="Open Triads" v={triads.open_triads?.toLocaleString() || '—'} c={C.a4} />
                                <Stat l="Closed Triads" v={triads.closed_triads?.toLocaleString() || '—'} c={C.a1} />
                                <Stat l="Closure Rate" v={((triads.closure_rate || 0) * 100).toFixed(1) + '%'} c={C.a6} />
                            </div>
                        </div>
                    )}
                    {richClub && Object.keys(richClub).length > 0 && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a5, fontSize: 14, margin: '0 0 12px' }}>Rich-Club Coefficient φ(k)</h4>
                            <HorizBar
                                items={Object.entries(richClub).map(([k, v]) => ({ label: `k=${k}`, value: v as number })).sort((a, b) => parseInt(a.label.slice(2)) - parseInt(b.label.slice(2)))}
                                color={C.a5}
                            />
                        </div>
                    )}
                </>
            )}

            {/* DISTRIBUTIONS */}
            {tab === 'distribution' && summary && (
                <>
                    <div style={cardS}>
                        <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Layer Distribution</h4>
                        <PieChart
                            data={Object.entries(summary.layers).map(([l, v]) => ({ label: l, value: v }))}
                            colors={[C.a2, C.a1, C.a3, C.a4, C.a5]}
                        />
                    </div>
                    <div style={cardS}>
                        <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Edge Type Distribution</h4>
                        <PieChart
                            data={Object.entries(summary.edge_types).map(([l, v]) => ({ label: l.replace(/_/g, ' '), value: v }))}
                            colors={[C.a1, C.a2, C.a3, C.a4, C.a5, C.a6, '#F0B27A', '#85929E']}
                        />
                    </div>
                </>
            )}
        </div>
    );
}
