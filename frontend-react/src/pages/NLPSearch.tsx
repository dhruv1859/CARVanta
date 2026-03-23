import { useState } from 'react';
import { executeQuery } from '../api/client';
import { TierBadge, ErrorMsg } from '../components/UIComponents';
import PageLoader from '../components/PageLoader';

const EXAMPLE_QUERIES = [
    "best antigens for leukemia",
    "worst targets overall",
    "safe antigens for breast cancer",
    "which antigens should I avoid",
    "top 5 tier 1 targets for melanoma",
    "targets that are failing",
    "show me options for brain tumors",
];

export default function NLPSearch() {
    const [query, setQuery] = useState('');
    const [limit, setLimit] = useState(25);
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async (q?: string) => {
        const searchQuery = q || query;
        if (!searchQuery.trim()) return;
        if (q) setQuery(q);
        setLoading(true); setError(''); setData(null);
        try {
            setData(await executeQuery(searchQuery, limit));
        } catch (e: any) {
            setError(e.response?.data?.detail || 'Query failed');
        } finally { setLoading(false); }
    };

    const isAscending = data?.parsed_query?.sort_ascending === true;
    const aiMeta = data?.parsed_query?.ai_metadata;
    const isAI = aiMeta?.method === 'semantic';
    const aiConfidence = aiMeta?.intent_confidence;

    return (
        <>
            <div className="page-header">
                <h2>🔍 NLP Query Search</h2>
                <p>AI-powered antigen discovery — understands natural language, intent, and context</p>
            </div>

            {/* Example query chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                {EXAMPLE_QUERIES.map(eq => (
                    <button key={eq} className="btn"
                        style={{
                            fontSize: 11, padding: '5px 12px', borderRadius: 20,
                            background: 'rgba(56,189,248,0.08)', border: '1px solid rgba(56,189,248,0.2)',
                            color: '#38BDF8', cursor: 'pointer', transition: 'all 0.2s'
                        }}
                        onClick={() => handleSearch(eq)}>
                        {eq}
                    </button>
                ))}
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group" style={{ flex: 3 }}>
                        <label>Query</label>
                        <input className="form-control"
                            placeholder='Try anything — "which antigens should I avoid for brain tumors?"'
                            value={query} onChange={e => setQuery(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                    </div>
                    <div className="form-group" style={{ flex: 0.5, minWidth: 100 }}>
                        <label>Limit</label>
                        <input className="form-control" type="number" min={1} max={200} value={limit}
                            onChange={e => setLimit(Math.max(1, Math.min(200, Number(e.target.value))))} />
                    </div>
                    <button className="btn btn-primary" onClick={() => handleSearch()} disabled={!query.trim() || loading}>
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <PageLoader theme="nlp" text="AI is analyzing your query..." />}

            {data?.parsed_query && (
                <div className="card">
                    <div className="card-header" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        Query Understanding
                        {/* AI vs Keyword badge */}
                        {isAI ? (
                            <span style={{
                                fontSize: 11, padding: '3px 10px', borderRadius: 12, fontWeight: 600,
                                background: 'rgba(139,92,246,0.15)', color: '#A78BFA',
                            }}>
                                🧠 AI Semantic ({Math.round((aiConfidence || 0) * 100)}% confidence)
                            </span>
                        ) : (
                            <span style={{
                                fontSize: 11, padding: '3px 10px', borderRadius: 12, fontWeight: 600,
                                background: 'rgba(148,163,184,0.15)', color: '#94A3B8',
                            }}>
                                🔤 Keyword Fallback
                            </span>
                        )}
                        {/* Sort direction badge */}
                        {isAscending ? (
                            <span style={{ fontSize: 11, background: 'rgba(239,68,68,0.15)', color: '#EF4444', padding: '3px 10px', borderRadius: 12, fontWeight: 600 }}>
                                ↑ Worst First
                            </span>
                        ) : (
                            <span style={{ fontSize: 11, background: 'rgba(16,185,129,0.15)', color: '#10B981', padding: '3px 10px', borderRadius: 12, fontWeight: 600 }}>
                                ↓ Best First
                            </span>
                        )}
                    </div>

                    {/* AI Intent */}
                    {aiMeta?.intent && (
                        <div style={{ marginBottom: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
                            <span style={{ fontSize: 12, color: '#64748B' }}>Intent detected:</span>
                            <span style={{
                                fontSize: 12, fontWeight: 600, padding: '2px 10px', borderRadius: 8,
                                background: aiMeta.intent === 'worst' ? 'rgba(239,68,68,0.12)' :
                                    aiMeta.intent === 'best' ? 'rgba(16,185,129,0.12)' :
                                        aiMeta.intent === 'filter_safety' ? 'rgba(59,130,246,0.12)' : 'rgba(148,163,184,0.12)',
                                color: aiMeta.intent === 'worst' ? '#EF4444' :
                                    aiMeta.intent === 'best' ? '#10B981' :
                                        aiMeta.intent === 'filter_safety' ? '#3B82F6' : '#94A3B8',
                            }}>
                                {aiMeta.intent}
                            </span>
                        </div>
                    )}

                    {/* Parsed parameters */}
                    <div style={{ fontSize: 13, color: '#94A3B8' }}>
                        {typeof data.parsed_query === 'object' ? (
                            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                                {Object.entries(data.parsed_query)
                                    .filter(([k]) => !['raw_query', 'feature_filters', 'ai_metadata'].includes(k))
                                    .map(([k, v]) => (
                                        v != null && v !== false && <span key={k}><strong>{k}:</strong> {String(v)} &nbsp;·&nbsp;</span>
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
                        <thead><tr><th>#</th><th>Antigen</th><th>Cancer</th><th>Source</th><th>CVS {isAscending ? '↑' : '↓'}</th><th>ML</th><th>Tier</th></tr></thead>
                        <tbody>
                            {data.results.map((r: any, i: number) => (
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
