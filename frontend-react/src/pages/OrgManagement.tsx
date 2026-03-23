import React, { useState, useEffect } from 'react';
import '../styles/enterprise.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface Organization {
  id: number;
  name: string;
  slug: string;
  role: string;
  member_count: number;
  plan_tier: string;
  joined_at: string;
}

interface OrgDetails {
  id: number;
  name: string;
  slug: string;
  description: string;
  logo_url: string | null;
  website: string | null;
  owner_id: number;
  plan_tier: string;
  member_count: number;
  max_members: number;
  total_analyses: number;
  industry: string;
  country: string;
  is_active: boolean;
  created_at: string;
}

interface Member {
  user_id: number;
  email: string;
  username: string;
  full_name: string;
  role: string;
  avatar_url: string | null;
  joined_at: string;
  last_active_at: string | null;
}

interface PendingInvite {
  email: string;
  role: string;
  expires_at: string;
}

const OrgManagement: React.FC = () => {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<OrgDetails | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const [activeTab, setActiveTab] = useState<'list' | 'detail' | 'create'>('list');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState({ type: '', text: '' });

  // Create form
  const [newOrg, setNewOrg] = useState({ name: '', description: '', industry: '', country: '' });

  // Invite form
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviteMessage, setInviteMessage] = useState('');

  const token = localStorage.getItem('token');
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/org/mine`, { headers });
      if (res.ok) {
        const data = await res.json();
        setOrganizations(data.organizations || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const selectOrg = async (orgId: number) => {
    try {
      const [detailRes, membersRes] = await Promise.all([
        fetch(`${API_BASE}/api/v5/enterprise/org/${orgId}`, { headers }),
        fetch(`${API_BASE}/api/v5/enterprise/org/${orgId}/members`, { headers }),
      ]);

      if (detailRes.ok) setSelectedOrg(await detailRes.json());
      if (membersRes.ok) {
        const data = await membersRes.json();
        setMembers(data.members || []);
        setPendingInvites(data.pending_invites || []);
      }
      setActiveTab('detail');
    } catch (e) { console.error(e); }
  };

  const createOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrg.name.trim()) {
      setMessage({ type: 'error', text: 'Organization name is required' });
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/org/create`, {
        method: 'POST', headers,
        body: JSON.stringify(newOrg),
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: data.message || 'Organization created!' });
        setNewOrg({ name: '', description: '', industry: '', country: '' });
        setActiveTab('list');
        fetchOrganizations();
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to create organization' }); }
  };

  const sendInvite = async () => {
    if (!inviteEmail || !selectedOrg) return;
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/org/${selectedOrg.id}/invite`, {
        method: 'POST', headers,
        body: JSON.stringify({ email: inviteEmail, role: inviteRole, message: inviteMessage }),
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: `Invitation sent to ${inviteEmail}` });
        setInviteEmail('');
        setInviteMessage('');
        selectOrg(selectedOrg.id);
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to send invite' }); }
  };

  const updateRole = async (userId: number, newRole: string) => {
    if (!selectedOrg) return;
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/org/${selectedOrg.id}/role`, {
        method: 'PUT', headers,
        body: JSON.stringify({ user_id: userId, role: newRole }),
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: 'Role updated' });
        selectOrg(selectedOrg.id);
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to update role' }); }
  };

  const removeMember = async (userId: number) => {
    if (!selectedOrg || !confirm('Remove this member from the organization?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/org/${selectedOrg.id}/member/${userId}`, {
        method: 'DELETE', headers,
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: 'Member removed' });
        selectOrg(selectedOrg.id);
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to remove member' }); }
  };

  const roleColors: Record<string, string> = {
    owner: '#f59e0b',
    admin: '#6366f1',
    member: '#10b981',
    viewer: '#64748b',
  };

  return (
    <div className="enterprise-page">
      <div className="enterprise-header">
        <div className="enterprise-header-content">
          <div className="enterprise-icon">🏢</div>
          <div>
            <h1>Organization Management</h1>
            <p>Create and manage your teams, roles, and workspaces</p>
          </div>
        </div>
        <div className="enterprise-header-actions">
          <button className="btn-secondary" onClick={() => { setActiveTab('list'); fetchOrganizations(); }}>
            My Organizations
          </button>
          <button className="btn-primary" onClick={() => setActiveTab('create')}>
            + New Organization
          </button>
        </div>
      </div>

      {message.text && (
        <div className={`enterprise-alert ${message.type}`}>{message.text}</div>
      )}

      {loading && <div className="enterprise-loading"><div className="spinner" /> Loading...</div>}

      {/* Organization List */}
      {!loading && activeTab === 'list' && (
        <div className="enterprise-content">
          {organizations.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🏢</div>
              <h3>No Organizations Yet</h3>
              <p>Create your first organization to start collaborating with your team.</p>
              <button className="btn-primary" onClick={() => setActiveTab('create')}>
                + Create Organization
              </button>
            </div>
          ) : (
            <div className="org-grid">
              {organizations.map(org => (
                <div key={org.id} className="org-card" onClick={() => selectOrg(org.id)}>
                  <div className="org-card-header">
                    <div className="org-avatar">{org.name.charAt(0).toUpperCase()}</div>
                    <div>
                      <h3>{org.name}</h3>
                      <span className="org-slug">/{org.slug}</span>
                    </div>
                  </div>
                  <div className="org-card-meta">
                    <span className="org-role" style={{ color: roleColors[org.role] }}>{org.role}</span>
                    <span>{org.member_count} members</span>
                    <span className="org-plan">{org.plan_tier}</span>
                  </div>
                  <span className="org-joined">Joined {new Date(org.joined_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Create Organization */}
      {activeTab === 'create' && (
        <div className="enterprise-content">
          <div className="enterprise-card" style={{ maxWidth: '600px', margin: '0 auto' }}>
            <h3>Create New Organization</h3>
            <form onSubmit={createOrg} className="org-form">
              <div className="form-group">
                <label>Organization Name *</label>
                <input
                  type="text"
                  value={newOrg.name}
                  onChange={e => setNewOrg({ ...newOrg, name: e.target.value })}
                  placeholder="e.g., Acme Research Lab"
                  required
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newOrg.description}
                  onChange={e => setNewOrg({ ...newOrg, description: e.target.value })}
                  placeholder="Brief description of your organization"
                  rows={3}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Industry</label>
                  <select value={newOrg.industry} onChange={e => setNewOrg({ ...newOrg, industry: e.target.value })}>
                    <option value="">Select</option>
                    <option value="biotech">Biotech</option>
                    <option value="pharma">Pharmaceutical</option>
                    <option value="hospital">Hospital / Healthcare</option>
                    <option value="research">Research Institute</option>
                    <option value="university">University</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Country</label>
                  <input
                    type="text"
                    value={newOrg.country}
                    onChange={e => setNewOrg({ ...newOrg, country: e.target.value })}
                    placeholder="e.g., United States"
                  />
                </div>
              </div>
              <div className="form-actions">
                <button type="button" className="btn-ghost" onClick={() => setActiveTab('list')}>Cancel</button>
                <button type="submit" className="btn-primary">Create Organization</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Organization Detail */}
      {activeTab === 'detail' && selectedOrg && (
        <div className="enterprise-content">
          <button className="btn-ghost back-btn" onClick={() => setActiveTab('list')}>
            ← Back to Organizations
          </button>

          <div className="org-detail-header">
            <div className="org-avatar large">{selectedOrg.name.charAt(0).toUpperCase()}</div>
            <div>
              <h2>{selectedOrg.name}</h2>
              <p className="org-slug">/{selectedOrg.slug}</p>
              {selectedOrg.description && <p>{selectedOrg.description}</p>}
            </div>
            <div className="org-detail-stats">
              <div className="org-stat"><span className="stat-num">{selectedOrg.member_count}</span><span>Members</span></div>
              <div className="org-stat"><span className="stat-num">{selectedOrg.max_members}</span><span>Max</span></div>
              <div className="org-stat"><span className="stat-num">{selectedOrg.total_analyses}</span><span>Analyses</span></div>
            </div>
          </div>

          {/* Members */}
          <div className="enterprise-card">
            <h3>👥 Members ({members.length})</h3>
            <div className="members-list">
              {members.map(member => (
                <div key={member.user_id} className="member-row">
                  <div className="member-info">
                    <div className="member-avatar">
                      {member.avatar_url
                        ? <img src={member.avatar_url} alt="" />
                        : member.full_name?.charAt(0) || member.username?.charAt(0) || '?'
                      }
                    </div>
                    <div>
                      <span className="member-name">{member.full_name || member.username}</span>
                      <span className="member-email">{member.email}</span>
                    </div>
                  </div>
                  <div className="member-actions">
                    <span className="role-badge" style={{ borderColor: roleColors[member.role] }}>
                      {member.role}
                    </span>
                    {member.role !== 'owner' && (
                      <>
                        <select
                          value={member.role}
                          onChange={e => updateRole(member.user_id, e.target.value)}
                          className="role-select"
                        >
                          <option value="viewer">Viewer</option>
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                        </select>
                        <button className="btn-icon danger" onClick={() => removeMember(member.user_id)} title="Remove member">
                          ✕
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pending Invites */}
            {pendingInvites.length > 0 && (
              <div className="pending-invites">
                <h4>Pending Invitations</h4>
                {pendingInvites.map((inv, i) => (
                  <div key={i} className="invite-row">
                    <span className="invite-email">{inv.email}</span>
                    <span className="role-badge">{inv.role}</span>
                    <span className="invite-expires">Expires {new Date(inv.expires_at).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Invite Form */}
            <div className="invite-form">
              <h4>Invite New Member</h4>
              <div className="invite-row-input">
                <input
                  type="email"
                  placeholder="email@example.com"
                  value={inviteEmail}
                  onChange={e => setInviteEmail(e.target.value)}
                />
                <select value={inviteRole} onChange={e => setInviteRole(e.target.value)}>
                  <option value="viewer">Viewer</option>
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
                <button className="btn-primary" onClick={sendInvite} disabled={!inviteEmail}>
                  Send Invite
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrgManagement;
