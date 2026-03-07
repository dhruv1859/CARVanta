export function TierBadge({ tier }) {
    const cls = tier?.includes('Tier 1') ? 'badge-tier1'
        : tier?.includes('Tier 2') ? 'badge-tier2'
            : tier?.includes('Tier 3') ? 'badge-tier3'
                : 'badge-tier4';
    return <span className={`badge ${cls}`}>{tier || 'N/A'}</span>;
}

export function DataSourceBadge({ source }) {
    const cls = source === 'real' ? 'badge-real'
        : source === 'validated' ? 'badge-validated'
            : 'badge-synthetic';
    return <span className={`badge ${cls}`}>{source || 'unknown'}</span>;
}

export function StatsCard({ value, label }) {
    return (
        <div className="stat-card">
            <div className="stat-value">{value}</div>
            <div className="stat-label">{label}</div>
        </div>
    );
}

export function ScoreCircle({ score, tier }) {
    const cls = tier?.includes('Tier 1') ? 'tier1'
        : tier?.includes('Tier 2') ? 'tier2'
            : tier?.includes('Tier 3') ? 'tier3'
                : 'tier4';
    return (
        <div className={`score-circle ${cls}`}>
            {typeof score === 'number' ? score.toFixed(3) : score}
        </div>
    );
}

export function FeatureBar({ label, value, max = 1 }) {
    const pct = Math.min((value / max) * 100, 100);
    return (
        <div className="feature-bar">
            <span className="feature-bar-label">{label}</span>
            <div className="feature-bar-track">
                <div className="feature-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="feature-bar-value">{typeof value === 'number' ? value.toFixed(3) : value}</span>
        </div>
    );
}

export function Loading({ text = 'Loading...' }) {
    return <div className="loading"><div className="spinner" />{text}</div>;
}

export function ErrorMsg({ msg }) {
    return msg ? <div className="error-msg">{msg}</div> : null;
}
