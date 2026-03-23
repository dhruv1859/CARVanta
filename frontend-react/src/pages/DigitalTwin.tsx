import { useState, useEffect } from 'react';
import api from '../api/client';
import '../styles/digital-twin.css';

/* ═══════════════════════════════════════════════════════════════════════════════
   CARVanta – Patient Digital Twin v5
   Full-featured frontend surfacing ALL backend engines:
     1. Immune Simulation (tumor regression, T-cell expansion, IL-6)
     2. CRS Risk Assessment (multi-factor scoring)
     3. Cancer-Specific Profiles (TME, clonal evolution)
     4. PK/PD Engine (compartmental pharmacokinetics)
     5. CAR-T Product Comparison (FDA-approved products)
     6. Biomarker Trajectory Predictions (6 organ systems)
   ═══════════════════════════════════════════════════════════════════════════════ */

const PRESETS = [
    { name: '👶 Pediatric ALL (5yo)', params: { patient_age: 5, cancer_stage: 'II', tumor_burden_mm: 25, antigen_expression: 0.9, prior_car_t: false, cancer_type: 'B-cell ALL' } },
    { name: '🧑 Adult DLBCL (45yo)', params: { patient_age: 45, cancer_stage: 'III', tumor_burden_mm: 60, antigen_expression: 0.75, prior_car_t: false, cancer_type: 'DLBCL' } },
    { name: '👴 Relapsed Myeloma (62yo)', params: { patient_age: 62, cancer_stage: 'IV', tumor_burden_mm: 90, antigen_expression: 0.6, prior_car_t: true, cancer_type: 'Multiple Myeloma', ldh: 450 } },
    { name: '⚠️ Aggressive MCL (58yo)', params: { patient_age: 58, cancer_stage: 'IV', tumor_burden_mm: 120, antigen_expression: 0.8, prior_car_t: false, cancer_type: 'Mantle Cell Lymphoma', ldh: 600 } },
];

type TabKey = 'setup' | 'results' | 'crs' | 'cancer' | 'pkpd' | 'products' | 'biomarkers';

export default function DigitalTwin() {
    // ─── State: Patient Parameters ────────────────────────────────────────
    const [params, setParams] = useState<any>({
        patient_age: 45, patient_weight: 70, cancer_type: 'B-cell Lymphoma',
        cancer_stage: 'III', tumor_burden_mm: 50, t_cell_dose: 1e8,
        antigen_expression: 0.7, prior_car_t: false, lymphodepletion: true,
        alc: null, ldh: null, days: 365,
    });

    // ─── State: Results ───────────────────────────────────────────────────
    const [result, setResult] = useState<any>(null);
    const [crsRisk, setCrsRisk] = useState<any>(null);
    const [cancerProfiles, setCancerProfiles] = useState<any[]>([]);
    const [cancerSim, setCancerSim] = useState<any>(null);
    const [pkResult, setPkResult] = useState<any>(null);
    const [products, setProducts] = useState<any[]>([]);
    const [productOutcome, setProductOutcome] = useState<any>(null);
    const [selectedProduct, setSelectedProduct] = useState('axi-cel');
    const [biomarkers, setBiomarkers] = useState<any>(null);

    // ─── State: UI ────────────────────────────────────────────────────────
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [activeTab, setActiveTab] = useState<TabKey>('setup');

    // ─── Load reference data on mount ─────────────────────────────────────
    useEffect(() => {
        loadReferenceData();
    }, []);

    const loadReferenceData = async () => {
        try {
            const [profilesRes, productsRes] = await Promise.allSettled([
                api.get('/api/v5/twin/cancer-profiles'),
                api.get('/api/v5/twin/products'),
            ]);
            if (profilesRes.status === 'fulfilled') {
                const data = profilesRes.value.data;
                setCancerProfiles(Array.isArray(data) ? data : data?.profiles || []);
            }
            if (productsRes.status === 'fulfilled') {
                const data = productsRes.value.data;
                setProducts(Array.isArray(data) ? data : data?.products || []);
            }
        } catch (e) { console.error(e); }
    };

    // ─── Run Full Simulation ──────────────────────────────────────────────
    const runSimulation = async () => {
        setLoading(true); setError('');
        try {
            const [simRes, crsRes] = await Promise.all([
                api.post('/api/v5/twin/simulate', params),
                api.post('/api/v5/twin/crs-risk', {
                    tumor_burden: params.tumor_burden_mm,
                    cancer_stage: params.cancer_stage,
                    ldh: params.ldh, prior_car_t: params.prior_car_t,
                    patient_age: params.patient_age,
                }),
            ]);
            setResult(simRes.data);
            setCrsRisk(crsRes.data);
            setActiveTab('results');
        } catch (e: any) { setError(e.message || 'Simulation failed'); }
        finally { setLoading(false); }
    };

    // ─── Run Cancer-Specific Simulation ───────────────────────────────────
    const runCancerSim = async () => {
        setLoading(true); setError('');
        try {
            const res = await api.post('/api/v5/twin/simulate-cancer', {
                cancer_type: params.cancer_type,
                days: params.days,
                tumor_burden_mm: params.tumor_burden_mm,
                patient_age: params.patient_age,
                prior_lines: 2,
                ecog_status: 1,
            });
            setCancerSim(res.data);
            setActiveTab('cancer');
        } catch (e: any) { setError(e.message || 'Cancer sim failed'); }
        finally { setLoading(false); }
    };

    // ─── Run PK/PD Simulation ─────────────────────────────────────────────
    const runPKSimulation = async () => {
        setLoading(true); setError('');
        try {
            const res = await api.post('/api/v5/twin/pk-simulation', {
                days: 60,
                infusion_dose: params.t_cell_dose,
                patient_weight: params.patient_weight,
                tumor_burden_ml: params.tumor_burden_mm,
                cancer_category: 'hematologic',
                lymphodepletion: params.lymphodepletion,
            });
            setPkResult(res.data);
            setActiveTab('pkpd');
        } catch (e: any) { setError(e.message || 'PK simulation failed'); }
        finally { setLoading(false); }
    };

    // ─── Run Product Outcome Prediction ───────────────────────────────────
    const runProductPrediction = async (productKey: string) => {
        setLoading(true); setError('');
        setSelectedProduct(productKey);
        try {
            const res = await api.post('/api/v5/twin/predict-product-outcome', {
                product_key: productKey,
                patient_age: params.patient_age,
                cancer_stage: params.cancer_stage,
                tumor_burden_mm: params.tumor_burden_mm,
                prior_lines: 3,
                ecog: 1,
                ldh: params.ldh,
            });
            setProductOutcome(res.data);
            setActiveTab('products');
        } catch (e: any) { setError(e.message || 'Product prediction failed'); }
        finally { setLoading(false); }
    };

    // ─── Run Biomarker Prediction ─────────────────────────────────────────
    const runBiomarkerPrediction = async () => {
        setLoading(true); setError('');
        try {
            const res = await api.post('/api/v5/twin/biomarkers', {
                days: 90,
                cancer_type: params.cancer_type,
                car_t_target: 'CD19',
                crs_severity: 0.5,
                patient_age: params.patient_age,
            });
            setBiomarkers(res.data);
            setActiveTab('biomarkers');
        } catch (e: any) { setError(e.message || 'Biomarker prediction failed'); }
        finally { setLoading(false); }
    };

    const applyPreset = (preset: any) => setParams((p: any) => ({ ...p, ...preset.params }));
    const upd = (field: string, val: any) => setParams((p: any) => ({ ...p, [field]: val }));

    const s = result?.summary;
    const t = result?.timeline;

    // ─── Chart Renderer ───────────────────────────────────────────────────
    const renderChart = (data: number[], color: string, label: string, maxVal?: number) => {
        if (!data || data.length === 0) return null;
        const max = maxVal || Math.max(...data, 1);
        const w = 600, h = 130;
        const points = data.map((v: number, i: number) =>
            `${(i / (data.length - 1)) * w},${h - (v / max) * h}`
        ).join(' ');
        return (
            <div className="twin-chart">
                <div className="twin-chart-label">{label}</div>
                <svg viewBox={`0 0 ${w} ${h}`} className="twin-svg">
                    <defs>
                        <linearGradient id={`grad-${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={color} stopOpacity="0.35"/>
                            <stop offset="100%" stopColor={color} stopOpacity="0"/>
                        </linearGradient>
                    </defs>
                    <polygon
                        points={`0,${h} ${points} ${w},${h}`}
                        fill={`url(#grad-${color.replace('#','')})`}
                    />
                    <polyline points={points} fill="none" stroke={color} strokeWidth="2.5"/>
                </svg>
                <div className="twin-chart-range">
                    <span>Day 0</span>
                    <span>Day {data.length * Math.floor(params.days / data.length)}</span>
                </div>
            </div>
        );
    };

    // ─── Multi-line Chart ─────────────────────────────────────────────────
    const renderMultiChart = (datasets: { data: number[], color: string, label: string }[], title: string) => {
        const w = 600, h = 140;
        const allVals = datasets.flatMap(d => d.data);
        const max = Math.max(...allVals, 1);

        return (
            <div className="twin-chart">
                <div className="twin-chart-label">{title}</div>
                <svg viewBox={`0 0 ${w} ${h}`} className="twin-svg">
                    {datasets.map((ds, idx) => {
                        if (!ds.data || ds.data.length === 0) return null;
                        const pts = ds.data.map((v, i) =>
                            `${(i / (ds.data.length - 1)) * w},${h - (v / max) * h}`
                        ).join(' ');
                        return (
                            <polyline key={idx} points={pts} fill="none" stroke={ds.color} strokeWidth="2" strokeDasharray={idx > 0 ? "4 2" : "none"}/>
                        );
                    })}
                </svg>
                <div className="twin-chart-legend">
                    {datasets.map((ds, i) => (
                        <span key={i} className="legend-item">
                            <span className="legend-swatch" style={{ background: ds.color }} />
                            {ds.label}
                        </span>
                    ))}
                </div>
            </div>
        );
    };

    const responseColor: any = { CR: '#10b981', PR: '#6366f1', SD: '#f59e0b', PD: '#ef4444' };
    const crsColor: any = { 0: '#10b981', 1: '#6366f1', 2: '#f59e0b', 3: '#f97316', 4: '#ef4444' };

    // ─── Tab Configuration ────────────────────────────────────────────────
    const tabs: { key: TabKey; icon: string; label: string; disabled?: boolean }[] = [
        { key: 'setup', icon: '🩺', label: 'Patient Setup' },
        { key: 'results', icon: '📊', label: 'Simulation', disabled: !result },
        { key: 'crs', icon: '⚠️', label: 'CRS Risk', disabled: !crsRisk },
        { key: 'cancer', icon: '🧬', label: 'Cancer Profiles' },
        { key: 'pkpd', icon: '💊', label: 'PK/PD' },
        { key: 'products', icon: '🏥', label: 'CAR-T Products' },
        { key: 'biomarkers', icon: '🔬', label: 'Biomarkers' },
    ];

    return (
        <div className="twin-page">
            <div className="twin-header">
                <h1>🧑‍⚕️ Patient Digital Twin</h1>
                <p className="page-subtitle">Simulate CAR-T treatment outcomes with 6 prediction engines</p>
            </div>

            {/* ─── Tab Bar ──────────────────────────────────────────────── */}
            <div className="twin-tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        className={activeTab === tab.key ? 'active' : ''}
                        onClick={() => setActiveTab(tab.key)}
                        disabled={tab.disabled}
                    >
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            {error && <div className="twin-error">{error}</div>}

            {/* ═══ TAB 1: Patient Setup ═══════════════════════════════════ */}
            {activeTab === 'setup' && (
                <div className="twin-setup">
                    <div className="card">
                        <h3>Quick Start — Patient Presets</h3>
                        <div className="twin-presets">
                            {PRESETS.map(p => (
                                <button key={p.name} className="twin-preset-btn" onClick={() => applyPreset(p)}>{p.name}</button>
                            ))}
                        </div>
                    </div>

                    <div className="twin-form-grid">
                        <div className="card">
                            <h3>👤 Demographics</h3>
                            <div className="twin-fields">
                                <label>Age <input type="number" value={params.patient_age} onChange={e => upd('patient_age', +e.target.value)} /></label>
                                <label>Weight (kg) <input type="number" value={params.patient_weight} onChange={e => upd('patient_weight', +e.target.value)} /></label>
                                <label>Cancer Type <input type="text" value={params.cancer_type} onChange={e => upd('cancer_type', e.target.value)} /></label>
                                <label>Stage
                                    <select value={params.cancer_stage} onChange={e => upd('cancer_stage', e.target.value)}>
                                        <option value="I">Stage I</option>
                                        <option value="II">Stage II</option>
                                        <option value="III">Stage III</option>
                                        <option value="IV">Stage IV</option>
                                    </select>
                                </label>
                            </div>
                        </div>
                        <div className="card">
                            <h3>🎯 Tumor & Target</h3>
                            <div className="twin-fields">
                                <label>Tumor Burden (mm) <input type="number" value={params.tumor_burden_mm} onChange={e => upd('tumor_burden_mm', +e.target.value)} /></label>
                                <label>Antigen Expression
                                    <input type="range" min="0.1" max="1.0" step="0.05" value={params.antigen_expression} onChange={e => upd('antigen_expression', +e.target.value)} />
                                    <span className="range-val">{(params.antigen_expression * 100).toFixed(0)}%</span>
                                </label>
                                <label>T-Cell Dose
                                    <select value={params.t_cell_dose} onChange={e => upd('t_cell_dose', +e.target.value)}>
                                        <option value={5e7}>5×10⁷ (Low)</option>
                                        <option value={1e8}>1×10⁸ (Standard)</option>
                                        <option value={2e8}>2×10⁸ (High)</option>
                                        <option value={5e8}>5×10⁸ (Max)</option>
                                    </select>
                                </label>
                                <label className="twin-check">
                                    <input type="checkbox" checked={params.prior_car_t} onChange={e => upd('prior_car_t', e.target.checked)} />
                                    Prior CAR-T therapy
                                </label>
                                <label className="twin-check">
                                    <input type="checkbox" checked={params.lymphodepletion} onChange={e => upd('lymphodepletion', e.target.checked)} />
                                    Lymphodepletion
                                </label>
                            </div>
                        </div>
                        <div className="card">
                            <h3>🧪 Lab Values (Optional)</h3>
                            <div className="twin-fields">
                                <label>ALC (×10⁹/L) <input type="number" step="0.1" placeholder="e.g. 1.2" onChange={e => upd('alc', e.target.value ? +e.target.value : null)} /></label>
                                <label>LDH (U/L) <input type="number" placeholder="e.g. 250" onChange={e => upd('ldh', e.target.value ? +e.target.value : null)} /></label>
                                <label>Simulation Days
                                    <select value={params.days} onChange={e => upd('days', +e.target.value)}>
                                        <option value={90}>90 days</option>
                                        <option value={180}>180 days</option>
                                        <option value={365}>365 days (1 yr)</option>
                                        <option value={730}>730 days (2 yr)</option>
                                    </select>
                                </label>
                            </div>
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="twin-action-bar">
                        <button className="twin-run-btn primary" onClick={runSimulation} disabled={loading}>
                            {loading ? '⏳ Running...' : '🧬 Run Full Simulation'}
                        </button>
                        <button className="twin-run-btn secondary" onClick={runCancerSim} disabled={loading}>
                            🧫 Cancer-Specific Sim
                        </button>
                        <button className="twin-run-btn secondary" onClick={runPKSimulation} disabled={loading}>
                            💊 PK/PD Analysis
                        </button>
                        <button className="twin-run-btn secondary" onClick={runBiomarkerPrediction} disabled={loading}>
                            🔬 Biomarker Forecast
                        </button>
                    </div>
                </div>
            )}

            {/* ═══ TAB 2: Simulation Results ══════════════════════════════ */}
            {activeTab === 'results' && result && s && t && (
                <div className="twin-results">
                    <div className="twin-summary-grid">
                        <div className="twin-summary-card">
                            <div className="twin-summary-value" style={{ color: responseColor[s.best_response] || '#e2e8f0' }}>{s.best_response}</div>
                            <div className="twin-summary-label">Best Response</div>
                        </div>
                        <div className="twin-summary-card">
                            <div className="twin-summary-value">{s.tumor_reduction_pct}%</div>
                            <div className="twin-summary-label">Tumor Reduction</div>
                        </div>
                        <div className="twin-summary-card">
                            <div className="twin-summary-value" style={{ color: crsColor[s.max_crs_grade] }}>{s.max_crs_grade}</div>
                            <div className="twin-summary-label">Max CRS Grade</div>
                        </div>
                        <div className="twin-summary-card">
                            <div className="twin-summary-value">{s.progression_free_survival_days}d</div>
                            <div className="twin-summary-label">PFS</div>
                        </div>
                        <div className="twin-summary-card">
                            <div className="twin-summary-value">{s.duration_of_response_days}d</div>
                            <div className="twin-summary-label">Duration of Response</div>
                        </div>
                        <div className="twin-summary-card">
                            <div className="twin-summary-value">{(s.peak_t_cells / 1e9).toFixed(1)}B</div>
                            <div className="twin-summary-label">Peak T-cells (Day {s.peak_t_cell_day})</div>
                        </div>
                    </div>

                    <div className="card">
                        <h3>📈 Tumor Regression Timeline</h3>
                        {renderChart(t.tumor_mm, '#ef4444', `Tumor Size (mm) — Nadir: ${s.nadir_tumor_mm}mm on Day ${s.nadir_tumor_day}`)}
                    </div>
                    <div className="card">
                        <h3>🧬 CAR-T Cell Expansion</h3>
                        {renderChart(t.t_cells, '#6366f1', `T-Cell Count — Peak: ${(s.peak_t_cells / 1e9).toFixed(1)}B on Day ${s.peak_t_cell_day}`)}
                    </div>
                    <div className="card">
                        <h3>🧪 IL-6 Cytokine Levels</h3>
                        {renderChart(t.il6, '#f59e0b', 'IL-6 (pg/mL) — CRS Biomarker')}
                    </div>
                    {t.crs_grade && (
                        <div className="card">
                            <h3>⚠️ CRS Grade Over Time</h3>
                            {renderChart(t.crs_grade, '#f97316', 'CRS Grade (0-4)', 4)}
                        </div>
                    )}
                </div>
            )}

            {/* ═══ TAB 3: CRS Risk Assessment ════════════════════════════ */}
            {activeTab === 'crs' && crsRisk && (
                <div className="twin-crs">
                    <div className="card" style={{ textAlign: 'center' }}>
                        <h3>⚠️ Cytokine Release Syndrome Risk Assessment</h3>
                        <div className="crs-gauge">
                            <div className="crs-gauge-fill" style={{
                                width: `${crsRisk.risk_score}%`,
                                background: crsRisk.risk_level === 'high' ? '#ef4444' : crsRisk.risk_level === 'moderate' ? '#f59e0b' : '#10b981'
                            }} />
                        </div>
                        <div className="crs-score">{crsRisk.risk_score}/100</div>
                        <div className="crs-severity" style={{
                            color: crsRisk.risk_level === 'high' ? '#ef4444' : crsRisk.risk_level === 'moderate' ? '#f59e0b' : '#10b981'
                        }}>
                            Grade {crsRisk.predicted_max_crs_grade} — {crsRisk.severity}
                        </div>
                        <div className="crs-management">{crsRisk.management_recommendation}</div>
                    </div>
                    <div className="card">
                        <h3>🔍 Risk Factor Breakdown</h3>
                        <div className="crs-factors">
                            {crsRisk.risk_factors?.map((f: any, i: number) => (
                                <div key={i} className={`crs-factor crs-${f.impact}`}>
                                    <span className="crs-factor-name">{f.factor}</span>
                                    <span className="crs-factor-pts">{f.points > 0 ? '+' : ''}{f.points} pts</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    {crsRisk.interventions && (
                        <div className="card">
                            <h3>💉 Recommended Interventions</h3>
                            <div className="interventions-list">
                                {crsRisk.interventions.map((int: any, i: number) => (
                                    <div key={i} className="intervention-item">
                                        <span className="intervention-name">{int.name || int}</span>
                                        {int.timing && <span className="intervention-timing">{int.timing}</span>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ═══ TAB 4: Cancer-Specific Profiles ═══════════════════════ */}
            {activeTab === 'cancer' && (
                <div className="twin-cancer">
                    {/* Available Cancer Profiles */}
                    {cancerProfiles.length > 0 && !cancerSim && (
                        <div className="card">
                            <h3>🧫 Available Cancer Profiles</h3>
                            <p className="card-desc">Each profile includes tumor microenvironment modeling, CAR-T targets, and historical response data.</p>
                            <div className="cancer-profiles-grid">
                                {cancerProfiles.map((prof: any, i: number) => (
                                    <div key={i} className="cancer-profile-card" onClick={() => {
                                        upd('cancer_type', prof.cancer_type || prof.name);
                                        runCancerSim();
                                    }}>
                                        <h4>{prof.name || prof.cancer_type}</h4>
                                        {prof.typical_response_rate && (
                                            <div className="profile-stat">
                                                <span>Response Rate</span>
                                                <span className="stat-val">{prof.typical_response_rate}%</span>
                                            </div>
                                        )}
                                        {prof.primary_target && (
                                            <div className="profile-stat">
                                                <span>Primary Target</span>
                                                <span className="stat-val">{prof.primary_target}</span>
                                            </div>
                                        )}
                                        {prof.median_pfs_months && (
                                            <div className="profile-stat">
                                                <span>Median PFS</span>
                                                <span className="stat-val">{prof.median_pfs_months} mo</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Cancer Simulation Result */}
                    {cancerSim && (
                        <>
                            <button className="twin-back-btn" onClick={() => setCancerSim(null)}>← Back to Profiles</button>
                            <div className="card">
                                <h3>🧬 Cancer-Specific Simulation: {cancerSim.cancer_type || params.cancer_type}</h3>
                                {cancerSim.summary && (
                                    <div className="twin-summary-grid">
                                        {Object.entries(cancerSim.summary).slice(0, 6).map(([key, val]: any) => (
                                            <div key={key} className="twin-summary-card">
                                                <div className="twin-summary-value">{typeof val === 'number' ? val.toFixed?.(1) || val : String(val)}</div>
                                                <div className="twin-summary-label">{key.replace(/_/g, ' ')}</div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            {cancerSim.timeline && (
                                <div className="card">
                                    <h3>📈 Tumor Dynamics</h3>
                                    {cancerSim.timeline.tumor_mm && renderChart(cancerSim.timeline.tumor_mm, '#ef4444', 'Tumor Size')}
                                    {cancerSim.timeline.t_cells && renderChart(cancerSim.timeline.t_cells, '#6366f1', 'CAR-T Cells')}
                                </div>
                            )}
                            {cancerSim.tme && (
                                <div className="card">
                                    <h3>🧫 Tumor Microenvironment</h3>
                                    <div className="tme-grid">
                                        {Object.entries(cancerSim.tme).map(([key, val]: any) => (
                                            <div key={key} className="tme-item">
                                                <span className="tme-label">{key.replace(/_/g, ' ')}</span>
                                                <span className="tme-value">{typeof val === 'number' ? val.toFixed(2) : String(val)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    )}

                    {cancerProfiles.length === 0 && !cancerSim && (
                        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                            <p>Run a cancer-specific simulation from the Setup tab to see results here.</p>
                            <button className="twin-run-btn secondary" onClick={runCancerSim}>🧫 Run Cancer Sim</button>
                        </div>
                    )}
                </div>
            )}

            {/* ═══ TAB 5: PK/PD Analysis ══════════════════════════════════ */}
            {activeTab === 'pkpd' && (
                <div className="twin-pkpd">
                    {!pkResult ? (
                        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                            <h3>💊 Pharmacokinetic / Pharmacodynamic Analysis</h3>
                            <p>Model CAR-T cell distribution across body compartments, cytokine kinetics, and drug interactions.</p>
                            <button className="twin-run-btn primary" onClick={runPKSimulation} disabled={loading}>
                                {loading ? '⏳ Running...' : '💊 Run PK/PD Simulation'}
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* PK Summary */}
                            {pkResult.summary && (
                                <div className="twin-summary-grid">
                                    {Object.entries(pkResult.summary).slice(0, 8).map(([key, val]: any) => (
                                        <div key={key} className="twin-summary-card">
                                            <div className="twin-summary-value">
                                                {typeof val === 'number' ? (val > 1e6 ? `${(val / 1e9).toFixed(1)}B` : val.toFixed(1)) : String(val)}
                                            </div>
                                            <div className="twin-summary-label">{key.replace(/_/g, ' ')}</div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Compartmental Charts */}
                            {pkResult.compartments && (
                                <div className="card">
                                    <h3>🫀 Compartmental Distribution</h3>
                                    {renderMultiChart(
                                        Object.entries(pkResult.compartments)
                                            .filter(([_, v]: any) => Array.isArray(v))
                                            .slice(0, 4)
                                            .map(([name, data]: any, i: number) => ({
                                                data, label: name.replace(/_/g, ' '),
                                                color: ['#6366f1', '#ef4444', '#10b981', '#f59e0b'][i % 4],
                                            })),
                                        'CAR-T Cells by Compartment'
                                    )}
                                </div>
                            )}

                            {/* Timeline */}
                            {pkResult.timeline && (
                                <div className="card">
                                    <h3>📈 PK Timeline</h3>
                                    {pkResult.timeline.blood && renderChart(pkResult.timeline.blood, '#ef4444', 'Blood Concentration')}
                                    {pkResult.timeline.tumor && renderChart(pkResult.timeline.tumor, '#6366f1', 'Tumor Infiltration')}
                                </div>
                            )}

                            <button className="twin-run-btn secondary" onClick={runPKSimulation} disabled={loading}>
                                ↻ Re-run PK/PD
                            </button>
                        </>
                    )}
                </div>
            )}

            {/* ═══ TAB 6: CAR-T Products ══════════════════════════════════ */}
            {activeTab === 'products' && (
                <div className="twin-products">
                    <div className="card">
                        <h3>🏥 FDA-Approved CAR-T Products</h3>
                        <p className="card-desc">Click a product to predict personalized outcomes for this patient.</p>
                        <div className="products-grid">
                            {products.map((prod: any, i: number) => (
                                <div
                                    key={i}
                                    className={`product-card ${selectedProduct === (prod.key || prod.product_key) ? 'selected' : ''}`}
                                    onClick={() => runProductPrediction(prod.key || prod.product_key)}
                                >
                                    <h4>{prod.name || prod.product_name}</h4>
                                    <div className="product-meta">
                                        {prod.manufacturer && <span>{prod.manufacturer}</span>}
                                        {prod.target && <span>Target: {prod.target}</span>}
                                        {prod.indications && <span>{prod.indications}</span>}
                                    </div>
                                    {prod.approval_year && <span className="product-year">FDA {prod.approval_year}</span>}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Product Outcome */}
                    {productOutcome && (
                        <div className="card">
                            <h3>📊 Predicted Outcome: {productOutcome.product_name || selectedProduct}</h3>
                            {productOutcome.prediction && (
                                <div className="twin-summary-grid">
                                    {Object.entries(productOutcome.prediction).slice(0, 8).map(([key, val]: any) => (
                                        <div key={key} className="twin-summary-card">
                                            <div className="twin-summary-value">
                                                {typeof val === 'number' ? val.toFixed(1) : String(val)}
                                            </div>
                                            <div className="twin-summary-label">{key.replace(/_/g, ' ')}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {productOutcome.clinical_context && (
                                <div className="clinical-context">
                                    <h4>📚 Clinical Context</h4>
                                    <p>{productOutcome.clinical_context}</p>
                                </div>
                            )}
                            {productOutcome.risk_factors && (
                                <div className="product-risks">
                                    <h4>⚠️ Risk Factors for This Patient</h4>
                                    {productOutcome.risk_factors.map((rf: any, i: number) => (
                                        <div key={i} className="risk-item">
                                            <span>{rf.factor || rf}</span>
                                            {rf.impact && <span className={`risk-impact ${rf.impact}`}>{rf.impact}</span>}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {products.length === 0 && (
                        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                            <p>Loading CAR-T product database...</p>
                        </div>
                    )}
                </div>
            )}

            {/* ═══ TAB 7: Biomarker Predictions ══════════════════════════ */}
            {activeTab === 'biomarkers' && (
                <div className="twin-biomarkers">
                    {!biomarkers ? (
                        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                            <h3>🔬 Biomarker Trajectory Predictions</h3>
                            <p>Predict post-infusion biomarker changes across 6 organ systems: CBC, immune, hepatic, renal, cardiac, inflammatory.</p>
                            <button className="twin-run-btn primary" onClick={runBiomarkerPrediction} disabled={loading}>
                                {loading ? '⏳ Running...' : '🔬 Generate Biomarker Report'}
                            </button>
                        </div>
                    ) : (
                        <>
                            {/* Biomarker system cards */}
                            {biomarkers.systems && Object.entries(biomarkers.systems).map(([system, data]: any) => (
                                <div key={system} className="card">
                                    <h3>{systemIcon(system)} {system.replace(/_/g, ' ')} Panel</h3>
                                    {data.markers && (
                                        <div className="biomarker-grid">
                                            {Object.entries(data.markers).map(([marker, vals]: any) => (
                                                <div key={marker} className="biomarker-item">
                                                    <div className="biomarker-name">{marker.replace(/_/g, ' ')}</div>
                                                    {Array.isArray(vals) && renderChart(vals, systemColor(system), marker.replace(/_/g, ' '))}
                                                    {typeof vals === 'object' && !Array.isArray(vals) && vals.trajectory && renderChart(vals.trajectory, systemColor(system), marker.replace(/_/g, ' '))}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    {!data.markers && data.trajectory && renderChart(data.trajectory, systemColor(system), system)}
                                </div>
                            ))}

                            {/* Flat biomarker data */}
                            {!biomarkers.systems && Object.entries(biomarkers).filter(([k]) => k !== 'metadata' && k !== 'patient').map(([key, val]: any) => (
                                <div key={key} className="card">
                                    <h3>{systemIcon(key)} {key.replace(/_/g, ' ')}</h3>
                                    {typeof val === 'object' && Object.entries(val).map(([sub, subVal]: any) => (
                                        <div key={sub} className="biomarker-item">
                                            <div className="biomarker-name">{sub.replace(/_/g, ' ')}</div>
                                            {Array.isArray(subVal) && renderChart(subVal, systemColor(key), sub.replace(/_/g, ' '))}
                                        </div>
                                    ))}
                                </div>
                            ))}

                            <button className="twin-run-btn secondary" onClick={runBiomarkerPrediction} disabled={loading}>
                                ↻ Re-run Biomarker Prediction
                            </button>
                        </>
                    )}
                </div>
            )}
        </div>
    );
}

// ─── Helper Functions ─────────────────────────────────────────────────────────

function systemIcon(system: string): string {
    const icons: Record<string, string> = {
        cbc: '🩸', hematologic: '🩸', immune: '🛡️', immune_recovery: '🛡️',
        hepatic: '🫁', liver: '🫁', renal: '🫘', kidney: '🫘',
        cardiac: '🫀', heart: '🫀', inflammatory: '🔥', cytokine: '🔥',
        coagulation: '💉', metabolic: '⚡',
    };
    const key = system.toLowerCase();
    for (const [k, v] of Object.entries(icons)) {
        if (key.includes(k)) return v;
    }
    return '📊';
}

function systemColor(system: string): string {
    const colors: Record<string, string> = {
        cbc: '#ef4444', hematologic: '#ef4444', immune: '#6366f1', immune_recovery: '#6366f1',
        hepatic: '#f59e0b', liver: '#f59e0b', renal: '#10b981', kidney: '#10b981',
        cardiac: '#f97316', heart: '#f97316', inflammatory: '#e11d48', cytokine: '#e11d48',
    };
    const key = system.toLowerCase();
    for (const [k, v] of Object.entries(colors)) {
        if (key.includes(k)) return v;
    }
    return '#6366f1';
}
