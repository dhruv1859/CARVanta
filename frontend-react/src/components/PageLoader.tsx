import '../styles/page-loaders.css';

type LoaderTheme = 'comparison' | 'heatmap' | 'synergy' | 'stratify' | 'nlp' | 'trials' |
    'leaderboard' | 'dataset' | 'drugs' | 'patents' | 'community' | 'batch' | 'audit';

interface Props {
    theme: LoaderTheme;
    text?: string;
}

export default function PageLoader({ theme, text }: Props) {
    return (
        <div className="page-loader">
            {theme === 'comparison' && <ComparisonLoader />}
            {theme === 'heatmap' && <HeatmapLoader />}
            {theme === 'synergy' && <SynergyLoader />}
            {theme === 'stratify' && <StratifyLoader />}
            {theme === 'nlp' && <NLPLoader />}
            {theme === 'trials' && <TrialsLoader />}
            {theme === 'leaderboard' && <LeaderboardLoader />}
            {theme === 'dataset' && <DatasetLoader />}
            {theme === 'drugs' && <DrugsLoader />}
            {theme === 'patents' && <PatentsLoader />}
            {theme === 'community' && <CommunityLoader />}
            {theme === 'batch' && <BatchLoader />}
            {theme === 'audit' && <AuditLoader />}
            <div className="page-loader-label">{text || 'Loading...'}</div>
        </div>
    );
}

/* ── Comparison: Balance Scale ───────────────── */
function ComparisonLoader() {
    return (
        <div className="loader-comparison">
            <div className="balance-beam" />
            <div className="balance-fulcrum" />
            <div className="balance-pan balance-pan-left">
                <div className="balance-dna-mini" style={{ position: 'absolute', left: 6, top: 3, background: '#3B82F6', color: '#3B82F6' }} />
                <div className="balance-dna-mini" style={{ position: 'absolute', left: 16, top: 3, background: '#60A5FA', color: '#60A5FA' }} />
            </div>
            <div className="balance-pan balance-pan-right">
                <div className="balance-dna-mini" style={{ position: 'absolute', left: 6, top: 3, background: '#8B5CF6', color: '#8B5CF6' }} />
                <div className="balance-dna-mini" style={{ position: 'absolute', left: 16, top: 3, background: '#A78BFA', color: '#A78BFA' }} />
            </div>
        </div>
    );
}

/* ── Heatmap: Cell Grid ──────────────────────── */
function HeatmapLoader() {
    const heatColors = ['#10B981', '#06B6D4', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'];
    return (
        <div className="loader-heatmap">
            {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} className="heat-cell"
                    style={{
                        background: heatColors[i % heatColors.length],
                        animationDelay: `${(i * 0.12)}s`,
                    }} />
            ))}
        </div>
    );
}

/* ── Synergy: Targets ────────────────────────── */
function SynergyLoader() {
    return (
        <div className="loader-synergy">
            <div className="synergy-target synergy-target-1" style={{ color: '#3B82F6' }}><div className="synergy-dot" /></div>
            <div className="synergy-target synergy-target-2" style={{ color: '#10B981' }}><div className="synergy-dot" /></div>
            <div className="synergy-target synergy-target-3" style={{ color: '#F59E0B' }}><div className="synergy-dot" /></div>
            <div className="synergy-link" style={{ top: 28, left: 28, width: 35, transform: 'rotate(10deg)' }} />
            <div className="synergy-link" style={{ top: 35, left: 28, width: 30, transform: 'rotate(50deg)' }} />
            <div className="synergy-link" style={{ top: 32, left: 50, width: 25, transform: 'rotate(-30deg)' }} />
        </div>
    );
}

/* ── Stratify: Patient Groups ────────────────── */
function StratifyLoader() {
    const groups = [
        { color: '#10B981', label: 'A', count: 3 },
        { color: '#3B82F6', label: 'B', count: 2 },
        { color: '#F59E0B', label: 'C', count: 4 },
    ];
    return (
        <div className="loader-stratify">
            {groups.map((g) => (
                <div key={g.label} className="strat-group">
                    {Array.from({ length: g.count }).map((_, i) => (
                        <div key={i} className="strat-person"
                            style={{ background: g.color, animationDelay: `${(i * 0.15)}s` }} />
                    ))}
                    <div className="strat-label">{g.label}</div>
                </div>
            ))}
        </div>
    );
}

/* ── NLP: Brain Pulse ────────────────────────── */
function NLPLoader() {
    return (
        <div className="loader-nlp">
            <div className="nlp-brain">🧠</div>
            <div className="nlp-wave" />
            <div className="nlp-wave" />
            <div className="nlp-wave" />
        </div>
    );
}

/* ── Trials: Test Tubes ──────────────────────── */
function TrialsLoader() {
    const tubes = [
        { border: '#3B82F6', liquid: '#3B82F6', delay: 0 },
        { border: '#10B981', liquid: '#10B981', delay: 0.3 },
        { border: '#8B5CF6', liquid: '#8B5CF6', delay: 0.6 },
        { border: '#F59E0B', liquid: '#F59E0B', delay: 0.9 },
    ];
    return (
        <div className="loader-trials">
            {tubes.map((t, i) => (
                <div key={i} className="test-tube" style={{ borderColor: t.border }}>
                    <div className="test-tube-liquid"
                        style={{ background: `${t.liquid}40`, animationDelay: `${t.delay}s` }} />
                    <div className="test-tube-bubble"
                        style={{ left: 3, animationDelay: `${t.delay + 0.2}s` }} />
                    <div className="test-tube-bubble"
                        style={{ left: 7, animationDelay: `${t.delay + 0.7}s` }} />
                </div>
            ))}
        </div>
    );
}

/* ── Leaderboard: Racing Bars ────────────────── */
function LeaderboardLoader() {
    const bars = [
        { color: '#10B981', delay: 0 },
        { color: '#3B82F6', delay: 0.2 },
        { color: '#8B5CF6', delay: 0.4 },
        { color: '#F59E0B', delay: 0.6 },
        { color: '#06B6D4', delay: 0.8 },
    ];
    return (
        <div className="loader-leaderboard">
            {bars.map((b, i) => (
                <div key={i} className="race-bar"
                    style={{ background: b.color, animationDelay: `${b.delay}s` }} />
            ))}
        </div>
    );
}

/* ── Dataset: Data Waterfall ──────────────────── */
function DatasetLoader() {
    const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#06B6D4', '#EF4444', '#EC4899', '#14B8A6'];
    return (
        <div className="loader-dataset">
            {colors.map((c, i) => (
                <div key={i} className="data-stream"
                    style={{
                        left: `${(i / colors.length) * 100}%`,
                        height: `${15 + Math.random() * 20}px`,
                        background: c,
                        animationDelay: `${i * 0.2}s`,
                    }} />
            ))}
        </div>
    );
}

/* ── Drug Interactions: Molecule Collision ────── */
function DrugsLoader() {
    return (
        <div className="loader-drugs">
            <div className="drug-pill" style={{ background: 'linear-gradient(90deg, #3B82F6, #60A5FA)' }} />
            <div className="drug-pill drug-pill-right" style={{ background: 'linear-gradient(90deg, #EF4444, #F87171)' }} />
            <div className="drug-spark" />
        </div>
    );
}

/* ── Patents: Gavel ──────────────────────────── */
function PatentsLoader() {
    return (
        <div className="loader-patents">
            <div className="gavel-head" />
            <div className="gavel-base" />
            <div className="gavel-ring" />
        </div>
    );
}

/* ── Community: Rocket ───────────────────────── */
function CommunityLoader() {
    return (
        <div className="loader-community">
            <div className="rocket">🚀</div>
            <div className="rocket-trail" style={{ left: '46%', background: '#F59E0B' }} />
            <div className="rocket-trail" style={{ left: '42%', background: '#EF4444', animationDelay: '0.3s' }} />
            <div className="rocket-trail" style={{ left: '50%', background: '#F59E0B', animationDelay: '0.6s' }} />
        </div>
    );
}

/* ── Batch: Funnel ───────────────────────────── */
function BatchLoader() {
    const geneColors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444'];
    return (
        <div className="loader-batch">
            <div className="funnel-top" />
            <div className="funnel-body" />
            <div className="funnel-stem" />
            {geneColors.map((c, i) => (
                <div key={i} className="funnel-gene"
                    style={{
                        background: c,
                        animationDelay: `${i * 0.4}s`,
                        '--x-start': `${-15 + i * 8}px`,
                    } as React.CSSProperties} />
            ))}
        </div>
    );
}

/* ── Audit Log: Cascading Lines ──────────────── */
function AuditLoader() {
    const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#64748B', '#06B6D4', '#F59E0B', '#3B82F6'];
    return (
        <div className="loader-audit">
            {colors.map((c, i) => (
                <div key={i} className="audit-line"
                    style={{
                        background: c,
                        animationDelay: `${i * 0.25}s`,
                        width: `${50 + Math.random() * 50}%`,
                    }} />
            ))}
        </div>
    );
}
