import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { MultiGateLogic } from "../schema";

interface LogicRecommendationProps {
  logic: MultiGateLogic;
}

export function IGLogicRecommendation({ logic }: LogicRecommendationProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="ig-card">
      <div className="ig-space-y-6">
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.375rem' }}>Recommended CAR-T Logic</h2>
          <p className="ig-text-sm ig-text-muted">
            Based on {logic.tumorCount ?? '?'} tumor antigen(s) and {logic.healthyCount ?? '?'} healthy antigen(s)
          </p>
        </div>

        <div className="ig-logic-block">
          <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Logic Gate Configuration
          </p>
          <p className="ig-logic-expr">{logic.bestLogic}</p>
        </div>

        <div>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>How It Works</h3>
          <p className="ig-text-sm ig-text-muted" style={{ lineHeight: 1.7 }}>
            {logic.description || logic.working}
          </p>
        </div>

        <div className="ig-grid-2">
          {[
            { label: 'Specificity', value: logic.specificity },
            { label: 'Selectivity', value: logic.selectivity },
          ].map(({ label, value }) => (
            <div key={label}>
              <div className="ig-flex-between ig-mb-4" style={{ marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)' }}>{label}</span>
                <span className="ig-badge">{value}/5</span>
              </div>
              <div className="ig-progress-bar">
                <div className="ig-progress-fill" style={{ width: `${(value / 5) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>

        <div className="ig-accordion-item">
          <button className="ig-accordion-trigger" onClick={() => setExpanded(!expanded)}>
            <span>Why this logic?</span>
            <ChevronDown size={16} style={{ transition: 'transform 0.2s', transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }} />
          </button>
          {expanded && (
            <div className="ig-accordion-content">
              <p>
                {logic.reason || `Selectivity (${logic.selectivity}/5), Specificity (${logic.specificity}/5). Configuration chosen for ${logic.description || 'optimal balance'}.`}
              </p>
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)' }}>
                <h4 style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: '0.5rem' }}>Key Benefits</h4>
                <ul style={{ paddingLeft: '1.25rem', color: 'var(--text-secondary)', fontSize: '0.875rem', lineHeight: 1.7 }}>
                  <li>High specificity minimizes off-target effects</li>
                  <li>Selectivity ensures accurate tumor recognition</li>
                  <li>Balanced safety and efficacy profile</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
