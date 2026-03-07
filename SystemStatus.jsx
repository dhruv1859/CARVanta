import { useState } from 'react';
import { fetchHealth } from '../api/client';
import { StatsCard, Loading, ErrorMsg } from '../components/UIComponents';

export default function SystemStatus() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleCheck = async () => {
        setLoading(true); setError(''); setData(null);
        try {
            setData(await fetchHealth());
        } catch (e) {
            setError('Cannot connect to CARVanta backend');
        } finally { setLoading(false); }
    };

    return (
        <>
            <div className="page-header">
                <h2>⚙️ System Status</h2>
                <p>CARVanta platform health check and engine diagnostics</p>
            </div>

            <div className="card" style={{ textAlign: 'center' }}>
                <button className="btn btn-primary" onClick={handleCheck} disabled={loading}>
                    {loading ? 'Checking...' : 'Check System Health'}
                </button>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Connecting to backend..." />}

            {data && (
                <>
                    <div className="stats-grid">
                        <StatsCard value={data.status} label="Status" />
                        <StatsCard value={data.version} label="Version" />
                        <StatsCard value={data.antigen_count?.toLocaleString()} label="Antigens Loaded" />
                        <StatsCard value={data.cancer_types} label="Cancer Types" />
                    </div>

                    <div className="card">
                        <div className="card-header">Engine Details</div>
                        <div className="grid-2">
                            <div>
                                <div style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>
                                    <strong>Model:</strong> {data.model}
                                </div>
                                <div style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>
                                    <strong>Total Biomarkers:</strong> {data.total_biomarkers?.toLocaleString()}
                                </div>
                                <div style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8 }}>
                                    <strong>Unique Biomarkers:</strong> {data.unique_biomarkers?.toLocaleString()}
                                </div>
                            </div>
                            <div>
                                <div className="stats-grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
                                    <StatsCard value={data.validated_targets || 0} label="🟢 Validated" />
                                    <StatsCard value={data.predicted_targets?.toLocaleString() || 0} label="🔴 Predicted" />
                                    <StatsCard value={data.training_instances?.toLocaleString() || 0} label="📊 Training" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {data.features && (
                        <div className="card">
                            <div className="card-header">Scoring Features</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                {data.features.map(f => (
                                    <span key={f} className="badge badge-tier2">{f}</span>
                                ))}
                            </div>
                        </div>
                    )}

                    {data.new_endpoints && (
                        <div className="card">
                            <div className="card-header">API Endpoints</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                {data.new_endpoints.map(e => (
                                    <span key={e} style={{
                                        padding: '4px 10px', borderRadius: 4, fontSize: 12, fontWeight: 600,
                                        fontFamily: 'monospace', background: 'var(--bg-secondary)', color: '#06B6D4',
                                        border: '1px solid var(--border)',
                                    }}>{e}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </>
    );
}
