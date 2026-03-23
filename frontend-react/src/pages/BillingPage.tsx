import React, { useState, useEffect } from 'react';
import '../styles/enterprise.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface Plan {
  tier: string;
  name: string;
  description: string;
  price_monthly: number;
  price_annual: number;
  annual_savings: number;
  features: Record<string, boolean>;
  limits: Record<string, number>;
}

interface UserSubscription {
  subscription_id?: number;
  plan_tier: string;
  plan_name: string;
  billing_cycle: string;
  status: string;
  features: Record<string, boolean>;
  limits: Record<string, number>;
  current_period_end?: string;
  cancel_at?: string;
  is_free: boolean;
}

interface UsageSummary {
  period: string;
  plan_tier: string;
  usage: Record<string, { used: number; limit: number; remaining: number; percentage: number }>;
}

interface InvoiceItem {
  id: number;
  invoice_number: string;
  amount: number;
  currency: string;
  status: string;
  description: string;
  paid_at: string | null;
  created_at: string;
}

const BillingPage: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<UserSubscription | null>(null);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [invoices, setInvoices] = useState<InvoiceItem[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const token = localStorage.getItem('token');
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [plansRes, subRes, usageRes, invRes] = await Promise.allSettled([
        fetch(`${API_BASE}/api/v5/enterprise/billing/plans`),
        fetch(`${API_BASE}/api/v5/enterprise/billing/subscription`, { headers }),
        fetch(`${API_BASE}/api/v5/enterprise/billing/usage`, { headers }),
        fetch(`${API_BASE}/api/v5/enterprise/billing/invoices`, { headers }),
      ]);

      if (plansRes.status === 'fulfilled' && plansRes.value.ok) {
        const data = await plansRes.value.json();
        setPlans(data.plans || []);
      }
      if (subRes.status === 'fulfilled' && subRes.value.ok) {
        setSubscription(await subRes.value.json());
      }
      if (usageRes.status === 'fulfilled' && usageRes.value.ok) {
        setUsage(await usageRes.value.json());
      }
      if (invRes.status === 'fulfilled' && invRes.value.ok) {
        const data = await invRes.value.json();
        setInvoices(data.invoices || []);
      }
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const subscribe = async (planTier: string) => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/billing/subscribe`, {
        method: 'POST', headers,
        body: JSON.stringify({ plan_tier: planTier, billing_cycle: billingCycle }),
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: data.message || 'Subscription updated!' });
        fetchAllData();
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to update subscription' }); }
    setActionLoading(false);
  };

  const cancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription?')) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/billing/cancel`, {
        method: 'POST', headers,
      });
      const data = await res.json();
      if (data.error) { setMessage({ type: 'error', text: data.error }); }
      else {
        setMessage({ type: 'success', text: data.message || 'Subscription cancelled' });
        fetchAllData();
      }
    } catch (e) { setMessage({ type: 'error', text: 'Failed to cancel' }); }
    setActionLoading(false);
  };

  const getFeatureLabel = (key: string) => key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  const getLimitLabel = (key: string) => key.replace(/_/g, ' ').replace('per ', '/');

  const tierColors: Record<string, string> = {
    free: '#64748b',
    pro: '#6366f1',
    enterprise: '#f59e0b',
  };

  return (
    <div className="enterprise-page">
      <div className="enterprise-header">
        <div className="enterprise-header-content">
          <div className="enterprise-icon">💳</div>
          <div>
            <h1>Billing & Subscription</h1>
            <p>Manage your plan, usage, and payment history</p>
          </div>
        </div>
      </div>

      {message.text && (
        <div className={`enterprise-alert ${message.type}`}>{message.text}</div>
      )}

      {loading && <div className="enterprise-loading"><div className="spinner" /> Loading billing data...</div>}

      {!loading && (
        <div className="enterprise-content">
          {/* Current Plan */}
          {subscription && (
            <div className="billing-current-plan">
              <div className="current-plan-info">
                <div className="plan-badge" style={{ borderColor: tierColors[subscription.plan_tier] || '#64748b' }}>
                  <span className="plan-tier-name">{subscription.plan_name}</span>
                  <span className={`plan-status ${subscription.status}`}>{subscription.status}</span>
                </div>
                <div className="plan-details">
                  {!subscription.is_free && <span>Billing: {subscription.billing_cycle}</span>}
                  {subscription.current_period_end && <span>Renews: {new Date(subscription.current_period_end).toLocaleDateString()}</span>}
                  {subscription.cancel_at && <span className="cancel-notice">Cancelling: {new Date(subscription.cancel_at).toLocaleDateString()}</span>}
                </div>
              </div>
              {!subscription.is_free && (
                <button className="btn-ghost btn-cancel" onClick={cancelSubscription} disabled={actionLoading}>
                  Cancel Plan
                </button>
              )}
            </div>
          )}

          {/* Usage */}
          {usage && usage.usage && Object.keys(usage.usage).length > 0 && (
            <div className="enterprise-card">
              <h3>📊 Current Usage — {usage.period}</h3>
              <div className="usage-grid">
                {Object.entries(usage.usage).map(([metric, data]) => (
                  <div key={metric} className="usage-item">
                    <div className="usage-header">
                      <span className="usage-metric">{getFeatureLabel(metric)}</span>
                      <span className="usage-count">{data.used.toLocaleString()} / {data.limit >= 999999 ? '∞' : data.limit.toLocaleString()}</span>
                    </div>
                    <div className="usage-bar-bg">
                      <div
                        className={`usage-bar-fill ${data.percentage > 90 ? 'danger' : data.percentage > 70 ? 'warning' : ''}`}
                        style={{ width: `${Math.min(100, data.percentage)}%` }}
                      />
                    </div>
                    <span className="usage-percentage">{data.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Billing Cycle Toggle */}
          <div className="billing-toggle">
            <button
              className={`toggle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
              onClick={() => setBillingCycle('monthly')}
            >Monthly</button>
            <button
              className={`toggle-btn ${billingCycle === 'annual' ? 'active' : ''}`}
              onClick={() => setBillingCycle('annual')}
            >Annual <span className="save-badge">Save ~17%</span></button>
          </div>

          {/* Plans Grid */}
          <div className="plans-grid">
            {plans.map(plan => {
              const isCurrent = subscription?.plan_tier === plan.tier;
              const price = billingCycle === 'annual' ? plan.price_annual : plan.price_monthly;
              const perMonth = billingCycle === 'annual' ? (plan.price_annual / 12).toFixed(0) : plan.price_monthly;

              return (
                <div key={plan.tier} className={`plan-card ${isCurrent ? 'current' : ''} ${plan.tier === 'pro' ? 'recommended' : ''}`}>
                  {plan.tier === 'pro' && <div className="recommended-badge">Most Popular</div>}
                  <div className="plan-card-header" style={{ borderTopColor: tierColors[plan.tier] || '#64748b' }}>
                    <h3>{plan.name}</h3>
                    <p className="plan-desc">{plan.description}</p>
                    <div className="plan-price">
                      <span className="price-amount">${perMonth}</span>
                      <span className="price-period">/mo</span>
                      {billingCycle === 'annual' && plan.price_annual > 0 && (
                        <span className="price-billed">billed ${price}/year</span>
                      )}
                    </div>
                  </div>
                  <div className="plan-features">
                    <h4>Features</h4>
                    {Object.entries(plan.features || {}).map(([feat, enabled]) => (
                      <div key={feat} className={`feature-item ${enabled ? 'enabled' : 'disabled'}`}>
                        <span>{enabled ? '✅' : '❌'}</span>
                        <span>{getFeatureLabel(feat)}</span>
                      </div>
                    ))}
                  </div>
                  <div className="plan-limits">
                    <h4>Limits</h4>
                    {Object.entries(plan.limits || {}).map(([key, val]) => (
                      <div key={key} className="limit-item">
                        <span>{getLimitLabel(key)}</span>
                        <span>{val >= 999999 ? 'Unlimited' : val.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                  <button
                    className={`plan-action-btn ${isCurrent ? 'current' : plan.tier === 'pro' ? 'primary' : ''}`}
                    onClick={() => subscribe(plan.tier)}
                    disabled={isCurrent || actionLoading}
                  >
                    {isCurrent ? 'Current Plan' : plan.price_monthly === 0 ? 'Downgrade' : 'Upgrade'}
                  </button>
                </div>
              );
            })}
          </div>

          {/* Invoices */}
          {invoices.length > 0 && (
            <div className="enterprise-card">
              <h3>🧾 Invoice History</h3>
              <div className="enterprise-table">
                <table>
                  <thead>
                    <tr><th>Invoice</th><th>Description</th><th>Amount</th><th>Status</th><th>Date</th></tr>
                  </thead>
                  <tbody>
                    {invoices.map(inv => (
                      <tr key={inv.id}>
                        <td className="mono">{inv.invoice_number}</td>
                        <td>{inv.description}</td>
                        <td className="amount">${inv.amount.toFixed(2)}</td>
                        <td><span className={`invoice-status ${inv.status}`}>{inv.status}</span></td>
                        <td>{new Date(inv.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BillingPage;
