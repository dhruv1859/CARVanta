import { useState, useEffect } from 'react';
import { fetchAntigens, fetchClinicalTrials } from '../api/client';
import { Loading, ErrorMsg, StatsCard } from '../components/UIComponents';

export default function ClinicalTrials() {
    const [antigens, setAntigens] = useState([]);
    const [selected, setSelected] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => { fetchAntigens('', 50).then(setAntigens).catch(() => { }); }, []);

    const handleLoad = async () => {
        if (!selected) return;
        setLoading(true); setError(''); setData(null);
        try {
            setData(await fetchClinicalTrials(selected));
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to load trials');
        } finally { setLoading(false); }
    };

    /* API returns: {gene, total_trials, car_t_trials, phase_distribution: {PHASE1: N, ...}, 
       status_distribution: {RECRUITING: N, ...}, recent_trials: [{nct_id, title, status, phases: [...]}], 
       cancer_types, source, status} */

    const phases = data?.phase_distribution || {};
    const statuses = data?.status_distribution || {};
    const trials = data?.recent_trials || [];

    return (
        <>
            <div className="page-header">
                <h2>💊 Clinical Trials</h2>
                <p>CAR-T clinical trial data from database and ClinicalTrials.gov</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group">
                        <label>Antigen</label>
                        <select className="form-control" value={selected} onChange={e => setSelected(e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(a => <option key={a} value={a}>{a}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleLoad} disabled={!selected || loading}>
                        {loading ? 'Loading...' : 'Load Trials'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Fetching clinical trial data..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.total_trials || 0} label="Total Trials" />
                        <StatsCard value={data.car_t_trials || 0} label="CAR-T Trials" />
                        <StatsCard value={statuses.RECRUITING || 0} label="Recruiting" />
                        <StatsCard value={statuses.COMPLETED || 0} label="Completed" />
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">Phase Distribution</div>
                            {Object.entries(phases).map(([phase, count]) => (
                                <div key={phase} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                                    <span style={{ fontWeight: 600 }}>{phase.replace('_', ' ')}</span>
                                    <span style={{ color: '#94A3B8' }}>{count} trials</span>
                                </div>
                            ))}
                        </div>
                        <div className="card">
                            <div className="card-header">Status Distribution</div>
                            {Object.entries(statuses).map(([status, count]) => (
                                <div key={status} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                                    <span style={{ fontWeight: 600, color: status === 'RECRUITING' ? '#10B981' : status === 'COMPLETED' ? '#3B82F6' : '#94A3B8' }}>
                                        {status === 'RECRUITING' ? '🟢' : status === 'ACTIVE' ? '🔵' : status === 'COMPLETED' ? '✅' : '⚪'} {status}
                                    </span>
                                    <span style={{ color: '#94A3B8' }}>{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {trials.length > 0 && (
                        <div className="card">
                            <div className="card-header">Recent Trials ({trials.length})</div>
                            <table className="data-table">
                                <thead><tr><th>NCT ID</th><th>Title</th><th>Phase</th><th>Status</th></tr></thead>
                                <tbody>
                                    {trials.slice(0, 20).map((t, i) => (
                                        <tr key={i}>
                                            <td>
                                                <a href={`https://clinicaltrials.gov/ct2/show/${t.nct_id}`}
                                                    target="_blank" rel="noreferrer"
                                                    style={{ color: '#3B82F6', textDecoration: 'none', fontWeight: 600 }}>
                                                    {t.nct_id}
                                                </a>
                                            </td>
                                            <td style={{ maxWidth: 400, fontSize: 12 }}>{t.title || 'N/A'}</td>
                                            <td>
                                                {(t.phases || []).map(p => (
                                                    <span key={p} className="badge badge-tier2" style={{ marginRight: 4 }}>{p}</span>
                                                ))}
                                            </td>
                                            <td style={{ fontSize: 12, color: t.status === 'RECRUITING' ? '#10B981' : '#94A3B8' }}>
                                                {t.status || 'N/A'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    <div style={{ marginTop: 12, fontSize: 12, color: '#64748B' }}>
                        Source: {data.source} · Cancer types: {Array.isArray(data.cancer_types) ? data.cancer_types.join(', ') : data.cancer_types}
                    </div>
                </>
            )}
        </>
    );
}
