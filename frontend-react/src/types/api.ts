/* ─── CARVanta API Type Definitions ──────────────────────────────────────── */

export interface AntigenScore {
    antigen: string;
    CVS: number;
    tier: string;
    confidence_score: number;
    cancer_type?: string;
    data_source?: string;
    source_database?: string;
    evidence_level?: string;
    ml_score?: number;
    features?: Record<string, number>;
}

export interface TissueRiskEntry {
    risk_score: number;
    risk_class: string;
}

export interface ToxicityReport {
    antigen: string;
    aggregate_toxicity_index: number;
    organs_analyzed: number;
    tissue_risk_map: Record<string, TissueRiskEntry>;
    critical_organ_alerts: string[];
    safety_recommendation?: string;
}

export interface MultiTargetResult {
    synergy_score: number;
    complementarity_score?: number;
    complementarity?: number;
    coverage_score?: number;
    combined_coverage?: number;
    escape_risk_reduction?: number;
    individual_scores: Record<string, { CVS: number; tier: string; confidence: number }>;
    recommendation?: string;
    ai_insight?: string;
}

export interface SubtypeAnalysis {
    subtype: string;
    population_share: string;
    aggression: string;
    predicted_benefit: number;
    benefit_label: string;
    estimated_response_rate: number;
}

export interface CoExpressionMarker {
    gene: string;
    group: string;
    correlation: string;
    tumor_expression: number;
    potential_use: string;
}

export interface SubgroupEntry {
    cancer_type: string;
    expression_level: string;
    prevalence: string;
    predicted_benefit: string;
}

export interface StratificationResult {
    antigen: string;
    cancer_type: string;
    cvs: number;
    tier: string;
    subtype_analysis: SubtypeAnalysis[];
    co_expression_markers: CoExpressionMarker[];
    estimated_eligibility_pct: number;
    overall_eligibility: string;
    n_subgroups: number;
    subgroups: SubgroupEntry[];
    recommendation: string;
    ai_insight: string;
}

export interface ParsedQuery {
    antigen?: string;
    cancer_type?: string;
    tier?: string;
    [key: string]: unknown;
}

export interface QueryResultItem {
    antigen: string;
    cancer_type: string;
    data_source: string;
    CVS: number;
    ml_score: number;
    tier: string;
}

export interface QueryResponse {
    parsed_query: ParsedQuery;
    results: QueryResultItem[];
    summary: string;
    total_matches: number;
    returned: number;
    search_method: string;
}

export interface ClinicalTrial {
    nct_id: string;
    title: string;
    status: string;
    phases: string[];
}

export interface ClinicalTrialsResult {
    gene: string;
    total_trials: number;
    car_t_trials: number;
    phase_distribution: Record<string, number>;
    status_distribution: Record<string, number>;
    recent_trials: ClinicalTrial[];
    cancer_types: string[];
    source: string;
}

export interface HealthStatus {
    status: string;
    model_loaded: boolean;
    total_biomarkers: number;
    unique_antigens: number;
    cancer_types: number;
    api_version: string;
    endpoints: string[];
}
