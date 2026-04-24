import React, { useState, useEffect } from 'react';

interface Project {
  project_id: string;
  title: string;
  description: string;
  status: string;
  members: number;
  experiments: number;
  created_at: string;
}

interface TeamMember {
  user_id: string;
  role: string;
  productivity_score: number;
  experiments_completed: number;
  publications_contributed: number;
  last_active_days_ago: number;
}

interface Notification {
  notification_id: string;
  type: string;
  icon: string;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  priority: string;
}

const API = '/api/v5/collab';

const CollaborationDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [projects, setProjects] = useState<Project[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [glossary, setGlossary] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [impact, setImpact] = useState<any>(null);
  const [funding, setFunding] = useState<any>(null);
  const [compliance, setCompliance] = useState<any>(null);
  const [reproducibility, setReproducibility] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [glossarySearch, setGlossarySearch] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [projRes, teamRes, impactRes, fundingRes, complianceRes, reproRes] = await Promise.allSettled([
        fetch(`${API}/projects`).then(r => r.json()),
        fetch(`${API}/analytics/productivity`).then(r => r.json()),
        fetch(`${API}/analytics/impact`).then(r => r.json()),
        fetch(`${API}/analytics/funding`).then(r => r.json()),
        fetch(`${API}/audit/compliance/FDA_21CFR11`).then(r => r.json()),
        fetch(`${API}/reproducibility/score`).then(r => r.json()),
      ]);
      if (projRes.status === 'fulfilled') setProjects(projRes.value.projects || []);
      if (teamRes.status === 'fulfilled') { setTeam(teamRes.value.members || []); setAnalytics(teamRes.value); }
      if (impactRes.status === 'fulfilled') setImpact(impactRes.value);
      if (fundingRes.status === 'fulfilled') setFunding(fundingRes.value);
      if (complianceRes.status === 'fulfilled') setCompliance(complianceRes.value);
      if (reproRes.status === 'fulfilled') setReproducibility(reproRes.value);
    } catch (e) { console.error('Dashboard load error', e); }
    setLoading(false);
  };

  const loadGlossary = async (q?: string) => {
    try {
      const params = q ? `?query=${encodeURIComponent(q)}` : '';
      const res = await fetch(`${API}/knowledge/glossary${params}`);
      const data = await res.json();
      setGlossary(data.results || []);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { if (activeTab === 'knowledge') loadGlossary(); }, [activeTab]);

  const tabs = [
    { id: 'overview', label: '📊 Overview', icon: '📊' },
    { id: 'team', label: '👥 Team', icon: '👥' },
    { id: 'projects', label: '📁 Projects', icon: '📁' },
    { id: 'impact', label: '📈 Impact', icon: '📈' },
    { id: 'funding', label: '💰 Funding', icon: '💰' },
    { id: 'compliance', label: '🔒 Compliance', icon: '🔒' },
    { id: 'workflows', label: '⚙️ Workflows', icon: '⚙️' },
    { id: 'knowledge', label: '📚 Knowledge', icon: '📚' },
    { id: 'reproducibility', label: '🔬 Rigor', icon: '🔬' },
    { id: 'inventory', label: '🧪 Inventory', icon: '🧪' },
    { id: 'training', label: '🎓 Training', icon: '🎓' },
    { id: 'ethics', label: '⚖️ Ethics', icon: '⚖️' },
    { id: 'sites', label: '🌐 Sites', icon: '🌐' },
    { id: 'publications', label: '📝 Pubs', icon: '📝' },
  ];

  const cardStyle: React.CSSProperties = {
    background: 'linear-gradient(135deg, rgba(30,30,45,0.9), rgba(20,20,35,0.95))',
    borderRadius: 12, border: '1px solid rgba(100,100,200,0.15)',
    padding: 20, marginBottom: 16,
  };

  const metricCardStyle: React.CSSProperties = {
    ...cardStyle, textAlign: 'center' as const, flex: 1, minWidth: 150,
  };

  const renderOverview = () => (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        {[
          { label: 'Projects', value: projects.length || analytics?.team_size || 0, color: '#4CAF50' },
          { label: 'Team Members', value: analytics?.team_size || 0, color: '#2196F3' },
          { label: 'Experiments', value: analytics?.team_summary?.total_experiments || 0, color: '#FF9800' },
          { label: 'Publications', value: impact?.publications?.total || 0, color: '#E91E63' },
          { label: 'Datasets', value: impact?.dataset_impact?.total_datasets_shared || 0, color: '#9C27B0' },
          { label: 'Active Grants', value: funding?.active_grants || 0, color: '#00BCD4' },
        ].map((m, i) => (
          <div key={i} style={metricCardStyle}>
            <div style={{ fontSize: 28, fontWeight: 700, color: m.color }}>{m.value}</div>
            <div style={{ fontSize: 12, color: '#aaa', marginTop: 4 }}>{m.label}</div>
          </div>
        ))}
      </div>
      <div style={cardStyle}>
        <h3 style={{ color: '#8be9fd', margin: '0 0 12px' }}>📊 Research Velocity</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          <div><span style={{ color: '#aaa' }}>Experiments/Week:</span> <b style={{ color: '#50fa7b' }}>{analytics?.velocity?.experiments_per_week || '—'}</b></div>
          <div><span style={{ color: '#aaa' }}>Datasets/Month:</span> <b style={{ color: '#50fa7b' }}>{analytics?.velocity?.datasets_per_month || '—'}</b></div>
          <div><span style={{ color: '#aaa' }}>Avg Productivity:</span> <b style={{ color: '#50fa7b' }}>{analytics?.team_summary?.avg_productivity_score || '—'}</b></div>
        </div>
      </div>
      {compliance && (
        <div style={cardStyle}>
          <h3 style={{ color: '#8be9fd', margin: '0 0 12px' }}>🔒 FDA 21 CFR Part 11 Compliance</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ fontSize: 32, fontWeight: 700, color: compliance.compliant ? '#50fa7b' : '#ff5555' }}>
              {compliance.compliance_pct}%
            </div>
            <div>
              <div style={{ color: '#aaa' }}>{compliance.requirements_met}/{compliance.requirements_total} requirements met</div>
              <div style={{ color: compliance.compliant ? '#50fa7b' : '#ffb86c', fontSize: 12, marginTop: 4 }}>
                {compliance.compliant ? '✅ Compliant' : '⚠️ Action needed'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTeam = () => (
    <div>
      <h3 style={{ color: '#8be9fd' }}>👥 Team Productivity ({analytics?.period_days || 90} days)</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(100,100,200,0.2)' }}>
              {['Member', 'Role', 'Score', 'Experiments', 'Pubs', 'Last Active'].map(h => (
                <th key={h} style={{ padding: '8px 12px', color: '#bd93f9', textAlign: 'left', fontSize: 12 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {team.map((m, i) => (
              <tr key={i} style={{ borderBottom: '1px solid rgba(100,100,200,0.1)' }}>
                <td style={{ padding: '8px 12px', color: '#f8f8f2' }}>{m.user_id}</td>
                <td style={{ padding: '8px 12px', color: '#aaa' }}>{m.role}</td>
                <td style={{ padding: '8px 12px' }}>
                  <span style={{ color: m.productivity_score > 50 ? '#50fa7b' : m.productivity_score > 20 ? '#ffb86c' : '#ff5555', fontWeight: 600 }}>
                    {m.productivity_score}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', color: '#f8f8f2' }}>{m.experiments_completed}</td>
                <td style={{ padding: '8px 12px', color: '#f8f8f2' }}>{m.publications_contributed}</td>
                <td style={{ padding: '8px 12px', color: m.last_active_days_ago < 7 ? '#50fa7b' : '#aaa' }}>
                  {m.last_active_days_ago === 0 ? 'Today' : `${m.last_active_days_ago}d ago`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderImpact = () => {
    if (!impact) return <div style={{ color: '#aaa' }}>Loading impact data...</div>;
    return (
      <div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
          {[
            { label: 'Total Citations', value: impact.citation_metrics?.total_citations, color: '#FF9800' },
            { label: 'h-index', value: impact.citation_metrics?.h_index, color: '#4CAF50' },
            { label: 'i10-index', value: impact.citation_metrics?.i10_index, color: '#2196F3' },
            { label: 'Dataset Downloads', value: impact.dataset_impact?.total_downloads, color: '#9C27B0' },
            { label: 'Reproducibility', value: `${impact.experiment_impact?.reproducibility_rate_pct}%`, color: '#00BCD4' },
          ].map((m, i) => (
            <div key={i} style={metricCardStyle}>
              <div style={{ fontSize: 24, fontWeight: 700, color: m.color }}>{m.value}</div>
              <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>{m.label}</div>
            </div>
          ))}
        </div>
        <div style={cardStyle}>
          <h3 style={{ color: '#8be9fd', margin: '0 0 12px' }}>📝 Publications by Tier</h3>
          {['tier_1', 'tier_2', 'tier_3'].map(tier => {
            const count = impact.publications?.by_tier?.[tier] || 0;
            const max = impact.publications?.total || 1;
            const colors: Record<string,string> = { tier_1: '#FFD700', tier_2: '#C0C0C0', tier_3: '#CD7F32' };
            return (
              <div key={tier} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#aaa' }}>
                  <span>{tier.replace('_', ' ').toUpperCase()}</span><span>{count}</span>
                </div>
                <div style={{ background: 'rgba(100,100,200,0.1)', borderRadius: 4, height: 8, marginTop: 4 }}>
                  <div style={{ background: colors[tier], borderRadius: 4, height: '100%', width: `${(count / max) * 100}%`, transition: 'width 0.5s' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderFunding = () => {
    if (!funding) return <div style={{ color: '#aaa' }}>Loading funding data...</div>;
    return (
      <div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <div style={metricCardStyle}>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#4CAF50' }}>${(funding.total_funding_usd / 1e6).toFixed(1)}M</div>
            <div style={{ fontSize: 11, color: '#aaa' }}>Total Funding</div>
          </div>
          <div style={metricCardStyle}>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#2196F3' }}>{funding.active_grants}</div>
            <div style={{ fontSize: 11, color: '#aaa' }}>Active Grants</div>
          </div>
          <div style={metricCardStyle}>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#FF9800' }}>${(funding.remaining_usd / 1e6).toFixed(1)}M</div>
            <div style={{ fontSize: 11, color: '#aaa' }}>Remaining</div>
          </div>
        </div>
        {funding.grants?.map((g: any, i: number) => (
          <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ color: '#f8f8f2', fontWeight: 600 }}>{g.source}</div>
              <div style={{ color: '#aaa', fontSize: 12 }}>{g.start_year}–{g.end_year} · {g.status}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: '#50fa7b', fontWeight: 600 }}>${(g.amount_usd / 1000).toFixed(0)}K</div>
              <div style={{ color: '#aaa', fontSize: 11 }}>Burn: {g.burn_rate_pct}%</div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderKnowledge = () => (
    <div>
      <div style={{ marginBottom: 16 }}>
        <input
          type="text" placeholder="Search glossary..."
          value={glossarySearch}
          onChange={e => { setGlossarySearch(e.target.value); loadGlossary(e.target.value); }}
          style={{ width: '100%', padding: '10px 16px', borderRadius: 8, border: '1px solid rgba(100,100,200,0.3)',
                   background: 'rgba(30,30,45,0.8)', color: '#f8f8f2', fontSize: 14 }}
        />
      </div>
      {glossary.map((g, i) => (
        <div key={i} style={cardStyle}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h4 style={{ color: '#bd93f9', margin: 0 }}>{g.term}</h4>
            <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10,
                          background: 'rgba(139,233,253,0.15)', color: '#8be9fd' }}>{g.category}</span>
          </div>
          <p style={{ color: '#ccc', fontSize: 13, margin: '0 0 8px', lineHeight: 1.5 }}>{g.definition}</p>
          {g.related?.length > 0 && (
            <div style={{ fontSize: 11, color: '#aaa' }}>
              Related: {g.related.map((r: string, j: number) => (
                <span key={j} style={{ color: '#50fa7b', cursor: 'pointer', marginRight: 8 }}
                      onClick={() => { setGlossarySearch(r); loadGlossary(r); }}>
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
      {glossary.length === 0 && <div style={{ color: '#aaa', textAlign: 'center', padding: 40 }}>No glossary entries found</div>}
    </div>
  );

  const renderReproducibility = () => {
    if (!reproducibility) return <div style={{ color: '#aaa' }}>Loading...</div>;
    const dims = reproducibility.dimensions || {};
    return (
      <div>
        <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
          <div style={metricCardStyle}>
            <div style={{ fontSize: 28, fontWeight: 700,
                         color: reproducibility.overall_score > 70 ? '#50fa7b' : reproducibility.overall_score > 50 ? '#ffb86c' : '#ff5555' }}>
              {reproducibility.overall_score}
            </div>
            <div style={{ fontSize: 11, color: '#aaa' }}>Overall Score</div>
          </div>
          <div style={metricCardStyle}>
            <div style={{ fontSize: 28, fontWeight: 700,
                         color: reproducibility.grade === 'A' ? '#50fa7b' : reproducibility.grade === 'B' ? '#8be9fd' : '#ffb86c' }}>
              {reproducibility.grade}
            </div>
            <div style={{ fontSize: 11, color: '#aaa' }}>Grade</div>
          </div>
        </div>
        {Object.entries(dims).map(([key, dim]: [string, any]) => (
          <div key={key} style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ color: '#bd93f9', fontWeight: 600, textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}</span>
              <span style={{ color: dim.score > 70 ? '#50fa7b' : '#ffb86c', fontWeight: 600 }}>{dim.score}/100</span>
            </div>
            <div style={{ background: 'rgba(100,100,200,0.1)', borderRadius: 4, height: 6 }}>
              <div style={{ background: dim.score > 70 ? '#50fa7b' : dim.score > 50 ? '#ffb86c' : '#ff5555',
                           borderRadius: 4, height: '100%', width: `${dim.score}%`, transition: 'width 0.5s' }} />
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              {Object.entries(dim.factors || {}).map(([f, v]: [string, any]) => (
                <span key={f} style={{ fontSize: 10, padding: '2px 6px', borderRadius: 6,
                      background: v ? 'rgba(80,250,123,0.15)' : 'rgba(255,85,85,0.15)',
                      color: v ? '#50fa7b' : '#ff5555' }}>
                  {v ? '✓' : '✗'} {f.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', color: '#8be9fd' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 16, animation: 'spin 1s linear infinite' }}>⚙️</div>
          <div>Loading Collaboration Hub...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ color: '#f8f8f2', margin: '0 0 4px', fontSize: 26 }}>
          👥 Research Collaboration Hub
        </h1>
        <p style={{ color: '#aaa', margin: 0, fontSize: 13 }}>
          22 engines · 121 endpoints · Analytics, protocols, workflows, inventory, ethics & training
        </p>
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 20, overflowX: 'auto', paddingBottom: 4 }}>
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '8px 14px', borderRadius: 8, border: 'none', cursor: 'pointer', whiteSpace: 'nowrap',
              fontSize: 12, fontWeight: 600, transition: 'all 0.2s',
              background: activeTab === tab.id ? 'linear-gradient(135deg, #bd93f9, #ff79c6)' : 'rgba(100,100,200,0.1)',
              color: activeTab === tab.id ? '#fff' : '#aaa',
            }}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'team' && renderTeam()}
      {activeTab === 'projects' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>📁 Research Projects</h3>
          {projects.length === 0 ? (
            <div style={{ ...cardStyle, textAlign: 'center', color: '#aaa' }}>
              No projects yet. Create your first research project to get started.
            </div>
          ) : projects.map((p, i) => (
            <div key={i} style={cardStyle}>
              <h4 style={{ color: '#f8f8f2', margin: '0 0 4px' }}>{p.title}</h4>
              <p style={{ color: '#aaa', fontSize: 12, margin: 0 }}>{p.description}</p>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'impact' && renderImpact()}
      {activeTab === 'funding' && renderFunding()}
      {activeTab === 'compliance' && compliance && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>🔒 Regulatory Compliance</h3>
          <div style={{ ...cardStyle, marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ color: '#f8f8f2', fontWeight: 600, fontSize: 16 }}>{compliance.regulation_name}</div>
                <div style={{ color: '#aaa', fontSize: 12 }}>Generated: {new Date(compliance.generated_at).toLocaleDateString()}</div>
              </div>
              <div style={{ fontSize: 32, fontWeight: 700, color: compliance.compliant ? '#50fa7b' : '#ff5555' }}>
                {compliance.compliance_pct}%
              </div>
            </div>
          </div>
          {Object.entries(compliance.requirements || {}).map(([key, req]: [string, any]) => (
            <div key={key} style={{ ...cardStyle, borderLeft: `3px solid ${req.met ? '#50fa7b' : '#ff5555'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#f8f8f2', fontSize: 13 }}>{req.description}</span>
                <span style={{ color: req.met ? '#50fa7b' : '#ff5555', fontWeight: 600 }}>{req.met ? '✅ Met' : '❌ Not Met'}</span>
              </div>
              <div style={{ color: '#aaa', fontSize: 11, marginTop: 4 }}>{req.evidence}</div>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'workflows' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>⚙️ Research Workflows</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>Pre-built CAR-T development pipelines with Gantt visualization</p>
          {['cart_development', 'clinical_trial_setup', 'biomarker_discovery'].map(wf => (
            <div key={wf} style={{ ...cardStyle, cursor: 'pointer' }}>
              <div style={{ color: '#bd93f9', fontWeight: 600 }}>{wf.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</div>
              <div style={{ color: '#aaa', fontSize: 12, marginTop: 4 }}>Click to view workflow template details</div>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'knowledge' && renderKnowledge()}
      {activeTab === 'reproducibility' && renderReproducibility()}

      {/* Inventory Tab */}
      {activeTab === 'inventory' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>🧪 Reagent Inventory & Equipment</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>8 CAR-T reagent catalog entries, 6 equipment items with calibration tracking</p>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            {[
              { label: 'Reagent Types', value: 8, color: '#4CAF50' },
              { label: 'Equipment', value: 6, color: '#2196F3' },
              { label: 'Critical Items', value: 5, color: '#FF9800' },
            ].map((m, i) => (
              <div key={i} style={metricCardStyle}>
                <div style={{ fontSize: 24, fontWeight: 700, color: m.color }}>{m.value}</div>
                <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>{m.label}</div>
              </div>
            ))}
          </div>
          {[
            { name: 'Anti-CD3/CD28 Dynabeads', cat: 'activation_reagent', critical: true, step: 'T-cell activation' },
            { name: 'Recombinant Human IL-2', cat: 'cytokine', critical: true, step: 'T-cell expansion' },
            { name: 'CAR Lentiviral Vector (GMP)', cat: 'viral_vector', critical: true, step: 'Transduction' },
            { name: 'CryoStor CS10', cat: 'cryopreservation', critical: true, step: 'Cryopreservation' },
            { name: 'Anti-CD19 PE (HIB19)', cat: 'flow_antibody', critical: false, step: 'Immunophenotyping' },
            { name: 'Anti-CAR Idiotype Ab', cat: 'flow_antibody', critical: true, step: 'CAR detection' },
          ].map((r, i) => (
            <div key={i} style={{ ...cardStyle, borderLeft: `3px solid ${r.critical ? '#ff79c6' : '#6272a4'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ color: '#f8f8f2', fontWeight: 600 }}>{r.name}</div>
                  <div style={{ color: '#aaa', fontSize: 11 }}>{r.cat} · {r.step}</div>
                </div>
                {r.critical && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10, background: 'rgba(255,121,198,0.15)', color: '#ff79c6' }}>Critical</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Training Tab */}
      {activeTab === 'training' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>🎓 Training & Competency</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>8 CAR-T training modules, 7 role-based requirement sets</p>
          {[
            { name: 'GMP Fundamentals', cat: 'regulatory', hours: 8, format: 'Instructor-led', passing: 80 },
            { name: 'Good Clinical Practice (ICH E6 R2)', cat: 'regulatory', hours: 12, format: 'Online', passing: 80 },
            { name: 'BSL-2 Biosafety', cat: 'safety', hours: 4, format: 'Hybrid', passing: 90 },
            { name: 'CAR-T Manufacturing Operations', cat: 'technical', hours: 40, format: 'Hands-on', passing: 85 },
            { name: 'Flow Cytometry for CAR-T', cat: 'technical', hours: 16, format: 'Hybrid', passing: 80 },
            { name: 'CRS & ICANS Management', cat: 'clinical', hours: 6, format: 'Instructor-led', passing: 90 },
            { name: 'Clinical Data Management', cat: 'data', hours: 8, format: 'Online', passing: 80 },
            { name: 'HIPAA Privacy & Security', cat: 'regulatory', hours: 2, format: 'Online', passing: 80 },
          ].map((t, i) => (
            <div key={i} style={cardStyle}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ color: '#f8f8f2', fontWeight: 600 }}>{t.name}</div>
                  <div style={{ color: '#aaa', fontSize: 11 }}>{t.format} · {t.hours}h · Pass: {t.passing}%</div>
                </div>
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10,
                  background: t.cat === 'regulatory' ? 'rgba(139,233,253,0.15)' : t.cat === 'technical' ? 'rgba(80,250,123,0.15)' : 'rgba(189,147,249,0.15)',
                  color: t.cat === 'regulatory' ? '#8be9fd' : t.cat === 'technical' ? '#50fa7b' : '#bd93f9'
                }}>{t.cat}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Ethics Tab */}
      {activeTab === 'ethics' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>⚖️ Ethics & IRB Management</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>IRB submissions, 5 informed consent modules, COI tracking</p>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            {[
              { label: 'Submission Types', value: 5, color: '#9C27B0' },
              { label: 'Consent Modules', value: 5, color: '#4CAF50' },
              { label: 'IRB Workflow Steps', value: 4, color: '#FF9800' },
            ].map((m, i) => (
              <div key={i} style={metricCardStyle}>
                <div style={{ fontSize: 24, fontWeight: 700, color: m.color }}>{m.value}</div>
                <div style={{ fontSize: 11, color: '#aaa', marginTop: 4 }}>{m.label}</div>
              </div>
            ))}
          </div>
          {['General Research', 'CAR-T Cell Therapy Specific', 'Biospecimen Banking', 'Genomic Data Sharing', 'HIPAA Authorization'].map((mod, i) => (
            <div key={i} style={cardStyle}>
              <div style={{ color: '#bd93f9', fontWeight: 600 }}>{mod}</div>
              <div style={{ color: '#aaa', fontSize: 11, marginTop: 4 }}>Informed consent module with structured sections</div>
            </div>
          ))}
        </div>
      )}

      {/* Multi-Site Tab */}
      {activeTab === 'sites' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>🌐 Global Research Network</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>8 CAR-T centers across 4 countries with federated analysis</p>
          {[
            { name: 'Memorial Sloan Kettering', city: 'New York, USA', patients: 150, years: 8 },
            { name: 'UPenn / Abramson Cancer Center', city: 'Philadelphia, USA', patients: 200, years: 10 },
            { name: 'Fred Hutchinson Cancer Center', city: 'Seattle, USA', patients: 180, years: 9 },
            { name: 'NCI (NIH Clinical Center)', city: 'Bethesda, USA', patients: 100, years: 12 },
            { name: 'MD Anderson Cancer Center', city: 'Houston, USA', patients: 160, years: 7 },
            { name: 'Great Ormond Street Hospital', city: 'London, UK', patients: 50, years: 6 },
            { name: 'Sheba Medical Center', city: 'Ramat Gan, Israel', patients: 40, years: 5 },
            { name: 'Peking University Cancer Hospital', city: 'Beijing, China', patients: 300, years: 6 },
          ].map((site, i) => (
            <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ color: '#f8f8f2', fontWeight: 600 }}>{site.name}</div>
                <div style={{ color: '#aaa', fontSize: 11 }}>{site.city}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ color: '#50fa7b', fontWeight: 600 }}>{site.patients}/yr</div>
                <div style={{ color: '#aaa', fontSize: 10 }}>{site.years}yr experience</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Publications Tab */}
      {activeTab === 'publications' && (
        <div>
          <h3 style={{ color: '#8be9fd' }}>📝 Publication Pipeline</h3>
          <p style={{ color: '#aaa', fontSize: 13 }}>8-journal database with CRediT roles and journal recommendations</p>
          {[
            { name: 'NEJM', jif: 158.5, tier: 1, accept: '5%' },
            { name: 'Nature Medicine', jif: 82.9, tier: 1, accept: '7%' },
            { name: 'Blood', jif: 25.4, tier: 1, accept: '18%' },
            { name: 'Science Translational Medicine', jif: 17.1, tier: 1, accept: '8%' },
            { name: 'JCI', jif: 15.9, tier: 1, accept: '10%' },
            { name: 'Molecular Therapy', jif: 12.1, tier: 2, accept: '22%' },
            { name: 'JITC', jif: 10.9, tier: 2, accept: '25%' },
            { name: 'Cytotherapy', jif: 4.3, tier: 3, accept: '35%' },
          ].map((j, i) => (
            <div key={i} style={{ ...cardStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ color: '#f8f8f2', fontWeight: 600 }}>{j.name}</div>
                <div style={{ color: '#aaa', fontSize: 11 }}>Tier {j.tier} · Accept: {j.accept}</div>
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: j.tier === 1 ? '#FFD700' : j.tier === 2 ? '#C0C0C0' : '#CD7F32' }}>
                {j.jif}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CollaborationDashboard;
