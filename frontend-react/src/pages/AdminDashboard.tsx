import React, { useState, useEffect } from 'react';
import '../styles/enterprise.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface PlatformHealth {
  status: string;
  uptime_percentage: number;
  metrics: {
    api_calls_today: number;
    errors_last_hour: number;
    active_users_24h: number;
    total_users: number;
    avg_response_ms: number;
    p95_response_ms: number;
  };
}

interface AuditStats {
  total_requests: number;
  today_requests: number;
  avg_latency_ms: number;
  error_rate: number;
  suspicious_events: number;
  unique_ips: number;
  severity_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  top_endpoints: Array<{ path: string; count: number }>;
  recent_alerts: Array<{
    id: number;
    timestamp: string;
    alert_type: string;
    severity: string;
    source_ip: string;
    details: string;
    is_resolved: number;
  }>;
}

interface ComplianceDashboard {
  overview: {
    total_users: number;
    verified_users: number;
    verification_rate: number;
    hipaa_enabled: boolean;
  };
  consent_stats: Record<string, { granted: number; rate: number }>;
  phi_access: { events_today: number };
  deletion_requests: { pending: number };
  baa: { active_agreements: number };
  audit_integrity: {
    chain_valid: boolean;
    integrity_score: number;
    total_entries: number;
  };
}

interface ChainIntegrity {
  chain_valid: boolean;
  integrity_score: number;
  total_entries: number;
  valid_entries: number;
  tampered_entries: number;
  broken_chain_links: number;
  verdict: string;
}

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'compliance' | 'security'>('overview');
  const [health, setHealth] = useState<PlatformHealth | null>(null);
  const [auditStats, setAuditStats] = useState<AuditStats | null>(null);
  const [compliance, setCompliance] = useState<ComplianceDashboard | null>(null);
  const [chainIntegrity, setChainIntegrity] = useState<ChainIntegrity | null>(null);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [healthRes, auditRes, complianceRes, integrityRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/v5/enterprise/analytics/health`, { headers }),
        fetch(`${API_BASE}/audit/stats`),
        fetch(`${API_BASE}/api/v5/enterprise/compliance/dashboard`, { headers }),
        fetch(`${API_BASE}/api/v5/enterprise/compliance/integrity`, { headers }),
      ]);

      if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
        setHealth(await healthRes.value.json());
      }
      if (auditRes.status === 'fulfilled' && auditRes.value.ok) {
        setAuditStats(await auditRes.value.json());
      }
      if (complianceRes.status === 'fulfilled' && complianceRes.value.ok) {
        setCompliance(await complianceRes.value.json());
      }
      if (integrityRes.status === 'fulfilled' && integrityRes.value.ok) {
        setChainIntegrity(await integrityRes.value.json());
      }
    } catch (e) { console.error('Dashboard fetch error:', e); }
    setLoading(false);
  };

  const getStatusColor = (status: string) => {
    if (status === 'healthy') return 'var(--color-success)';
    if (status === 'degraded') return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  return (
    <div className="enterprise-page">
      <div className="enterprise-header">
        <div className="enterprise-header-content">
          <div className="enterprise-icon">🛡️</div>
          <div>
            <h1>Enterprise Admin Dashboard</h1>
            <p>Platform health, security monitoring, compliance & audit trail</p>
          </div>
        </div>
        <button className="enterprise-refresh-btn" onClick={fetchDashboardData}>
          ↻ Refresh
        </button>
      </div>

      <div className="enterprise-tabs">
        {(['overview', 'audit', 'compliance', 'security'] as const).map(tab => (
          <button
            key={tab}
            className={`enterprise-tab ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'overview' ? '📊 Overview' :
             tab === 'audit' ? '📋 Audit Trail' :
             tab === 'compliance' ? '🔒 Compliance' : '🚨 Security'}
          </button>
        ))}
      </div>

      {loading && <div className="enterprise-loading"><div className="spinner" /> Loading dashboard data...</div>}

      {!loading && activeTab === 'overview' && (
        <div className="enterprise-content">
          {/* Platform Health */}
          <div className="enterprise-stats-grid">
            <div className="enterprise-stat-card highlight">
              <div className="stat-icon" style={{ color: getStatusColor(health?.status || 'unknown') }}>●</div>
              <div className="stat-info">
                <span className="stat-label">Platform Status</span>
                <span className="stat-value" style={{ color: getStatusColor(health?.status || 'unknown') }}>
                  {health?.status?.toUpperCase() || 'LOADING'}
                </span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">📈</div>
              <div className="stat-info">
                <span className="stat-label">Uptime</span>
                <span className="stat-value">{health?.uptime_percentage || 0}%</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-info">
                <span className="stat-label">API Calls Today</span>
                <span className="stat-value">{health?.metrics?.api_calls_today?.toLocaleString() || 0}</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">👥</div>
              <div className="stat-info">
                <span className="stat-label">Active Users (24h)</span>
                <span className="stat-value">{health?.metrics?.active_users_24h || 0}</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">⏱️</div>
              <div className="stat-info">
                <span className="stat-label">Avg Response</span>
                <span className="stat-value">{health?.metrics?.avg_response_ms || 0}ms</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">🚨</div>
              <div className="stat-info">
                <span className="stat-label">Errors (1h)</span>
                <span className="stat-value danger">{health?.metrics?.errors_last_hour || 0}</span>
              </div>
            </div>
          </div>

          {/* Audit Summary */}
          {auditStats && (
            <div className="enterprise-card">
              <h3>Audit Trail Summary</h3>
              <div className="enterprise-metrics-row">
                <div className="metric"><span className="metric-value">{auditStats.total_requests?.toLocaleString()}</span><span className="metric-label">Total Entries</span></div>
                <div className="metric"><span className="metric-value">{auditStats.today_requests?.toLocaleString()}</span><span className="metric-label">Today</span></div>
                <div className="metric"><span className="metric-value">{auditStats.avg_latency_ms}ms</span><span className="metric-label">Avg Latency</span></div>
                <div className="metric"><span className="metric-value danger">{auditStats.error_rate}%</span><span className="metric-label">Error Rate</span></div>
                <div className="metric"><span className="metric-value warning">{auditStats.suspicious_events}</span><span className="metric-label">Suspicious</span></div>
              </div>
            </div>
          )}

          {/* Chain Integrity */}
          {chainIntegrity && (
            <div className={`enterprise-card ${chainIntegrity.chain_valid ? 'integrity-valid' : 'integrity-invalid'}`}>
              <h3>🔗 Audit Chain Integrity</h3>
              <div className="integrity-badge">
                <span className={`verdict ${chainIntegrity.chain_valid ? 'intact' : 'compromised'}`}>
                  {chainIntegrity.verdict}
                </span>
                <span className="integrity-score">{chainIntegrity.integrity_score}%</span>
              </div>
              <div className="enterprise-metrics-row">
                <div className="metric"><span className="metric-value">{chainIntegrity.total_entries}</span><span className="metric-label">Total Entries</span></div>
                <div className="metric"><span className="metric-value success">{chainIntegrity.valid_entries}</span><span className="metric-label">Valid</span></div>
                <div className="metric"><span className="metric-value danger">{chainIntegrity.tampered_entries}</span><span className="metric-label">Tampered</span></div>
                <div className="metric"><span className="metric-value warning">{chainIntegrity.broken_chain_links}</span><span className="metric-label">Broken Links</span></div>
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && activeTab === 'audit' && auditStats && (
        <div className="enterprise-content">
          <div className="enterprise-card">
            <h3>📋 Top Endpoints</h3>
            <div className="enterprise-table">
              <table>
                <thead><tr><th>Endpoint</th><th>Requests</th><th>Share</th></tr></thead>
                <tbody>
                  {auditStats.top_endpoints?.map((ep, i) => (
                    <tr key={i}>
                      <td className="endpoint-path">{ep.path}</td>
                      <td>{ep.count.toLocaleString()}</td>
                      <td>
                        <div className="progress-bar">
                          <div className="progress-fill" style={{ width: `${Math.min(100, (ep.count / (auditStats.top_endpoints[0]?.count || 1)) * 100)}%` }} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="enterprise-two-col">
            <div className="enterprise-card">
              <h3>Severity Breakdown</h3>
              {Object.entries(auditStats.severity_breakdown || {}).map(([sev, count]) => (
                <div key={sev} className="breakdown-item">
                  <span className={`severity-badge ${sev}`}>{sev}</span>
                  <span className="breakdown-count">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
            <div className="enterprise-card">
              <h3>Category Breakdown</h3>
              {Object.entries(auditStats.category_breakdown || {}).slice(0, 8).map(([cat, count]) => (
                <div key={cat} className="breakdown-item">
                  <span className="category-name">{cat.replace(/_/g, ' ')}</span>
                  <span className="breakdown-count">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!loading && activeTab === 'compliance' && compliance && (
        <div className="enterprise-content">
          <div className="enterprise-stats-grid">
            <div className="enterprise-stat-card">
              <div className="stat-icon">👤</div>
              <div className="stat-info">
                <span className="stat-label">Total Users</span>
                <span className="stat-value">{compliance.overview.total_users}</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-info">
                <span className="stat-label">Verified Users</span>
                <span className="stat-value">{compliance.overview.verified_users}</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-info">
                <span className="stat-label">Verification Rate</span>
                <span className="stat-value">{compliance.overview.verification_rate}%</span>
              </div>
            </div>
            <div className="enterprise-stat-card">
              <div className="stat-icon">{compliance.overview.hipaa_enabled ? '🟢' : '🔴'}</div>
              <div className="stat-info">
                <span className="stat-label">HIPAA Mode</span>
                <span className="stat-value">{compliance.overview.hipaa_enabled ? 'ENABLED' : 'DISABLED'}</span>
              </div>
            </div>
          </div>
          <div className="enterprise-two-col">
            <div className="enterprise-card">
              <h3>🔐 Consent Status</h3>
              {Object.entries(compliance.consent_stats || {}).map(([type, data]) => (
                <div key={type} className="consent-item">
                  <span className="consent-type">{type.replace(/_/g, ' ')}</span>
                  <div className="consent-bar-container">
                    <div className="consent-bar" style={{ width: `${data.rate}%` }} />
                    <span className="consent-rate">{data.rate}%</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="enterprise-card">
              <h3>📊 Compliance Metrics</h3>
              <div className="compliance-metric"><span>PHI Access Events Today</span><span className="metric-number">{compliance.phi_access.events_today}</span></div>
              <div className="compliance-metric"><span>Pending Deletion Requests</span><span className="metric-number warning">{compliance.deletion_requests.pending}</span></div>
              <div className="compliance-metric"><span>Active BAA Agreements</span><span className="metric-number">{compliance.baa.active_agreements}</span></div>
              <div className="compliance-metric"><span>Audit Integrity Score</span><span className="metric-number success">{compliance.audit_integrity?.integrity_score || 0}%</span></div>
            </div>
          </div>
        </div>
      )}

      {!loading && activeTab === 'security' && (
        <div className="enterprise-content">
          <div className="enterprise-card">
            <h3>🚨 Recent Security Alerts</h3>
            {auditStats?.recent_alerts && auditStats.recent_alerts.length > 0 ? (
              <div className="enterprise-table">
                <table>
                  <thead><tr><th>Time</th><th>Type</th><th>Severity</th><th>Source IP</th><th>Details</th><th>Status</th></tr></thead>
                  <tbody>
                    {auditStats.recent_alerts.map((alert, i) => (
                      <tr key={i}>
                        <td className="timestamp">{new Date(alert.timestamp).toLocaleString()}</td>
                        <td>{alert.alert_type?.replace(/_/g, ' ')}</td>
                        <td><span className={`severity-badge ${alert.severity}`}>{alert.severity}</span></td>
                        <td className="mono">{alert.source_ip}</td>
                        <td>{alert.details}</td>
                        <td><span className={`status-badge ${alert.is_resolved ? 'resolved' : 'active'}`}>{alert.is_resolved ? 'Resolved' : 'Active'}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">✅</div>
                <p>No security alerts detected. All systems nominal.</p>
              </div>
            )}
          </div>
          <div className="enterprise-card">
            <h3>🔍 Security Overview</h3>
            <div className="enterprise-metrics-row">
              <div className="metric"><span className="metric-value">{auditStats?.unique_ips || 0}</span><span className="metric-label">Unique IPs</span></div>
              <div className="metric"><span className="metric-value warning">{auditStats?.suspicious_events || 0}</span><span className="metric-label">Suspicious Events</span></div>
              <div className="metric"><span className="metric-value danger">{auditStats?.error_rate || 0}%</span><span className="metric-label">Error Rate</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
