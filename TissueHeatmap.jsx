import { useState, useEffect } from 'react';
import { fetchAntigens, fetchToxicity } from '../api/client';
import { Loading, ErrorMsg, StatsCard } from '../components/UIComponents';

function riskColor(score) {
    if (score >= 0.7) return { bg: 'rgba(239,68,68,0.25)', color: '#EF4444' };
    if (score >= 0.4) return { bg: 'rgba(245,158,11,0.25)', color: '#F59E0B' };
    if (score >= 0.1) return { bg: 'rgba(59,130,246,0.15)', color: '#3B82F6' };
    return { bg: 'rgba(16,185,129,0.15)', color: '#10B981' };
}

export default function TissueHeatmap() {
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
            setData(await fetchToxicity(selected));
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to load heatmap');
        } finally { setLoading(false); }
    };

    const tissueMap = data?.tissue_risk_map || {};
    const alerts = data?.critical_organ_alerts || [];

    return (
        <>
            <div className="page-header">
                <h2>🧫 Tissue Risk Heatmap</h2>
                <p>Off-tumor toxicity prediction across normal tissues using GTEx expression data</p>
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
                        {loading ? 'Loading...' : 'Generate Heatmap'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Analyzing tissue expression..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.antigen || selected} label="Antigen" />
                        <StatsCard value={data.aggregate_toxicity_index?.toFixed(3) || 'N/A'} label="Aggregate Toxicity" />
                        <StatsCard value={data.organs_analyzed || Object.keys(tissueMap).length} label="Organs Analyzed" />
                        <StatsCard value={alerts.length} label="Critical Alerts" />
                    </div>

                    <div className="card">
                        <div className="card-header">Tissue Risk Map — {selected}</div>
                        <div className="heatmap-grid">
                            {Object.entries(tissueMap)
                                .sort(([, a], [, b]) => (b.risk_score || 0) - (a.risk_score || 0))
                                .map(([tissue, info]) => {
                                    const score = info.risk_score || 0;
                                    const { bg, color } = riskColor(score);
                                    return (
                                        <div key={tissue} className="heatmap-cell" style={{ background: bg, color }}>
                                            <div className="tissue-name">{tissue}</div>
                                            <div className="tissue-score">{score.toFixed(3)}</div>
                                            <div style={{ fontSize: 10, marginTop: 2, opacity: 0.8 }}>{info.risk_class}</div>
                                        </div>
                                    );
                                })}
                        </div>
                        {alerts.length > 0 && (
                            <div className="error-msg" style={{ marginTop: 16 }}>
                                ⚠️ Critical organ alerts: {alerts.join(', ')}
                            </div>
                        )}
                        {data.safety_recommendation && (
                            <div className="success-msg" style={{ marginTop: 12 }}>{data.safety_recommendation}</div>
                        )}
                    </div>
                </>
            )}
        </>
    );
}
