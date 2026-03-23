import '../styles/auth.css';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
    const { user, updateProfile, logout } = useAuth();
    const [editing, setEditing] = useState(false);
    const [fullName, setFullName] = useState(user?.full_name || '');
    const [bio, setBio] = useState((user as any)?.bio || '');
    const [institution, setInstitution] = useState(user?.institution || '');
    const [saving, setSaving] = useState(false);
    const [msg, setMsg] = useState('');

    if (!user) return null;

    const initials = user.full_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

    const handleSave = async () => {
        setSaving(true); setMsg('');
        try {
            await updateProfile({ full_name: fullName, bio, institution });
            setMsg('Profile updated!');
            setEditing(false);
        } catch (e: any) { setMsg(e.message); }
        finally { setSaving(false); }
    };

    return (
        <div className="profile-page">
            <h1 style={{ marginBottom: 24 }}>👤 My Profile</h1>

            <div className="profile-header">
                <div className="profile-avatar-large">{initials}</div>
                <div className="profile-info">
                    <h2>{user.full_name}</h2>
                    <p>@{user.username} · {user.role} {user.institution ? `at ${user.institution}` : ''}</p>
                    <p style={{ color: '#6366f1', fontSize: 12, marginTop: 4 }}>{user.email}</p>
                </div>
            </div>

            <div className="profile-stats">
                <div className="profile-stat">
                    <div className="profile-stat-value">{user.total_analyses}</div>
                    <div className="profile-stat-label">Analyses</div>
                </div>
                <div className="profile-stat">
                    <div className="profile-stat-value">{user.login_count}</div>
                    <div className="profile-stat-label">Logins</div>
                </div>
                <div className="profile-stat">
                    <div className="profile-stat-value" style={{ textTransform: 'capitalize' }}>{user.role}</div>
                    <div className="profile-stat-label">Role</div>
                </div>
                <div className="profile-stat">
                    <div className="profile-stat-value">🟢</div>
                    <div className="profile-stat-label">Status</div>
                </div>
            </div>

            <div className="profile-form">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3>Account Settings</h3>
                    {!editing && (
                        <button className="btn btn-sm" style={{ background: '#6366f1', border: 'none', color: 'white', padding: '8px 16px', borderRadius: 8, cursor: 'pointer' }} onClick={() => setEditing(true)}>
                            ✏️ Edit
                        </button>
                    )}
                </div>

                {msg && <div style={{ color: msg.includes('updated') ? '#10b981' : '#f87171', marginBottom: 12, fontSize: 13 }}>{msg}</div>}

                <div className="auth-form" style={{ gap: 14 }}>
                    <div className="auth-field">
                        <label>Full Name</label>
                        <input value={fullName} onChange={e => setFullName(e.target.value)} disabled={!editing} />
                    </div>
                    <div className="auth-field">
                        <label>Bio</label>
                        <input value={bio} onChange={e => setBio(e.target.value)} disabled={!editing} placeholder="Tell us about your research..." />
                    </div>
                    <div className="auth-field">
                        <label>Institution</label>
                        <input value={institution} onChange={e => setInstitution(e.target.value)} disabled={!editing} placeholder="University, Hospital, Lab..." />
                    </div>

                    {editing && (
                        <div style={{ display: 'flex', gap: 12 }}>
                            <button className="auth-submit" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
                                {saving ? '⏳ Saving...' : '💾 Save Changes'}
                            </button>
                            <button style={{ flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', borderRadius: 12, padding: 14, cursor: 'pointer' }} onClick={() => setEditing(false)}>
                                Cancel
                            </button>
                        </div>
                    )}
                </div>
            </div>

            <div style={{ marginTop: 24, textAlign: 'center' }}>
                <button onClick={logout} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171', padding: '12px 32px', borderRadius: 12, cursor: 'pointer', fontSize: 14, fontWeight: 600 }}>
                    🚪 Sign Out
                </button>
            </div>
        </div>
    );
}
