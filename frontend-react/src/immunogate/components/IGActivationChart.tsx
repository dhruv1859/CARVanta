import type { TruthTableEntry } from "../schema";

interface ActivationChartProps {
  truthTable: TruthTableEntry[];
}

export function IGActivationChart({ truthTable }: ActivationChartProps) {
  const groupedData = truthTable.reduce((acc, entry) => {
    const activeT = entry.tumorState.filter(Boolean).length;
    const hasHealthy = entry.healthyState.some(Boolean);
    const key = hasHealthy ? "withHealthy" : "noHealthy";
    if (!acc[activeT]) acc[activeT] = { withHealthy: 0, noHealthy: 0, total: 0 };
    const slot = acc[activeT]!;
    if (entry.carTActive) { slot[key]++; slot.total++; }
    return acc;
  }, {} as Record<number, { withHealthy: number; noHealthy: number; total: number }>);

  const maxValue = Math.max(...Object.values(groupedData).map(d => d.total), 1);
  const dataPoints = Object.keys(groupedData).map(Number).sort((a, b) => a - b);
  const totalActive = Object.values(groupedData).reduce((sum, d) => sum + d.total, 0);
  const peakPoint = dataPoints.length > 0
    ? dataPoints.reduce((max, p) => {
        const pData = groupedData[p];
        const maxData = groupedData[max];
        return pData && maxData && pData.total > maxData.total ? p : max;
      }, dataPoints[0]!)
    : 0;

  return (
    <div className="ig-card">
      <div style={{ marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.375rem' }}>Activation Analysis</h2>
        <p className="ig-text-sm ig-text-muted">CAR-T activation by tumor antigen count</p>
      </div>

      <div className="ig-space-y-6">
        <div className="ig-space-y-4">
          {dataPoints.map((count) => {
            const data = groupedData[count];
            if (!data) return null;
            const withHealthyWidth = (data.withHealthy / maxValue) * 100;
            const noHealthyWidth = (data.noHealthy / maxValue) * 100;
            return (
              <div key={count}>
                <div className="ig-flex-between" style={{ marginBottom: '0.375rem' }}>
                  <span className="ig-text-sm" style={{ fontWeight: 500 }}>
                    {count} Tumor Antigen{count !== 1 ? 's' : ''}
                  </span>
                  <span className="ig-badge">{data.total} active</span>
                </div>
                <div style={{ position: 'relative', height: '2rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', overflow: 'hidden', border: '1px solid var(--border)' }}>
                  <div
                    style={{ position: 'absolute', left: 0, top: 0, height: '100%', background: 'var(--accent-indigo)', transition: 'width 0.6s', width: `${noHealthyWidth}%` }}
                    title={`No healthy: ${data.noHealthy}`}
                  />
                  <div
                    style={{ position: 'absolute', left: `${noHealthyWidth}%`, top: 0, height: '100%', background: 'rgba(239,68,68,0.6)', transition: 'width 0.6s', width: `${withHealthyWidth}%` }}
                    title={`With healthy: ${data.withHealthy}`}
                  />
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, mixBlendMode: 'difference', color: 'white' }}>{data.total} activations</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center', padding: '1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', flexWrap: 'wrap' }}>
          {[
            { color: 'var(--accent-indigo)', label: 'H = 0 (No healthy antigens)' },
            { color: 'rgba(239,68,68,0.6)', label: 'H ≥ 1 (With healthy antigens)' },
          ].map(({ color, label }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ width: 16, height: 16, borderRadius: 4, background: color }} />
              <span className="ig-text-xs ig-text-muted">{label}</span>
            </div>
          ))}
        </div>

        <div className="ig-grid-2">
          {[
            { label: 'Peak Activation', value: `${peakPoint} Tumor Antigens` },
            { label: 'Total Active States', value: totalActive },
          ].map(({ label, value }) => (
            <div key={label} style={{ padding: '0.75rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
              <p style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</p>
              <p style={{ fontSize: '1.25rem', fontWeight: 300 }}>{value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
