import { useMemo } from "react";
import { CheckCircle2, AlertCircle, AlertTriangle, Info } from "lucide-react";
import type { TruthTableEntry } from "../schema";

interface ToxicityAnalysisProps {
  truthTable: TruthTableEntry[];
  tumorAntigens: string[];
  healthyAntigens: string[];
  rawExpression?: string;
}

export function IGToxicityAnalysis({ truthTable, tumorAntigens, healthyAntigens, rawExpression }: ToxicityAnalysisProps) {
  const safeEntries = truthTable.filter((e) => e.riskLevel === "Safe");
  const moderateEntries = truthTable.filter((e) => e.riskLevel === "Moderate");
  const highRiskEntries = truthTable.filter((e) => e.riskLevel === "High");

  const activeRows = truthTable.filter(e => e.carTActive);
  const maxOT = activeRows.length > 0 ? Math.max(...activeRows.map(e => e.offTarget)) : 0;
  const maxCT = activeRows.length > 0 ? Math.max(...activeRows.map(e => e.cytokineToxicity)) : 0;
  const overallRisk = maxOT === 1 ? "High" : maxCT >= 0.6 ? "Moderate" : "Safe";

  const riskConfig = {
    Safe: { color: '#22c55e', bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)', icon: <CheckCircle2 size={18} /> },
    Moderate: { color: '#f59e0b', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', icon: <AlertCircle size={18} /> },
    High: { color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)', icon: <AlertTriangle size={18} /> },
  };

  return (
    <div className="ig-space-y-6">
      {/* Formula Explanation */}
      <div className="ig-card" style={{ background: 'rgba(59,130,246,0.05)', borderColor: 'rgba(59,130,246,0.2)' }}>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <Info size={18} style={{ color: 'var(--accent-blue)', flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--accent-blue)', marginBottom: '0.75rem' }}>Toxicity Calculation Formulas</h3>
            <div className="ig-space-y-4">
              <div>
                <p style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.375rem' }}>Off-Target Score</p>
                <p className="ig-font-mono" style={{ fontSize: '0.75rem', background: 'var(--bg-surface)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  OT = 1 if any healthy antigen is present AND CAR-T is active, else 0
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Indicates potential attack on healthy cells</p>
              </div>
              <div>
                <p style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '0.375rem' }}>Cytokine Toxicity Score</p>
                <p className="ig-font-mono" style={{ fontSize: '0.75rem', background: 'var(--bg-surface)', padding: '0.5rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                  CT = (Active Tumor Antigens / Total Tumor Antigens) × Activation Status
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Measures potential cytokine release severity (0–1)</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="ig-grid-3">
        {[
          { label: 'Safe', count: safeEntries.length, key: 'Safe' as const },
          { label: 'Moderate', count: moderateEntries.length, key: 'Moderate' as const },
          { label: 'High Risk', count: highRiskEntries.length, key: 'High' as const },
        ].map(({ label, count, key }) => {
          const cfg = riskConfig[key];
          return (
            <div key={label} style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: cfg.bg, border: `1px solid ${cfg.border}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: cfg.color }}>
                {cfg.icon}<span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{label}</span>
              </div>
              <p style={{ fontSize: '1.5rem', fontWeight: 300, color: cfg.color }}>
                {truthTable.length > 0 ? ((count / truthTable.length) * 100).toFixed(1) : 0}%
              </p>
            </div>
          );
        })}
      </div>

      {/* Overall Summary Table */}
      <div className="ig-card">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.375rem' }}>Overall Toxicity Risk Profile</h2>
        <p className="ig-text-sm ig-text-muted" style={{ marginBottom: '1rem' }}>
          Summary of Off-Target (OT) and Cytokine Toxicity (CT) risks based on CAR-T activation state.
        </p>
        <table className="ig-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'center' }}>CAR-T Output</th>
              <th style={{ textAlign: 'center' }}>Overall OT Score</th>
              <th style={{ textAlign: 'center' }}>Overall CT Score (Max)</th>
              <th>Risk Level</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ background: 'rgba(34,197,94,0.05)' }}>
              <td style={{ textAlign: 'center', fontWeight: 700, fontSize: '1.125rem' }}>0</td>
              <td style={{ textAlign: 'center' }}><span className="ig-font-mono ig-font-semibold ig-text-muted">0</span></td>
              <td style={{ textAlign: 'center' }}><span className="ig-font-mono ig-text-muted">0.00</span></td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#22c55e' }}>
                  <CheckCircle2 size={16} /><span>Safe</span>
                </div>
              </td>
            </tr>
            <tr style={{ background: riskConfig[overallRisk]?.bg }}>
              <td style={{ textAlign: 'center', fontWeight: 700, fontSize: '1.125rem' }}>1</td>
              <td style={{ textAlign: 'center' }}><span className="ig-font-mono ig-font-semibold" style={{ fontSize: '1.125rem' }}>{maxOT}</span></td>
              <td style={{ textAlign: 'center' }}><span className="ig-font-mono ig-font-semibold" style={{ fontSize: '1.125rem' }}>{maxCT.toFixed(2)}</span></td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: riskConfig[overallRisk]?.color }}>
                  {riskConfig[overallRisk]?.icon}
                  <span style={{ fontWeight: 600, fontSize: '1.125rem' }}>{overallRisk}</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
