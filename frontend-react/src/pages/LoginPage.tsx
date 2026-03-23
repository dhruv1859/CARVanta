import '../styles/auth.css';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';

export default function LoginPage() {
    const { login, register } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Login fields
    const [loginId, setLoginId] = useState('');
    const [loginPwd, setLoginPwd] = useState('');

    // Register fields
    const [regEmail, setRegEmail] = useState('');
    const [regUsername, setRegUsername] = useState('');
    const [regPassword, setRegPassword] = useState('');
    const [regName, setRegName] = useState('');
    const [regRole, setRegRole] = useState('researcher');
    const [regInstitution, setRegInstitution] = useState('');
    const [regCountry, setRegCountry] = useState('');

    // Verification state
    const [showVerification, setShowVerification] = useState(false);
    const [verificationCode, setVerificationCode] = useState('');
    const [verificationEmail, setVerificationEmail] = useState('');
    const [verificationPassword, setVerificationPassword] = useState('');
    const [resendCooldown, setResendCooldown] = useState(0);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); setError(''); setSuccess('');
        try {
            await login(loginId, loginPwd);
        } catch (err: any) {
            // Check if server says email not verified
            const msg = err.message || 'Login failed';
            if (msg.includes('Email not verified') || msg.includes('not verified')) {
                // Redirect to verification step
                setVerificationEmail(loginId);
                setVerificationPassword(loginPwd);
                setShowVerification(true);
                setError('');
                setSuccess('Your email is not verified yet. Enter the code sent to your email, or click "Resend Code".');
                return;
            }
            setError(msg);
        } finally { setLoading(false); }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); setError(''); setSuccess('');
        try {
            const result = await register(
                regEmail, regUsername, regPassword, regName,
                regRole, regInstitution, regCountry
            );

            // Show verification step
            setVerificationEmail(regEmail);
            setVerificationPassword(regPassword);
            setShowVerification(true);
            setSuccess('Account created! Check your email for a verification code.');
            setError('');
        } catch (err: any) {
            setError(err.message || 'Registration failed');
        } finally { setLoading(false); }
    };

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true); setError(''); setSuccess('');
        try {
            const res = await api.post('/api/v5/auth/verify-email', {
                email: verificationEmail,
                code: verificationCode,
            });

            if (res.data.error) {
                setError(res.data.error);
                return;
            }

            if (res.data.verified) {
                setSuccess('✅ Email verified! Logging you in...');
                // Auto-login after verification
                setTimeout(async () => {
                    try {
                        await login(verificationEmail, verificationPassword);
                    } catch {
                        setSuccess('Email verified! You can now sign in.');
                        setShowVerification(false);
                        setIsRegister(false);
                        setLoginId(verificationEmail);
                    }
                }, 1000);
            }
        } catch (err: any) {
            setError(err.message || 'Verification failed');
        } finally { setLoading(false); }
    };

    const handleResend = async () => {
        if (resendCooldown > 0) return;
        setLoading(true); setError(''); setSuccess('');
        try {
            const res = await api.post('/api/v5/auth/resend-verification', {
                email: verificationEmail,
                full_name: regName || 'User',
            });

            if (res.data.error) {
                setError(res.data.error);
            } else {
                setSuccess('New verification code sent! Check your email.');
                // Start cooldown timer
                setResendCooldown(60);
                const timer = setInterval(() => {
                    setResendCooldown(prev => {
                        if (prev <= 1) { clearInterval(timer); return 0; }
                        return prev - 1;
                    });
                }, 1000);
            }
        } catch (err: any) {
            setError(err.message || 'Failed to resend');
        } finally { setLoading(false); }
    };

    const handleSkipVerification = async () => {
        // Not available — verification is mandatory
        // This function intentionally does nothing
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                {/* Left: Branding */}
                <div className="auth-brand">
                    <div className="auth-brand-content">
                        <div className="auth-logo">🧬</div>
                        <h1 className="auth-title">CARVanta</h1>
                        <p className="auth-subtitle">Immunotherapy Intelligence Platform</p>
                        <div className="auth-features">
                            <div className="auth-feature">
                                <span className="auth-feature-icon">🔬</span>
                                <span>AI-Powered Antigen Scoring</span>
                            </div>
                            <div className="auth-feature">
                                <span className="auth-feature-icon">🧑‍⚕️</span>
                                <span>Patient Digital Twin Simulator</span>
                            </div>
                            <div className="auth-feature">
                                <span className="auth-feature-icon">🌍</span>
                                <span>Global Disease Intelligence</span>
                            </div>
                            <div className="auth-feature">
                                <span className="auth-feature-icon">💊</span>
                                <span>Drug Discovery Engine</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right: Form */}
                <div className="auth-form-panel">

                    {/* ─── Verification Step ─── */}
                    {showVerification ? (
                        <>
                            <div className="auth-verify-header">
                                <div className="auth-verify-icon">📧</div>
                                <h2 className="auth-verify-title">Verify Your Email</h2>
                                <p className="auth-verify-subtitle">
                                    We sent a 6-digit code to <strong>{verificationEmail}</strong>
                                </p>
                            </div>

                            {error && <div className="auth-error">{error}</div>}
                            {success && <div className="auth-success">{success}</div>}

                            <form onSubmit={handleVerify} className="auth-form">
                                <div className="auth-field">
                                    <label>Verification Code</label>
                                    <input
                                        type="text"
                                        value={verificationCode}
                                        onChange={e => {
                                            const val = e.target.value.replace(/\D/g, '').slice(0, 6);
                                            setVerificationCode(val);
                                        }}
                                        placeholder="Enter 6-digit code"
                                        className="auth-code-input"
                                        maxLength={6}
                                        autoFocus
                                        required
                                    />
                                </div>
                                <button type="submit" className="auth-submit" disabled={loading || verificationCode.length !== 6}>
                                    {loading ? '⏳ Verifying...' : '✅ Verify Email'}
                                </button>
                            </form>

                            <div className="auth-verify-actions">
                                <button
                                    className="auth-link-btn"
                                    onClick={handleResend}
                                    disabled={resendCooldown > 0 || loading}
                                >
                                    {resendCooldown > 0 ? `Resend code (${resendCooldown}s)` : '📩 Resend Code'}
                                </button>
                            </div>
                        </>
                    ) : (
                        <>
                            {/* ─── Login / Register Tabs ─── */}
                            <div className="auth-tabs">
                                <button className={`auth-tab ${!isRegister ? 'active' : ''}`} onClick={() => { setIsRegister(false); setError(''); setSuccess(''); }}>
                                    Sign In
                                </button>
                                <button className={`auth-tab ${isRegister ? 'active' : ''}`} onClick={() => { setIsRegister(true); setError(''); setSuccess(''); }}>
                                    Create Account
                                </button>
                            </div>

                            {error && <div className="auth-error">{error}</div>}
                            {success && <div className="auth-success">{success}</div>}

                            {!isRegister ? (
                                <form onSubmit={handleLogin} className="auth-form">
                                    <div className="auth-field">
                                        <label>Email or Username</label>
                                        <input type="text" value={loginId} onChange={e => setLoginId(e.target.value)} placeholder="Enter email or username" required />
                                    </div>
                                    <div className="auth-field">
                                        <label>Password</label>
                                        <input type="password" value={loginPwd} onChange={e => setLoginPwd(e.target.value)} placeholder="Enter password" required />
                                    </div>
                                    <button type="submit" className="auth-submit" disabled={loading}>
                                        {loading ? '⏳ Signing in...' : '🔐 Sign In'}
                                    </button>
                                </form>
                            ) : (
                                <form onSubmit={handleRegister} className="auth-form">
                                    <div className="auth-row">
                                        <div className="auth-field">
                                            <label>Full Name</label>
                                            <input type="text" value={regName} onChange={e => setRegName(e.target.value)} placeholder="Dr. Jane Smith" required />
                                        </div>
                                        <div className="auth-field">
                                            <label>Username</label>
                                            <input type="text" value={regUsername} onChange={e => setRegUsername(e.target.value)} placeholder="jsmith" required />
                                        </div>
                                    </div>
                                    <div className="auth-field">
                                        <label>Email</label>
                                        <input type="email" value={regEmail} onChange={e => setRegEmail(e.target.value)} placeholder="jane@research.org" required />
                                    </div>
                                    <div className="auth-field">
                                        <label>Password</label>
                                        <input type="password" value={regPassword} onChange={e => setRegPassword(e.target.value)} placeholder="Min 8 characters" required minLength={8} />
                                    </div>
                                    <div className="auth-row">
                                        <div className="auth-field">
                                            <label>Role</label>
                                            <select value={regRole} onChange={e => setRegRole(e.target.value)}>
                                                <option value="researcher">🔬 Researcher</option>
                                                <option value="clinician">🧑‍⚕️ Clinician</option>
                                                <option value="patient">🩺 Patient</option>
                                            </select>
                                        </div>
                                        <div className="auth-field">
                                            <label>Country</label>
                                            <input type="text" value={regCountry} onChange={e => setRegCountry(e.target.value)} placeholder="India" />
                                        </div>
                                    </div>
                                    <div className="auth-field">
                                        <label>Institution (optional)</label>
                                        <input type="text" value={regInstitution} onChange={e => setRegInstitution(e.target.value)} placeholder="MIT, AIIMS, Oxford..." />
                                    </div>
                                    <button type="submit" className="auth-submit" disabled={loading}>
                                        {loading ? '⏳ Creating account...' : '🚀 Create Account'}
                                    </button>
                                </form>
                            )}
                        </>
                    )}

                    <p className="auth-footer">
                        By continuing, you agree to CARVanta's Terms of Service and Privacy Policy.
                    </p>
                </div>
            </div>
        </div>
    );
}
