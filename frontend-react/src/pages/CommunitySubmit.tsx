import { useState } from 'react';
import { submitCommunity } from '../api/client';
import { TierBadge } from '../components/UIComponents';

export default function CommunitySubmit() {
    const [form, setForm] = useState({ antigen_name: '', submitter_name: '', evidence_url: '', notes: '' });
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: any) => {
        e.preventDefault();
        if (!form.antigen_name || !form.submitter_name) return;
        setLoading(true); setError(''); setResult(null);
        try {
            const data = await submitCommunity(form);
            setResult(data);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Submission failed');
        } finally { setLoading(false); }
    };

    const verificationBadge = (v: any) => {
        if (!v) return null;
        const isNew = v.newly_added;
        const method = v.method;
        const sources = v.sources_found || [];
        if (method === 'local_database') {
            return (
                <span style={{
                    fontSize: 11, padding: '4px 12px', borderRadius: 12, fontWeight: 600,
                    background: 'rgba(16,185,129,0.12)', color: '#10B981',
                }}>
                    ✅ CARVanta Database
                </span>
            );
        }
        if (isNew && sources.length > 0) {
            return (
                <span style={{
                    fontSize: 11, padding: '4px 12px', borderRadius: 12, fontWeight: 600,
                    background: 'rgba(139,92,246,0.12)', color: '#A78BFA',
                }}>
                    🧬 Verified via {sources.join(' & ')}
                </span>
            );
        }
        return null;
    };

    return (
        <>
            <div className="page-header">
                <h2>🌐 Community Antigen Discovery</h2>
                <p>Submit new antigen candidates — CARVanta verifies them against NCBI Gene & UniProt in real-time</p>
            </div>

            <div className="grid-2">
                <div className="card">
                    <div className="card-header">Submit New Antigen</div>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Antigen / Gene Symbol *</label>
                            <input className="form-control" placeholder="e.g. CD19, ALPP, CRIB, ROR1..."
                                value={form.antigen_name}
                                onChange={e => setForm({ ...form, antigen_name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Your Name *</label>
                            <input className="form-control" placeholder="e.g. Dr. Jane Smith"
                                value={form.submitter_name}
                                onChange={e => setForm({ ...form, submitter_name: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Evidence URL (optional)</label>
                            <input className="form-control" placeholder="e.g. https://pubmed.ncbi.nlm.nih.gov/..."
                                value={form.evidence_url}
                                onChange={e => setForm({ ...form, evidence_url: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Notes (optional)</label>
                            <textarea className="form-control" rows={3} placeholder="Why is this a promising target?"
                                value={form.notes}
                                onChange={e => setForm({ ...form, notes: e.target.value })}
                                style={{ resize: 'vertical' }} />
                        </div>
                        <button className="btn btn-primary" type="submit"
                            disabled={loading || !form.antigen_name || !form.submitter_name}>
                            {loading ? '🔍 Verifying against NCBI & UniProt...' : '🚀 Submit & Verify'}
                        </button>
                        {loading && (
                            <div style={{ marginTop: 12, fontSize: 12, color: '#A78BFA', display: 'flex', alignItems: 'center', gap: 8 }}>
                                <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>🧬</span>
                                Searching NCBI Gene & UniProt databases... This may take up to 15 seconds.
                            </div>
                        )}
                    </form>
                </div>

                <div className="card">
                    <div className="card-header">Verification Result</div>
                    {error && (
                        <div className="error-msg">{error}</div>
                    )}
                    {!result && !error && !loading && (
                        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>🧬</div>
                            <div>Submit an antigen to verify & score</div>
                            <div style={{ fontSize: 12, marginTop: 8, lineHeight: 1.8 }}>
                                CARVanta will:<br />
                                1. Check its local database<br />
                                2. If unknown, search NCBI Gene & UniProt<br />
                                3. Verified genes are scored and added to CARVanta
                            </div>
                        </div>
                    )}
                    {result && (
                        <div style={{ padding: 20 }}>
                            {result.accepted ? (
                                <>
                                    <div className="success-msg" style={{ marginBottom: 16, textAlign: 'left', lineHeight: 1.6 }}>
                                        {result.message}
                                    </div>

                                    {/* Verification source badge */}
                                    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                                        {verificationBadge(result.verification)}
                                    </div>

                                    {/* Gene info from NCBI/UniProt */}
                                    {result.gene_info && (
                                        <div style={{
                                            padding: 12, borderRadius: 8, marginBottom: 16,
                                            background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.15)',
                                        }}>
                                            <div style={{ fontSize: 12, fontWeight: 600, color: '#A78BFA', marginBottom: 6 }}>
                                                🔬 Gene Details (from world databases)
                                            </div>
                                            <div style={{ fontSize: 13, lineHeight: 1.8 }}>
                                                {result.gene_info.full_name && (
                                                    <div><strong>Full Name:</strong> {result.gene_info.full_name}</div>
                                                )}
                                                <div><strong>Organism:</strong> {result.gene_info.organism}</div>
                                                {result.gene_info.source_url && (
                                                    <div>
                                                        <strong>Source:</strong>{' '}
                                                        <a href={result.gene_info.source_url} target="_blank" rel="noopener noreferrer"
                                                            style={{ color: '#38BDF8' }}>
                                                            View on {result.verification?.sources_found?.[0] || 'Database'} ↗
                                                        </a>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    <div style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 48, fontWeight: 800, marginBottom: 8 }}>
                                            {result.cvs_score?.toFixed(3)}
                                        </div>
                                        <div style={{ marginBottom: 12 }}>
                                            <TierBadge tier={result.tier} />
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className="error-msg" style={{ marginBottom: 16, textAlign: 'left', lineHeight: 1.6 }}>
                                        ❌ {result.message}
                                    </div>
                                    {result.verification?.sources_checked?.length > 0 && (
                                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
                                            Databases checked: {result.verification.sources_checked.join(', ')}
                                        </div>
                                    )}
                                </>
                            )}
                            <div style={{ textAlign: 'center', marginTop: 12 }}>
                                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                                    {result.antigen}
                                </div>
                                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                    Submitted by {result.submitter}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="card" style={{ marginTop: 20 }}>
                <div className="card-header">How It Works</div>
                <div className="grid-3">
                    <div style={{ textAlign: 'center', padding: 20 }}>
                        <div style={{ fontSize: 32, marginBottom: 8 }}>1️⃣</div>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>Submit</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            Enter any gene symbol — known or newly discovered
                        </div>
                    </div>
                    <div style={{ textAlign: 'center', padding: 20 }}>
                        <div style={{ fontSize: 32, marginBottom: 8 }}>2️⃣</div>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>AI Verifies</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            CARVanta searches NCBI Gene & UniProt to verify the gene is real
                        </div>
                    </div>
                    <div style={{ textAlign: 'center', padding: 20 }}>
                        <div style={{ fontSize: 32, marginBottom: 8 }}>3️⃣</div>
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>Score & Grow</div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                            Verified genes are scored and added to CARVanta's database
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
