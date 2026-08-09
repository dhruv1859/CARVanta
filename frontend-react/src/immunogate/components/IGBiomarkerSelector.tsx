import { useState, useMemo } from "react";
import { Search, ArrowUp, ArrowDown, X } from "lucide-react";
import type { Biomarker } from "../schema";

interface BiomarkerSelectorProps {
  biomarkers: Biomarker[];
  selectedTumor: Biomarker[];
  selectedHealthy: Biomarker[];
  onSelectTumor: (biomarkers: Biomarker[]) => void;
  onSelectHealthy: (biomarkers: Biomarker[]) => void;
}

export function IGBiomarkerSelector({
  biomarkers, selectedTumor, selectedHealthy, onSelectTumor, onSelectHealthy,
}: BiomarkerSelectorProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [indicationFilter, setIndicationFilter] = useState("all");

  const categories = useMemo(() => {
    const cats = new Set(biomarkers.map((b) => b.category));
    return ["all", ...Array.from(cats)];
  }, [biomarkers]);

  const filteredBiomarkers = useMemo(() => {
    return biomarkers.filter((b) => {
      const matchesSearch = b.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = categoryFilter === "all" || b.category === categoryFilter;
      const matchesIndication =
        indicationFilter === "all" ||
        (indicationFilter === "up" && b.indication.includes("↑")) ||
        (indicationFilter === "down" && b.indication.includes("↓"));
      return matchesSearch && matchesCategory && matchesIndication;
    });
  }, [biomarkers, searchTerm, categoryFilter, indicationFilter]);

  const isTumorSelected = (b: Biomarker) => selectedTumor.some((s) => s.name === b.name);
  const isHealthySelected = (b: Biomarker) => selectedHealthy.some((s) => s.name === b.name);

  const toggleTumor = (b: Biomarker) => {
    if (isTumorSelected(b)) onSelectTumor(selectedTumor.filter((s) => s.name !== b.name));
    else if (selectedTumor.length < 5) onSelectTumor([...selectedTumor, b]);
  };

  const toggleHealthy = (b: Biomarker) => {
    if (isHealthySelected(b)) onSelectHealthy(selectedHealthy.filter((s) => s.name !== b.name));
    else if (selectedHealthy.length < 5) onSelectHealthy([...selectedHealthy, b]);
  };

  return (
    <div className="ig-space-y-6">
      {/* Filter Bar */}
      <div className="ig-card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: '0.75rem', alignItems: 'center' }}>
          <div style={{ position: 'relative', gridColumn: '1 / 3' }}>
            <Search size={14} style={{ position: 'absolute', left: '0.625rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              className="ig-input"
              style={{ paddingLeft: '2rem' }}
              placeholder="Search biomarkers..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <select className="ig-select" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            {categories.map((cat) => (<option key={cat} value={cat}>{cat === "all" ? "All Categories" : cat}</option>))}
          </select>
          <select className="ig-select" value={indicationFilter} onChange={(e) => setIndicationFilter(e.target.value)}>
            <option value="all">All Indications</option>
            <option value="up">Upregulated ↑</option>
            <option value="down">Downregulated ↓</option>
          </select>
        </div>
      </div>

      {/* Counters */}
      <div style={{ display: 'flex', gap: '1rem' }}>
        {[
          { label: 'Tumor Antigens', count: selectedTumor.length },
          { label: 'Healthy Antigens', count: selectedHealthy.length },
        ].map(({ label, count }) => (
          <div key={label} className="ig-card" style={{ flex: 1 }}>
            <div className="ig-flex-between">
              <div>
                <p style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>{label}</p>
                <p style={{ fontSize: '1.5rem', fontWeight: 300 }}>{count}<span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>/5</span></p>
              </div>
              <span className={`ig-badge ${count > 0 ? 'ig-badge-primary' : ''}`}>{count === 0 ? 'None' : count === 5 ? 'Full' : 'Active'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Two-Panel */}
      <div className="ig-grid-2">
        {/* Available */}
        <div className="ig-card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Available Biomarkers <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontWeight: 400 }}>({filteredBiomarkers.length})</span>
          </h3>
          <div className="ig-scroll">
            <div className="ig-space-y-4">
              {filteredBiomarkers.map((biomarker, index) => {
                const tumorSelected = isTumorSelected(biomarker);
                const healthySelected = isHealthySelected(biomarker);
                const canT = tumorSelected || selectedTumor.length < 5;
                const canH = healthySelected || selectedHealthy.length < 5;
                return (
                  <div
                    key={`${biomarker.name}-${index}`}
                    style={{
                      display: 'flex', alignItems: 'flex-start', gap: '0.75rem', padding: '0.75rem',
                      borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)',
                      background: (tumorSelected || healthySelected) ? 'var(--bg-surface)' : 'transparent',
                      transition: 'background 0.15s',
                    }}
                  >
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <p style={{ fontSize: '0.875rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{biomarker.name}</p>
                        {biomarker.indication.includes("↑") && <ArrowUp size={12} style={{ color: 'var(--accent-red)', flexShrink: 0 }} />}
                        {biomarker.indication.includes("↓") && <ArrowDown size={12} style={{ color: 'var(--accent-indigo)', flexShrink: 0 }} />}
                      </div>
                      <span className="ig-badge">{biomarker.category}</span>
                    </div>
                    <div style={{ display: 'flex', gap: '0.375rem' }}>
                      <button
                        className={`ig-btn ig-btn-sm ${tumorSelected ? 'ig-btn-primary' : 'ig-btn-secondary'}`}
                        onClick={() => toggleTumor(biomarker)}
                        disabled={!canT}
                        title="Tumor antigen"
                      >T</button>
                      <button
                        className={`ig-btn ig-btn-sm ${healthySelected ? 'ig-btn-primary' : 'ig-btn-secondary'}`}
                        onClick={() => toggleHealthy(biomarker)}
                        disabled={!canH}
                        title="Healthy antigen"
                      >H</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Selected */}
        <div className="ig-card">
          <div className="ig-flex-between ig-mb-4">
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Selected Biomarkers</h3>
            <button
              className="ig-btn ig-btn-secondary ig-btn-sm"
              onClick={() => { onSelectTumor([]); onSelectHealthy([]); }}
              disabled={selectedTumor.length === 0 && selectedHealthy.length === 0}
            >Clear All</button>
          </div>
          <div className="ig-space-y-6">
            {[
              { label: 'Tumor Antigens', items: selectedTumor, max: 5, toggle: toggleTumor, colorClass: 'ig-badge-primary', bg: 'rgba(99,102,241,0.08)' },
              { label: 'Healthy Antigens', items: selectedHealthy, max: 5, toggle: toggleHealthy, colorClass: '', bg: 'var(--bg-surface)' },
            ].map(({ label, items, max, toggle, bg }) => (
              <div key={label}>
                <h4 style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                  {label} ({items.length}/{max})
                </h4>
                <div className="ig-space-y-4">
                  {items.length === 0 ? (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', padding: '1rem', textAlign: 'center', border: '1px dashed var(--border)', borderRadius: 'var(--radius-sm)' }}>
                      No {label.toLowerCase()} selected
                    </p>
                  ) : items.map((biomarker) => (
                    <div key={biomarker.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)', background: bg, border: '1px solid var(--border)' }}>
                      <div>
                        <p style={{ fontSize: '0.875rem', fontWeight: 500 }}>{biomarker.name}</p>
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{biomarker.category}</p>
                      </div>
                      <button className="ig-btn ig-btn-ghost ig-btn-sm" onClick={() => toggle(biomarker)}><X size={14} /></button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
