import axios from 'axios';

const api = axios.create({
    baseURL: '',
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
});

/* ── Antigen List ─────────────────────────────────────── */
export const fetchAntigens = (search = '', limit = 50) =>
    api.get('/antigens', { params: { search, limit } }).then(r => r.data?.antigens || []);

/* ── Scoring ──────────────────────────────────────────── */
export const scoreAntigen = (antigen_name) =>
    api.post('/score', { antigen_name }).then(r => r.data);

export const batchScore = (antigens) =>
    api.post('/batch_score', { antigens }).then(r => r.data);

/* ── Rankings ─────────────────────────────────────────── */
export const fetchRankings = (top_n = 25, cancer_type = null) => {
    const params = { top_n };
    if (cancer_type) params.cancer_type = cancer_type;
    return api.get('/rank', { params }).then(r => r.data);
};

export const fetchCancerTypes = () =>
    api.get('/api/cancer-types').then(r => r.data);

/* ── Safety ───────────────────────────────────────────── */
export const fetchToxicity = (antigen) =>
    api.get(`/api/safety/${antigen}/toxicity`).then(r => r.data);

/* ── Multi-Target ─────────────────────────────────────── */
export const fetchMultiTarget = (antigens) =>
    api.post('/api/multi-target', { antigens }).then(r => r.data);

/* ── Patient Stratification ───────────────────────────── */
export const fetchStratification = (antigen_name, cancer_type = null) =>
    api.post('/api/stratify', { antigen_name, cancer_type }).then(r => r.data);

/* ── NLP Query ────────────────────────────────────────── */
export const executeQuery = (query: string, limit?: number) =>
    api.post('/api/query', { query, limit }, { timeout: 300000 }).then(r => r.data);

/* ── Clinical Trials ──────────────────────────────────── */
export const fetchClinicalTrials = (antigen) =>
    api.get(`/api/clinical-trials/${antigen}`).then(r => r.data);

/* ── Dataset Intelligence ─────────────────────────────── */
export const fetchDatasetIntel = () =>
    api.get('/api/dataset-intelligence').then(r => r.data);

/* ── Health ────────────────────────────────────────────── */
export const fetchHealth = () =>
    api.get('/health').then(r => r.data);

/* ═══════════════════════════════════════════════════════════
   v5 — International Roadmap API Functions
   ═══════════════════════════════════════════════════════════ */

/* ── Drug Interactions ────────────────────────────────── */
export const fetchDrugInteractions = (antigen: string) =>
    api.get(`/api/drug-interactions/${antigen}`).then(r => r.data);

export const fetchAllDrugInteractions = () =>
    api.get('/api/drug-interactions').then(r => r.data);

/* ── SHAP Explainability ─────────────────────────────── */
export const fetchExplanation = (antigen: string) =>
    api.get(`/api/explain/${antigen}`).then(r => r.data);

/* ── Citations ────────────────────────────────────────── */
export const fetchCitation = (antigen: string) =>
    api.get(`/api/cite/${antigen}`).then(r => r.data);

/* ── FHIR Export ──────────────────────────────────────── */
export const fetchFHIR = (antigen: string) =>
    api.get(`/api/fhir/${antigen}`).then(r => r.data);

/* ── Patent Landscape ─────────────────────────────────── */
export const fetchPatents = (antigen: string) =>
    api.get(`/api/patents/${antigen}`).then(r => r.data);

export const fetchAllPatents = () =>
    api.get('/api/patents').then(r => r.data);

/* ── Gene Notation ────────────────────────────────────── */
export const fetchGeneIds = (antigen: string) =>
    api.get(`/api/gene-ids/${antigen}`).then(r => r.data);

/* ── Score History ────────────────────────────────────── */
export const fetchScoreHistory = (antigen: string) =>
    api.get(`/api/score-history/${antigen}`).then(r => r.data);

export const recordSnapshot = (antigen: string) =>
    api.post(`/api/score-snapshot?antigen_name=${antigen}`).then(r => r.data);

/* ── Community Submit ─────────────────────────────────── */
export const submitCommunity = (data: { antigen_name: string; submitter_name: string; evidence_url?: string; notes?: string }) =>
    api.post('/api/community/submit', data, { timeout: 60000 }).then(r => r.data);

/* ── Benchmarks ───────────────────────────────────────── */
export const fetchBenchmarks = () =>
    api.get('/api/dataset/benchmarks').then(r => r.data);

/* ── Model Card ───────────────────────────────────────── */
export const fetchModelCard = () =>
    api.get('/api/model-card').then(r => r.data);

/* ── SDK Info ─────────────────────────────────────────── */
export const fetchSDKInfo = () =>
    api.get('/api/sdk-info').then(r => r.data);

/* ── Audit Log ────────────────────────────────────────── */
export const fetchAuditLog = (limit = 100) =>
    api.get('/api/audit-log', { params: { limit } }).then(r => r.data);

/* ── Batch Upload ─────────────────────────────────────── */
export const batchUpload = (genes: string[], cancer_type?: string) =>
    api.post('/api/batch-upload', { genes, cancer_type }).then(r => r.data);

export default api;
