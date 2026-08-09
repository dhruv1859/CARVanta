import { useState } from "react";
import { Dna, FlaskConical, Target, Shield, BookOpen, Users, ChevronRight, X } from "lucide-react";

interface LandingDashboardProps {
  onGetStarted: () => void;
}

const features = [
  { icon: <Target size={22} />, title: "Dual Gate Logic Analysis", description: "Advanced AND/OR/NOT gate combinations for optimal CAR-T cell specificity and selectivity." },
  { icon: <Dna size={22} />, title: "Biomarker Selection", description: "Comprehensive database of 1098+ biomarkers with tumor and healthy antigen classification." },
  { icon: <FlaskConical size={22} />, title: "Toxicity Prediction", description: "Real-time on-target and off-tumor toxicity analysis with risk assessment." },
  { icon: <Shield size={22} />, title: "AI-Powered Insights", description: "OpenAI integration for intelligent interpretation and therapeutic recommendations." },
];

const references = [
  "Wishart DS, et al. MarkerDB: An online database of molecular biomarkers. Nucleic Acids Res. 2021;49(D1):D1259–D1267.",
  "MarkerDB. Pancreatic ductal adenocarcinoma biomarker dataset. Available from: https://markerdb.ca/conditions/335",
  "cBioPortal for Cancer Genomics. Pancreatic cancer (PDAC-MSK 2024) study. Available from: https://www.cbioportal.org",
  "National Library of Medicine. Pancreatic ductal adenocarcinoma biomarker research. Available from: https://pmc.ncbi.nlm.nih.gov/articles/PMC8311531/",
  "National Cancer Institute, Genomic Data Commons. TCGA PanCancer Atlas publications. Available from: https://gdc.cancer.gov",
  "cBioPortal. Pancreatic adenocarcinoma (TCGA PanCancer Atlas) study. Available from: https://www.cbioportal.org/study/summary?id=paad_tcga_pan_can_atlas_2018",
  "Rawla P, Sunkara T, Gaduputi V. Biomarkers in the diagnosis of pancreatic cancer. World J Gastroenterol. 2019;25(42):6463–6479.",
  "Han X, Wang Y, Wei J, Han W. Multi-antigen-targeted chimeric antigen receptor T cells for cancer therapy. J Hematol Oncol. 2019;12(1).",
  "ImmunoGate Platform. Dual Logic CAR-T Designer for PDAC. Designed by Iyer S. Available from: https://duallogiccart1-1.onrender.com/",
];

export function IGLandingDashboard({ onGetStarted }: LandingDashboardProps) {
  const [showRefs, setShowRefs] = useState(false);

  return (
    <div className="ig-page" style={{ padding: '0 1.5rem 4rem' }}>
      {/* Hero */}
      <div className="ig-hero">
        <div style={{ width: 64, height: 64, borderRadius: 16, background: 'linear-gradient(135deg, var(--accent-indigo), var(--accent-purple))', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', boxShadow: '0 8px 32px rgba(99,102,241,0.35)' }}>
          <Dna size={32} color="white" />
        </div>
        <h1 className="ig-hero-title">ImmunoGate PDAC</h1>
        <p className="ig-hero-subtitle">
          AI-Powered Dual Gate Logic CAR-T Cell Therapy Platform for Pancreatic Ductal Adenocarcinoma
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <button className="ig-btn ig-btn-primary ig-btn-lg" onClick={onGetStarted}>
            Get Started <ChevronRight size={18} />
          </button>
          <button className="ig-btn ig-btn-secondary ig-btn-lg" onClick={() => setShowRefs(true)}>
            <BookOpen size={18} /> References
          </button>
        </div>
      </div>

      {/* About */}
      <div className="ig-card ig-mb-6" style={{ maxWidth: 900, margin: '0 auto 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <BookOpen size={20} style={{ color: 'var(--accent-indigo)' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 300 }}>About</h2>
        </div>
        <p className="ig-text-sm ig-text-muted" style={{ lineHeight: 1.8, marginBottom: '0.875rem' }}>
          Immuno-Gate is a comprehensive computational platform designed to optimize CAR-T cell therapy for Pancreatic Ductal Adenocarcinoma (PDAC) through advanced dual gate logic design. By integrating biomarker databases, Boolean logic systems, and artificial intelligence, this platform enables researchers to design safer and more effective CAR-T therapies.
        </p>
        <p className="ig-text-sm ig-text-muted" style={{ lineHeight: 1.8 }}>
          The platform addresses the critical challenge of achieving tumor specificity while minimizing off-tumor toxicity—a major hurdle in CAR-T therapy development. Through systematic analysis of tumor-associated antigens (TAA) and healthy tissue markers, Immuno-Gate recommends optimal dual gate logic configurations (AND, OR, NOT gates) to maximize therapeutic efficacy.
        </p>
      </div>

      {/* Features */}
      <div style={{ maxWidth: 900, margin: '0 auto 1.5rem' }}>
        <h2 style={{ fontSize: '1.75rem', fontWeight: 300, textAlign: 'center', marginBottom: '1.5rem' }}>Key Features</h2>
        <div className="ig-grid-2" style={{ gap: '1rem' }}>
          {features.map((feature, index) => (
            <div key={index} className="ig-feature-card">
              <div className="ig-feature-icon">{feature.icon}</div>
              <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>{feature.title}</h3>
              <p className="ig-text-sm ig-text-muted" style={{ lineHeight: 1.6 }}>{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Credits */}
      <div className="ig-card" style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <Users size={20} style={{ color: 'var(--accent-indigo)' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 300 }}>Credits</h2>
        </div>
        <div className="ig-space-y-4">
          {[
            { title: 'Development Team', desc: 'Immuno-Gate Platform • Bioinformatics Research Initiative' },
            { title: 'Author & Co-Author', desc: 'Sridhar Viswanathan Iyer (Author) • Dr. Diwakar Sharma (Corresponding Author)' },
            { title: 'Technologies', desc: 'Built with React, TypeScript, Express, OpenAI API, and CARVanta Platform' },
            { title: 'Data Sources', desc: 'Biomarker database compiled from peer-reviewed literature and clinical studies on PDAC-associated antigens and dual gate CAR-T logic design principles' },
          ].map(({ title, desc }) => (
            <div key={title}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.25rem' }}>{title}</h3>
              <p className="ig-text-sm ig-text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <p className="ig-text-xs ig-text-muted ig-text-center" style={{ marginTop: '3rem' }}>
        © 2024 Immuno-Gate · A research platform for CAR-T therapy optimization · Integrated into CARVanta
      </p>

      {/* References Dialog */}
      {showRefs && (
        <div className="ig-dialog-overlay" onClick={() => setShowRefs(false)}>
          <div className="ig-dialog" onClick={e => e.stopPropagation()}>
            <div className="ig-flex-between" style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <BookOpen size={20} style={{ color: 'var(--accent-indigo)' }} />
                <h2 className="ig-dialog-title">References</h2>
              </div>
              <button className="ig-btn ig-btn-ghost ig-btn-sm" onClick={() => setShowRefs(false)}><X size={18} /></button>
            </div>
            <div className="ig-dialog-body">
              <ol style={{ paddingLeft: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                {references.map((ref, index) => (
                  <li key={index} className="ig-text-sm ig-text-muted" style={{ lineHeight: 1.6 }}>
                    <span className="ig-font-mono" style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>[{index + 1}]</span>
                    {ref}
                  </li>
                ))}
              </ol>
            </div>
            <div className="ig-dialog-footer">
              <button className="ig-btn ig-btn-primary ig-btn-sm" onClick={() => setShowRefs(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
