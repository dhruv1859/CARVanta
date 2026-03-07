import { useState } from 'react';
import { fetchDatasetIntel } from '../api/client';
import { StatsCard, Loading, ErrorMsg } from '../components/UIComponents';

export default function DatasetIntel() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleLoad = async () => {
        setLoading(true); setError(''); setData(null);
        try {
            setData(await fetchDatasetIntel());
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to load dataset intelligence');
        } finally { setLoading(false); }
    };

    const tiers = data?.tiers || {};
    const val = tiers.validated || {};
    const pred = tiers.predicted || {};
    const syn = tiers.synthetic || {};
    const inv = data?.investor_framing || {};

    return (
        <>
            <div className="page-header">
                <h2>📊 Dataset Intelligence</h2>
                <p>3-Tier biomarker classification — separating REAL validated targets from AI-generated training data</p>
            </div>

            <div className="card" style={{ textAlign: 'center' }}>
                <button className="btn btn-primary" onClick={handleLoad} disabled={loading}>
                    {loading ? 'Analyzing...' : 'Load Dataset Analysis'}
                </button>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Analyzing dataset composition..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.total_rows?.toLocaleString()} label="Total Rows" />
                        <StatsCard value={data.unique_biomarkers?.toLocaleString()} label="Unique Biomarkers" />
                        <StatsCard value={data.cancer_types} label="Cancer Types" />
                        <StatsCard value={val.unique_antigens || 0} label="Validated Targets" />
                    </div>

                    <div className="card">
                        <div className="card-header">3-Tier Dataset Architecture</div>
                        <div className="tier-layer validated">
                            <div className="tier-layer-info">
                                <div className="tier-layer-title">🟢 Validated Layer</div>
                                <div className="tier-layer-desc">{val.description || 'Real biomarkers backed by clinical databases'}</div>
                            </div>
                            <div className="tier-layer-stat">
                                <strong>{val.unique_antigens || 0}</strong>
                                <small>antigens · {val.rows?.toLocaleString() || 0} rows</small>
                            </div>
                        </div>

                        <div className="tier-layer predicted">
                            <div className="tier-layer-info">
                                <div className="tier-layer-title">🟡 Predicted Layer</div>
                                <div className="tier-layer-desc">{pred.description || 'AI-predicted cross-cancer associations'}</div>
                            </div>
                            <div className="tier-layer-stat">
                                <strong>AI</strong>
                                <small>predicted</small>
                            </div>
                        </div>

                        <div className="tier-layer synthetic">
                            <div className="tier-layer-info">
                                <div className="tier-layer-title">🔴 Synthetic Layer</div>
                                <div className="tier-layer-desc">{syn.description || 'AI-generated training instances'}</div>
                            </div>
                            <div className="tier-layer-stat">
                                <strong>{syn.unique_antigens?.toLocaleString() || 0}</strong>
                                <small>antigens · {syn.rows?.toLocaleString() || 0} rows</small>
                            </div>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">Source Databases</div>
                            {data.source_databases && Object.entries(data.source_databases).map(([db, count]) => (
                                <div key={db} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                                    <span style={{ fontWeight: 600 }}>
                                        {db === 'TCGA' ? '🧬' : db === 'UniProt' ? '🧪' : db === 'Literature' ? '📚' : '🤖'} {db}
                                    </span>
                                    <span style={{ color: '#94A3B8' }}>{count.toLocaleString()} rows</span>
                                </div>
                            ))}
                        </div>

                        <div className="card">
                            <div className="card-header">Evidence Levels</div>
                            {data.evidence_levels && Object.entries(data.evidence_levels).map(([level, count]) => (
                                <div key={level} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                                    <span style={{ fontWeight: 600 }}>
                                        {level === 'clinical' ? '✅' : level === 'preclinical' ? '🔬' : '🤖'} {level}
                                    </span>
                                    <span style={{ color: '#94A3B8' }}>{count.toLocaleString()} rows</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {inv.headline && (
                        <div className="card">
                            <div className="card-header">🚀 {inv.headline}</div>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ color: '#EF4444', marginBottom: 6, fontSize: 13 }}>❌ <strong>Don't say:</strong> "We have 100k biomarkers"</div>
                                <div style={{ color: '#10B981', fontSize: 13 }}>✅ <strong>Instead say:</strong></div>
                            </div>
                            <div className="investor-quote">
                                "We built an AI-augmented biomarker intelligence platform with:"
                            </div>
                            <ul style={{ paddingLeft: 20, fontSize: 13, color: '#94A3B8', lineHeight: 2 }}>
                                {inv.points?.map((p, i) => <li key={i}><strong>{p}</strong></li>)}
                            </ul>

                            {inv.pitch_lines && (
                                <>
                                    <div className="card-header" style={{ marginTop: 16 }}>🎯 Investor Pitch Lines</div>
                                    {inv.pitch_lines.map((pl, i) => (
                                        <div key={i} className="investor-quote">"{pl}"</div>
                                    ))}
                                </>
                            )}

                            <div className="success-msg" style={{ marginTop: 16 }}>
                                👍 That's how you turn a "fake-looking dataset" into a <strong>deep tech advantage</strong>
                            </div>
                        </div>
                    )}
                </>
            )}
        </>
    );
}
