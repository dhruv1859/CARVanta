import React, { useState, useEffect } from 'react';
import '../styles/enterprise.css';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface MFAStatus {
  mfa_enabled: boolean;
  setup_started: boolean;
  enabled_at: string | null;
  last_verified_at: string | null;
  backup_codes_remaining: number;
  is_locked: boolean;
}

interface MFASetupData {
  setup_initiated: boolean;
  totp_uri: string;
  qr_code: string;
  secret: string;
  message: string;
}

const MFASetup: React.FC = () => {
  const [status, setStatus] = useState<MFAStatus | null>(null);
  const [setupData, setSetupData] = useState<MFASetupData | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [verifyCode, setVerifyCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [regenCode, setRegenCode] = useState('');
  const [step, setStep] = useState<'status' | 'setup' | 'verify' | 'backup' | 'disable'>('status');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem('token');
  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/mfa/status`, { headers });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) { console.error(e); }
  };

  const initiateSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/mfa/setup`, {
        method: 'POST', headers,
      });
      const data = await res.json();
      if (data.error) { setError(data.error); }
      else {
        setSetupData(data);
        setStep('setup');
      }
    } catch (e) { setError('Failed to initiate MFA setup'); }
    setLoading(false);
  };

  const verifySetup = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      setError('Enter a 6-digit code from your authenticator app');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/mfa/verify-setup`, {
        method: 'POST', headers,
        body: JSON.stringify({ code: verifyCode }),
      });
      const data = await res.json();
      if (data.error) { setError(data.error); }
      else if (data.mfa_enabled) {
        setBackupCodes(data.backup_codes || []);
        setStep('backup');
        setSuccess('MFA successfully enabled!');
        fetchStatus();
      }
    } catch (e) { setError('Verification failed'); }
    setLoading(false);
  };

  const disableMFA = async () => {
    if (!disableCode) {
      setError('Enter your current TOTP code to disable MFA');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/mfa/disable`, {
        method: 'POST', headers,
        body: JSON.stringify({ code: disableCode }),
      });
      const data = await res.json();
      if (data.error) { setError(data.error); }
      else {
        setSuccess('MFA has been disabled');
        setStep('status');
        setDisableCode('');
        fetchStatus();
      }
    } catch (e) { setError('Failed to disable MFA'); }
    setLoading(false);
  };

  const regenerateCodes = async () => {
    if (!regenCode) {
      setError('Enter your TOTP code to regenerate backup codes');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/api/v5/enterprise/mfa/regenerate-backup-codes`, {
        method: 'POST', headers,
        body: JSON.stringify({ code: regenCode }),
      });
      const data = await res.json();
      if (data.error) { setError(data.error); }
      else {
        setBackupCodes(data.backup_codes || []);
        setStep('backup');
        setSuccess('New backup codes generated');
        setRegenCode('');
        fetchStatus();
      }
    } catch (e) { setError('Failed to regenerate codes'); }
    setLoading(false);
  };

  const copySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setSuccess('Secret copied to clipboard');
      setTimeout(() => setSuccess(''), 2000);
    }
  };

  const copyBackupCodes = () => {
    navigator.clipboard.writeText(backupCodes.join('\n'));
    setSuccess('Backup codes copied to clipboard');
    setTimeout(() => setSuccess(''), 2000);
  };

  return (
    <div className="enterprise-page">
      <div className="enterprise-header">
        <div className="enterprise-header-content">
          <div className="enterprise-icon">🔐</div>
          <div>
            <h1>Multi-Factor Authentication</h1>
            <p>Protect your account with TOTP-based two-factor authentication</p>
          </div>
        </div>
      </div>

      {error && <div className="enterprise-alert error">{error}</div>}
      {success && <div className="enterprise-alert success">{success}</div>}

      {/* Status View */}
      {step === 'status' && status && (
        <div className="enterprise-content">
          <div className="mfa-status-card">
            <div className={`mfa-status-indicator ${status.mfa_enabled ? 'enabled' : 'disabled'}`}>
              <div className="mfa-shield-icon">{status.mfa_enabled ? '🛡️' : '⚠️'}</div>
              <h2>{status.mfa_enabled ? 'MFA is Active' : 'MFA is Not Enabled'}</h2>
              <p>{status.mfa_enabled
                ? 'Your account is protected with two-factor authentication'
                : 'Enable MFA to add an extra layer of security to your account'}
              </p>
            </div>

            {status.mfa_enabled ? (
              <div className="mfa-details">
                <div className="mfa-detail-row">
                  <span>Status</span>
                  <span className="mfa-badge enabled">Active</span>
                </div>
                <div className="mfa-detail-row">
                  <span>Enabled Since</span>
                  <span>{status.enabled_at ? new Date(status.enabled_at).toLocaleDateString() : 'N/A'}</span>
                </div>
                <div className="mfa-detail-row">
                  <span>Last Verified</span>
                  <span>{status.last_verified_at ? new Date(status.last_verified_at).toLocaleString() : 'N/A'}</span>
                </div>
                <div className="mfa-detail-row">
                  <span>Backup Codes Remaining</span>
                  <span className={status.backup_codes_remaining < 4 ? 'danger' : ''}>
                    {status.backup_codes_remaining} / 12
                  </span>
                </div>
                <div className="mfa-actions">
                  <button className="btn-secondary" onClick={() => setStep('disable')}>
                    Disable MFA
                  </button>
                  <button className="btn-primary" onClick={() => {
                    setStep('status');
                    setRegenCode('');
                  }}>
                    Regenerate Backup Codes
                  </button>
                </div>
                {/* Inline regenerate */}
                <div className="mfa-regen-section">
                  <h4>Regenerate Backup Codes</h4>
                  <p>Enter your current TOTP code to generate new backup codes.</p>
                  <div className="mfa-code-input-group">
                    <input
                      type="text"
                      maxLength={6}
                      placeholder="000000"
                      value={regenCode}
                      onChange={e => setRegenCode(e.target.value.replace(/\D/g, ''))}
                      className="mfa-code-input"
                    />
                    <button className="btn-primary" onClick={regenerateCodes} disabled={loading}>
                      {loading ? 'Processing...' : 'Regenerate'}
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="mfa-setup-cta">
                <div className="mfa-benefits">
                  <div className="benefit">✅ Protects against password theft</div>
                  <div className="benefit">✅ Required for enterprise compliance</div>
                  <div className="benefit">✅ Works with Google Authenticator, Authy, 1Password</div>
                  <div className="benefit">✅ Includes 12 backup recovery codes</div>
                </div>
                <button className="btn-primary btn-large" onClick={initiateSetup} disabled={loading}>
                  {loading ? 'Setting up...' : '🔐 Enable MFA'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Setup: QR Code */}
      {step === 'setup' && setupData && (
        <div className="enterprise-content">
          <div className="mfa-setup-card">
            <h2>Step 1: Scan QR Code</h2>
            <p>Open your authenticator app and scan this QR code:</p>

            <div className="qr-container">
              {setupData.qr_code ? (
                <img src={setupData.qr_code} alt="MFA QR Code" className="qr-image" />
              ) : (
                <div className="qr-placeholder">
                  <p>QR code unavailable. Use manual entry below.</p>
                </div>
              )}
            </div>

            <div className="manual-entry">
              <h4>Can't scan? Enter manually:</h4>
              <div className="secret-display">
                <code>{setupData.secret}</code>
                <button className="btn-copy" onClick={copySecret}>📋 Copy</button>
              </div>
            </div>

            <h2 style={{ marginTop: '2rem' }}>Step 2: Verify</h2>
            <p>Enter the 6-digit code from your authenticator app:</p>
            <div className="mfa-code-input-group">
              <input
                type="text"
                maxLength={6}
                placeholder="000000"
                value={verifyCode}
                onChange={e => setVerifyCode(e.target.value.replace(/\D/g, ''))}
                className="mfa-code-input large"
                autoFocus
              />
              <button className="btn-primary" onClick={verifySetup} disabled={loading || verifyCode.length !== 6}>
                {loading ? 'Verifying...' : 'Verify & Enable'}
              </button>
            </div>
            <button className="btn-ghost" onClick={() => { setStep('status'); setSetupData(null); }}>
              Cancel Setup
            </button>
          </div>
        </div>
      )}

      {/* Backup Codes */}
      {step === 'backup' && backupCodes.length > 0 && (
        <div className="enterprise-content">
          <div className="mfa-backup-card">
            <div className="backup-header">
              <h2>🔑 Backup Recovery Codes</h2>
              <p className="backup-warning">
                Save these codes securely. Each code can only be used once.
                <br/><strong>You won't be able to see them again.</strong>
              </p>
            </div>
            <div className="backup-codes-grid">
              {backupCodes.map((code, i) => (
                <div key={i} className="backup-code">
                  <span className="code-index">{i + 1}</span>
                  <code>{code}</code>
                </div>
              ))}
            </div>
            <div className="backup-actions">
              <button className="btn-primary" onClick={copyBackupCodes}>📋 Copy All Codes</button>
              <button className="btn-secondary" onClick={() => {
                setStep('status');
                setBackupCodes([]);
                fetchStatus();
              }}>
                I've Saved My Codes ✓
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disable MFA */}
      {step === 'disable' && (
        <div className="enterprise-content">
          <div className="mfa-disable-card">
            <h2>⚠️ Disable MFA</h2>
            <p>This will remove two-factor authentication from your account. Enter your current TOTP code to confirm:</p>
            <div className="mfa-code-input-group">
              <input
                type="text"
                maxLength={6}
                placeholder="000000"
                value={disableCode}
                onChange={e => setDisableCode(e.target.value.replace(/\D/g, ''))}
                className="mfa-code-input"
                autoFocus
              />
              <button className="btn-danger" onClick={disableMFA} disabled={loading}>
                {loading ? 'Disabling...' : 'Confirm Disable'}
              </button>
            </div>
            <button className="btn-ghost" onClick={() => { setStep('status'); setDisableCode(''); }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MFASetup;
