import { useState, useMemo } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line
} from "recharts";
import { Users, Activity, ShieldAlert, Cpu, Filter } from "lucide-react";

const NUM_PATIENTS = 184;
const TUMOR_ANTIGENS = ["KRAS", "TP53", "SMAD4", "CDKN2A", "CA19-9", "MUC1", "CEA", "Mesothelin"];
const COLORS = ['#6366f1', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6', '#10b981'];
const RISK_COLORS: Record<string, string> = { "Safe": "#10b981", "Moderate": "#f59e0b", "High Risk": "#ef4444" };

function weightedRandom(items: any[], weights: number[]) {
  const sum = weights.reduce((a, b) => a + b, 0);
  let rand = Math.random() * sum;
  for (let i = 0; i < items.length; i++) {
    if (rand < weights[i]) return items[i];
    rand -= weights[i];
  }
  return items[0];
}

function generatePatients() {
  const patients = [];
  for (let i = 1; i <= NUM_PATIENTS; i++) {
    const age = Math.floor(Math.random() * 45) + 40;
    const gender: 'Male' | 'Female' = Math.random() > 0.45 ? "Male" : "Female";
    const stage = weightedRandom(["Stage I", "Stage II", "Stage III", "Stage IV"], [10, 50, 30, 10]) as string;
    const mutationBurden = weightedRandom(["Low", "Moderate", "High"], [30, 50, 20]);
    const tAntigens: string[] = [];
    if (Math.random() < 0.90) tAntigens.push("KRAS");
    if (Math.random() < 0.70) tAntigens.push("TP53");
    if (Math.random() < 0.50) tAntigens.push("SMAD4");
    if (Math.random() < 0.30) tAntigens.push("CDKN2A");
    if (Math.random() < 0.85) tAntigens.push("CA19-9");
    if (Math.random() < 0.65) tAntigens.push("MUC1");
    if (Math.random() < 0.45) tAntigens.push("CEA");
    if (Math.random() < 0.55) tAntigens.push("Mesothelin");
    const hAntigens: string[] = [];
    if (Math.random() < 0.15) hAntigens.push("CA125");
    if (Math.random() < 0.25 && tAntigens.includes("CEA")) hAntigens.push("CEA_Normal");
    if (Math.random() < 0.10 && tAntigens.includes("MUC1")) hAntigens.push("MUC1_Normal");
    let logicRecommended = "Single Target";
    if (tAntigens.length >= 3 && hAntigens.length > 0) logicRecommended = "Multi Logic";
    else if (tAntigens.length >= 2) logicRecommended = "Dual Logic";
    let risk = "Safe";
    if (hAntigens.length > 0) { risk = Math.random() > 0.3 ? "High Risk" : "Moderate"; }
    else if (tAntigens.length > 4) { risk = "Moderate"; }
    patients.push({ id: `P${i.toString().padStart(3, '0')}`, age, gender, stage, mutationBurden, tAntigens, hAntigens, logicRecommended, risk, survivalMonths: Math.floor(Math.random() * (stage === "Stage IV" ? 12 : stage === "Stage III" ? 24 : 48)) + 1 });
  }
  return patients;
}

const mockPatients = generatePatients();

export function IGPatientDataInsights() {
  const [filterStage, setFilterStage] = useState("All");

  const filteredPatients = useMemo(() =>
    filterStage === "All" ? mockPatients : mockPatients.filter(p => p.stage === filterStage),
    [filterStage]);

  const genderData = useMemo(() => {
    const counts = { Male: 0, Female: 0 };
    filteredPatients.forEach(p => counts[p.gender as keyof typeof counts]++);
    return [{ name: "Male", value: counts.Male }, { name: "Female", value: counts.Female }];
  }, [filteredPatients]);

  const stageData = useMemo(() => {
    const counts: Record<string, number> = { "Stage I": 0, "Stage II": 0, "Stage III": 0, "Stage IV": 0 };
    filteredPatients.forEach(p => counts[p.stage]++);
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [filteredPatients]);

  const biomarkerData = useMemo(() => {
    const counts: Record<string, number> = {};
    TUMOR_ANTIGENS.forEach(a => counts[a] = 0);
    filteredPatients.forEach(p => p.tAntigens.forEach(a => { if (counts[a] !== undefined) counts[a]++; }));
    return Object.entries(counts).map(([name, value]) => ({ name, frequency: (value / filteredPatients.length) * 100 })).sort((a, b) => b.frequency - a.frequency);
  }, [filteredPatients]);

  const logicData = useMemo(() => {
    const counts: Record<string, number> = { "Single Target": 0, "Dual Logic": 0, "Multi Logic": 0 };
    filteredPatients.forEach(p => counts[p.logicRecommended]++);
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [filteredPatients]);

  const riskData = useMemo(() => {
    const counts: Record<string, number> = { "Safe": 0, "Moderate": 0, "High Risk": 0 };
    filteredPatients.forEach(p => counts[p.risk]++);
    return Object.entries(counts).map(([name, value]) => ({ name, value }));
  }, [filteredPatients]);

  const survivalData = useMemo(() => {
    const data = [];
    for (let month = 0; month <= 48; month += 4) {
      const byStage = (stage: string) => {
        const total = mockPatients.filter(p => p.stage === stage).length;
        const alive = mockPatients.filter(p => p.stage === stage && p.survivalMonths > month).length;
        return total > 0 ? +(alive / total * 100).toFixed(1) : 0;
      };
      data.push({ month, "Stage I": byStage("Stage I"), "Stage II": byStage("Stage II"), "Stage III": byStage("Stage III"), "Stage IV": byStage("Stage IV") });
    }
    return data;
  }, []);

  const tooltipStyle = { background: 'var(--bg-card-solid)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.75rem' };

  return (
    <div className="ig-space-y-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 300, marginBottom: '0.25rem' }}>PDAC Patient Data Insights</h2>
          <p className="ig-text-sm ig-text-muted">TCGA PanCancer Atlas PDAC cohort analytics ({filteredPatients.length} Patients)</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '0.25rem 0.75rem' }}>
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          <select className="ig-select" style={{ border: 'none', background: 'transparent', padding: '0.25rem' }} value={filterStage} onChange={(e) => setFilterStage(e.target.value)}>
            {["All", "Stage I", "Stage II", "Stage III", "Stage IV"].map(s => <option key={s} value={s}>{s === "All" ? "All Stages" : s}</option>)}
          </select>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Demographics */}
        <div className="ig-card">
          <h3 className="ig-text-sm ig-font-semibold ig-mb-4" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Users size={14} /> Demographics Overview</h3>
          <div style={{ display: 'flex', height: 250 }}>
            <div style={{ width: '50%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={genderData} cx="50%" cy="50%" innerRadius={35} outerRadius={70} paddingAngle={5} dataKey="value">
                    {genderData.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: '0.75rem' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ width: '50%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stageData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} stroke="var(--border)" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                  <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="value" fill="var(--accent-indigo)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* CAR-T Logic */}
        <div className="ig-card">
          <h3 className="ig-text-sm ig-font-semibold ig-mb-4" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Cpu size={14} /> CAR-T Logic Strategy Breakdown</h3>
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={logicData} layout="vertical" margin={{ left: 30 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} stroke="var(--border)" />
                <XAxis type="number" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="value" fill="var(--accent-cyan)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Survival */}
        <div className="ig-card">
          <h3 className="ig-text-sm ig-font-semibold ig-mb-4" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Activity size={14} /> Overall Survival vs Tumor Stage</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={survivalData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} stroke="var(--border)" />
                <XAxis dataKey="month" label={{ value: 'Months', position: 'insideBottomRight', offset: -5, style: { fontSize: 10, fill: 'var(--text-muted)' } }} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                <YAxis label={{ value: 'Survival (%)', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: 'var(--text-muted)' } }} tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend verticalAlign="top" wrapperStyle={{ fontSize: '0.75rem' }} />
                <Line type="monotone" dataKey="Stage I" stroke="#10b981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Stage II" stroke="#6366f1" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Stage III" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Stage IV" stroke="#ef4444" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Biomarker Frequency */}
        <div className="ig-card">
          <h3 className="ig-text-sm ig-font-semibold ig-mb-4">Patient Molecular Profile Frequencies</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={biomarkerData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} stroke="var(--border)" />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: 'var(--text-muted)' }} angle={-45} textAnchor="end" height={55} />
                <YAxis tick={{ fontSize: 9, fill: 'var(--text-muted)' }} />
                <Tooltip formatter={(val: number | string) => (typeof val === 'number' ? val.toFixed(1) + '%' : val)} contentStyle={tooltipStyle} />
                <Bar dataKey="frequency" fill="var(--accent-green)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Patient Table */}
      <div className="ig-card">
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>CAR-T Simulation by Patient (Genomic Profiling)</h3>
        <div className="ig-scroll" style={{ maxHeight: 320 }}>
          <table className="ig-table">
            <thead>
              <tr>
                <th>ID</th><th>Stage</th><th>Tumor Antigens</th><th>Healthy Veto Antigens</th><th style={{ textAlign: 'center' }}>Logic</th><th style={{ textAlign: 'center' }}>Predicted Risk</th>
              </tr>
            </thead>
            <tbody>
              {filteredPatients.map((p) => (
                <tr key={p.id}>
                  <td className="ig-font-mono ig-text-sm">{p.id}</td>
                  <td className="ig-text-sm">{p.stage}</td>
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {p.tAntigens.map(a => <span key={a} className="ig-badge" style={{ fontSize: '0.65rem' }}>{a}</span>)}
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                      {p.hAntigens.length > 0
                        ? p.hAntigens.map(a => <span key={a} className="ig-badge ig-badge-primary" style={{ fontSize: '0.65rem' }}>{a}</span>)
                        : <span className="ig-text-xs ig-text-muted">None</span>}
                    </div>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`ig-badge ${p.logicRecommended === 'Multi Logic' ? 'ig-badge-primary' : ''}`}>{p.logicRecommended}</span>
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`ig-badge ${p.risk === 'High Risk' ? 'ig-badge-red' : p.risk === 'Moderate' ? 'ig-badge-yellow' : 'ig-badge-green'}`}>
                      {p.risk}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
