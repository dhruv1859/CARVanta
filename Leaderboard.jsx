import { useState, useEffect } from 'react';
import { fetchRankings, fetchCancerTypes } from '../api/client';
import { TierBadge, Loading, ErrorMsg } from '../components/UIComponents';

export default function Leaderboard() {
    const [topN, setTopN] = useState(25);
    const [cancerTypes, setCancerTypes] = useState([]);
    const [cancer, setCancer] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => { fetchCancerTypes().then(setCancerTypes).catch(() => { }); }, []);

    const handleLoad = async () => {
        setLoading(true); setError(''); setData(null);
        try {
            setData(await fetchRankings(topN, cancer || null));
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to load rankings');
        } finally { setLoading(false); }
    };

    return (
        <>
            <div className="page-header">
                <h2>🏆 Global CAR-T Leaderboard</h2>
                <p>Adaptive ML-driven rankings — blending rule-based CVS (60%) + ML regression (40%)</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group">
                        <label>Top N</label>
                        <input type="number" className="form-control" value={topN}
                            onChange={e => setTopN(Number(e.target.value))} min={5} max={100} />
                    </div>
                    <div className="form-group">
                        <label>Cancer Type</label>
                        <select className="form-control" value={cancer} onChange={e => setCancer(e.target.value)}>
                            <option value="">All (Global)</option>
                            {cancerTypes.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleLoad} disabled={loading}>
                        {loading ? 'Loading...' : 'Load Leaderboard'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Computing adaptive rankings..." />}

            {data && data.length > 0 && (
                <div className="card">
                    <div className="card-header">
                        Top {data.length} Antigens {cancer && `— ${cancer}`}
                    </div>
                    {data.map((item, i) => {
                        const inp = item.input || {};
                        const res = item.result || {};
                        return (
                            <div className="rank-item" key={i}>
                                <div className={`rank-number ${i < 3 ? 'top-3' : ''}`}>#{i + 1}</div>
                                <div className="rank-details">
                                    <div className="rank-name">{inp.antigen || '?'}</div>
                                    <div className="rank-cancer">{inp.cancer_type || ''}</div>
                                </div>
                                <div className="rank-scores">
                                    <div className="rank-score">
                                        <div className="rank-score-value" style={{ color: '#3B82F6' }}>
                                            {res.CVS?.toFixed(3)}
                                        </div>
                                        <div className="rank-score-label">CVS</div>
                                    </div>
                                    <div className="rank-score">
                                        <div className="rank-score-value" style={{ color: '#06B6D4' }}>
                                            {res.ml_score?.toFixed(3)}
                                        </div>
                                        <div className="rank-score-label">ML</div>
                                    </div>
                                    <TierBadge tier={res.tier} />
                                </div>
                            </div>
                        );
                    })}

                    {data[0] && (
                        <div className="success-msg" style={{ marginTop: 16 }}>
                            🥇 Top candidate: <strong>{data[0].input?.antigen}</strong> ({data[0].input?.cancer_type}) —
                            Score: {data[0].result?.CVS?.toFixed(3)}
                        </div>
                    )}
                </div>
            )}
        </>
    );
}
