import { useState, useMemo } from "react";
import type { TruthTableEntry } from "../schema";

interface ActivationHeatmapProps {
  truthTable: TruthTableEntry[];
  tumorAntigens?: string[];
  healthyAntigens?: string[];
  rawExpression?: string;
}

export function IGActivationHeatmap({ truthTable, rawExpression = "" }: ActivationHeatmapProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const { expT, expH, dimensions } = useMemo(() => {
    const tNodes = Array.from(new Set(rawExpression.match(/T[1-5]/g) || [])).sort();
    const hNodes = Array.from(new Set(rawExpression.match(/H[1-5]/g) || [])).sort();
    const rows = truthTable.length;
    let cols = Math.ceil(Math.sqrt(rows));
    if (rows === 4) cols = 2;
    else if (rows === 8) cols = 4;
    else if (rows === 16) cols = 4;
    else if (rows === 32) cols = 8;
    else if (rows === 64) cols = 8;
    return { expT: tNodes, expH: hNodes, dimensions: { cols } };
  }, [rawExpression, truthTable.length]);

  const activeCount = truthTable.filter(r => r.carTActive).length;
  const inactiveCount = truthTable.length - activeCount;
  const activationProb = truthTable.length > 0 ? (activeCount / truthTable.length) * 100 : 0;

  return (
    <div className="ig-card">
      <div className="ig-mb-4">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.375rem' }}>Truth-Table Aligned Activation Heatmap</h2>
        <p className="ig-text-sm ig-text-muted">CAR-T activation outcomes plotted across evaluated logic configurations.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Total States', value: truthTable.length, color: 'var(--text-primary)', bg: 'var(--bg-surface)', border: 'var(--border)' },
          { label: 'Active States', value: activeCount, color: '#22c55e', bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)' },
          { label: 'Inactive States', value: inactiveCount, color: '#ef4444', bg: 'rgba(239,68,68,0.08)', border: 'rgba(239,68,68,0.2)' },
          { label: 'Activation Probability', value: `${activationProb.toFixed(1)}%`, color: 'var(--text-primary)', bg: 'var(--bg-surface)', border: 'var(--border)' },
        ].map(({ label, value, color, bg, border }) => (
          <div key={label} style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: bg, border: `1px solid ${border}`, textAlign: 'center' }}>
            <p style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 300, color }}>{value}</p>
          </div>
        ))}
      </div>

      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', padding: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', marginBottom: '1.5rem', fontSize: '0.875rem', flexWrap: 'wrap' }}>
          {[
            { color: '#22c55e', label: 'Active CAR-T State (Output = 1)' },
            { color: '#ef4444', label: 'Inactive CAR-T State (Output = 0)' },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <div style={{ width: 18, height: 18, borderRadius: 4, background: color }} />
              <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
            </div>
          ))}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${dimensions.cols}, minmax(0, 1fr))`,
            gap: '0.5rem',
            maxWidth: dimensions.cols > 4 ? '100%' : '60%',
            margin: '0 auto',
          }}
        >
          {truthTable.map((row, idx) => (
            <div
              key={idx}
              className={`ig-heatmap-cell ${row.carTActive ? 'active' : 'inactive'}`}
              style={{ opacity: hoveredIdx !== null && hoveredIdx !== idx ? 0.6 : 1 }}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
              title={`Row ${idx + 1}: ${row.carTActive ? 'Active' : 'Inactive'}\nTumor: ${row.tumorState.map((s, i) => `${expT[i] || ('T' + (i+1))}=${s ? 1 : 0}`).join(', ')}\nHealthy: ${row.healthyState.map((s, i) => `${expH[i] || ('H' + (i+1))}=${s ? 1 : 0}`).join(', ')}`}
            >
              {row.carTActive ? "1" : "0"}
            </div>
          ))}
        </div>
      </div>

      <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 'var(--radius-sm)' }}>
        <p className="ig-text-sm" style={{ color: 'var(--accent-blue)', lineHeight: 1.6 }}>
          <strong>Scientific Interpretation:</strong> Configurations returning higher green ratios possess stronger tumor killing potential. Higher red ratios enforce safety via veto-gates, effectively suppressing Off-Target risks.
        </p>
      </div>
    </div>
  );
}
