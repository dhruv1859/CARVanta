import { useState, useEffect } from 'react';
import { fetchAntigens, fetchCancerTypes, fetchStratification } from '../api/client';
import { Loading, ErrorMsg, StatsCard, TierBadge } from '../components/UIComponents';

export default function Stratification() {
    const [antigens, setAntigens] = useState([]);
    const [cancerTypes, setCancerTypes] = useState([]);
    const [antigen, setAntigen] = useState('');
    const [cancer, setCancer] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAntigens('', 50).then(setAntigens).catch(() => { });
        fetchCancerTypes().then(d => setCancerTypes(Array.isArray(d) ? d : [])).catch(() => { });
    }, []);

    const handleStratify = async () => {
        if (!antigen) return;
        setLoading(true); setError(''); setData(null);
        try {
            const res = await fetchStratification(antigen, cancer || null);
            setData(res);
        } catch (e) {
            setError(e.response?.data?.detail || e.message || 'Stratification failed');
        } finally { setLoading(false); }
    };

    const subtypes = (data && Array.isArray(data.subtype_analysis)) ? data.subtype_analysis : [];
    const subgroups = (data && Array.isArray(data.subgroups)) ? data.subgroups : [];

    const safePercent = (val) => {
        if (val == null) return 'N/A';
        const n = Number(val);
        return isNaN(n) ? String(val) : `${Math.round(n * 100)}%`;
    };

    return (
        <>
            <div className="page-header">
                <h2>👥 Patient Stratification</h2>
                <p>Identify patient subgroups using the Biomarker Stratification Engine</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group">
                        <label>Antigen</label>
                        <select className="form-control" value={antigen} onChange={e => setAntigen(e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(a => <option key={a} value={a}>{a}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Cancer Type (optional)</label>
                        <select className="form-control" value={cancer} onChange={e => setCancer(e.target.value)}>
                            <option value="">All Types</option>
                            {cancerTypes.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleStratify} disabled={!antigen || loading}>
                        {loading ? 'Stratifying...' : 'Run Stratification'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Identifying patient subgroups..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.antigen || antigen} label="Antigen" />
                        <StatsCard value={data.cancer_type || 'All'} label="Cancer Type" />
                        <StatsCard value={data.cvs != null ? Number(data.cvs).toFixed(3) : 'N/A'} label="CVS Score" />
                        <StatsCard
                            value={data.overall_eligibility || (data.estimated_eligibility_pct != null ? `${data.estimated_eligibility_pct}%` : 'N/A')}
                            label="Eligibility"
                        />
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">
                                <TierBadge tier={data.tier || 'Unknown'} /> {data.antigen || antigen} — {data.n_subgroups || subtypes.length} Subgroups
                            </div>
                        </div>
                        <div className="card">
                            <div className="card-header">Co-Expression Markers</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                                {Array.isArray(data.co_expression_markers) && data.co_expression_markers.length > 0 ? (
                                    data.co_expression_markers.map((m, i) => {
                                        const label = typeof m === 'string' ? m : (m.gene || m.name || JSON.stringify(m));
                                        const group = typeof m === 'object' ? m.group : null;
                                        return (
                                            <span key={i} className="badge badge-tier2" title={group || ''}>
                                                {label}
                                            </span>
                                        );
                                    })
                                ) : (
                                    <span style={{ color: '#64748B', fontSize: 13 }}>None identified</span>
                                )}
                            </div>
                        </div>
                    </div>

                    {subtypes.length > 0 && (
                        <div className="card">
                            <div className="card-header">Subtype Analysis</div>
                            <table className="data-table">
                                <thead>
                                    <tr><th>Subtype</th><th>Population</th><th>Aggression</th><th>Benefit</th><th>Response Rate</th></tr>
                                </thead>
                                <tbody>
                                    {subtypes.map((st, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 600 }}>{st.subtype || 'Unknown'}</td>
                                            <td>{st.population_share || 'N/A'}</td>
                                            <td>
                                                <span style={{ color: st.aggression === 'high' ? '#EF4444' : st.aggression === 'medium' ? '#F59E0B' : '#10B981' }}>
                                                    {st.aggression || 'unknown'}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`badge ${st.benefit_label && st.benefit_label.includes('High') ? 'badge-tier1' : 'badge-tier2'}`}>
                                                    {st.benefit_label || 'N/A'}
                                                </span>
                                            </td>
                                            <td>{safePercent(st.estimated_response_rate)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {subgroups.length > 0 && (
                        <div className="card">
                            <div className="card-header">Patient Subgroups</div>
                            <table className="data-table">
                                <thead><tr><th>Cancer Type</th><th>Expression</th><th>Prevalence</th><th>Predicted Benefit</th></tr></thead>
                                <tbody>
                                    {subgroups.map((sg, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 600 }}>{sg.cancer_type || 'Unknown'}</td>
                                            <td>{sg.expression_level || 'N/A'}</td>
                                            <td>{sg.prevalence || 'N/A'}</td>
                                            <td>{sg.predicted_benefit || 'N/A'}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {data.recommendation && (
                        <div className="success-msg" style={{ marginTop: 12 }}>{data.recommendation}</div>
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
