import { useMemo } from "react";
import type { TruthTableEntry } from "../schema";

interface TruthTableViewerProps {
  truthTable: TruthTableEntry[];
  tumorAntigens: string[];
  healthyAntigens: string[];
  rawExpression?: string;
}

export function IGTruthTableViewer({ truthTable, tumorAntigens, healthyAntigens, rawExpression }: TruthTableViewerProps) {
  const { columns } = useMemo(() => {
    const usedT = Array.from(new Set((rawExpression || "").match(/T[1-5]/g) || [])).sort();
    const usedH = Array.from(new Set((rawExpression || "").match(/H[1-5]/g) || [])).sort();
    if (usedT.length === 0 && usedH.length === 0) {
      if (tumorAntigens.length > 0) usedT.push(...tumorAntigens.map((_, i) => `T${i + 1}`));
      if (healthyAntigens.length > 0) usedH.push(...healthyAntigens.map((_, i) => `H${i + 1}`));
    }
    const cols: string[] = [];
    usedT.forEach(t => { const idx = parseInt(t.replace('T', '')) - 1; cols.push(tumorAntigens[idx] || t); });
    usedH.forEach(h => { const idx = parseInt(h.replace('H', '')) - 1; cols.push(healthyAntigens[idx] || h); });
    cols.push("Output", "CAR-T State");
    return { columns: cols };
  }, [tumorAntigens, healthyAntigens, truthTable, rawExpression]);

  const activeStates = truthTable.filter(e => e.carTActive).length;
  const inactiveStates = truthTable.length - activeStates;

  return (
    <div className="ig-card">
      <div className="ig-mb-4">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.375rem' }}>Truth Table</h2>
        <p className="ig-text-sm ig-text-muted">Symbolic representation of CAR-T activation states</p>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table className="ig-table" style={{ minWidth: 'max-content' }}>
          <thead>
            <tr>{columns.map((col) => (<th key={col}>{col}</th>))}</tr>
          </thead>
          <tbody>
            {truthTable.map((entry, idx) => (
              <tr key={idx} className={entry.carTActive ? 'ig-table-active' : ''}>
                {entry.tumorState.map((state, i) => (
                  <td key={`t-${i}`} style={{ textAlign: 'center' }}>
                    <span className="ig-font-mono ig-text-sm">{state ? "1" : "0"}</span>
                  </td>
                ))}
                {entry.healthyState.map((state, i) => (
                  <td key={`h-${i}`} style={{ textAlign: 'center' }}>
                    <span className="ig-font-mono ig-text-sm">{state ? "1" : "0"}</span>
                  </td>
                ))}
                <td style={{ textAlign: 'center' }}>
                  <span className="ig-font-mono ig-text-sm ig-font-semibold">{entry.carTActive ? "1" : "0"}</span>
                </td>
                <td style={{ textAlign: 'center' }}>
                  <span
                    className="ig-badge"
                    style={entry.carTActive
                      ? { background: 'rgba(34,197,94,0.15)', color: '#22c55e', borderColor: 'rgba(34,197,94,0.3)' }
                      : { background: 'rgba(148,163,184,0.1)', color: 'var(--text-muted)', borderColor: 'var(--border)' }
                    }
                  >
                    {entry.carTActive ? "Active" : "Inactive"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Safety Indicator</h3>
        <div className="ig-grid-3">
          {[
            { label: 'Active States', value: activeStates, color: '#22c55e', bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)' },
            { label: 'Inactive States', value: inactiveStates, color: 'var(--text-secondary)', bg: 'var(--bg-surface)', border: 'var(--border)' },
            { label: 'Total Combinations', value: truthTable.length, color: 'var(--text-secondary)', bg: 'var(--bg-surface)', border: 'var(--border)' },
          ].map(({ label, value, color, bg, border }) => (
            <div key={label} style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: bg, border: `1px solid ${border}` }}>
              <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</p>
              <p style={{ fontSize: '1.5rem', fontWeight: 300, color }}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
