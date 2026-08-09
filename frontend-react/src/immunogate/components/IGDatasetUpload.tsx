import { useState, useCallback } from "react";
import { Upload, X, FileText, CheckCircle2 } from "lucide-react";
import Papa from "papaparse";
import * as XLSX from "xlsx";

interface DatasetUploadProps {
  type: "biomarkers" | "logic" | "truthTable" | "clinical";
  title: string;
  description: string;
  onUpload: (data: any[], filename: string) => void;
  uploadedFile?: string;
  isLocked?: boolean;
}

export function IGDatasetUpload({
  type, title, description, onUpload, uploadedFile, isLocked,
}: DatasetUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [preview, setPreview] = useState<any[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const processFile = useCallback((file: File) => {
    const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls');
    const isCsv = file.name.endsWith('.csv') || file.name.endsWith('.tsv');

    if (type === "truthTable" && !isExcel) {
      showToast("Please upload an Excel file (.xlsx or .xls)");
      return;
    }
    if (type !== "truthTable" && !isCsv) {
      showToast("Please upload a CSV or TSV file");
      return;
    }
    setIsUploading(true);

    if (isExcel) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = e.target?.result;
          const workbook = XLSX.read(data, { type: 'binary' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet);
          if (jsonData && jsonData.length > 0) {
            setPreview(jsonData.slice(0, 10));
            onUpload(jsonData, file.name);
            showToast(`✓ ${file.name} uploaded with ${jsonData.length} rows`);
          }
          setIsUploading(false);
        } catch (error: any) {
          showToast(`Upload failed: ${error.message}`);
          setIsUploading(false);
        }
      };
      reader.readAsBinaryString(file);
    } else {
      const isTsv = file.name.endsWith('.tsv');
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        delimiter: isTsv ? '\t' : '',
        complete: (results) => {
          if (results.data && results.data.length > 0) {
            setPreview(results.data.slice(0, 10));
            onUpload(results.data, file.name);
            showToast(`✓ ${file.name} uploaded with ${results.data.length} rows`);
          }
          setIsUploading(false);
        },
        error: (error) => {
          showToast(`Upload failed: ${error.message}`);
          setIsUploading(false);
        },
      });
    }
  }, [onUpload, type]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (file) processFile(file);
    }
  }, [processFile]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file) processFile(file);
    }
  }, [processFile]);

  return (
    <div className="ig-card">
      {toastMsg && (
        <div style={{ position: 'fixed', bottom: '1rem', right: '1rem', background: 'var(--bg-card-solid)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '0.75rem 1rem', zIndex: 100, fontSize: '0.875rem', color: 'var(--text-primary)', boxShadow: 'var(--shadow)' }}>
          {toastMsg}
        </div>
      )}
      <div className="ig-mb-4">
        <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.25rem' }}>{title}</h3>
        <p className="ig-text-sm ig-text-muted">{description}</p>
      </div>
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
        onDrop={handleDrop}
        className={`ig-upload-zone ${isDragging ? 'dragging' : ''} ${uploadedFile ? 'uploaded' : ''} ${isLocked ? 'locked' : ''}`}
      >
        <input
          type="file"
          accept={type === "truthTable" ? ".xlsx,.xls" : ".csv,.tsv"}
          onChange={handleFileInput}
          className="ig-upload-input"
          disabled={isUploading || isLocked}
        />
        {isUploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
            <div className="ig-spinner" />
            <p className="ig-text-sm ig-text-muted">Processing...</p>
          </div>
        ) : uploadedFile ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={40} style={{ color: 'var(--accent-green)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={16} />
              <span className="ig-text-sm" style={{ fontWeight: 500 }}>{uploadedFile}</span>
            </div>
            <p className="ig-text-xs ig-text-muted">Click or drag to replace</p>
            {preview.length > 0 && (
              <button
                className="ig-btn ig-btn-secondary ig-btn-sm"
                onClick={(e) => { e.stopPropagation(); setShowPreview(!showPreview); }}
              >
                {showPreview ? "Hide" : "Show"} Preview
              </button>
            )}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
            <Upload size={40} style={{ color: 'var(--text-muted)' }} />
            <p className="ig-text-sm" style={{ fontWeight: 500 }}>
              {type === "truthTable" ? "Drop Excel file here or click to browse" : "Drop CSV or TSV file here or click to browse"}
            </p>
            <p className="ig-text-xs ig-text-muted">
              {type === "truthTable" ? "Supports .xlsx, .xls up to 10MB" : "Supports CSV and TSV files up to 10MB"}
            </p>
          </div>
        )}
      </div>

      {showPreview && preview.length > 0 && (
        <div style={{ marginTop: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '1rem', background: 'var(--bg-surface)' }}>
          <div className="ig-flex-between ig-mb-4">
            <h4 className="ig-text-sm ig-font-semibold">Preview (first 10 rows)</h4>
            <button className="ig-btn ig-btn-ghost ig-btn-sm" onClick={() => setShowPreview(false)}><X size={14} /></button>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="ig-table" style={{ fontSize: '0.75rem' }}>
              <thead>
                <tr>{Object.keys(preview[0] || {}).map((key) => (<th key={key}>{key}</th>))}</tr>
              </thead>
              <tbody>
                {preview.map((row, idx) => (
                  <tr key={idx}>{Object.values(row).map((value: any, ci) => (<td key={ci}>{String(value)}</td>))}</tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
