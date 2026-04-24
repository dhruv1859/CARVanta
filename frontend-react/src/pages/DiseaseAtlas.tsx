import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import api from '../api/client';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Types                                                                 */
/* ═══════════════════════════════════════════════════════════════════════ */

interface DiseaseProfile {
    disease_id: string; name: string; category: string;
    incidence_per_100k: number; prevalence: number;
    median_age: number; five_year_survival: number;
    standard_treatments: string[];
}
interface RegionalData {
    region: string; incidence: number; mortality: number;
    survival_rate: number;
}
interface PrevalenceEntry {
    cancer_type: string; overall_prevalence_pct: number;
    n_studies: number; subtypes: { subtype: string; prevalence_pct: number; confidence: number }[];
}
interface EthnicEntry {
    ethnic_group: string; prevalence_pct: number;
    sample_size: number; data_quality: string;
}
interface CoexpressionPair {
    antigen_1: string; antigen_2: string; coexpression_pct: number;
}
interface AccessGapCountry {
    country: string; readiness_score: number; annual_rr_cases: number;
    treatment_capacity: number; treatment_gap: number; gap_pct: number;
    approved_products: number; composite_access_score: number;
}
interface InfrastructureCountry {
    country: string; gmp_facilities: number; qualified_centres: number;
    hematologists_per_100k: number; icu_beds_per_100k: number;
    readiness_score: number; bottleneck: string;
}
interface JourneyStep {
    step: string; days: number; cumulative_days: number;
    category: string; is_bottleneck: boolean;
}
interface TrendPoint {
    year: number; incidence_per_100k?: number; five_year_survival?: number;
}
interface TreatmentAdoption {
    year: number; [modality: string]: number;
}
interface BurdenData {
    annual_incidence: number; annual_deaths: number;
    years_of_life_lost_yll: number; years_lived_with_disability_yld: number;
    total_dalys: number; economic_burden_usd: number;
}
interface RegulatoryProduct {
    product: string; total_approvals: number;
    approved_countries: { country: string; regulatory_body: string; approval_date: string; indications: string[] }[];
    not_yet_approved: { country: string; regulatory_body: string; expected_review_months: number }[];
}

type AtlasTab = 'diseases' | 'prevalence' | 'coexpression' | 'access' | 'infrastructure' |
    'journey' | 'trends' | 'burden' | 'adoption' | 'regulatory';

/* ═══════════════════════════════════════════════════════════════════════ */
/* Styles                                                                */
/* ═══════════════════════════════════════════════════════════════════════ */

const C = {
    bg: '#0a0a0f', card: 'rgba(255,255,255,0.03)', border: 'rgba(255,255,255,0.08)',
    text: '#e2e8f0', muted: '#64748b',
    a1: '#4ECDC4', a2: '#FF6B6B', a3: '#45B7D1', a4: '#FFEAA7', a5: '#DDA0DD', a6: '#96CEB4',
};
const cardS: React.CSSProperties = { background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, padding: 20, marginBottom: 16 };
const statS = (c: string): React.CSSProperties => ({ background: `${c}0a`, border: `1px solid ${c}25`, borderRadius: 12, padding: '14px 12px', textAlign: 'center' });

const Stat = ({ l, v, sub, c = C.a1 }: { l: string; v: string | number; sub?: string; c?: string }) => (
    <div style={statS(c)}>
        <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 1 }}>{l}</div>
        <div style={{ fontSize: 22, fontWeight: 800, color: c, marginTop: 4, fontFamily: 'monospace' }}>{v}</div>
        {sub && <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>{sub}</div>}
    </div>
);

const Badge = ({ t, c }: { t: string; c: string }) => (
    <span style={{ background: `${c}22`, color: c, padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 600, marginLeft: 4 }}>{t}</span>
);

const Btn = ({ onClick, label, color = C.a1, disabled = false }: { onClick: () => void; label: string; color?: string; disabled?: boolean }) => (
    <button onClick={onClick} disabled={disabled} style={{
        background: `linear-gradient(135deg, ${color}, ${color}cc)`, color: '#000', border: 'none',
        borderRadius: 10, padding: '9px 22px', fontWeight: 700, cursor: disabled ? 'wait' : 'pointer', fontSize: 13, opacity: disabled ? 0.5 : 1,
    }}>{label}</button>
);

const HorizBar = ({ items, color = C.a1 }: { items: { label: string; value: number }[]; color?: string }) => {
    const maxV = Math.max(...items.map(i => i.value), 0.001);
    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {items.map((d, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                    <span style={{ width: 130, color: C.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.label}</span>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 4, height: 16, overflow: 'hidden' }}>
                        <div style={{ width: `${(d.value / maxV) * 100}%`, height: '100%', background: `linear-gradient(90deg, ${color}88, ${color})`, borderRadius: 4, transition: 'width 0.4s' }} />
                    </div>
                    <span style={{ width: 60, textAlign: 'right', color, fontFamily: 'monospace', fontSize: 10 }}>
                        {d.value < 1 ? (d.value * 100).toFixed(1) + '%' : d.value.toFixed(1)}
                    </span>
                </div>
            ))}
        </div>
    );
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Mini Canvas Line Chart                                                */
/* ═══════════════════════════════════════════════════════════════════════ */

const LineChart = ({ data, xKey, yKeys, colors: lineColors, height = 200 }: {
    data: any[]; xKey: string; yKeys: string[]; colors: string[]; height?: number;
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || data.length === 0) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        const W = canvas.width = canvas.parentElement?.clientWidth || 500;
        const H = canvas.height = height * 2;

        ctx.fillStyle = '#0a0a0f';
        ctx.fillRect(0, 0, W, H);

        const maxVal = Math.max(...data.flatMap(d => yKeys.map(k => typeof d[k] === 'number' ? d[k] : 0)), 0.001);
        const minVal = Math.min(...data.flatMap(d => yKeys.map(k => typeof d[k] === 'number' ? d[k] : maxVal)));
        const range = maxVal - minVal || 1;
        const padX = 40, padY = 20;
        const stepX = (W - padX * 2) / Math.max(data.length - 1, 1);

        // Grid
        ctx.strokeStyle = 'rgba(255,255,255,0.04)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = padY + (H - padY * 2) * i / 4;
            ctx.beginPath(); ctx.moveTo(padX, y); ctx.lineTo(W - padX, y); ctx.stroke();
        }

        // Lines
        yKeys.forEach((key, ki) => {
            ctx.beginPath();
            ctx.strokeStyle = lineColors[ki % lineColors.length];
            ctx.lineWidth = 2;
            data.forEach((d, i) => {
                const x = padX + i * stepX;
                const y = padY + (1 - (d[key] - minVal) / range) * (H - padY * 2);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();
        });

        // X labels
        ctx.fillStyle = '#666'; ctx.font = '18px monospace'; ctx.textAlign = 'center';
        const step = Math.ceil(data.length / 8);
        data.forEach((d, i) => { if (i % step === 0) ctx.fillText(String(d[xKey]), padX + i * stepX, H - 4); });

        // Legend
        ctx.font = '18px Inter, sans-serif';
        yKeys.forEach((key, ki) => {
            ctx.fillStyle = lineColors[ki]; ctx.fillRect(padX + ki * 120, 8, 16, 16);
            ctx.fillStyle = '#aaa'; ctx.textAlign = 'left'; ctx.fillText(key, padX + ki * 120 + 22, 22);
        });
    }, [data, xKey, yKeys, lineColors, height]);
    return <canvas ref={canvasRef} style={{ width: '100%', height, borderRadius: 10, border: `1px solid ${C.border}` }} />;
};

/* ═══════════════════════════════════════════════════════════════════════ */
/* Main Component                                                        */
/* ═══════════════════════════════════════════════════════════════════════ */

export default function DiseaseAtlas() {
    const [tab, setTab] = useState<AtlasTab>('diseases');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    /* Data */
    const [diseases, setDiseases] = useState<DiseaseProfile[]>([]);
    const [selectedDisease, setSelectedDisease] = useState('dlbcl');
    const [prevalence, setPrevalence] = useState<{ cancer_specific: PrevalenceEntry[] } | null>(null);
    const [selectedAntigen, setSelectedAntigen] = useState('CD19');
    const [ethnicPrev, setEthnicPrev] = useState<{ ethnic_prevalence: EthnicEntry[] } | null>(null);
    const [coexMatrix, setCoexMatrix] = useState<{ top_pairs: CoexpressionPair[] } | null>(null);
    const [accessGaps, setAccessGaps] = useState<{ countries: AccessGapCountry[] } | null>(null);
    const [infrastructure, setInfrastructure] = useState<{ countries: InfrastructureCountry[] } | null>(null);
    const [journey, setJourney] = useState<{ journey_steps: JourneyStep[] } | null>(null);
    const [journeyCountry, setJourneyCountry] = useState('US');
    const [incTrend, setIncTrend] = useState<any>(null);
    const [survTrend, setSurvTrend] = useState<any>(null);
    const [burden, setBurden] = useState<BurdenData | null>(null);
    const [adoption, setAdoption] = useState<any>(null);
    const [regulatory, setRegulatory] = useState<{ products: RegulatoryProduct[] } | null>(null);

    /* API */
    const call = async (fn: () => Promise<void>) => {
        setLoading(true); setError('');
        try { await fn(); } catch (e: any) { setError(e.message); } finally { setLoading(false); }
    };

    useEffect(() => { call(async () => {
        const r = await api.get('/api/v5/atlas/diseases');
        setDiseases(r.data?.diseases || []);
    }); }, []);

    const loadPrevalence = () => call(async () => {
        const r = await api.get(`/api/v5/atlas/prevalence/${selectedAntigen}`);
        setPrevalence(r.data);
        const e = await api.get(`/api/v5/atlas/prevalence/${selectedAntigen}/ethnicity`, { params: { cancer_type: selectedDisease } });
        setEthnicPrev(e.data);
    });
    const loadCoex = () => call(async () => {
        const r = await api.get('/api/v5/atlas/coexpression', { params: { cancer_type: selectedDisease } });
        setCoexMatrix(r.data);
    });
    const loadAccess = () => call(async () => {
        const r = await api.get(`/api/v5/atlas/access-gaps/${selectedDisease}`);
        setAccessGaps(r.data);
    });
    const loadInfra = () => call(async () => {
        const r = await api.get('/api/v5/atlas/infrastructure');
        setInfrastructure(r.data);
    });
    const loadJourney = () => call(async () => {
        const r = await api.get('/api/v5/atlas/patient-journey', { params: { country: journeyCountry, cancer_type: selectedDisease } });
        setJourney(r.data);
    });
    const loadTrends = () => call(async () => {
        const r = await api.get(`/api/v5/atlas/trends/incidence/${selectedDisease}`);
        setIncTrend(r.data);
        const s = await api.get(`/api/v5/atlas/trends/survival/${selectedDisease}`);
        setSurvTrend(s.data);
    });
    const loadBurden = () => call(async () => {
        const r = await api.get(`/api/v5/atlas/trends/burden/${selectedDisease}`);
        setBurden(r.data);
    });
    const loadAdoption = () => call(async () => {
        const r = await api.get(`/api/v5/atlas/trends/treatment-adoption/${selectedDisease}`);
        setAdoption(r.data);
    });
    const loadRegulatory = () => call(async () => {
        const r = await api.get('/api/v5/atlas/regulatory-map');
        setRegulatory(r.data);
    });

    /* Format helpers */
    const fmt = (n: number) => n >= 1e9 ? `$${(n/1e9).toFixed(1)}B` : n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;

    /* Tab defs */
    const tabs: { id: AtlasTab; label: string; icon: string }[] = [
        { id: 'diseases', label: 'Diseases', icon: '🏥' },
        { id: 'prevalence', label: 'Prevalence', icon: '📊' },
        { id: 'coexpression', label: 'Co-Expression', icon: '🧬' },
        { id: 'access', label: 'Access Gaps', icon: '🌍' },
        { id: 'infrastructure', label: 'Infrastructure', icon: '🏗️' },
        { id: 'journey', label: 'Patient Journey', icon: '🛤️' },
        { id: 'trends', label: 'Trends', icon: '📈' },
        { id: 'burden', label: 'Disease Burden', icon: '⚖️' },
        { id: 'adoption', label: 'Treatment Adoption', icon: '💊' },
        { id: 'regulatory', label: 'Regulatory Map', icon: '🗺️' },
    ];

    /* ── Disease selector ─────────────────────────────────────────── */
    const DiseaseSelector = () => (
        <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
            <select value={selectedDisease} onChange={e => setSelectedDisease(e.target.value)}
                style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13 }}>
                {['dlbcl','all','multiple_myeloma','aml','breast_cancer','lung_cancer','melanoma','ovarian_cancer','pancreatic_cancer','glioblastoma'].map(d => (
                    <option key={d} value={d}>{d.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</option>
                ))}
            </select>
            <select value={selectedAntigen} onChange={e => setSelectedAntigen(e.target.value)}
                style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13 }}>
                {['CD19','CD20','CD22','BCMA','CD38','GPRC5D','HER2','EGFR','GD2','Mesothelin','GPC3','PSMA','EpCAM','MUC1','CD33','CD123'].map(a => (
                    <option key={a} value={a}>{a}</option>
                ))}
            </select>
        </div>
    );

    /* ── Render ────────────────────────────────────────────────────── */
    return (
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24, fontFamily: 'Inter, system-ui, sans-serif' }}>
            <h1 style={{ fontSize: 26, fontWeight: 800, margin: '0 0 4px', background: 'linear-gradient(135deg, #FF6B6B, #FFEAA7, #4ECDC4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                🌐 Disease Atlas
            </h1>
            <p style={{ color: C.muted, fontSize: 13, marginBottom: 20 }}>Global epidemiology, antigen prevalence, treatment access, and regulatory landscape for CAR-T therapies</p>

            {/* Tab bar */}
            <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap', marginBottom: 20, overflowX: 'auto' }}>
                {tabs.map(t => (
                    <button key={t.id} onClick={() => setTab(t.id)} style={{
                        background: tab === t.id ? `${C.a1}15` : 'transparent',
                        border: `1px solid ${tab === t.id ? C.a1 : 'rgba(255,255,255,0.08)'}`,
                        borderRadius: 8, padding: '6px 12px', color: tab === t.id ? C.a1 : C.muted,
                        cursor: 'pointer', fontSize: 11, fontWeight: tab === t.id ? 700 : 400, transition: 'all 0.2s', whiteSpace: 'nowrap',
                    }}>{t.icon} {t.label}</button>
                ))}
            </div>

            {error && <div style={{ background: 'rgba(255,107,107,0.1)', border: '1px solid rgba(255,107,107,0.3)', borderRadius: 10, padding: '10px 16px', marginBottom: 16, color: C.a2, fontSize: 13 }}>⚠️ {error}</div>}

            {/* DISEASES */}
            {tab === 'diseases' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
                    {diseases.length === 0 && <p style={{ color: C.muted }}>Loading diseases...</p>}
                    {diseases.map((d, i) => (
                        <div key={i} onClick={() => setSelectedDisease(d.disease_id)} style={{
                            ...cardS, cursor: 'pointer', borderLeft: `3px solid ${selectedDisease === d.disease_id ? C.a1 : 'transparent'}`,
                            transition: 'all 0.2s',
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <h4 style={{ color: '#fff', fontSize: 14, margin: 0 }}>{d.name}</h4>
                                <Badge t={d.category} c={C.a3} />
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 10, fontSize: 11, color: C.muted }}>
                                <div>Incidence: <span style={{ color: C.a2 }}>{d.incidence_per_100k}/100K</span></div>
                                <div>5yr Surv: <span style={{ color: C.a6 }}>{(d.five_year_survival * 100).toFixed(0)}%</span></div>
                                <div>Median Age: <span style={{ color: '#fff' }}>{d.median_age}</span></div>
                                <div>Prevalence: <span style={{ color: C.a4 }}>{d.prevalence?.toLocaleString()}</span></div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* PREVALENCE */}
            {tab === 'prevalence' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadPrevalence} label="Load Prevalence" disabled={loading} />
                    {prevalence && (
                        <div style={{ marginTop: 16 }}>
                            <h3 style={{ color: C.a3, fontSize: 16, marginBottom: 12 }}>{selectedAntigen} Expression Across Cancers</h3>
                            <HorizBar items={prevalence.cancer_specific.map(c => ({ label: c.cancer_type, value: c.overall_prevalence_pct / 100 }))} color={C.a3} />
                        </div>
                    )}
                    {ethnicPrev && (
                        <div style={{ ...cardS, marginTop: 16 }}>
                            <h4 style={{ color: C.a5, fontSize: 14, margin: '0 0 12px' }}>Ethnic Disparity — {selectedAntigen} in {selectedDisease}</h4>
                            <HorizBar items={ethnicPrev.ethnic_prevalence.map(e => ({ label: e.ethnic_group, value: e.prevalence_pct / 100 }))} color={C.a5} />
                        </div>
                    )}
                </>
            )}

            {/* CO-EXPRESSION */}
            {tab === 'coexpression' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadCoex} label="Load Co-Expression" color={C.a6} disabled={loading} />
                    {coexMatrix && (
                        <div style={{ marginTop: 16 }}>
                            <h3 style={{ color: C.a6, fontSize: 16, marginBottom: 12 }}>Top Co-Expression Pairs</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {coexMatrix.top_pairs.map((p, i) => (
                                    <div key={i} style={{ ...cardS, marginBottom: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                            <Badge t={p.antigen_1} c={C.a3} />
                                            <span style={{ color: '#444' }}>×</span>
                                            <Badge t={p.antigen_2} c={C.a1} />
                                        </div>
                                        <span style={{ color: C.a6, fontFamily: 'monospace', fontWeight: 700 }}>{p.coexpression_pct}%</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* ACCESS GAPS */}
            {tab === 'access' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadAccess} label="Analyze Access Gaps" color={C.a2} disabled={loading} />
                    {accessGaps && (
                        <div style={{ marginTop: 16 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, marginBottom: 16 }}>
                                <Stat l="Countries" v={accessGaps.countries.length} c={C.a3} />
                                <Stat l="Highest Access" v={(accessGaps as any).highest_access} c={C.a6} />
                                <Stat l="Lowest Access" v={(accessGaps as any).lowest_access} c={C.a2} />
                                <Stat l="Total Gap" v={(accessGaps as any).total_global_gap?.toLocaleString()} c={C.a4} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                {accessGaps.countries.map((c, i) => (
                                    <div key={i} style={{ ...cardS, marginBottom: 0, borderLeft: `3px solid ${c.composite_access_score > 60 ? C.a6 : c.composite_access_score > 30 ? C.a4 : C.a2}` }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ color: '#fff', fontWeight: 700, fontSize: 14 }}>{c.country}</span>
                                            <span style={{ color: C.a1, fontFamily: 'monospace', fontWeight: 700 }}>{c.composite_access_score.toFixed(1)}</span>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 8, fontSize: 11, color: C.muted }}>
                                            <div>R/R Cases: <span style={{ color: '#fff' }}>{c.annual_rr_cases.toLocaleString()}</span></div>
                                            <div>Capacity: <span style={{ color: C.a6 }}>{c.treatment_capacity}</span></div>
                                            <div>Gap: <span style={{ color: C.a2 }}>{c.gap_pct}%</span></div>
                                            <div>Products: <span style={{ color: C.a3 }}>{c.approved_products}</span></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* INFRASTRUCTURE */}
            {tab === 'infrastructure' && (
                <>
                    <Btn onClick={loadInfra} label="Load Infrastructure Data" color={C.a4} disabled={loading} />
                    {infrastructure && (
                        <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
                            {infrastructure.countries.map((c, i) => (
                                <div key={i} style={{ ...cardS, marginBottom: 0 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                        <span style={{ color: '#fff', fontSize: 14, fontWeight: 700 }}>{c.country}</span>
                                        <div>
                                            <span style={{ color: C.a1, fontFamily: 'monospace', fontSize: 14 }}>{(c.readiness_score * 100).toFixed(0)}%</span>
                                            <Badge t={c.bottleneck} c={c.bottleneck === 'No critical bottleneck' ? C.a6 : C.a2} />
                                        </div>
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, fontSize: 11, color: C.muted }}>
                                        <div>GMP: <span style={{ color: '#fff' }}>{c.gmp_facilities}</span></div>
                                        <div>Centres: <span style={{ color: '#fff' }}>{c.qualified_centres}</span></div>
                                        <div>Hematologists: <span style={{ color: '#fff' }}>{c.hematologists_per_100k}/100K</span></div>
                                        <div>ICU Beds: <span style={{ color: '#fff' }}>{c.icu_beds_per_100k}/100K</span></div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}

            {/* PATIENT JOURNEY */}
            {tab === 'journey' && (
                <>
                    <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center' }}>
                        <select value={journeyCountry} onChange={e => setJourneyCountry(e.target.value)}
                            style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${C.border}`, borderRadius: 8, padding: '8px 12px', color: '#fff', fontSize: 13 }}>
                            {['US', 'EU', 'UK', 'JP', 'CN', 'IN', 'BR'].map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                        <Btn onClick={loadJourney} label="Map Journey" color={C.a4} disabled={loading} />
                    </div>
                    {journey && (
                        <div style={{ marginTop: 8 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
                                <Stat l="Total Days" v={(journey as any).total_days} c={C.a4} />
                                <Stat l="Total Weeks" v={(journey as any).total_weeks} c={C.a1} />
                                <Stat l="Bottlenecks" v={(journey as any).n_bottlenecks} c={C.a2} />
                            </div>
                            <div style={{ position: 'relative' }}>
                                {journey.journey_steps.map((s, i) => (
                                    <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
                                        <div style={{ width: 24, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                            <div style={{ width: 12, height: 12, borderRadius: '50%', background: s.is_bottleneck ? C.a2 : C.a1, boxShadow: s.is_bottleneck ? `0 0 8px ${C.a2}` : 'none' }} />
                                            {i < journey.journey_steps.length - 1 && <div style={{ width: 2, flex: 1, background: 'rgba(255,255,255,0.1)' }} />}
                                        </div>
                                        <div style={{ flex: 1, ...cardS, marginBottom: 0, padding: '10px 14px', borderLeft: `2px solid ${s.is_bottleneck ? C.a2 : 'transparent'}` }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span style={{ color: '#fff', fontWeight: 600, fontSize: 13 }}>{s.step}</span>
                                                <span style={{ color: s.is_bottleneck ? C.a2 : C.a1, fontFamily: 'monospace', fontSize: 12 }}>{s.days}d</span>
                                            </div>
                                            <div style={{ fontSize: 10, color: C.muted, marginTop: 4 }}>
                                                Day {s.cumulative_days} · {s.category}
                                                {s.is_bottleneck && <Badge t="BOTTLENECK" c={C.a2} />}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* TRENDS */}
            {tab === 'trends' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadTrends} label="Load Trends" color={C.a3} disabled={loading} />
                    {incTrend && (
                        <div style={{ ...cardS, marginTop: 16 }}>
                            <h4 style={{ color: C.a3, fontSize: 14, margin: '0 0 12px' }}>Incidence Trend — {selectedDisease}</h4>
                            <LineChart data={incTrend.historical || []} xKey="year" yKeys={['incidence_per_100k']} colors={[C.a3]} />
                            <div style={{ marginTop: 10, fontSize: 12, color: C.muted }}>
                                Trend: <Badge t={incTrend.trend?.direction || '?'} c={incTrend.trend?.direction === 'increasing' ? C.a2 : C.a6} />
                                <span style={{ marginLeft: 8 }}>R²: {incTrend.trend?.r_squared}</span>
                            </div>
                        </div>
                    )}
                    {survTrend && (
                        <div style={cardS}>
                            <h4 style={{ color: C.a6, fontSize: 14, margin: '0 0 12px' }}>5-Year Survival Trend</h4>
                            <LineChart data={survTrend.historical || []} xKey="year" yKeys={['five_year_survival']} colors={[C.a6]} />
                            <div style={{ marginTop: 10, fontSize: 12, color: C.muted }}>
                                Current: {(survTrend.current_survival * 100).toFixed(1)}% · Improvement: +{(survTrend.total_improvement * 100).toFixed(1)}pp
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* DISEASE BURDEN */}
            {tab === 'burden' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadBurden} label="Calculate Burden" color={C.a2} disabled={loading} />
                    {burden && (
                        <div style={{ marginTop: 16 }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12 }}>
                                <Stat l="Annual Cases" v={burden.annual_incidence.toLocaleString()} c={C.a3} />
                                <Stat l="Annual Deaths" v={burden.annual_deaths.toLocaleString()} c={C.a2} />
                                <Stat l="YLL" v={burden.years_of_life_lost_yll.toLocaleString()} c={C.a4} />
                                <Stat l="YLD" v={burden.years_lived_with_disability_yld.toLocaleString()} c={C.a5} />
                                <Stat l="Total DALYs" v={burden.total_dalys.toLocaleString()} c={C.a1} />
                                <Stat l="Economic Burden" v={fmt(burden.economic_burden_usd)} c={C.a2} />
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* TREATMENT ADOPTION */}
            {tab === 'adoption' && (
                <>
                    <DiseaseSelector />
                    <Btn onClick={loadAdoption} label="Load Adoption Trends" color={C.a6} disabled={loading} />
                    {adoption && (
                        <div style={{ ...cardS, marginTop: 16 }}>
                            <h4 style={{ color: C.a6, fontSize: 14, margin: '0 0 12px' }}>Treatment Modality Adoption Over Time</h4>
                            <LineChart
                                data={adoption.timeline || []}
                                xKey="year"
                                yKeys={adoption.modalities || []}
                                colors={[C.a2, C.a3, C.a4, C.a1, C.a5, C.a6]}
                            />
                            <p style={{ color: C.muted, fontSize: 12, marginTop: 12 }}>{adoption.key_insight}</p>
                        </div>
                    )}
                </>
            )}

            {/* REGULATORY MAP */}
            {tab === 'regulatory' && (
                <>
                    <Btn onClick={loadRegulatory} label="Load Regulatory Map" color={C.a4} disabled={loading} />
                    {regulatory && (
                        <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                            {regulatory.products.map((p, i) => (
                                <div key={i} style={cardS}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                                        <h4 style={{ color: '#fff', fontSize: 14, margin: 0 }}>{p.product.replace(/_/g, ' ')}</h4>
                                        <Badge t={`${p.total_approvals} approvals`} c={C.a6} />
                                    </div>
                                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                                        {p.approved_countries.map((c, j) => (
                                            <div key={j} style={{ background: `${C.a6}10`, border: `1px solid ${C.a6}25`, borderRadius: 8, padding: '6px 10px', fontSize: 11 }}>
                                                <span style={{ color: C.a6, fontWeight: 700 }}>{c.country}</span>
                                                <span style={{ color: C.muted, marginLeft: 4 }}>{c.regulatory_body} · {c.approval_date}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                        {p.not_yet_approved.map((c, j) => (
                                            <div key={j} style={{ background: `${C.a2}08`, border: `1px solid ${C.a2}15`, borderRadius: 8, padding: '6px 10px', fontSize: 11 }}>
                                                <span style={{ color: C.a2 }}>{c.country}</span>
                                                <span style={{ color: C.muted, marginLeft: 4 }}>~{c.expected_review_months}mo</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
