import { useState } from 'react';
import { executeQuery } from '../api/client';
import { TierBadge, Loading, ErrorMsg } from '../components/UIComponents';

export default function NLPSearch() {
    const [query, setQuery] = useState('');
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async () => {
        if (!query.trim()) return;
        setLoading(true); setError(''); setData(null);
        try {
            setData(await executeQuery(query));
        } catch (e) {
            setError(e.response?.data?.detail || 'Query failed');
        } finally { setLoading(false); }
    };

    return (
        <>
            <div className="page-header">
                <h2>🔍 NLP Query Search</h2>
                <p>Natural language biomarker queries — e.g. "top tier 1 antigens for leukemia with high safety"</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group" style={{ flex: 3 }}>
                        <label>Query</label>
                        <input className="form-control" placeholder='e.g. "safe antigens for breast cancer"'
                            value={query} onChange={e => setQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                    </div>
                    <button className="btn btn-primary" onClick={handleSearch} disabled={!query.trim() || loading}>
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Processing query..." />}

            {data?.parsed_query && (
                <div className="card">
                    <div className="card-header">Query Interpretation</div>
                    <div style={{ fontSize: 13, color: '#94A3B8' }}>
                        {typeof data.parsed_query === 'object' ? (
                            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                {Object.entries(data.parsed_query).map(([k, v]) => (
                                    v && <span key={k}><strong>{k}:</strong> {String(v)} &nbsp;·&nbsp;</span>
                                ))}
                            </div>
                        ) : <p>{data.parsed_query}</p>}
                    </div>
                    {data.summary && <p style={{ marginTop: 8, fontSize: 12, color: '#64748B' }}>{data.summary}</p>}
                    <div style={{ marginTop: 6, fontSize: 11, color: '#64748B' }}>
                        {data.total_matches} matches · Showing {data.returned} · Method: {data.search_method}
                    </div>
                </div>
            )}

            {data?.results && data.results.length > 0 && (
                <div className="card">
                    <div className="card-header">Results ({data.results.length})</div>
                    <table className="data-table">
                        <thead><tr><th>#</th><th>Antigen</th><th>Cancer</th><th>Source</th><th>CVS</th><th>ML</th><th>Tier</th></tr></thead>
                        <tbody>
                            {data.results.map((r, i) => (
                                <tr key={i}>
                                    <td>{i + 1}</td>
                                    <td style={{ fontWeight: 600 }}>{r.antigen}</td>
                                    <td>{r.cancer_type}</td>
                                    <td><span className={`badge ${r.data_source === 'real' ? 'badge-real' : 'badge-tier2'}`}>{r.data_source}</span></td>
                                    <td>{r.CVS?.toFixed(3)}</td>
                                    <td>{r.ml_score?.toFixed(3)}</td>
                                    <td><TierBadge tier={r.tier} /></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
