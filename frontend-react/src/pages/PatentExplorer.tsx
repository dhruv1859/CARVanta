import { useState, useEffect } from 'react';
import { fetchAllPatents, fetchPatents } from '../api/client';
import { ErrorMsg } from '../components/UIComponents';
import PageLoader from '../components/PageLoader';

export default function PatentExplorer() {
    const [allData, setAllData] = useState<any>(null);
    const [selected, setSelected] = useState('');
    const [detail, setDetail] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAllPatents()
            .then(setAllData)
            .catch(() => setError('Failed to load patent data'))
            .finally(() => setLoading(false));
    }, []);

    const handleSelect = async (antigen: string) => {
        setSelected(antigen);
        try {
            const data = await fetchPatents(antigen);
            setDetail(data);
        } catch { setDetail(null); }
    };

    const ftoColors: Record<string, string> = { good: '#10B981', moderate: '#F59E0B', limited: '#EF4444', uncharted: '#8B5CF6' };

    return (
        <>
            <div className="page-header">
                <h2>⚖️ Patent Landscape Explorer</h2>
                <p>Analyze intellectual property positions and freedom-to-operate for CAR-T targets</p>
            </div>

            <ErrorMsg msg={error} />
            {loading && <PageLoader theme="patents" text="Loading patent database..." />}

            {allData && (
                <>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">{allData.total_antigens_catalogued}</div>
                            <div className="stat-label">Antigens Mapped</div>
                        </div>
                        {['good', 'moderate', 'limited'].map(fto => (
                            <div className="stat-card" key={fto}>
                                <div className="stat-value" style={{ color: ftoColors[fto] }}>
                                    {Object.values(allData.antigens || {}).filter((a: any) => a.freedom_to_operate === fto).length}
                                </div>
                                <div className="stat-label">FTO: {fto}</div>
                            </div>
                        ))}
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">Antigen Patent Map</div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                {Object.entries(allData.antigens || {}).map(([antigen, info]: [string, any]) => (
                                    <button key={antigen} onClick={() => handleSelect(antigen)}
                                        style={{
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                                            border: selected === antigen ? '2px solid var(--accent-blue)' : '1px solid var(--border)',
                                            background: selected === antigen ? 'rgba(59,130,246,0.08)' : 'var(--bg-secondary)',
                                            color: 'var(--text-primary)', fontFamily: 'var(--font)', fontSize: 13,
                                        }}>
                                        <span style={{ fontWeight: 600 }}>{antigen}</span>
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{info.total_patents} patents</span>
                                            <span className="badge" style={{
                                                background: `${ftoColors[info.freedom_to_operate] || ftoColors.uncharted}20`,
                                                color: ftoColors[info.freedom_to_operate] || ftoColors.uncharted, fontSize: 10,
                                            }}>
                                                {info.freedom_to_operate}
                                            </span>
                                            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Cliff: {info.patent_cliff_year}</span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header">
                                {selected ? `${selected} — Patent Details` : 'Select an antigen'}
                            </div>
                            {detail && detail.has_patents && (
                                <>
                                    <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                                        <div className="stat-card" style={{ flex: 1, minWidth: 120 }}>
                                            <div className="stat-value">{detail.total_patents}</div>
                                            <div className="stat-label">Total Patents</div>
                                        </div>
                                        <div className="stat-card" style={{ flex: 1, minWidth: 120 }}>
                                            <div className="stat-value" style={{ color: ftoColors[detail.freedom_to_operate] }}>
                                                {detail.freedom_to_operate?.toUpperCase()}
                                            </div>
                                            <div className="stat-label">Freedom to Operate</div>
                                        </div>
                                        <div className="stat-card" style={{ flex: 1, minWidth: 120 }}>
                                            <div className="stat-value">{detail.patent_cliff_year}</div>
                                            <div className="stat-label">Patent Cliff</div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {detail.key_patents?.map((p: any, i: number) => (
                                            <div key={i} style={{
                                                padding: '14px 16px', borderRadius: 10,
                                                border: '1px solid var(--border)', background: 'var(--bg-secondary)',
                                            }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                    <span style={{ fontWeight: 700, fontSize: 13, color: 'var(--accent-blue)' }}>{p.id}</span>
                                                    <span className="badge" style={{
                                                        background: p.status === 'expired' ? 'rgba(16,185,129,0.12)' : 'rgba(245,158,11,0.12)',
                                                        color: p.status === 'expired' ? '#10B981' : '#F59E0B', fontSize: 10,
                                                    }}>{p.status}</span>
                                                </div>
                                                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{p.title}</div>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>
                                                    {p.assignee} · {p.year} · {p.type?.replace(/_/g, ' ')}
                                                </div>
                                                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                                    {p.summary}
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <div className="investor-quote" style={{ marginTop: 16 }}>
                                        💡 {detail.recommendation}
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </>
            )}
        </>
    );
}
