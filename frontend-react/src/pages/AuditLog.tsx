import { useState, useEffect } from 'react';
import { fetchAuditLog } from '../api/client';
import { Loading, ErrorMsg } from '../components/UIComponents';
import PageLoader from '../components/PageLoader';

export default function AuditLog() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [limit, setLimit] = useState(50);

    const loadData = () => {
        setLoading(true);
        fetchAuditLog(limit)
            .then(setData)
            .catch(() => setError('Failed to load audit log'))
            .finally(() => setLoading(false));
    };

    useEffect(() => { loadData(); }, [limit]);

    const statusColor = (code: number) => {
        if (code >= 200 && code < 300) return '#10B981';
        if (code >= 400 && code < 500) return '#F59E0B';
        if (code >= 500) return '#EF4444';
        return '#94A3B8';
    };

    return (
        <>
            <div className="page-header">
                <h2>📜 Audit Log</h2>
                <p>Regulatory compliance — view all API requests with timestamps, endpoints, and response metrics</p>
            </div>

            {data?.stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{data.stats.total_requests || 0}</div>
                        <div className="stat-label">Total Requests</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{(data.stats.avg_latency_ms || 0).toFixed(0)}ms</div>
                        <div className="stat-label">Avg Latency</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{data.stats.unique_ips || 0}</div>
                        <div className="stat-label">Unique IPs</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{data.stats.top_endpoints?.length || 0}</div>
                        <div className="stat-label">Endpoints Hit</div>
                    </div>
                </div>
            )}

            <ErrorMsg msg={error} />
            {loading && <PageLoader theme="audit" text="Loading audit log..." />}

            {data && (
                <div className="card">
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span>Recent Requests ({data.entries?.length || 0} shown)</span>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <select className="form-control" value={limit} onChange={e => setLimit(Number(e.target.value))}
                                style={{ width: 'auto', padding: '4px 10px', fontSize: 12 }}>
                                <option value={25}>25</option>
                                <option value={50}>50</option>
                                <option value={100}>100</option>
                                <option value={500}>500</option>
                            </select>
                            <button className="btn btn-secondary" onClick={loadData} style={{ fontSize: 11, padding: '4px 12px' }}>
                                🔄 Refresh
                            </button>
                        </div>
                    </div>

                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                            <thead>
                                <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                    <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Timestamp</th>
                                    <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)' }}>Method</th>
                                    <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)' }}>Path</th>
                                    <th style={{ textAlign: 'center', padding: '8px 6px', color: 'var(--text-muted)' }}>Status</th>
                                    <th style={{ textAlign: 'right', padding: '8px 6px', color: 'var(--text-muted)' }}>Latency</th>
                                    <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)' }}>IP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.entries?.map((entry: any, i: number) => (
                                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                        <td style={{ padding: '8px 6px', fontFamily: 'monospace', whiteSpace: 'nowrap', color: 'var(--text-muted)', fontSize: 11 }}>
                                            {new Date(entry.timestamp).toLocaleString()}
                                        </td>
                                        <td style={{ padding: '8px 6px' }}>
                                            <span className="badge" style={{
                                                background: entry.method === 'GET' ? 'rgba(16,185,129,0.12)' : 'rgba(59,130,246,0.12)',
                                                color: entry.method === 'GET' ? '#10B981' : '#3B82F6',
                                                fontSize: 10,
                                            }}>{entry.method}</span>
                                        </td>
                                        <td style={{ padding: '8px 6px', fontFamily: 'monospace', fontSize: 11, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {entry.path}
                                        </td>
                                        <td style={{ padding: '8px 6px', textAlign: 'center' }}>
                                            <span style={{
                                                fontWeight: 700, fontSize: 11,
                                                color: statusColor(entry.status_code),
                                            }}>{entry.status_code}</span>
                                        </td>
                                        <td style={{ padding: '8px 6px', textAlign: 'right', fontFamily: 'monospace', fontSize: 11 }}>
                                            {entry.latency_ms?.toFixed(0)}ms
                                        </td>
                                        <td style={{ padding: '8px 6px', fontSize: 11, color: 'var(--text-muted)' }}>
                                            {entry.client_ip}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {data.stats?.top_endpoints?.length > 0 && (
                        <div style={{ marginTop: 16, padding: '12px 16px', borderRadius: 8, background: 'var(--bg-secondary)' }}>
                            <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-secondary)' }}>
                                Top Endpoints
                            </div>
                            {data.stats.top_endpoints.map((ep: any, i: number) => (
                                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 12 }}>
                                    <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{ep.path}</span>
                                    <span style={{ fontWeight: 600 }}>{ep.count}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </>
    );
}
