import { useState, useEffect } from 'react';
import { fetchAntigens, fetchMultiTarget } from '../api/client';
import { TierBadge, Loading, ErrorMsg, StatsCard } from '../components/UIComponents';

export default function MultiTarget() {
    const [antigens, setAntigens] = useState([]);
    const [picks, setPicks] = useState(['', '']);
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => { fetchAntigens('', 100).then(setAntigens).catch(() => { }); }, []);

    const updatePick = (i, v) => { const n = [...picks]; n[i] = v; setPicks(n); };
    const addSlot = () => setPicks([...picks, '']);

    const handleAnalyze = async () => {
        const valid = picks.filter(Boolean);
        if (valid.length < 2) return;
        setLoading(true); setError(''); setData(null);
        try {
            setData(await fetchMultiTarget(valid));
        } catch (e) {
            setError(e.response?.data?.detail || 'Multi-target analysis failed');
        } finally { setLoading(false); }
    };

    return (
        <>
            <div className="page-header">
                <h2>🎯 Multi-Target Synergy</h2>
                <p>Evaluate multi-antigen CAR-T combinations using the Antigen Synergy Matrix</p>
            </div>

            <div className="card">
                <div className="card-header">Select Antigens (min 2)</div>
                {picks.map((p, i) => (
                    <div key={i} className="form-group">
                        <label>Target {i + 1}</label>
                        <select className="form-control" value={p} onChange={e => updatePick(i, e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(a => <option key={a} value={a}>{a}</option>)}
                        </select>
                    </div>
                ))}
                <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                    <button className="btn btn-secondary" onClick={addSlot}>+ Add Target</button>
                    <button className="btn btn-primary" onClick={handleAnalyze}
                        disabled={picks.filter(Boolean).length < 2 || loading}>
                        {loading ? 'Analyzing...' : 'Analyze Synergy'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Computing synergy matrix..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.synergy_score?.toFixed(3) || 'N/A'} label="Synergy Score" />
                        <StatsCard value={data.complementarity_score?.toFixed(3) || data.complementarity?.toFixed(3) || '—'} label="Complementarity" />
                        <StatsCard value={data.coverage_score?.toFixed(3) || data.combined_coverage?.toFixed(3) || 'N/A'} label="Coverage" />
                        <StatsCard value={data.escape_risk_reduction?.toFixed(3) || 'N/A'} label="Escape Risk ↓" />
                    </div>

                    {data.individual_scores && (
                        <div className="card">
                            <div className="card-header">Individual Antigen Scores</div>
                            <table className="data-table">
                                <thead><tr><th>Antigen</th><th>CVS</th><th>Confidence</th><th>Tier</th></tr></thead>
                                <tbody>
                                    {Object.entries(data.individual_scores).map(([name, scores]) => (
                                        <tr key={name}>
                                            <td style={{ fontWeight: 600 }}>{name}</td>
                                            <td>{scores.CVS?.toFixed(3)}</td>
                                            <td>{scores.confidence?.toFixed(3)}</td>
                                            <td><TierBadge tier={scores.tier} /></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {data.recommendation && (
                        <div className="success-msg">{data.recommendation}</div>
                    )}
                    {data.ai_insight && (
                        <div className="card">
                            <div className="card-header">AI Insight</div>
                            <p style={{ fontSize: 13, color: '#94A3B8', lineHeight: 1.7 }}>{data.ai_insight}</p>
                        </div>
                    )}
                </>
            )}
        </>
    );
}
