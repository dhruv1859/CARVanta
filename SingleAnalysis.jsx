import { useState, useEffect } from 'react';
import { scoreAntigen, fetchAntigens } from '../api/client';
import { TierBadge, DataSourceBadge, ScoreCircle, FeatureBar, Loading, ErrorMsg } from '../components/UIComponents';
import { Radar } from 'react-chartjs-2';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip } from 'chart.js';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

export default function SingleAnalysis() {
    const [antigens, setAntigens] = useState([]);
    const [search, setSearch] = useState('');
    const [selected, setSelected] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchAntigens(search, 50)
            .then(setAntigens)
            .catch(() => setAntigens([]));
    }, [search]);

    const handleScore = async () => {
        if (!selected) return;
        setLoading(true); setError(''); setResult(null);
        try {
            const data = await scoreAntigen(selected);
            setResult(data);
        } catch (e) {
            setError(e.response?.data?.detail || 'Failed to score antigen');
        } finally { setLoading(false); }
    };

    const radarData = result ? {
        labels: ['Tumor Spec.', 'Safety', 'Stability', 'Evidence', 'Immunogen.', 'Surface', 'Tissue Risk', 'Protein Val.'],
        datasets: [{
            label: selected,
            data: [
                result.features?.tumor_specificity ?? 0,
                result.features?.safety ?? 0,
                result.features?.stability ?? 0,
                result.features?.evidence ?? 0,
                result.features?.immunogenicity ?? 0,
                result.features?.surface_accessibility ?? 0,
                1 - (result.features?.tissue_risk ?? 0),
                result.features?.protein_validation ?? 0,
            ],
            backgroundColor: 'rgba(59,130,246,0.15)',
            borderColor: '#3B82F6',
            borderWidth: 2,
            pointBackgroundColor: '#3B82F6',
        }]
    } : null;

    const radarOpts = {
        scales: {
            r: {
                beginAtZero: true, max: 1,
                ticks: { color: '#64748B', backdropColor: 'transparent', stepSize: 0.25 },
                pointLabels: { color: '#94A3B8', font: { size: 11 } },
                grid: { color: 'rgba(30,41,59,0.6)' },
                angleLines: { color: 'rgba(30,41,59,0.6)' },
            }
        },
        plugins: { legend: { display: false } },
        maintainAspectRatio: true,
    };

    return (
        <>
            <div className="page-header">
                <h2>🔬 Single Antigen Analysis</h2>
                <p>Score any antigen using CARVanta v4 Adaptive ML-Driven scoring across 8 clinical features</p>
            </div>

            <div className="card">
                <div className="input-row">
                    <div className="form-group">
                        <label>Search Antigens</label>
                        <input className="form-control" placeholder="Type to search..." value={search}
                            onChange={e => setSearch(e.target.value)} />
                    </div>
                    <div className="form-group">
                        <label>Select Antigen</label>
                        <select className="form-control" value={selected} onChange={e => setSelected(e.target.value)}>
                            <option value="">-- select --</option>
                            {antigens.map(a => <option key={a} value={a}>{a}</option>)}
                        </select>
                    </div>
                    <button className="btn btn-primary" onClick={handleScore} disabled={!selected || loading}>
                        {loading ? 'Scoring...' : 'Score Antigen'}
                    </button>
                </div>
            </div>

            <ErrorMsg msg={error} />
            {loading && <Loading text="Computing adaptive score..." />}

            {result && (
                <>
                    <div className="grid-2">
                        <div className="card">
                            <div className="card-header">Score Summary</div>
                            <div className="score-display">
                                <ScoreCircle score={result.CVS} tier={result.tier} />
                                <div>
                                    <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>{result.antigen}</div>
                                    <TierBadge tier={result.tier} />
                                    <DataSourceBadge source={result.data_source} />
                                    <div style={{ marginTop: 8, fontSize: 12, color: '#94A3B8' }}>
                                        ML Score: <strong>{result.ml_score?.toFixed(3)}</strong> &nbsp;·&nbsp;
                                        Confidence: <strong>{result.confidence_label}</strong>
                                    </div>
                                    {result.source_database && (
                                        <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
                                            Source: {result.source_database} · Evidence: {result.evidence_level}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-header">Radar Profile</div>
                            {radarData && <Radar data={radarData} options={radarOpts} />}
                        </div>
                    </div>

                    <div className="card">
                        <div className="card-header">Feature Breakdown</div>
                        {result.features && Object.entries(result.features).map(([k, v]) => (
                            <FeatureBar key={k} label={k.replace(/_/g, ' ')} value={v} />
                        ))}
                    </div>

                    {result.safety_report && (
                        <div className="card">
                            <div className="card-header">Safety Profile</div>
                            <div className="grid-3">
                                <div className="stat-card">
                                    <div className="stat-value">{result.safety_report.risk_level || 'N/A'}</div>
                                    <div className="stat-label">Risk Level</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-value">{result.safety_report.critical_organ_flags || 0}</div>
                                    <div className="stat-label">Critical Organ Flags</div>
                                </div>
                                <div className="stat-card">
                                    <div className="stat-value">{result.safety_report.overall_safety?.toFixed(3) || 'N/A'}</div>
                                    <div className="stat-label">Overall Safety</div>
                                </div>
                            </div>
                        </div>
                    )}
                </>
            )}
        </>
    );
}
