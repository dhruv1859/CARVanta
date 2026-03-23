import { useState } from 'react';
import { batchUpload } from '../api/client';
import { TierBadge, Loading, ErrorMsg } from '../components/UIComponents';
import PageLoader from '../components/PageLoader';

export default function BatchUpload() {
    const [geneText, setGeneText] = useState('');
    const [cancerType, setCancerType] = useState('');
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleUpload = async () => {
        const genes = geneText.split(/[\n,;\s]+/).map(g => g.trim()).filter(g => g.length > 0);
        if (genes.length === 0) return;
        setLoading(true); setError(''); setResult(null);
        try {
            const data = await batchUpload(genes, cancerType || undefined);
            setResult(data);
        } catch (e: any) {
            setError(e.response?.data?.detail || 'Batch upload failed');
        } finally { setLoading(false); }
    };

    const exampleGenes = 'CD19\nBCMA\nHER2\nEGFR\nCD20\nPSMA\nGD2\nCD38\nMESOTHELIN\nMUC1';

    return (
        <>
            <div className="page-header">
                <h2>📋 Batch Gene Upload</h2>
                <p>Score up to 500 genes at once — paste a list or upload from your pipeline</p>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">Gene List Input</div>
                    <div className="form-group">
                        <label>Paste gene symbols (one per line, or comma/space separated)</label>
                        <textarea className="form-control" rows={12}
                            placeholder="CD19&#10;BCMA&#10;HER2&#10;EGFR&#10;..."
                            value={geneText}
                            onChange={e => setGeneText(e.target.value)}
                            style={{ resize: 'vertical', fontFamily: 'monospace', fontSize: 13 }} />
                    </div>
                    <div className="form-group">
                        <label>Cancer type filter (optional)</label>
                        <input className="form-control" placeholder="e.g. B-ALL, DLBCL, AML..."
                            value={cancerType} onChange={e => setCancerType(e.target.value)} />
                    </div>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                        <button className="btn btn-primary" onClick={handleUpload}
                            disabled={loading || !geneText.trim()}>
                            {loading ? 'Scoring...' : '🚀 Score All Genes'}
                        </button>
                        <button className="btn btn-secondary" onClick={() => setGeneText(exampleGenes)}
                            style={{ fontSize: 11 }}>
                            Load Example (10 genes)
                        </button>
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            {geneText.split(/[\n,;\s]+/).filter(g => g.trim()).length} genes detected
                        </span>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">Results</div>
                    {!result && !loading && !error && (
                        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
                            <div>Paste genes and click "Score All" to see results</div>
                        </div>
                    )}
                    <ErrorMsg msg={error} />
                    {loading && <PageLoader theme="batch" text="Scoring genes in batch..." />}
                    {result && (
                        <>
                            <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
                                <div className="stat-card" style={{ flex: 1, minWidth: 90 }}>
                                    <div className="stat-value">{result.total_genes}</div>
                                    <div className="stat-label">Total</div>
                                </div>
                                <div className="stat-card" style={{ flex: 1, minWidth: 90 }}>
                                    <div className="stat-value" style={{ color: '#10B981' }}>{result.scored}</div>
                                    <div className="stat-label">Scored</div>
                                </div>
                                <div className="stat-card" style={{ flex: 1, minWidth: 90 }}>
                                    <div className="stat-value" style={{ color: '#EF4444' }}>{result.errors}</div>
                                    <div className="stat-label">Errors</div>
                                </div>
                            </div>

                            {result.tier_distribution && (
                                <div style={{ marginBottom: 16 }}>
                                    <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: 'var(--text-secondary)' }}>
                                        Tier Distribution
                                    </div>
                                    {Object.entries(result.tier_distribution).map(([tier, count]: [string, any]) => (
                                        <div key={tier} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                            <TierBadge tier={tier} />
                                            <div style={{ flex: 1, height: 6, background: 'var(--bg-secondary)', borderRadius: 3 }}>
                                                <div style={{
                                                    height: '100%', borderRadius: 3,
                                                    width: `${(count / result.scored) * 100}%`,
                                                    background: tier.includes('1') ? '#10B981' : tier.includes('2') ? '#06B6D4' : tier.includes('3') ? '#F59E0B' : '#EF4444',
                                                }} />
                                            </div>
                                            <span style={{ fontSize: 12, fontWeight: 600, width: 24, textAlign: 'right' }}>{count}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            <div style={{ maxHeight: 350, overflowY: 'auto' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                                    <thead>
                                        <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                            <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)' }}>Gene</th>
                                            <th style={{ textAlign: 'right', padding: '8px 6px', color: 'var(--text-muted)' }}>CVS</th>
                                            <th style={{ textAlign: 'left', padding: '8px 6px', color: 'var(--text-muted)' }}>Tier</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.results?.sort((a: any, b: any) => (b.CVS || 0) - (a.CVS || 0)).map((r: any, i: number) => (
                                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '8px 6px', fontWeight: 600 }}>{r.antigen}</td>
                                                <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 700, fontFamily: 'monospace' }}>
                                                    {r.CVS?.toFixed(3)}
                                                </td>
                                                <td style={{ padding: '8px 6px' }}><TierBadge tier={r.tier} /></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </>
    );
}
