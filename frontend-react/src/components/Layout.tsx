import { NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import SnapshotButton from './SnapshotButton';
import '../styles/auth.css';

const NAV_ITEMS = [
    { path: '/', icon: '🔬', label: 'Single Antigen Analysis' },
    { path: '/compare', icon: '⚖️', label: 'Antigen Comparison' },
    { path: '/heatmap', icon: '🧫', label: 'Tissue Risk Heatmap' },
    { path: '/synergy', icon: '🎯', label: 'Multi-Target Synergy' },
    { path: '/stratify', icon: '👥', label: 'Patient Stratification' },
    { path: '/search', icon: '🔍', label: 'NLP Query Search' },
    { path: '/trials', icon: '🧪', label: 'Clinical Trials' },
    { path: '/leaderboard', icon: '🏆', label: 'Global Leaderboard' },
    { path: '/dataset', icon: '📊', label: 'Dataset Intelligence' },
    { path: '/drugs', icon: '💊', label: 'Drug Interactions' },
    { path: '/patents', icon: '⚖️', label: 'Patent Explorer' },
    { path: '/community', icon: '🌐', label: 'Community Submit' },
    { path: '/batch', icon: '📋', label: 'Batch Upload' },
    { path: '/audit', icon: '📜', label: 'Audit Log' },
    { path: '/status', icon: '⚙️', label: 'System Status' },
    { path: '/profile', icon: '👤', label: 'My Profile' },
    { path: '/twin', icon: '🧑‍⚕️', label: 'Patient Digital Twin' },
    { path: '/genomics', icon: '🧬', label: 'Genomic Profiler' },
    { path: '/adverse-events', icon: '⚠️', label: 'Adverse Events' },
    { path: '/outcomes', icon: '📊', label: 'Outcomes Tracker' },
    { path: '/population', icon: '🌍', label: 'Population Simulator' },
    { path: '/wizard', icon: '📝', label: 'Patient Wizard' },
    { path: '/multi-omics', icon: '🧬', label: 'Multi-Omics Engine' },
    // Enterprise section
    { path: '/admin', icon: '🛡️', label: 'Admin Dashboard', section: 'Enterprise' },
    { path: '/mfa', icon: '🔐', label: 'MFA Security' },
    { path: '/billing', icon: '💳', label: 'Billing & Plans' },
    { path: '/organizations', icon: '🏢', label: 'Organizations' },
];

function getInitialTheme(): 'dark' | 'light' {
    const stored = localStorage.getItem('carvanta-theme');
    if (stored === 'light' || stored === 'dark') return stored;
    return 'dark'; // Default
}

export default function Layout({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = useState<'dark' | 'light'>(getInitialTheme);
    const { user, logout } = useAuth();

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('carvanta-theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const initials = user?.full_name?.split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase() || '??';

    return (
        <div className="app-layout">
            <aside className="sidebar">
                <div className="sidebar-brand">
                    <h1>◆ CARVanta</h1>
                    <p>AI-Augmented Biomarker Intelligence Platform · v5 Adaptive Scoring</p>
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
                <button className="theme-toggle" onClick={toggleTheme} title="Toggle theme">
                    <span className="theme-toggle-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
                    {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                </button>
                {user && (
                    <div className="user-menu">
                        <div className="user-avatar">{initials}</div>
                        <div className="user-info">
                            <div className="user-name">{user.full_name}</div>
                            <div className="user-role">{user.role}</div>
                        </div>
                        <button className="user-logout" onClick={logout} title="Sign out">🚪</button>
                    </div>
                )}
                <div className="sidebar-footer">
                    <div>CARVanta v5 · Enterprise Edition</div>
                    <div>© CARVanta — carvanta.ai</div>
                </div>
            </aside>
            <main className="main-content">
                {children}
                <SnapshotButton />
            </main>
        </div>
    );
}

