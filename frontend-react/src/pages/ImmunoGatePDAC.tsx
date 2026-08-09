import { useState } from 'react';
import { ArrowRight, ArrowLeft, Lock, RotateCcw, Dna } from 'lucide-react';
import { IGLandingDashboard } from '../immunogate/components/IGLandingDashboard';
import { IGProgressStepper } from '../immunogate/components/IGProgressStepper';
import { IGDatasetUpload } from '../immunogate/components/IGDatasetUpload';
import { IGBiomarkerSelector } from '../immunogate/components/IGBiomarkerSelector';
import { IGLogicRecommendation } from '../immunogate/components/IGLogicRecommendation';
import { IGTruthTableViewer } from '../immunogate/components/IGTruthTableViewer';
import { IGToxicityAnalysis } from '../immunogate/components/IGToxicityAnalysis';
import { IGPatientDataInsights } from '../immunogate/components/IGPatientDataInsights';
import { IGActivationHeatmap } from '../immunogate/components/IGActivationHeatmap';
import { IGActivationChart } from '../immunogate/components/IGActivationChart';
import { IGAIConclusion } from '../immunogate/components/IGAIConclusion';
import { recommendLogic, mapLogicExpressionToAntigens, type LogicType } from '../immunogate/logic_engine/logicRecommendationService';
import type { Biomarker, SelectedBiomarkers, MultiGateLogic, TruthTableEntry } from '../immunogate/schema';
import '../styles/immuno-gate.css';

const API_BASE = import.meta.env.VITE_API_URL || '';

export default function ImmunoGatePDAC() {
  const [showLanding, setShowLanding] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);
  const [activeResultTab, setActiveResultTab] = useState('logic');

  const [biomarkersData, setBiomarkersData] = useState<Biomarker[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<{ biomarkers?: string; clinicalData?: string }>({});
  const [isUploadLocked, setIsUploadLocked] = useState(false);
  const [logicType, setLogicType] = useState<LogicType>('multi');
  const [selectedBiomarkers, setSelectedBiomarkers] = useState<SelectedBiomarkers>({ tumor: [], healthy: [] });
  const [analysis, setAnalysis] = useState<{ logic: MultiGateLogic | null; truthTable: TruthTableEntry[]; conclusion: string }>({
    logic: null, truthTable: [], conclusion: '',
  });
  const [isGeneratingConclusion, setIsGeneratingConclusion] = useState(false);

  const handleBiomarkersUpload = async (data: any[], filename: string) => {
    const biomarkers: Biomarker[] = data.map((row: any) => ({
      name: row['Serum Protein Biomarker'] || row.name || '',
      category: row.Category || row.category || '',
      indication: row.Indication || row.indication || '',
    }));
    try {
      await fetch(`${API_BASE}/api/immunogate/datasets/biomarkers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: biomarkers }),
      });
    } catch (_) { /* continue even if backend call fails */ }
    setBiomarkersData(biomarkers);
    setUploadedFiles(prev => ({ ...prev, biomarkers: filename }));
  };

  const handleClinicalDataUpload = async (data: any[], filename: string) => {
    setUploadedFiles(prev => ({ ...prev, clinicalData: filename }));
  };

  const canProceedToStep1 = !!(uploadedFiles.biomarkers && isUploadLocked);
  const canProceedToStep2 = selectedBiomarkers.tumor.length >= 1;
  const canProceedToStep3 = analysis.logic !== null;

  const handleGenerateAnalysis = async () => {
    const tumorCount = selectedBiomarkers.tumor.length;
    const healthyCount = selectedBiomarkers.healthy.length;
    try {
      const recommendation = recommendLogic(tumorCount, healthyCount, logicType);
      if (!recommendation) throw new Error('No logic recommendation available for the selected antigen count.');

      const tumorAntigenNames = selectedBiomarkers.tumor.map(b => b.name);
      const healthyAntigenNames = selectedBiomarkers.healthy.map(b => b.name);
      const mappedLogic = mapLogicExpressionToAntigens(recommendation.Logic_Expression, tumorAntigenNames, healthyAntigenNames);

      const logic: MultiGateLogic = {
        bestLogic: mappedLogic,
        logicName: recommendation.Logic_Name,
        specificity: recommendation.Specificity,
        selectivity: recommendation.Selectivity,
        rawExpression: recommendation.Logic_Expression,
        description: recommendation.Description,
        tumorCount,
        healthyCount,
      };

      // Try backend truth table endpoint, fallback to local generation
      let truthTable: TruthTableEntry[] = [];
      try {
        const res = await fetch(`${API_BASE}/api/immunogate/truth-table`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ logic }),
        });
        if (res.ok) truthTable = await res.json();
        else truthTable = generateTruthTableLocally(logic);
      } catch (_) {
        truthTable = generateTruthTableLocally(logic);
      }

      setAnalysis({ logic, truthTable, conclusion: '' });
      setCurrentStep(3);
    } catch (error) {
      console.error('Error generating analysis:', error);
    }
  };

  const handleGenerateConclusion = async () => {
    setIsGeneratingConclusion(true);
    try {
      const response = await fetch(`${API_BASE}/api/immunogate/generate-conclusion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          selectedTumor: selectedBiomarkers.tumor.map(b => b.name),
          selectedHealthy: selectedBiomarkers.healthy.map(b => b.name),
          logic: analysis.logic,
          truthTable: analysis.truthTable,
        }),
      });
      if (!response.ok) throw new Error('Failed to generate conclusion');
      const data = await response.json();
      setAnalysis(prev => ({ ...prev, conclusion: data.conclusion }));
    } catch (error) {
      setAnalysis(prev => ({
        ...prev,
        conclusion: 'Error generating AI conclusion. Please ensure the OpenAI API key is configured correctly in CARVanta backend.',
      }));
    } finally {
      setIsGeneratingConclusion(false);
    }
  };

  const handleReset = () => {
    setShowLanding(true);
    setCurrentStep(0);
    setBiomarkersData([]);
    setUploadedFiles({});
    setIsUploadLocked(false);
    setSelectedBiomarkers({ tumor: [], healthy: [] });
    setAnalysis({ logic: null, truthTable: [], conclusion: '' });
    setActiveResultTab('logic');
  };

  if (showLanding) {
    return <IGLandingDashboard onGetStarted={() => setShowLanding(false)} />;
  }

  const RESULT_TABS = [
    { id: 'logic', label: 'Logic' },
    { id: 'truthTable', label: 'Truth Table' },
    { id: 'toxicity', label: 'Toxicity' },
    { id: 'patientData', label: 'Patient Data' },
    { id: 'visualizations', label: 'Visualizations' },
    { id: 'conclusion', label: 'AI Conclusion' },
  ];

  return (
    <div className="ig-page">
      {/* Header */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 40, borderBottom: '1px solid var(--border)',
        background: 'rgba(14,14,18,0.92)', backdropFilter: 'blur(12px)', padding: '0 1.5rem',
      }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button className="ig-btn ig-btn-ghost ig-btn-sm" onClick={() => setShowLanding(true)}>
              <ArrowLeft size={16} /> Back
            </button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: 'linear-gradient(135deg, var(--accent-indigo), var(--accent-purple))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Dna size={18} color="white" />
              </div>
              <div>
                <p style={{ fontWeight: 600, fontSize: '0.95rem', lineHeight: 1.2 }}>ImmunoGate PDAC</p>
                <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CAR-T Analysis Platform</p>
              </div>
            </div>
          </div>
          <button className="ig-btn ig-btn-secondary ig-btn-sm" onClick={handleReset}>
            <RotateCcw size={14} /> Reset
          </button>
        </div>
      </header>

      {/* Main */}
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1.5rem' }}>
        <div className="ig-space-y-6">
          {/* Stepper */}
          <div className="ig-card">
            <IGProgressStepper currentStep={currentStep} onStepClick={setCurrentStep} />
          </div>

          {/* ── Step 0: Upload ── */}
          {currentStep === 0 && (
            <div className="ig-space-y-6">
              <div>
                <h2 className="ig-section-title">Upload Datasets</h2>
                <p className="ig-section-desc">Upload biomarkers dataset to begin analysis</p>
              </div>
              <div className="ig-grid-2">
                <IGDatasetUpload
                  type="biomarkers"
                  title="Biomarkers Dataset"
                  description="Upload CSV with biomarker information"
                  onUpload={handleBiomarkersUpload}
                  uploadedFile={uploadedFiles.biomarkers}
                  isLocked={isUploadLocked}
                />
                <IGDatasetUpload
                  type="clinical"
                  title="Clinical TCGA Dataset"
                  description="Upload CSV with patient clinical profiles"
                  onUpload={handleClinicalDataUpload}
                  uploadedFile={uploadedFiles.clinicalData}
                  isLocked={isUploadLocked}
                />
              </div>
              {uploadedFiles.biomarkers && !isUploadLocked && (
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <button className="ig-btn ig-btn-primary" onClick={() => setIsUploadLocked(true)}>
                    <Lock size={16} /> Lock Datasets and Continue
                  </button>
                </div>
              )}
              {isUploadLocked && (
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.875rem 1.25rem', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 'var(--radius-sm)' }}>
                    <Lock size={16} style={{ color: 'var(--accent-indigo)' }} />
                    <span className="ig-text-sm" style={{ fontWeight: 500 }}>Datasets are locked and saved</span>
                  </div>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button className="ig-btn ig-btn-primary" onClick={() => setCurrentStep(1)} disabled={!canProceedToStep1}>
                  Next: Select Biomarkers <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 1: Select Biomarkers ── */}
          {currentStep === 1 && (
            <div className="ig-space-y-6">
              <div>
                <h2 className="ig-section-title">Select Biomarkers</h2>
                <p className="ig-section-desc">Choose 1–5 tumor and 0–5 healthy antigens for analysis</p>
              </div>
              <IGBiomarkerSelector
                biomarkers={biomarkersData}
                selectedTumor={selectedBiomarkers.tumor}
                selectedHealthy={selectedBiomarkers.healthy}
                onSelectTumor={(tumor) => setSelectedBiomarkers(prev => ({ ...prev, tumor }))}
                onSelectHealthy={(healthy) => setSelectedBiomarkers(prev => ({ ...prev, healthy }))}
              />
              {/* Logic Type Selection */}
              <div className="ig-card">
                <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Logic Type Selection</h3>
                <div className="ig-radio-group">
                  {[
                    { value: 'dual', label: 'Dual Logic CAR-T', desc: 'AND/OR gate combinations optimized for 1–2 antigen pairs' },
                    { value: 'multi', label: 'Multi Logic CAR-T', desc: 'Complex multi-gate logic for broader antigen profiles' },
                  ].map(({ value, label, desc }) => (
                    <label key={value} className="ig-radio-label" style={{ padding: '0.75rem', border: `1px solid ${logicType === value ? 'rgba(99,102,241,0.4)' : 'var(--border)'}`, borderRadius: 'var(--radius-sm)', background: logicType === value ? 'rgba(99,102,241,0.05)' : 'transparent', transition: 'all 0.2s' }}>
                      <input type="radio" value={value} checked={logicType === value} onChange={() => setLogicType(value as LogicType)} />
                      <div>
                        <span style={{ fontWeight: 500 }}>{label}</span>
                        <p className="ig-text-xs ig-text-muted" style={{ marginTop: '0.125rem' }}>{desc}</p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="ig-btn ig-btn-secondary" onClick={() => setCurrentStep(0)} disabled={isUploadLocked}>
                  <ArrowLeft size={16} /> Back to Upload
                </button>
                <button className="ig-btn ig-btn-primary" onClick={() => setCurrentStep(2)} disabled={!canProceedToStep2}>
                  Next: Generate Analysis <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 2: Analyze ── */}
          {currentStep === 2 && (
            <div className="ig-space-y-6">
              <div>
                <h2 className="ig-section-title">Generate Analysis</h2>
                <p className="ig-section-desc">Review your selections and generate the CAR-T analysis</p>
              </div>
              <div className="ig-grid-2">
                {[
                  { title: 'Selected Tumor Antigens', items: selectedBiomarkers.tumor, bg: 'rgba(99,102,241,0.08)', border: 'rgba(99,102,241,0.2)' },
                  { title: 'Selected Healthy Antigens', items: selectedBiomarkers.healthy, bg: 'var(--bg-surface)', border: 'var(--border)' },
                ].map(({ title, items, bg, border }) => (
                  <div key={title} className="ig-card">
                    <h3 className="ig-text-sm ig-font-semibold ig-mb-4">{title}</h3>
                    <div className="ig-space-y-4">
                      {items.length === 0 ? (
                        <p className="ig-text-sm ig-text-muted" style={{ fontStyle: 'italic' }}>None selected</p>
                      ) : items.map((b) => (
                        <div key={b.name} style={{ padding: '0.5rem 0.75rem', background: bg, border: `1px solid ${border}`, borderRadius: 'var(--radius-sm)', fontSize: '0.875rem' }}>
                          {b.name}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="ig-btn ig-btn-secondary" onClick={() => setCurrentStep(1)}>
                  <ArrowLeft size={16} /> Back
                </button>
                <button className="ig-btn ig-btn-primary" onClick={handleGenerateAnalysis}>
                  Generate Analysis <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 3: Design ── */}
          {currentStep === 3 && analysis.logic && (
            <div className="ig-space-y-6">
              <div>
                <h2 className="ig-section-title">CAR-T Design</h2>
                <p className="ig-section-desc">Personalized CAR-T configuration based on selected antigens</p>
              </div>
              <div className="ig-card">
                <div className="ig-space-y-6">
                  <div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Selected Antigens</h3>
                    <div className="ig-grid-2">
                      {[
                        { title: 'Tumor Antigens', items: selectedBiomarkers.tumor, color: 'var(--accent-indigo)', bg: 'rgba(99,102,241,0.08)', border: 'rgba(99,102,241,0.2)' },
                        { title: 'Healthy Antigens', items: selectedBiomarkers.healthy, color: 'var(--text-muted)', bg: 'var(--bg-surface)', border: 'var(--border)' },
                      ].map(({ title, items, color, bg, border }) => (
                        <div key={title}>
                          <h4 className="ig-text-xs ig-text-muted ig-font-semibold" style={{ textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>{title}</h4>
                          <div className="ig-space-y-4">
                            {items.length === 0 ? <p className="ig-text-sm ig-text-muted" style={{ fontStyle: 'italic' }}>None selected</p>
                              : items.map((b) => (
                                <div key={b.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0.75rem', background: bg, border: `1px solid ${border}`, borderRadius: 'var(--radius-sm)' }}>
                                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, flexShrink: 0 }} />
                                  <span className="ig-text-sm ig-font-semibold">{b.name}</span>
                                </div>
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>Recommended Logic Gate</h3>
                    <div className="ig-logic-block">
                      <p style={{ fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                        Dual Gate & Multi Gate Configuration
                      </p>
                      <p className="ig-logic-expr">{analysis.logic.bestLogic}</p>
                      <div className="ig-grid-2" style={{ marginTop: '1rem', gap: '0.75rem' }}>
                        {[
                          { label: 'Specificity', value: analysis.logic.specificity },
                          { label: 'Selectivity', value: analysis.logic.selectivity },
                        ].map(({ label, value }) => (
                          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.625rem 0.875rem', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                            <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, color: 'var(--text-muted)' }}>{label}</span>
                            <span className="ig-badge">{value}/5</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="ig-btn ig-btn-secondary" onClick={() => setCurrentStep(2)}>
                  <ArrowLeft size={16} /> Back to Analysis
                </button>
                <button className="ig-btn ig-btn-primary" onClick={() => setCurrentStep(4)}>
                  View Detailed Results <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* ── Step 4: Results ── */}
          {currentStep === 4 && analysis.logic && (
            <div className="ig-space-y-6">
              <div>
                <h2 className="ig-section-title">Analysis Results</h2>
                <p className="ig-section-desc">Comprehensive CAR-T therapy analysis and recommendations</p>
              </div>

              {/* Tab Bar */}
              <div className="ig-tabs-list">
                {RESULT_TABS.map(tab => (
                  <button
                    key={tab.id}
                    className={`ig-tab-trigger ${activeResultTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveResultTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div>
                {activeResultTab === 'logic' && <IGLogicRecommendation logic={analysis.logic} />}
                {activeResultTab === 'truthTable' && (
                  <IGTruthTableViewer
                    truthTable={analysis.truthTable}
                    tumorAntigens={selectedBiomarkers.tumor.map(b => b.name)}
                    healthyAntigens={selectedBiomarkers.healthy.map(b => b.name)}
                    rawExpression={analysis.logic.rawExpression}
                  />
                )}
                {activeResultTab === 'toxicity' && (
                  <IGToxicityAnalysis
                    truthTable={analysis.truthTable}
                    tumorAntigens={selectedBiomarkers.tumor.map(b => b.name)}
                    healthyAntigens={selectedBiomarkers.healthy.map(b => b.name)}
                    rawExpression={analysis.logic.rawExpression}
                  />
                )}
                {activeResultTab === 'patientData' && <IGPatientDataInsights />}
                {activeResultTab === 'visualizations' && (
                  <div className="ig-space-y-6">
                    <IGActivationHeatmap
                      truthTable={analysis.truthTable}
                      tumorAntigens={selectedBiomarkers.tumor.map(b => b.name)}
                      healthyAntigens={selectedBiomarkers.healthy.map(b => b.name)}
                      rawExpression={analysis.logic.rawExpression}
                    />
                    <IGActivationChart truthTable={analysis.truthTable} />
                  </div>
                )}
                {activeResultTab === 'conclusion' && (
                  <IGAIConclusion
                    conclusion={analysis.conclusion}
                    isGenerating={isGeneratingConclusion}
                    onGenerate={handleGenerateConclusion}
                  />
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <button className="ig-btn ig-btn-secondary" onClick={() => setCurrentStep(3)}>
                  <ArrowLeft size={16} /> Back to Design
                </button>
                <button className="ig-btn ig-btn-secondary" onClick={() => setCurrentStep(1)}>
                  Start New Analysis
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

/* ── Local truth table generation (fallback when backend unavailable) ── */
function generateTruthTableLocally(logic: MultiGateLogic): TruthTableEntry[] {
  const expr = logic.rawExpression || logic.bestLogic;
  const tMatches = Array.from(new Set(expr.match(/T[1-5]/g) || [])).sort();
  const hMatches = Array.from(new Set(expr.match(/H[1-5]/g) || [])).sort();
  const tCount = tMatches.length || (logic.tumorCount ?? 1);
  const hCount = hMatches.length || (logic.healthyCount ?? 0);
  const total = Math.pow(2, tCount + hCount);
  const table: TruthTableEntry[] = [];

  for (let i = 0; i < total; i++) {
    const bits = i.toString(2).padStart(tCount + hCount, '0').split('').map(b => b === '1');
    const tumorState = bits.slice(0, tCount);
    const healthyState = bits.slice(tCount);
    const carTActive = evaluateExpression(expr, tumorState, healthyState);
    const anyHealthy = healthyState.some(Boolean);
    const offTarget = carTActive && anyHealthy ? 1 : 0;
    const activeTumors = tumorState.filter(Boolean).length;
    const cytokineToxicity = carTActive ? activeTumors / Math.max(tCount, 1) : 0;
    const riskLevel: 'Safe' | 'Moderate' | 'High' =
      offTarget === 1 ? 'High' : cytokineToxicity >= 0.6 ? 'Moderate' : 'Safe';
    table.push({
      combination: bits.join(''),
      tumorState,
      healthyState,
      carTActive,
      status: carTActive ? 'Active/KILL' : 'Inactive/OFF',
      offTarget,
      cytokineToxicity,
      riskLevel,
    });
  }
  return table;
}

function evaluateExpression(expr: string, tumorState: boolean[], healthyState: boolean[]): boolean {
  let e = expr;
  tumorState.forEach((val, i) => { e = e.replace(new RegExp(`\\bT${i + 1}\\b`, 'g'), val ? '1' : '0'); });
  healthyState.forEach((val, i) => { e = e.replace(new RegExp(`\\bH${i + 1}\\b`, 'g'), val ? '1' : '0'); });
  // Handle NOT(x) → replace with inverted value
  e = e.replace(/NOT\(1\)/g, '0').replace(/NOT\(0\)/g, '1');
  // Handle AND
  while (e.includes(' AND ')) {
    e = e.replace(/(\d) AND (\d)/g, (_, a, b) => (a === '1' && b === '1') ? '1' : '0');
  }
  // Handle OR
  while (e.includes(' OR ')) {
    e = e.replace(/(\d) OR (\d)/g, (_, a, b) => (a === '1' || b === '1') ? '1' : '0');
  }
  // Handle parens
  while (e.includes('(')) {
    e = e.replace(/\((\d)\)/g, '$1');
  }
  return e.trim() === '1';
}
