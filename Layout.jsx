import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
    { path: '/', icon: '🔬', label: 'Single Antigen Analysis' },
    { path: '/compare', icon: '⚖️', label: 'Antigen Comparison' },
    { path: '/heatmap', icon: '🧫', label: 'Tissue Risk Heatmap' },
    { path: '/synergy', icon: '🎯', label: 'Multi-Target Synergy' },
    { path: '/stratify', icon: '👥', label: 'Patient Stratification' },
    { path: '/search', icon: '🔍', label: 'NLP Query Search' },
    { path: '/trials', icon: '💊', label: 'Clinical Trials' },
    { path: '/leaderboard', icon: '🏆', label: 'Global Leaderboard' },
    { path: '/dataset', icon: '📊', label: 'Dataset Intelligence' },
    { path: '/status', icon: '⚙️', label: 'System Status' },
];

export default function Layout({ children }) {
    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <h1>◆ CARVanta</h1>
                    <p>AI-Augmented Biomarker Intelligence Platform · v4 Adaptive ML-Driven Scoring</p>
                </div>
                <nav className="sidebar-nav">
                    {NAV_ITEMS.map(item => (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            end={item.path === '/'}
                            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                        >
                            <span className="nav-icon">{item.icon}</span>
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
                <div className="sidebar-footer">
                    <div>CARVanta v4 · Enterprise Edition</div>
                    <div>© CARVanta — carvanta.ai</div>
                </div>
            </aside>
            <main className="main-content">
                {children}
            </main>
        </div>
    );
}
