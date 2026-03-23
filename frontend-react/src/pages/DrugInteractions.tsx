import { useState, useEffect } from 'react';
import { fetchAllDrugInteractions, fetchDrugInteractions } from '../api/client';
import { ErrorMsg } from '../components/UIComponents';
import PageLoader from '../components/PageLoader';

export default function DrugInteractions() {
    const [allData, setAllData] = useState<any>(null);
    const [selected, setSelected] = useState('');
    const [detail, setDetail] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAllDrugInteractions()
            .then(setAllData)
            .catch(() => setError('Failed to load drug interactions'))
            .finally(() => setLoading(false));
    }, []);

    const handleSelect = async (antigen: string) => {
        setSelected(antigen);
        try {
            const data = await fetchDrugInteractions(antigen);
            setDetail(data);
        } catch { setDetail(null); }
    };

    const riskColors = { low: '#10B981', moderate: '#F59E0B', high: '#EF4444' };
    const interactionColors = { competing: '#EF4444', synergistic: '#10B981', neutral: '#94A3B8' };

    return (
        <>
            <div className="page-header">
                <h2>💊 Drug Interaction Browser</h2>
                <p>Explore antigen-drug interactions that may affect CAR-T therapy development</p>
            </div>

            <ErrorMsg msg={error} />
            {loading && <PageLoader theme="drugs" text="Loading interaction database..." />}

            {allData && (
                <>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value">{allData.total_antigens_catalogued}</div>
                            <div className="stat-label">Antigens Catalogued</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{Object.values(allData.antigens || {}).reduce((s: number, a: any) => s + (a.total_drugs || 0), 0)}</div>
                            <div className="stat-label">Total Interactions</div>
                        </div>
                    </div>

                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">Select Antigen</div>
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
                                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{info.total_drugs} drugs</span>
                                            <span className="badge" style={{
                                                background: `${riskColors[info.risk_level] || '#94A3B8'}20`,
                                                color: riskColors[info.risk_level] || '#94A3B8', fontSize: 10,
                                            }}>
                                                {info.risk_level}
                                            </span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header">
                                {selected ? `${selected} — Drug Details` : 'Select an antigen to view details'}
                            </div>
                            {detail && detail.has_interactions && (
                                <>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                                        {detail.drugs?.map((drug: any, i: number) => (
                                            <div key={i} style={{
                                                padding: '14px 16px', borderRadius: 10,
                                                border: '1px solid var(--border)', background: 'var(--bg-secondary)',
                                            }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                                                    <span style={{ fontWeight: 700, fontSize: 14 }}>{drug.drug}</span>
                                                    <span className="badge" style={{
                                                        background: `${interactionColors[drug.interaction] || '#94A3B8'}20`,
                                                        color: interactionColors[drug.interaction] || '#94A3B8',
                                                    }}>
                                                        {drug.interaction}
                                                    </span>
                                                </div>
                                                <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                                                    {drug.clinical_note}
                                                </div>
                                                {drug.severity && (
                                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                                        Severity: {drug.severity}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                    {detail.recommendation && (
                                        <div className="investor-quote" style={{ marginTop: 16 }}>
                                            💡 {detail.recommendation}
                                        </div>
                                    )}
                                </>
                            )}
                            {detail && !detail.has_interactions && (
                                <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
                                    No known drug interactions catalogued for {selected}.
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </>
    );
}
