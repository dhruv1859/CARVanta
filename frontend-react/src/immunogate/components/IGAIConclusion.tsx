import { useState } from "react";
import { Download, Copy, Check, Sparkles, X } from "lucide-react";

interface AIConclusionProps {
  conclusion: string;
  isGenerating: boolean;
  onGenerate: () => void;
}

export function IGAIConclusion({ conclusion, isGenerating, onGenerate }: AIConclusionProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(conclusion);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([conclusion], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cart-analysis-conclusion-${new Date().toISOString().split("T")[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="ig-card">
        <div className="ig-flex-between ig-mb-4">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.25rem' }}>AI-Powered Conclusion</h2>
            <p className="ig-text-sm ig-text-muted">Research-grade analysis and recommendations</p>
          </div>
          <button className="ig-btn ig-btn-primary ig-btn-sm" onClick={onGenerate} disabled={isGenerating}>
            <Sparkles size={14} />
            {isGenerating ? "Generating..." : conclusion ? "Regenerate" : "Generate"}
          </button>
        </div>

        {isGenerating ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem', gap: '1rem' }}>
            <div className="ig-spinner" />
            <p className="ig-text-sm ig-text-muted">Analyzing data and generating conclusions...</p>
          </div>
        ) : conclusion ? (
          <>
            <div style={{ padding: '1rem', background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', fontSize: '0.875rem', lineHeight: 1.7, whiteSpace: 'pre-wrap', marginBottom: '1rem' }}>
              {conclusion.slice(0, 300)}...
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button className="ig-btn ig-btn-primary ig-btn-sm" onClick={() => setShowDialog(true)}>View Full Conclusion</button>
              <button className="ig-btn ig-btn-secondary ig-btn-sm" onClick={handleCopy}>
                {copied ? <Check size={14} /> : <Copy size={14} />} Copy
              </button>
              <button className="ig-btn ig-btn-secondary ig-btn-sm" onClick={handleDownload}>
                <Download size={14} /> Download
              </button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <Sparkles size={40} style={{ color: 'var(--text-muted)', margin: '0 auto 1rem' }} />
            <p className="ig-text-sm ig-text-muted" style={{ marginBottom: '0.5rem' }}>
              Click "Generate" to create an AI-powered research conclusion
            </p>
            <p className="ig-text-xs ig-text-muted">Note: OpenAI API key required for this feature</p>
          </div>
        )}
      </div>

      {showDialog && (
        <div className="ig-dialog-overlay" onClick={() => setShowDialog(false)}>
          <div className="ig-dialog" onClick={e => e.stopPropagation()}>
            <div className="ig-flex-between" style={{ marginBottom: '1rem' }}>
              <div>
                <h2 className="ig-dialog-title">Research-Grade Conclusion</h2>
                <p className="ig-text-sm ig-text-muted">AI-generated analysis of CAR-T therapy configuration</p>
              </div>
              <button className="ig-btn ig-btn-ghost ig-btn-sm" onClick={() => setShowDialog(false)}><X size={18} /></button>
            </div>
            <div className="ig-dialog-body">
              <div style={{ fontSize: '0.875rem', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{conclusion}</div>
            </div>
            <div className="ig-dialog-footer">
              <button className="ig-btn ig-btn-secondary ig-btn-sm" onClick={handleCopy}>
                {copied ? <Check size={14} /> : <Copy size={14} />} Copy
              </button>
              <button className="ig-btn ig-btn-secondary ig-btn-sm" onClick={handleDownload}>
                <Download size={14} /> Download
              </button>
              <button className="ig-btn ig-btn-primary ig-btn-sm" onClick={() => setShowDialog(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
