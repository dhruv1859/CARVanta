import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import api from '../api/client';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Types                                                                 */
/* ═══════════════════════════════════════════════════════════════════════ */

interface NodeDetail {
    id: string; name: string; group: string; layer: string;
    val: number; score?: number; confidence?: number;
    druggability?: string; gene_family?: string; primary_pathway?: string;
    domain?: string; cancer_type?: string; tier?: string;
}
interface Neighbour {
    id: string; name: string; group: string; relationship: string; weight: number;
}
interface SimilarNode {
    node_id: string; name: string; group: string; layer: string;
    score?: number; signals: { ensemble: number; jaccard: number; attribute: number; cosine: number };
}
interface IndicationSuggestion {
    disease_id: string; disease_name: string; repurpose_score: number;
    avg_similarity: number; n_similar_antigens: number;
}
interface PathResult {
    found: boolean; path?: string[]; hops?: number;
    total_weight?: number; message?: string;
}
interface LinkPrediction {
    source: string; target: string;
    source_name: string; target_name: string;
    ensemble_score: number; common_neighbours: number;
    jaccard: number; adamic_adar: number;
}

type DetailTab = 'overview' | 'neighbours' | 'similar' | 'indication' | 'paths' | 'predictions' | 'diffusion';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Colour Map                                                            */
/* ═══════════════════════════════════════════════════════════════════════ */

const GC: Record<string, string> = {
    Disease: '#FF6B6B', Pathway: '#4ECDC4', Antigen: '#45B7D1',
    GeneFamily: '#96CEB4', ProteinDomain: '#DDA0DD',
};
const C = {
    bg: '#0a0a0f', card: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)',
    text: '#e2e8f0', muted: '#64748b',
    a1: '#4ECDC4', a2: '#FF6B6B', a3: '#45B7D1', a4: '#FFEAA7', a5: '#DDA0DD', a6: '#96CEB4',
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Styles                                                                */
/* ═══════════════════════════════════════════════════════════════════════ */

const card: React.CSSProperties = { background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 20, marginBottom: 16 };
const statBox = (c: string): React.CSSProperties => ({ background: `${c}0a`, border: `1px solid ${c}25`, borderRadius: 12, padding: '14px 12px', textAlign: 'center' });

const Stat = ({ l, v, c = C.a1 }: { l: string; v: string | number; c?: string }) => (
    <div style={statBox(c)}>
        <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 1 }}>{l}</div>
        <div style={{ fontSize: 22, fontWeight: 800, color: c, marginTop: 4, fontFamily: 'monospace' }}>{v}</div>
    </div>
);

const Badge = ({ t, c }: { t: string; c: string }) => (
    <span style={{ background: `${c}22`, color: c, padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600 }}>{t}</span>
);

const Btn = ({ onClick, label, color = C.a1, disabled = false }: { onClick: () => void; label: string; color?: string; disabled?: boolean }) => (
    <button onClick={onClick} disabled={disabled} style={{
        background: `linear-gradient(135deg, ${color}, ${color}cc)`, color: '#000', border: 'none',
        borderRadius: 10, padding: '9px 22px', fontWeight: 700, cursor: disabled ? 'wait' : 'pointer', fontSize: 13, opacity: disabled ? 0.5 : 1,
    }}>{label}</button>
);

/* ═══════════════════════════════════════════════════════════════════════ */
/* Radial Chart (Mini)                                                   */
/* ═══════════════════════════════════════════════════════════════════════ */

const RadialScore = ({ score, label, color, size = 80 }: { score: number; label: string; color: string; size?: number }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const S = canvas.width = canvas.height = size * 2;
        const cx = S / 2, cy = S / 2, r = S / 2 - 8;

        ctx.clearRect(0, 0, S, S);
        // BG arc
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.05)'; ctx.lineWidth = 6; ctx.stroke();
        // Score arc
        ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * score);
        ctx.strokeStyle = color; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.stroke();
        // Text
        ctx.fillStyle = '#fff'; ctx.font = `bold ${S * 0.18}px monospace`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText((score * 100).toFixed(0) + '%', cx, cy);
        ctx.fillStyle = C.muted; ctx.font = `${S * 0.08}px Inter, sans-serif`;
        ctx.fillText(label, cx, cy + S * 0.16);
    }, [score, label, color, size]);
    return <canvas ref={canvasRef} style={{ width: size, height: size }} />;
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Main Component                                                        */
/* ═══════════════════════════════════════════════════════════════════════ */

export default function NeuralBridgeDetail() {
    /* State */
    const [nodeId, setNodeId] = useState('');
    const [nodeInput, setNodeInput] = useState('antigen_CD19');
    const [tab, setTab] = useState<DetailTab>('overview');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const [nodeDetail, setNodeDetail] = useState<NodeDetail | null>(null);
    const [neighbours, setNeighbours] = useState<Neighbour[]>([]);
    const [similarNodes, setSimilarNodes] = useState<SimilarNode[]>([]);
    const [indications, setIndications] = useState<IndicationSuggestion[]>([]);
    const [pathTarget, setPathTarget] = useState('disease_dlbcl');
    const [pathResult, setPathResult] = useState<PathResult | null>(null);
    const [predictions, setPredictions] = useState<LinkPrediction[]>([]);
    const [heatResult, setHeatResult] = useState<any>(null);

    const [graphNodes, setGraphNodes] = useState<any[]>([]);
    const [graphLinks, setGraphLinks] = useState<any[]>([]);

    /* Load graph on mount */
    useEffect(() => {
        api.get('/api/v5/bridge/graph')
            .then(r => {
                if (r.data?.data) {
                    setGraphNodes(r.data.data.nodes || []);
                    setGraphLinks(r.data.data.links || []);
                }
            })
            .catch(() => {});
    }, []);

    /* Find node from graph */
    const findNode = useCallback((id: string): NodeDetail | null => {
        return graphNodes.find((n: any) => n.id === id) || null;
    }, [graphNodes]);

    /* Get neighbours */
    const getNeighbours = useCallback((id: string): Neighbour[] => {
        const nbs: Neighbour[] = [];
        for (const l of graphLinks) {
            const s = typeof l.source === 'object' ? l.source.id : l.source;
            const t = typeof l.target === 'object' ? l.target.id : l.target;
            if (s === id) {
                const n = findNode(t);
                if (n) nbs.push({ id: t, name: n.name, group: n.group, relationship: l.relationship || '', weight: l.weight || 0.5 });
            } else if (t === id) {
                const n = findNode(s);
                if (n) nbs.push({ id: s, name: n.name, group: n.group, relationship: l.relationship || '', weight: l.weight || 0.5 });
            }
        }
        return nbs.sort((a, b) => b.weight - a.weight);
    }, [graphLinks, findNode]);

    /* Load node detail */
    const loadNode = () => {
        const id = nodeInput.trim();
        if (!id) return;
        setNodeId(id);
        const detail = findNode(id);
        if (detail) {
            setNodeDetail(detail);
            setNeighbours(getNeighbours(id));
            setError('');
        } else {
            setError(`Node "${id}" not found in graph`);
            setNodeDetail(null);
        }
    };

    /* API calls */
    const call = async (fn: () => Promise<void>) => {
        setLoading(true); setError('');
        try { await fn(); } catch (e: any) { setError(e.message); } finally { setLoading(false); }
    };

    const loadSimilar = () => call(async () => {
        const r = await api.get(`/api/v5/bridge/similar/${nodeId}`);
        setSimilarNodes(r.data?.recommendations || []);
        setTab('similar');
    });

    const loadIndications = () => call(async () => {
        const r = await api.get(`/api/v5/bridge/indication-expansion/${nodeId}`);
        setIndications(r.data?.expansion_suggestions || []);
        setTab('indication');
    });

    const findPath = () => call(async () => {
        const r = await api.get(`/api/v5/bridge/path/${nodeId}/${pathTarget}`);
        setPathResult(r.data);
        setTab('paths');
    });

    const loadPredictions = () => call(async () => {
        const r = await api.get('/api/v5/bridge/predict-links', { params: { top_n: 20 } });
        setPredictions(r.data?.predictions || []);
        setTab('predictions');
    });

    const runHeatFromNode = () => call(async () => {
        const r = await api.get('/api/v5/bridge/diffusion/heat', { params: { seeds: nodeId, steps: 10, rate: 0.3 } });
        setHeatResult(r.data);
        setTab('diffusion');
    });

    /* Neighbourhood group breakdown */
    const nbGroupBreakdown = useMemo(() => {
        const counts: Record<string, number> = {};
        neighbours.forEach(n => { counts[n.group] = (counts[n.group] || 0) + 1; });
        return counts;
    }, [neighbours]);

    /* Auto-suggestions */
    const suggestions = useMemo(() => {
        if (nodeInput.length < 2) return [];
        const q = nodeInput.toLowerCase();
        return graphNodes.filter((n: any) => n.id.toLowerCase().includes(q) || n.name?.toLowerCase().includes(q)).slice(0, 8);
    }, [nodeInput, graphNodes]);

    /* Tab defs */
    const tabs: { id: DetailTab; label: string; icon: string }[] = [
        { id: 'overview', label: 'Overview', icon: '📋' },
        { id: 'neighbours', label: 'Neighbours', icon: '🔗' },
        { id: 'similar', label: 'Similar', icon: '🧬' },
        { id: 'indication', label: 'Indication Expansion', icon: '🎯' },
        { id: 'paths', label: 'Paths', icon: '🛤️' },
        { id: 'predictions', label: 'Link Prediction', icon: '🔮' },
        { id: 'diffusion', label: 'Diffusion', icon: '🔥' },
    ];

    /* ── Render ────────────────────────────────────────────────────── */
    return (
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24, fontFamily: 'Inter, system-ui, sans-serif' }}>
            <h1 style={{ fontSize: 24, fontWeight: 800, margin: '0 0 4px', background: 'linear-gradient(135deg, #45B7D1, #4ECDC4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Node Explorer
            </h1>
            <p style={{ color: C.muted, fontSize: 13, marginBottom: 20 }}>Deep-dive into any node: neighbours, similarity, indication expansion, paths, and signal diffusion.</p>

            {/* Search bar */}
            <div style={{ ...card, position: 'relative' }}>
                <div style={{ display: 'flex', gap: 8 }}>
                    <input value={nodeInput} onChange={e => setNodeInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && loadNode()}
                        placeholder="Enter node ID (e.g., antigen_CD19, disease_dlbcl)"
                        style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`, borderRadius: 10, padding: '10px 16px', color: '#fff', fontSize: 14, outline: 'none' }}
                    />
                    <Btn onClick={loadNode} label="Load Node" />
                </div>
                {suggestions.length > 0 && !nodeDetail && (
                    <div style={{ position: 'absolute', top: '100%', left: 20, right: 20, background: '#1a1a2e', border: `1px solid ${C.border}`, borderRadius: '0 0 10px 10px', zIndex: 50, maxHeight: 200, overflowY: 'auto' }}>
                        {suggestions.map((s: any, i: number) => (
                            <div key={i} onClick={() => { setNodeInput(s.id); }}
                                style={{ padding: '8px 16px', cursor: 'pointer', fontSize: 12, color: '#ccc', borderBottom: `1px solid ${C.border}` }}
                                onMouseEnter={e => (e.currentTarget.style.background = `${C.a1}11`)}
                                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                                <span style={{ color: '#fff', fontWeight: 600 }}>{s.name}</span>
                                <span style={{ color: C.muted, marginLeft: 8, fontSize: 10 }}>{s.id}</span>
                                <Badge t={s.group} c={GC[s.group] || '#888'} />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {error && <div style={{ background: 'rgba(255,107,107,0.1)', border: '1px solid rgba(255,107,107,0.3)', borderRadius: 10, padding: '10px 16px', marginBottom: 16, color: C.a2, fontSize: 13 }}>⚠️ {error}</div>}

            {nodeDetail && (
                <>
                    {/* Tab bar */}
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 20 }}>
                        {tabs.map(t => (
                            <button key={t.id} onClick={() => {
                                setTab(t.id);
                                if (t.id === 'similar' && similarNodes.length === 0) loadSimilar();
                                if (t.id === 'indication' && indications.length === 0) loadIndications();
                                if (t.id === 'predictions' && predictions.length === 0) loadPredictions();
                            }} style={{
                                background: tab === t.id ? `${C.a1}15` : 'transparent',
                                border: `1px solid ${tab === t.id ? C.a1 : 'rgba(255,255,255,0.1)'}`,
                                borderRadius: 10, padding: '7px 14px', color: tab === t.id ? C.a1 : C.muted,
                                cursor: 'pointer', fontSize: 12, fontWeight: tab === t.id ? 700 : 400, transition: 'all 0.2s',
                            }}>
                                {t.icon} {t.label}
                            </button>
                        ))}
                    </div>

                    {/* OVERVIEW */}
                    {tab === 'overview' && (
                        <>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 12, marginBottom: 16 }}>
                                <Stat l="Group" v={nodeDetail.group} c={GC[nodeDetail.group] || '#888'} />
                                <Stat l="Layer" v={nodeDetail.layer} c={C.a3} />
                                <Stat l="Neighbours" v={neighbours.length} c={C.a1} />
                                {nodeDetail.score !== undefined && <Stat l="Score" v={nodeDetail.score.toFixed(3)} c={C.a4} />}
                                {nodeDetail.confidence !== undefined && <Stat l="Confidence" v={nodeDetail.confidence.toFixed(3)} c={C.a6} />}
                                {nodeDetail.druggability && <Stat l="Druggability" v={nodeDetail.druggability.split(' ')[0]} c={C.a5} />}
                            </div>
                            {(nodeDetail.score !== undefined || nodeDetail.confidence !== undefined) && (
                                <div style={{ ...card, display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap' }}>
                                    {nodeDetail.score !== undefined && <RadialScore score={nodeDetail.score} label="Target Score" color={C.a1} />}
                                    {nodeDetail.confidence !== undefined && <RadialScore score={nodeDetail.confidence} label="Confidence" color={C.a4} />}
                                </div>
                            )}
                            <div style={card}>
                                <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Properties</h4>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 8 }}>
                                    {Object.entries(nodeDetail).filter(([k]) => !['id', 'val'].includes(k)).map(([k, v]) => (
                                        <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: `1px solid ${C.border}`, fontSize: 12 }}>
                                            <span style={{ color: C.muted }}>{k.replace(/_/g, ' ')}</span>
                                            <span style={{ color: '#fff', fontWeight: 500, maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }}>{String(v)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div style={card}>
                                <h4 style={{ color: '#fff', fontSize: 14, margin: '0 0 12px' }}>Neighbour Groups</h4>
                                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                    {Object.entries(nbGroupBreakdown).map(([g, count]) => (
                                        <div key={g} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <span style={{ width: 10, height: 10, borderRadius: '50%', background: GC[g] || '#888' }} />
                                            <span style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{count}</span>
                                            <span style={{ color: C.muted, fontSize: 12 }}>{g}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    {/* NEIGHBOURS */}
                    {tab === 'neighbours' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                            {neighbours.map((nb, i) => (
                                <div key={i} onClick={() => { setNodeInput(nb.id); loadNode(); }}
                                    style={{ ...card, marginBottom: 0, cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', transition: 'border-color 0.2s' }}
                                    onMouseEnter={e => (e.currentTarget.style.borderColor = GC[nb.group] || '#888')}
                                    onMouseLeave={e => (e.currentTarget.style.borderColor = C.border)}>
                                    <div>
                                        <span style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>{nb.name}</span>
                                        <Badge t={nb.group} c={GC[nb.group] || '#888'} />
                                        <span style={{ color: C.muted, fontSize: 11, marginLeft: 8 }}>{nb.relationship}</span>
                                    </div>
                                    <span style={{ color: C.a1, fontFamily: 'monospace', fontSize: 12 }}>w={nb.weight.toFixed(3)}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* SIMILAR */}
                    {tab === 'similar' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {loading && <p style={{ color: C.muted }}>Loading...</p>}
                            {similarNodes.map((s, i) => (
                                <div key={i} style={{ ...card, marginBottom: 0 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <span style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>{s.name}</span>
                                            <Badge t={s.group} c={GC[s.group] || '#888'} />
                                        </div>
                                        <span style={{ color: C.a5, fontFamily: 'monospace', fontSize: 14, fontWeight: 700 }}>{s.signals.ensemble.toFixed(3)}</span>
                                    </div>
                                    <div style={{ display: 'flex', gap: 16, marginTop: 8, fontSize: 11, color: C.muted }}>
                                        <span>Jaccard: <span style={{ color: C.a1 }}>{s.signals.jaccard.toFixed(3)}</span></span>
                                        <span>Attribute: <span style={{ color: C.a4 }}>{s.signals.attribute.toFixed(3)}</span></span>
                                        <span>Cosine: <span style={{ color: C.a3 }}>{s.signals.cosine.toFixed(3)}</span></span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* INDICATION EXPANSION */}
                    {tab === 'indication' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {loading && <p style={{ color: C.muted }}>Analyzing...</p>}
                            {indications.length === 0 && !loading && <p style={{ color: C.muted }}>No expansion suggestions found</p>}
                            {indications.map((ind, i) => (
                                <div key={i} style={{ ...card, marginBottom: 0, borderLeft: `3px solid ${C.a2}` }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                        <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>{ind.disease_name}</span>
                                        <span style={{ color: C.a2, fontFamily: 'monospace', fontWeight: 700 }}>{(ind.repurpose_score * 100).toFixed(1)}%</span>
                                    </div>
                                    <div style={{ fontSize: 11, color: C.muted, marginTop: 6 }}>
                                        Avg similarity: {ind.avg_similarity.toFixed(3)} · {ind.n_similar_antigens} similar antigens in this disease
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* PATHS */}
                    {tab === 'paths' && (
                        <div style={card}>
                            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                <div style={{ padding: '9px 14px', background: `${C.a1}15`, borderRadius: 8, fontSize: 13, color: C.a1, fontWeight: 600 }}>{nodeId}</div>
                                <span style={{ color: C.a4, alignSelf: 'center', fontSize: 18 }}>→</span>
                                <input value={pathTarget} onChange={e => setPathTarget(e.target.value)} placeholder="Target node" style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13, outline: 'none' }} />
                                <Btn onClick={findPath} label="Find Path" color={C.a4} disabled={loading} />
                            </div>
                            {pathResult && (
                                pathResult.found ? (
                                    <div style={{ background: `${C.a4}08`, border: `1px solid ${C.a4}20`, borderRadius: 12, padding: 16 }}>
                                        <div style={{ color: C.a4, fontWeight: 700, marginBottom: 8 }}>{pathResult.hops} hops</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
                                            {pathResult.path?.map((p, i) => (
                                                <React.Fragment key={i}>
                                                    <span style={{ background: `${C.a4}18`, padding: '4px 10px', borderRadius: 6, fontSize: 12, color: C.a4 }}>{p.replace(/^(antigen_|disease_|pathway_|family_|domain_)/, '')}</span>
                                                    {i < (pathResult.path?.length || 0) - 1 && <span style={{ color: '#444' }}>→</span>}
                                                </React.Fragment>
                                            ))}
                                        </div>
                                    </div>
                                ) : <p style={{ color: C.a2 }}>No path found</p>
                            )}
                        </div>
                    )}

                    {/* LINK PREDICTIONS */}
                    {tab === 'predictions' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {loading && <p style={{ color: C.muted }}>Predicting...</p>}
                            {predictions.map((p, i) => (
                                <div key={i} style={{ ...card, marginBottom: 0 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                                            <span style={{ color: C.a3, fontWeight: 600 }}>{p.source_name}</span>
                                            <span style={{ color: '#444' }}>⟷</span>
                                            <span style={{ color: C.a2, fontWeight: 600 }}>{p.target_name}</span>
                                        </div>
                                        <span style={{ color: C.a4, fontFamily: 'monospace', fontWeight: 700 }}>{p.ensemble_score.toFixed(4)}</span>
                                    </div>
                                    <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 10, color: C.muted }}>
                                        <span>CN: {p.common_neighbours}</span>
                                        <span>Jaccard: {p.jaccard.toFixed(3)}</span>
                                        <span>Adamic-Adar: {p.adamic_adar.toFixed(3)}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* DIFFUSION */}
                    {tab === 'diffusion' && (
                        <div style={card}>
                            <h4 style={{ color: C.a2, fontSize: 14, margin: '0 0 8px' }}>🔥 Heat Diffusion from {nodeDetail.name}</h4>
                            <Btn onClick={runHeatFromNode} label="Run Heat Diffusion" color={C.a2} disabled={loading} />
                            {heatResult && (
                                <div style={{ marginTop: 16 }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 10, marginBottom: 16 }}>
                                        <Stat l="Heated Nodes" v={heatResult.top_heated_nodes?.length || 0} c={C.a2} />
                                        <Stat l="Total Heat" v={(heatResult.total_heat || 0).toFixed(3)} c={C.a4} />
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                        {heatResult.top_heated_nodes?.slice(0, 15).map((n: any, i: number) => (
                                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                                                <span style={{ width: 120, color: C.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{n.node.replace(/^(antigen_|disease_|pathway_)/, '')}</span>
                                                <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 4, height: 14, overflow: 'hidden' }}>
                                                    <div style={{ width: `${n.heat * 100}%`, height: '100%', background: `linear-gradient(90deg, ${C.a2}88, ${C.a2})`, borderRadius: 4 }} />
                                                </div>
                                                <span style={{ width: 50, textAlign: 'right', color: C.a2, fontFamily: 'monospace', fontSize: 10 }}>{n.heat.toFixed(4)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
