import { useState, useEffect } from 'react';
import { fetchAntigens, batchScore } from '../api/client';
import { TierBadge, Loading, ErrorMsg } from '../components/UIComponents';

export default function Comparison() {
    const [antigens, setAntigens] = useState([]);
    const [antigenA, setAntigenA] = useState('');
    const [antigenB, setAntigenB] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => { fetchAntigens('', 100).then(setAntigens).catch(() => { }); }, []);

    const handleCompare = async () => {
        if (!antigenA || !antigenB) return;
        setLoading(true); setError(''); setResults(null);
        try {
            const data = await batchScore([antigenA, antigenB]);
            setResults(data);
        } catch (e) {
            setError(e.response?.data?.detail || 'Comparison failed');
        } finally { setLoading(false); }
    };

    const a = results?.[0];
    const b = results?.[1];

    return (
        <>
            <div className="page-header">
                <h2>⚖️ Antigen Comparison</h2>
                <p>Side-by-side adaptive scoring comparison of two antigens</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group">
                        <label>Antigen A</label>
                        <select className="form-control" value={antigenA} onChange={e => setAntigenA(e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(ag => <option key={ag} value={ag}>{ag}</option>)}
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Antigen B</label>
                        <select className="form-control" value={antigenB} onChange={e => setAntigenB(e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(ag => <option key={ag} value={ag}>{ag}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleCompare}
                        disabled={!antigenA || !antigenB || loading}>
                        {loading ? 'Comparing...' : 'Compare'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Computing scores..." />}

            {a && b && (
                <>
                    <div className="grid-2">
                        {[a, b].map((r) => (
                            <div className="card" key={r.antigen}>
                                <div className="card-header">{r.antigen}</div>
                                <div className="score-display">
                                    <div className={`score-circle ${r.tier?.includes('Tier 1') ? 'tier1' : r.tier?.includes('Tier 2') ? 'tier2' : 'tier3'}`}>
                                        {r.CVS?.toFixed(3)}
                                    </div>
                                    <div>
                                        <TierBadge tier={r.tier} />
                                        <div style={{ marginTop: 8, fontSize: 13, color: '#94A3B8' }}>
                                            Confidence: <strong>{r.confidence_score?.toFixed(3)}</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div className="card">
                        <div className="card-header">Head-to-Head</div>
                        <table className="data-table">
                            <thead><tr><th>Metric</th><th>{a.antigen}</th><th>{b.antigen}</th><th>Winner</th></tr></thead>
                            <tbody>
                                <tr>
                                    <td style={{ fontWeight: 600 }}>CVS Score</td>
                                    <td>{a.CVS?.toFixed(3)}</td>
                                    <td>{b.CVS?.toFixed(3)}</td>
                                    <td style={{ color: (a.CVS ?? 0) >= (b.CVS ?? 0) ? '#10B981' : '#EF4444', fontWeight: 700 }}>
                                        {(a.CVS ?? 0) >= (b.CVS ?? 0) ? a.antigen : b.antigen}
                                    </td>
                                </tr>
                                <tr>
                                    <td style={{ fontWeight: 600 }}>Confidence</td>
                                    <td>{a.confidence_score?.toFixed(3)}</td>
                                    <td>{b.confidence_score?.toFixed(3)}</td>
                                    <td style={{ color: (a.confidence_score ?? 0) >= (b.confidence_score ?? 0) ? '#10B981' : '#EF4444', fontWeight: 700 }}>
                                        {(a.confidence_score ?? 0) >= (b.confidence_score ?? 0) ? a.antigen : b.antigen}
                                    </td>
                                </tr>
                                <tr>
                                    <td style={{ fontWeight: 600 }}>Tier</td>
                                    <td><TierBadge tier={a.tier} /></td>
                                    <td><TierBadge tier={b.tier} /></td>
                                    <td>—</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </>
    );
}
