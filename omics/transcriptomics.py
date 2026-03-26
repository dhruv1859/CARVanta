"""
CARVanta – Transcriptomics Analyzer
======================================
RNA-seq expression analysis using TCGA and GTEx data.
Computes tumor vs. normal differential expression, tissue-specific profiles,
and expression percentile rankings across 33 cancer types.
"""

import math
import random
import hashlib
from typing import Optional


# ─── Simulated TCGA/GTEx Reference Data ──────────────────────────────────────────
# In production, these would come from actual TCGA/GTEx downloads.
# Here we simulate realistic expression distributions for 33 cancer types.

TCGA_CANCER_TYPES = [
    "ACC", "BLCA", "BRCA", "CESC", "CHOL", "COAD", "DLBC", "ESCA",
    "GBM", "HNSC", "KICH", "KIRC", "KIRP", "LAML", "LGG", "LIHC",
    "LUAD", "LUSC", "MESO", "OV", "PAAD", "PCPG", "PRAD", "READ",
    "SARC", "SKCM", "STAD", "TGCT", "THCA", "THYM", "UCEC", "UCS", "UVM",
]

# Cancer type friendly names
CANCER_NAMES = {
    "ACC": "Adrenocortical Carcinoma", "BLCA": "Bladder Urothelial Carcinoma",
    "BRCA": "Breast Invasive Carcinoma", "CESC": "Cervical Cancer",
    "CHOL": "Cholangiocarcinoma", "COAD": "Colon Adenocarcinoma",
    "DLBC": "Diffuse Large B-Cell Lymphoma", "ESCA": "Esophageal Carcinoma",
    "GBM": "Glioblastoma", "HNSC": "Head and Neck Squamous Cell",
    "KICH": "Kidney Chromophobe", "KIRC": "Kidney Clear Cell",
    "KIRP": "Kidney Papillary Cell", "LAML": "Acute Myeloid Leukemia",
    "LGG": "Brain Lower Grade Glioma", "LIHC": "Liver Hepatocellular",
    "LUAD": "Lung Adenocarcinoma", "LUSC": "Lung Squamous Cell",
    "MESO": "Mesothelioma", "OV": "Ovarian Serous Cystadenocarcinoma",
    "PAAD": "Pancreatic Adenocarcinoma", "PCPG": "Pheochromocytoma",
    "PRAD": "Prostate Adenocarcinoma", "READ": "Rectum Adenocarcinoma",
    "SARC": "Sarcoma", "SKCM": "Skin Cutaneous Melanoma",
    "STAD": "Stomach Adenocarcinoma", "TGCT": "Testicular Germ Cell",
    "THCA": "Thyroid Carcinoma", "THYM": "Thymoma",
    "UCEC": "Uterine Corpus Endometrial", "UCS": "Uterine Carcinosarcoma",
    "UVM": "Uveal Melanoma",
}

# Known CAR-T targets that are significantly overexpressed in specific cancers
KNOWN_TARGET_CANCERS = {
    "CD19": ["DLBC", "LAML"], "CD20": ["DLBC"], "CD22": ["DLBC", "LAML"],
    "BCMA": ["DLBC"], "CD38": ["DLBC", "LAML"],
    "CD33": ["LAML"], "CD123": ["LAML"],
    "HER2": ["BRCA", "STAD", "ESCA"], "EGFR": ["LUAD", "LUSC", "GBM", "HNSC"],
    "MSLN": ["MESO", "OV", "PAAD"], "GPC3": ["LIHC"],
    "PSMA": ["PRAD"], "MUC1": ["BRCA", "LUAD", "PAAD", "OV"],
    "EpCAM": ["COAD", "READ", "STAD", "BRCA"],
    "CEA": ["COAD", "READ", "PAAD", "STAD"],
    "CD30": ["DLBC", "THYM"], "CD70": ["KIRC", "DLBC"],
    "CLDN18.2": ["STAD", "PAAD"],
    "DLL3": ["LUSC"], "ROR1": ["BRCA", "LUAD"],
    "GD2": ["SARC"], "B7H3": ["GBM", "LUAD"],
    "TROP2": ["BRCA", "BLCA", "LUAD"],
    "NECTIN4": ["BLCA", "BRCA"],
    "FRα": ["OV", "LUAD"],
    "CD5": ["THYM"],
}


class TranscriptomicsAnalyzer:
    """
    Analyzes gene expression from RNA-seq data across TCGA cancer types.
    Computes differential expression, specificity scores, and expression profiles.
    """

    def __init__(self):
        self._cache = {}

    def _gene_seed(self, gene: str) -> int:
        """Deterministic seed for reproducible per-gene results."""
        return int(hashlib.md5(gene.upper().encode()).hexdigest()[:8], 16)

    def analyze(self, gene_symbol: str, cancer_type: Optional[str] = None) -> dict:
        """
        Full transcriptomic analysis for a gene across TCGA cancer types.

        Returns:
            Expression profile across all cancer types, tumor vs. normal
            differential expression, specificity scores, and percentile rankings.
        """
        gene = gene_symbol.upper().strip()
        cache_key = f"{gene}_{cancer_type}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        seed = self._gene_seed(gene)
        rng = random.Random(seed)

        # Known target bonus
        known_cancers = KNOWN_TARGET_CANCERS.get(gene, [])
        is_known_target = len(known_cancers) > 0

        # Generate expression profile across all TCGA types
        expression_profile = {}
        all_tumor_values = []
        all_normal_values = []

        for ct in TCGA_CANCER_TYPES:
            ct_seed = int(hashlib.md5(f"{gene}_{ct}".encode()).hexdigest()[:8], 16)
            ct_rng = random.Random(ct_seed)

            # Base expression (log2 TPM)
            base_expr = ct_rng.gauss(4.5, 2.5)

            # Significant overexpression in known target cancers
            if ct in known_cancers:
                tumor_expr = max(0, base_expr + ct_rng.gauss(5.0, 1.0))
                normal_expr = max(0, base_expr * ct_rng.uniform(0.05, 0.25))
            elif is_known_target:
                tumor_expr = max(0, base_expr + ct_rng.gauss(0.5, 1.0))
                normal_expr = max(0, base_expr * ct_rng.uniform(0.3, 0.8))
            else:
                tumor_expr = max(0, base_expr + ct_rng.gauss(1.0, 2.0))
                normal_expr = max(0, base_expr * ct_rng.uniform(0.4, 1.2))

            # Compute fold change and stats
            fold_change = tumor_expr / max(normal_expr, 0.01)
            log2fc = math.log2(max(fold_change, 0.001))

            # Simulated p-value (more significant for known targets)
            if ct in known_cancers:
                p_value = ct_rng.uniform(1e-15, 1e-6)
            elif abs(log2fc) > 2:
                p_value = ct_rng.uniform(1e-8, 0.01)
            else:
                p_value = ct_rng.uniform(0.01, 0.5)

            n_tumor_samples = ct_rng.randint(100, 800)
            n_normal_samples = ct_rng.randint(20, 100)

            profile_entry = {
                "cancer_type": ct,
                "cancer_name": CANCER_NAMES.get(ct, ct),
                "tumor_expression_tpm": round(tumor_expr, 2),
                "normal_expression_tpm": round(normal_expr, 2),
                "log2_fold_change": round(log2fc, 3),
                "fold_change": round(fold_change, 2),
                "p_value": float(f"{p_value:.2e}"),
                "adjusted_p_value": float(f"{min(p_value * 33, 1.0):.2e}"),
                "is_significant": p_value < 0.05 and abs(log2fc) > 1,
                "is_overexpressed": log2fc > 1 and p_value < 0.05,
                "n_tumor_samples": n_tumor_samples,
                "n_normal_samples": n_normal_samples,
            }

            expression_profile[ct] = profile_entry
            all_tumor_values.append(tumor_expr)
            all_normal_values.append(normal_expr)

        # Compute global stats
        overexpressed_types = [ct for ct, p in expression_profile.items() if p["is_overexpressed"]]
        significant_types = [ct for ct, p in expression_profile.items() if p["is_significant"]]

        # Tumor specificity (how specific is expression to tumor vs normal)
        mean_tumor = sum(all_tumor_values) / len(all_tumor_values)
        mean_normal = sum(all_normal_values) / len(all_normal_values)
        global_specificity = min(1.0, max(0.0, (mean_tumor - mean_normal) / max(mean_tumor, 0.01)))

        # Expression consistency (low variance = more consistent)
        if len(all_tumor_values) > 1:
            tumor_mean = sum(all_tumor_values) / len(all_tumor_values)
            variance = sum((x - tumor_mean) ** 2 for x in all_tumor_values) / len(all_tumor_values)
            consistency = max(0.0, 1.0 - min(1.0, math.sqrt(variance) / max(tumor_mean, 1.0)))
        else:
            consistency = 0.5

        # Transcriptomics layer score (0-1)
        specificity_component = global_specificity * 0.4
        overexpr_component = min(1.0, len(overexpressed_types) / 5) * 0.3
        consistency_component = consistency * 0.3
        layer_score = round(min(1.0, specificity_component + overexpr_component + consistency_component), 4)

        # Top cancer types by fold change
        sorted_types = sorted(
            expression_profile.items(),
            key=lambda x: x[1]["log2_fold_change"],
            reverse=True,
        )
        top_cancers = [
            {"cancer_type": ct, "cancer_name": CANCER_NAMES.get(ct, ct),
             "log2fc": p["log2_fold_change"], "p_value": p["p_value"]}
            for ct, p in sorted_types[:5]
        ]

        # Focus on specific cancer type if requested
        focus_profile = None
        if cancer_type and cancer_type.upper() in expression_profile:
            focus_profile = expression_profile[cancer_type.upper()]

        result = {
            "gene": gene,
            "layer": "transcriptomics",
            "layer_score": layer_score,
            "data_source": "TCGA/GTEx",
            "total_cancer_types_analyzed": len(TCGA_CANCER_TYPES),
            "overexpressed_in": len(overexpressed_types),
            "significantly_altered_in": len(significant_types),
            "global_tumor_specificity": round(global_specificity, 4),
            "expression_consistency": round(consistency, 4),
            "mean_tumor_expression": round(mean_tumor, 2),
            "mean_normal_expression": round(mean_normal, 2),
            "global_fold_change": round(mean_tumor / max(mean_normal, 0.01), 2),
            "top_cancer_types": top_cancers,
            "is_known_target": is_known_target,
            "known_target_cancers": known_cancers,
            "expression_profile": expression_profile,
            "focus_cancer": focus_profile,
            "summary": self._generate_summary(gene, layer_score, overexpressed_types, top_cancers),
        }

        self._cache[cache_key] = result
        return result

    def _generate_summary(self, gene: str, score: float, overexpr: list, top: list) -> str:
        """Generate a human-readable transcriptomics summary."""
        if score >= 0.7:
            quality = "strong"
        elif score >= 0.4:
            quality = "moderate"
        else:
            quality = "weak"

        top_names = ", ".join(t["cancer_name"] for t in top[:3])
        return (
            f"{gene} shows {quality} transcriptomic evidence as a CAR-T target "
            f"(score: {score:.2f}). Overexpressed in {len(overexpr)}/33 TCGA cancer types. "
            f"Highest differential expression in: {top_names}."
        )

    def get_expression_heatmap(self, genes: list[str]) -> dict:
        """Generate expression heatmap data for multiple genes across cancer types."""
        heatmap = {}
        for gene in genes[:20]:  # Cap at 20 genes
            analysis = self.analyze(gene)
            heatmap[gene] = {
                ct: {
                    "tumor": profile["tumor_expression_tpm"],
                    "normal": profile["normal_expression_tpm"],
                    "log2fc": profile["log2_fold_change"],
                    "significant": profile["is_significant"],
                }
                for ct, profile in analysis["expression_profile"].items()
            }

        return {
            "genes": list(heatmap.keys()),
            "cancer_types": TCGA_CANCER_TYPES,
            "cancer_names": CANCER_NAMES,
            "data": heatmap,
        }

    def get_differential_expression(self, gene: str, cancer_type: str) -> dict:
        """Get detailed differential expression for a specific gene-cancer pair."""
        analysis = self.analyze(gene, cancer_type)
        profile = analysis.get("focus_cancer")
        if not profile:
            return {"error": f"No data for {gene} in {cancer_type}"}

        seed = int(hashlib.md5(f"{gene}_{cancer_type}_de".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Generate sample-level expression distributions
        n_tumor = profile["n_tumor_samples"]
        n_normal = profile["n_normal_samples"]
        tumor_mean = profile["tumor_expression_tpm"]
        normal_mean = profile["normal_expression_tpm"]

        tumor_samples = [max(0, rng.gauss(tumor_mean, tumor_mean * 0.3)) for _ in range(min(n_tumor, 50))]
        normal_samples = [max(0, rng.gauss(normal_mean, normal_mean * 0.4)) for _ in range(min(n_normal, 30))]

        return {
            "gene": gene.upper(),
            "cancer_type": cancer_type.upper(),
            "cancer_name": CANCER_NAMES.get(cancer_type.upper(), cancer_type),
            "tumor_samples": [round(v, 2) for v in tumor_samples],
            "normal_samples": [round(v, 2) for v in normal_samples],
            "tumor_mean": round(tumor_mean, 2),
            "normal_mean": round(normal_mean, 2),
            "log2_fold_change": profile["log2_fold_change"],
            "p_value": profile["p_value"],
            "effect_size": round(abs(profile["log2_fold_change"]) / max(1.0, (sum(tumor_samples) / len(tumor_samples)) * 0.1), 3),
        }

    # ─── Survival Analysis ───────────────────────────────────────────────────

    def survival_analysis(self, gene: str, cancer_type: str = "BRCA") -> dict:
        """
        Kaplan-Meier survival analysis based on gene expression levels.
        Stratifies patients into high/low expression groups and computes
        survival statistics including hazard ratio and log-rank p-value.
        """
        gene = gene.upper().strip()
        ct = cancer_type.upper()
        seed = int(hashlib.md5(f"{gene}_{ct}_surv".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        known_cancers = KNOWN_TARGET_CANCERS.get(gene, [])
        is_relevant = ct in known_cancers

        # Generate survival data for high/low expression groups
        n_high = rng.randint(100, 400)
        n_low = rng.randint(100, 400)

        # Median survival months
        if is_relevant:
            high_median = rng.uniform(8, 24)
            low_median = rng.uniform(24, 60)
        else:
            high_median = rng.uniform(18, 48)
            low_median = rng.uniform(20, 52)

        # Generate individual survival times
        high_times = []
        high_censored = []
        for _ in range(n_high):
            t = max(0.5, rng.expovariate(1.0 / high_median))
            censored = rng.random() > 0.7
            high_times.append(round(min(t, 120), 1))
            high_censored.append(censored)

        low_times = []
        low_censored = []
        for _ in range(n_low):
            t = max(0.5, rng.expovariate(1.0 / low_median))
            censored = rng.random() > 0.65
            low_times.append(round(min(t, 120), 1))
            low_censored.append(censored)

        # Kaplan-Meier curve data points
        km_high = self._compute_km_curve(high_times, high_censored, rng)
        km_low = self._compute_km_curve(low_times, low_censored, rng)

        # Hazard ratio
        hr = round(low_median / max(high_median, 0.1), 2)
        hr_ci_low = round(hr * rng.uniform(0.7, 0.9), 2)
        hr_ci_high = round(hr * rng.uniform(1.1, 1.4), 2)

        # Log-rank p-value
        if is_relevant:
            log_rank_p = rng.uniform(1e-8, 0.01)
        elif abs(high_median - low_median) > 10:
            log_rank_p = rng.uniform(0.001, 0.05)
        else:
            log_rank_p = rng.uniform(0.05, 0.8)

        # 5-year survival rates
        high_5yr = round(sum(1 for t in high_times if t >= 60) / max(len(high_times), 1), 3)
        low_5yr = round(sum(1 for t in low_times if t >= 60) / max(len(low_times), 1), 3)

        return {
            "gene": gene,
            "cancer_type": ct,
            "cancer_name": CANCER_NAMES.get(ct, ct),
            "analysis_type": "kaplan_meier_survival",
            "expression_cutoff": "median",
            "high_expression_group": {
                "n_patients": n_high,
                "median_survival_months": round(high_median, 1),
                "five_year_survival_rate": high_5yr,
                "events": sum(1 for c in high_censored if not c),
                "censored": sum(1 for c in high_censored if c),
            },
            "low_expression_group": {
                "n_patients": n_low,
                "median_survival_months": round(low_median, 1),
                "five_year_survival_rate": low_5yr,
                "events": sum(1 for c in low_censored if not c),
                "censored": sum(1 for c in low_censored if c),
            },
            "hazard_ratio": hr,
            "hazard_ratio_ci": [hr_ci_low, hr_ci_high],
            "log_rank_p_value": float(f"{log_rank_p:.2e}"),
            "is_significant": log_rank_p < 0.05,
            "prognostic_direction": "poor" if high_median < low_median else "favorable",
            "km_curve_high": km_high,
            "km_curve_low": km_low,
            "summary": (
                f"High {gene} expression is associated with "
                f"{'poor' if high_median < low_median else 'favorable'} prognosis in {CANCER_NAMES.get(ct, ct)} "
                f"(HR={hr}, p={log_rank_p:.2e}). Median survival: "
                f"{high_median:.1f} months (high) vs {low_median:.1f} months (low)."
            ),
        }

    def _compute_km_curve(self, times: list, censored: list, rng) -> list:
        """Compute Kaplan-Meier step function data points."""
        events = sorted(
            [(t, not c) for t, c in zip(times, censored)],
            key=lambda x: x[0],
        )
        n_at_risk = len(events)
        survival = 1.0
        curve = [{"time": 0, "survival": 1.0, "at_risk": n_at_risk}]

        for i, (time, is_event) in enumerate(events):
            if is_event and n_at_risk > 0:
                survival *= (n_at_risk - 1) / n_at_risk
                curve.append({
                    "time": round(time, 1),
                    "survival": round(survival, 4),
                    "at_risk": n_at_risk,
                })
            n_at_risk -= 1

            if len(curve) > 50:
                break

        return curve

    # ─── Coexpression Network ────────────────────────────────────────────────

    def coexpression_network(self, gene: str, n_neighbors: int = 20) -> dict:
        """
        Build coexpression network for a gene.
        Identifies genes with correlated expression patterns,
        important for understanding target biology and combination strategies.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 42)

        # Coexpressed gene pools by functional category
        immune_genes = ["CD3D", "CD3E", "CD4", "CD8A", "CD8B", "FOXP3", "CTLA4", "PDCD1",
                        "LAG3", "TIGIT", "HAVCR2", "ICOS", "CD28", "GZMB", "PRF1", "IFNG",
                        "TNF", "IL2", "IL2RA", "IL7R", "CD69", "CD27", "CD274", "CD44"]
        signaling_genes = ["AKT1", "MTOR", "PIK3CA", "KRAS", "BRAF", "MAPK1", "MAPK3",
                           "JAK1", "JAK2", "STAT3", "STAT5A", "SRC", "RAF1", "MEK1",
                           "ERK1", "RAS", "WNT1", "NOTCH1", "NFKB1", "MYC"]
        surface_genes = ["CD19", "CD20", "CD22", "CD33", "CD38", "HER2", "EGFR", "MSLN",
                         "GPC3", "PSMA", "EpCAM", "MUC1", "BCMA", "CD70", "CD30",
                         "TROP2", "NECTIN4", "B7H3", "FRα", "CLDN18.2"]
        metabolic_genes = ["HK2", "PKM", "LDHA", "GLUT1", "GLS", "FASN", "ACLY",
                           "IDH1", "IDH2", "SDH", "FH", "MDH2", "CS", "ACO2",
                           "OGDH", "DLST", "DLD", "PDH", "PDHB"]
        apoptosis_genes = ["BCL2", "BAX", "BAK1", "MCL1", "BIM", "BID", "PUMA",
                           "NOXA", "CASP3", "CASP8", "CASP9", "RIPK1", "RIPK3",
                           "MLKL", "FADD", "TRADD", "XIAP", "SMAC"]

        all_candidate_genes = immune_genes + signaling_genes + surface_genes + metabolic_genes + apoptosis_genes
        all_candidate_genes = [g for g in all_candidate_genes if g != gene]
        rng.shuffle(all_candidate_genes)

        # Select neighbors
        selected = all_candidate_genes[:n_neighbors]
        neighbors = []

        for i, neighbor_gene in enumerate(selected):
            n_seed = int(hashlib.md5(f"{gene}_{neighbor_gene}".encode()).hexdigest()[:8], 16)
            n_rng = random.Random(n_seed)

            # Correlation coefficient
            if neighbor_gene in immune_genes and gene in surface_genes:
                correlation = n_rng.uniform(0.3, 0.85)
            elif neighbor_gene in surface_genes and gene in surface_genes:
                correlation = n_rng.uniform(0.2, 0.7)
            else:
                correlation = n_rng.uniform(-0.3, 0.6)

            p_value = max(1e-30, 10 ** (-abs(correlation) * n_rng.uniform(5, 20)))

            # Determine category
            category = "other"
            if neighbor_gene in immune_genes:
                category = "immune"
            elif neighbor_gene in signaling_genes:
                category = "signaling"
            elif neighbor_gene in surface_genes:
                category = "surface"
            elif neighbor_gene in metabolic_genes:
                category = "metabolic"
            elif neighbor_gene in apoptosis_genes:
                category = "apoptosis"

            # Mutual information
            mi = round(abs(correlation) * n_rng.uniform(0.5, 1.5), 3)

            neighbors.append({
                "gene": neighbor_gene,
                "correlation": round(correlation, 4),
                "p_value": float(f"{p_value:.2e}"),
                "category": category,
                "mutual_information": mi,
                "interaction_type": "positive" if correlation > 0 else "negative",
                "is_significant": p_value < 0.01,
                "rank": i + 1,
            })

        # Sort by absolute correlation
        neighbors.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        for i, n in enumerate(neighbors):
            n["rank"] = i + 1

        # Network statistics
        positive_corr = [n for n in neighbors if n["correlation"] > 0]
        negative_corr = [n for n in neighbors if n["correlation"] < 0]
        significant = [n for n in neighbors if n["is_significant"]]

        # Network edges for visualization
        edges = []
        for n in neighbors[:15]:
            edges.append({
                "source": gene,
                "target": n["gene"],
                "weight": abs(n["correlation"]),
                "type": n["interaction_type"],
                "category": n["category"],
            })

        # Add some inter-neighbor edges
        for i in range(min(10, len(selected) - 1)):
            for j in range(i + 1, min(i + 3, len(selected))):
                e_rng = random.Random(seed + i * 100 + j)
                if e_rng.random() > 0.6:
                    edges.append({
                        "source": selected[i],
                        "target": selected[j],
                        "weight": round(e_rng.uniform(0.2, 0.6), 3),
                        "type": "positive" if e_rng.random() > 0.3 else "negative",
                        "category": "inter-neighbor",
                    })

        # Hub score (how connected is this gene)
        hub_score = round(sum(abs(n["correlation"]) for n in neighbors) / max(len(neighbors), 1), 3)

        return {
            "gene": gene,
            "analysis_type": "coexpression_network",
            "n_neighbors": len(neighbors),
            "neighbors": neighbors,
            "network_edges": edges,
            "network_stats": {
                "positive_correlations": len(positive_corr),
                "negative_correlations": len(negative_corr),
                "significant_correlations": len(significant),
                "mean_correlation": round(sum(n["correlation"] for n in neighbors) / max(len(neighbors), 1), 4),
                "max_correlation": round(max(n["correlation"] for n in neighbors), 4) if neighbors else 0,
                "hub_score": hub_score,
            },
            "category_breakdown": {
                "immune": len([n for n in neighbors if n["category"] == "immune"]),
                "signaling": len([n for n in neighbors if n["category"] == "signaling"]),
                "surface": len([n for n in neighbors if n["category"] == "surface"]),
                "metabolic": len([n for n in neighbors if n["category"] == "metabolic"]),
                "apoptosis": len([n for n in neighbors if n["category"] == "apoptosis"]),
            },
        }

    # ─── GSEA Pathway Enrichment ─────────────────────────────────────────────

    def gsea_pathway_enrichment(self, gene: str) -> dict:
        """
        Gene Set Enrichment Analysis.
        Identifies biological pathways and gene ontology terms
        enriched in genes coexpressed with the target.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 200)

        # Pathways database
        pathways = [
            {"id": "GO:0006955", "name": "Immune Response", "category": "Biological Process", "size": 1429},
            {"id": "GO:0006915", "name": "Apoptotic Process", "category": "Biological Process", "size": 893},
            {"id": "GO:0007165", "name": "Signal Transduction", "category": "Biological Process", "size": 3214},
            {"id": "GO:0006954", "name": "Inflammatory Response", "category": "Biological Process", "size": 653},
            {"id": "GO:0008283", "name": "Cell Proliferation", "category": "Biological Process", "size": 1789},
            {"id": "GO:0016477", "name": "Cell Migration", "category": "Biological Process", "size": 887},
            {"id": "GO:0007155", "name": "Cell Adhesion", "category": "Biological Process", "size": 1023},
            {"id": "GO:0006281", "name": "DNA Repair", "category": "Biological Process", "size": 456},
            {"id": "GO:0006935", "name": "Chemotaxis", "category": "Biological Process", "size": 543},
            {"id": "GO:0001525", "name": "Angiogenesis", "category": "Biological Process", "size": 412},
            {"id": "KEGG:hsa04151", "name": "PI3K-Akt Signaling", "category": "KEGG Pathway", "size": 354},
            {"id": "KEGG:hsa04010", "name": "MAPK Signaling", "category": "KEGG Pathway", "size": 295},
            {"id": "KEGG:hsa04060", "name": "Cytokine-Cytokine Receptor", "category": "KEGG Pathway", "size": 294},
            {"id": "KEGG:hsa04110", "name": "Cell Cycle", "category": "KEGG Pathway", "size": 124},
            {"id": "KEGG:hsa04210", "name": "Apoptosis", "category": "KEGG Pathway", "size": 136},
            {"id": "KEGG:hsa04310", "name": "Wnt Signaling", "category": "KEGG Pathway", "size": 158},
            {"id": "KEGG:hsa04660", "name": "T Cell Receptor Signaling", "category": "KEGG Pathway", "size": 101},
            {"id": "KEGG:hsa04650", "name": "NK Cell Mediated Cytotoxicity", "category": "KEGG Pathway", "size": 131},
            {"id": "KEGG:hsa05200", "name": "Pathways in Cancer", "category": "KEGG Pathway", "size": 526},
            {"id": "KEGG:hsa04514", "name": "Cell Adhesion Molecules", "category": "KEGG Pathway", "size": 145},
            {"id": "REACTOME:R-HSA-168256", "name": "Immune System", "category": "Reactome", "size": 2038},
            {"id": "REACTOME:R-HSA-5653656", "name": "Vesicle-mediated Transport", "category": "Reactome", "size": 662},
            {"id": "REACTOME:R-HSA-162582", "name": "Signal Transduction", "category": "Reactome", "size": 2611},
            {"id": "REACTOME:R-HSA-1280218", "name": "Adaptive Immune System", "category": "Reactome", "size": 759},
            {"id": "REACTOME:R-HSA-1280215", "name": "Cytokine Signaling in Immune System", "category": "Reactome", "size": 691},
            {"id": "HALLMARK:HALLMARK_INFLAMMATORY_RESPONSE", "name": "Inflammatory Response", "category": "MSigDB Hallmark", "size": 200},
            {"id": "HALLMARK:HALLMARK_TNFA_SIGNALING_VIA_NFKB", "name": "TNFα Signaling via NFκB", "category": "MSigDB Hallmark", "size": 200},
            {"id": "HALLMARK:HALLMARK_APOPTOSIS", "name": "Apoptosis", "category": "MSigDB Hallmark", "size": 161},
            {"id": "HALLMARK:HALLMARK_P53_PATHWAY", "name": "p53 Pathway", "category": "MSigDB Hallmark", "size": 200},
            {"id": "HALLMARK:HALLMARK_MYC_TARGETS_V1", "name": "MYC Targets V1", "category": "MSigDB Hallmark", "size": 200},
        ]

        # Score each pathway
        enriched = []
        for pw in pathways:
            pw_seed = int(hashlib.md5(f"{gene}_{pw['id']}".encode()).hexdigest()[:8], 16)
            pw_rng = random.Random(pw_seed)

            # Enrichment score
            nes = pw_rng.gauss(0, 1.5)
            nominal_p = max(1e-10, 10 ** (-abs(nes) * pw_rng.uniform(1, 5)))
            fdr_q = min(1.0, nominal_p * len(pathways) * pw_rng.uniform(0.5, 2.0))
            fwer_p = min(1.0, nominal_p * len(pathways))

            n_leading_edge = int(pw["size"] * pw_rng.uniform(0.1, 0.4))

            enriched.append({
                "pathway_id": pw["id"],
                "pathway_name": pw["name"],
                "category": pw["category"],
                "gene_set_size": pw["size"],
                "enrichment_score": round(nes, 4),
                "normalized_enrichment_score": round(nes, 4),
                "nominal_p_value": float(f"{nominal_p:.2e}"),
                "fdr_q_value": round(fdr_q, 4),
                "fwer_p_value": round(fwer_p, 4),
                "n_leading_edge_genes": n_leading_edge,
                "is_significant": fdr_q < 0.25,
                "direction": "upregulated" if nes > 0 else "downregulated",
            })

        # Sort by NES
        enriched.sort(key=lambda x: abs(x["normalized_enrichment_score"]), reverse=True)

        significant = [e for e in enriched if e["is_significant"]]
        up = [e for e in significant if e["direction"] == "upregulated"]
        down = [e for e in significant if e["direction"] == "downregulated"]

        return {
            "gene": gene,
            "analysis_type": "gsea_pathway_enrichment",
            "total_pathways_tested": len(pathways),
            "significant_pathways": len(significant),
            "upregulated_pathways": len(up),
            "downregulated_pathways": len(down),
            "pathways": enriched,
            "top_upregulated": up[:5],
            "top_downregulated": down[:5],
            "databases_used": ["GO", "KEGG", "Reactome", "MSigDB Hallmarks"],
        }

    # ─── Isoform Analysis ────────────────────────────────────────────────────

    def isoform_analysis(self, gene: str) -> dict:
        """
        Transcript isoform analysis.
        Identifies splice variants and their relative expression,
        critical for identifying the correct CAR-T target epitope.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 300)

        n_isoforms = rng.randint(2, 8)
        n_exons = rng.randint(5, 25)
        gene_length_bp = n_exons * rng.randint(100, 500)

        isoforms = []
        total_expression = 0

        for i in range(n_isoforms):
            iso_rng = random.Random(seed + 300 + i)

            # Isoform metadata
            transcript_id = f"ENST{iso_rng.randint(10000000, 99999999)}.{iso_rng.randint(1, 5)}"
            n_iso_exons = max(2, n_exons - iso_rng.randint(0, n_exons // 2))
            coding_length = n_iso_exons * iso_rng.randint(80, 400)
            protein_length = coding_length // 3

            # Expression level (first isoform is canonical/dominant)
            if i == 0:
                expression = iso_rng.uniform(50, 200)
            elif i == 1:
                expression = iso_rng.uniform(10, 80)
            else:
                expression = iso_rng.uniform(0.5, 20)

            total_expression += expression

            # Exon structure
            exon_structure = []
            current_pos = iso_rng.randint(1000, 50000)
            for j in range(n_iso_exons):
                exon_len = iso_rng.randint(50, 500)
                exon_structure.append({
                    "exon_number": j + 1,
                    "start": current_pos,
                    "end": current_pos + exon_len,
                    "length": exon_len,
                    "is_coding": j > 0 and j < n_iso_exons - 1,
                })
                current_pos += exon_len + iso_rng.randint(500, 10000)

            # Functional domains
            domains = []
            domain_types = ["Extracellular domain", "Transmembrane domain", "Intracellular domain",
                            "Signal peptide", "Ig-like domain", "EGF-like domain", "Kinase domain",
                            "SH2 domain", "PDZ domain"]
            n_domains = iso_rng.randint(1, 4)
            for d in iso_rng.sample(domain_types, min(n_domains, len(domain_types))):
                d_start = iso_rng.randint(1, max(1, protein_length - 50))
                d_len = iso_rng.randint(20, min(150, protein_length - d_start))
                domains.append({
                    "name": d,
                    "start_aa": d_start,
                    "end_aa": d_start + d_len,
                    "length_aa": d_len,
                })

            # CAR-T epitope presence
            has_car_t_epitope = i == 0 or iso_rng.random() > 0.4

            isoforms.append({
                "transcript_id": transcript_id,
                "isoform_number": i + 1,
                "is_canonical": i == 0,
                "n_exons": n_iso_exons,
                "coding_length_bp": coding_length,
                "protein_length_aa": protein_length,
                "expression_tpm": round(expression, 2),
                "exon_structure": exon_structure[:5],  # First 5 exons
                "functional_domains": domains,
                "has_car_t_epitope": has_car_t_epitope,
                "nmd_candidate": protein_length < 100 and iso_rng.random() > 0.5,
            })

        # Normalize expression percentages
        for iso in isoforms:
            iso["expression_fraction"] = round(iso["expression_tpm"] / max(total_expression, 0.01), 4)

        # Dominant isoform analysis
        dominant = isoforms[0]
        epitope_isoforms = [iso for iso in isoforms if iso["has_car_t_epitope"]]
        epitope_coverage = sum(iso["expression_fraction"] for iso in epitope_isoforms)

        return {
            "gene": gene,
            "analysis_type": "isoform_analysis",
            "total_isoforms": n_isoforms,
            "total_exons": n_exons,
            "gene_length_bp": gene_length_bp,
            "isoforms": isoforms,
            "dominant_isoform": dominant["transcript_id"],
            "dominant_expression_fraction": dominant["expression_fraction"],
            "epitope_positive_isoforms": len(epitope_isoforms),
            "epitope_coverage": round(epitope_coverage, 4),
            "alternative_splicing_complexity": round(n_isoforms / 8.0, 3),
            "summary": (
                f"{gene} has {n_isoforms} transcript isoforms. Canonical isoform "
                f"({dominant['transcript_id']}) accounts for {dominant['expression_fraction']:.0%} "
                f"of total expression. CAR-T epitope present in {len(epitope_isoforms)}/{n_isoforms} "
                f"isoforms ({epitope_coverage:.0%} expression coverage)."
            ),
        }

    # ─── GTEx Normal Tissue Profile ──────────────────────────────────────────

    def gtex_normal_tissue_profile(self, gene: str) -> dict:
        """
        Normal tissue expression profile from GTEx.
        Critical for identifying off-target toxicity risk —
        high expression in vital normal tissues = high CAR-T danger.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 400)

        # GTEx tissues (54 tissue types)
        tissues = {
            "Brain - Cortex": {"vital": True, "regenerative": False},
            "Brain - Cerebellum": {"vital": True, "regenerative": False},
            "Brain - Hippocampus": {"vital": True, "regenerative": False},
            "Heart - Left Ventricle": {"vital": True, "regenerative": False},
            "Heart - Atrial Appendage": {"vital": True, "regenerative": False},
            "Lung": {"vital": True, "regenerative": True},
            "Liver": {"vital": True, "regenerative": True},
            "Kidney - Cortex": {"vital": True, "regenerative": False},
            "Kidney - Medulla": {"vital": True, "regenerative": False},
            "Pancreas": {"vital": True, "regenerative": False},
            "Small Intestine": {"vital": False, "regenerative": True},
            "Colon - Sigmoid": {"vital": False, "regenerative": True},
            "Colon - Transverse": {"vital": False, "regenerative": True},
            "Stomach": {"vital": False, "regenerative": True},
            "Esophagus - Mucosa": {"vital": False, "regenerative": True},
            "Esophagus - Muscularis": {"vital": False, "regenerative": True},
            "Skin - Sun Exposed": {"vital": False, "regenerative": True},
            "Skin - Not Sun Exposed": {"vital": False, "regenerative": True},
            "Breast - Mammary": {"vital": False, "regenerative": True},
            "Adipose - Subcutaneous": {"vital": False, "regenerative": False},
            "Adipose - Visceral": {"vital": False, "regenerative": False},
            "Muscle - Skeletal": {"vital": False, "regenerative": True},
            "Nerve - Tibial": {"vital": False, "regenerative": False},
            "Thyroid": {"vital": False, "regenerative": True},
            "Adrenal Gland": {"vital": False, "regenerative": False},
            "Pituitary": {"vital": True, "regenerative": False},
            "Spleen": {"vital": False, "regenerative": True},
            "Whole Blood": {"vital": False, "regenerative": True},
            "Bone Marrow": {"vital": False, "regenerative": True},
            "Lymphocytes": {"vital": False, "regenerative": True},
            "Testis": {"vital": False, "regenerative": True},
            "Ovary": {"vital": False, "regenerative": False},
            "Uterus": {"vital": False, "regenerative": True},
            "Prostate": {"vital": False, "regenerative": True},
            "Bladder": {"vital": False, "regenerative": True},
            "Salivary Gland": {"vital": False, "regenerative": True},
        }

        known_cancers = KNOWN_TARGET_CANCERS.get(gene, [])
        is_heme_target = any(c in ["DLBC", "LAML"] for c in known_cancers)

        tissue_profiles = {}
        vital_tissue_risks = []

        for tissue_name, tissue_info in tissues.items():
            t_seed = int(hashlib.md5(f"{gene}_{tissue_name}".encode()).hexdigest()[:8], 16)
            t_rng = random.Random(t_seed)

            # Expression in normal tissue
            if is_heme_target and ("Blood" in tissue_name or "Bone" in tissue_name or "Spleen" in tissue_name or "Lymph" in tissue_name):
                expression = t_rng.uniform(2.0, 15.0)
            elif tissue_info["vital"]:
                expression = t_rng.uniform(0.1, 3.0)
            else:
                expression = t_rng.uniform(0.0, 5.0)

            n_samples = t_rng.randint(50, 500)
            std_dev = expression * t_rng.uniform(0.2, 0.6)

            profile = {
                "tissue": tissue_name,
                "expression_tpm": round(expression, 2),
                "std_deviation": round(std_dev, 2),
                "n_samples": n_samples,
                "is_vital": tissue_info["vital"],
                "is_regenerative": tissue_info["regenerative"],
                "expression_category": "high" if expression > 5 else "moderate" if expression > 1 else "low",
                "toxicity_risk": "high" if (expression > 3 and tissue_info["vital"]) else
                                 "moderate" if (expression > 1 and tissue_info["vital"]) else "low",
            }

            tissue_profiles[tissue_name] = profile

            if expression > 2 and tissue_info["vital"]:
                vital_tissue_risks.append({
                    "tissue": tissue_name,
                    "expression": round(expression, 2),
                    "risk_level": profile["toxicity_risk"],
                })

        # Safety metrics
        vital_tissues = {k: v for k, v in tissue_profiles.items() if v["is_vital"]}
        max_vital_expr = max(v["expression_tpm"] for v in vital_tissues.values()) if vital_tissues else 0
        mean_vital_expr = sum(v["expression_tpm"] for v in vital_tissues.values()) / max(len(vital_tissues), 1)

        all_expr = [v["expression_tpm"] for v in tissue_profiles.values()]
        tissue_specificity_index = 1.0 - (sum(1 for e in all_expr if e > 1) / max(len(all_expr), 1))

        return {
            "gene": gene,
            "analysis_type": "gtex_normal_tissue",
            "total_tissues": len(tissue_profiles),
            "tissue_profiles": tissue_profiles,
            "safety_assessment": {
                "max_vital_tissue_expression": round(max_vital_expr, 2),
                "mean_vital_tissue_expression": round(mean_vital_expr, 2),
                "vital_tissue_risks": sorted(vital_tissue_risks, key=lambda x: x["expression"], reverse=True),
                "tissue_specificity_index": round(tissue_specificity_index, 3),
                "n_tissues_with_high_expression": sum(1 for e in all_expr if e > 5),
                "n_vital_tissues_at_risk": len(vital_tissue_risks),
                "overall_safety": "good" if len(vital_tissue_risks) == 0 else
                                  "moderate" if len(vital_tissue_risks) <= 2 else "concerning",
            },
        }

    # ─── Pan-Cancer Meta-Analysis ────────────────────────────────────────────

    def pan_cancer_meta_analysis(self, gene: str) -> dict:
        """
        Pan-cancer meta-analysis combining data across all TCGA cancer types.
        Computes aggregate statistics, heterogeneity measures (I² Cochran's Q),
        and forest plot data for publication-quality evidence synthesis.
        """
        gene = gene.upper().strip()
        analysis = self.analyze(gene)
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 500)

        # Extract per-cancer effect sizes
        effects = []
        for ct, profile in analysis["expression_profile"].items():
            weight = profile["n_tumor_samples"] + profile["n_normal_samples"]
            effects.append({
                "cancer_type": ct,
                "cancer_name": CANCER_NAMES.get(ct, ct),
                "log2fc": profile["log2_fold_change"],
                "se": round(abs(profile["log2_fold_change"]) * rng.uniform(0.1, 0.4), 3),
                "weight": weight,
                "p_value": profile["p_value"],
                "n_total": weight,
                "ci_lower": round(profile["log2_fold_change"] - rng.uniform(0.3, 1.0), 3),
                "ci_upper": round(profile["log2_fold_change"] + rng.uniform(0.3, 1.0), 3),
            })

        # Fixed-effect pooled estimate
        total_weight = sum(e["weight"] for e in effects)
        pooled_log2fc = sum(e["log2fc"] * e["weight"] for e in effects) / max(total_weight, 1)
        pooled_se = 1.0 / math.sqrt(max(total_weight, 1))

        # Heterogeneity stats (Cochran's Q and I²)
        q_statistic = sum(
            e["weight"] * (e["log2fc"] - pooled_log2fc) ** 2
            for e in effects
        )
        df = len(effects) - 1
        i_squared = max(0, (q_statistic - df) / max(q_statistic, 0.01) * 100)
        tau_squared = max(0, (q_statistic - df) / max(total_weight - sum(e["weight"] ** 2 for e in effects) / total_weight, 1))

        # Random-effects pooled estimate
        re_weights = [1.0 / (e["se"] ** 2 + tau_squared + 0.01) for e in effects]
        re_total = sum(re_weights)
        re_pooled = sum(e["log2fc"] * w for e, w in zip(effects, re_weights)) / max(re_total, 0.01)

        # Forest plot data (sorted by effect size)
        forest_plot = sorted(effects, key=lambda x: x["log2fc"], reverse=True)

        return {
            "gene": gene,
            "analysis_type": "pan_cancer_meta_analysis",
            "n_cancer_types": len(effects),
            "total_samples": total_weight,
            "fixed_effect": {
                "pooled_log2fc": round(pooled_log2fc, 4),
                "pooled_se": round(pooled_se, 4),
                "z_score": round(pooled_log2fc / max(pooled_se, 0.001), 2),
                "p_value": float(f"{max(1e-30, 10 ** (-abs(pooled_log2fc / max(pooled_se, 0.001)) * 0.5)):.2e}"),
            },
            "random_effects": {
                "pooled_log2fc": round(re_pooled, 4),
                "tau_squared": round(tau_squared, 4),
            },
            "heterogeneity": {
                "cochran_q": round(q_statistic, 2),
                "df": df,
                "i_squared": round(i_squared, 1),
                "i_squared_interpretation": "low" if i_squared < 25 else "moderate" if i_squared < 75 else "high",
                "tau_squared": round(tau_squared, 4),
            },
            "forest_plot": forest_plot,
            "summary": (
                f"Pan-cancer meta-analysis of {gene} across {len(effects)} TCGA cancer types "
                f"(N={total_weight}). Pooled log2FC={pooled_log2fc:.2f} (fixed-effect). "
                f"Heterogeneity: I²={i_squared:.0f}% "
                f"({'low' if i_squared < 25 else 'moderate' if i_squared < 75 else 'substantial'})."
            ),
        }

    # ─── Expression Correlation Matrix ───────────────────────────────────────

    def expression_correlation_matrix(self, genes: list, cancer_type: str = "BRCA") -> dict:
        """
        Compute pairwise expression correlation matrix for a set of genes.
        Useful for identifying co-targeting opportunities.
        """
        genes = [g.upper().strip() for g in genes[:15]]
        seed = int(hashlib.md5(f"{'_'.join(genes)}_{cancer_type}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        matrix = {}
        for i, g1 in enumerate(genes):
            matrix[g1] = {}
            for j, g2 in enumerate(genes):
                if g1 == g2:
                    matrix[g1][g2] = 1.0
                elif g2 in matrix and g1 in matrix[g2]:
                    matrix[g1][g2] = matrix[g2][g1]
                else:
                    pair_seed = int(hashlib.md5(f"{min(g1, g2)}_{max(g1, g2)}".encode()).hexdigest()[:8], 16)
                    pair_rng = random.Random(pair_seed)
                    corr = round(pair_rng.uniform(-0.5, 0.9), 4)
                    matrix[g1][g2] = corr

        # Identify strongest correlations
        pairs = []
        for i, g1 in enumerate(genes):
            for j, g2 in enumerate(genes):
                if i < j:
                    pairs.append({
                        "gene1": g1,
                        "gene2": g2,
                        "correlation": matrix[g1][g2],
                        "is_strong": abs(matrix[g1][g2]) > 0.5,
                    })
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "genes": genes,
            "cancer_type": cancer_type,
            "analysis_type": "expression_correlation_matrix",
            "matrix": matrix,
            "top_correlations": pairs[:10],
            "n_strong_correlations": sum(1 for p in pairs if p["is_strong"]),
        }

    # ─── Alternative Splicing Analysis ───────────────────────────────────────

    def alternative_splicing_analysis(self, gene: str) -> dict:
        """
        Analyze alternative splicing events for the target gene across
        cancer types. Identifies therapeutically relevant isoform switches.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 7000)

        splice_types = [
            "exon skipping (SE)", "alternative 5' splice site (A5SS)",
            "alternative 3' splice site (A3SS)", "mutually exclusive exons (MXE)",
            "retained intron (RI)",
        ]

        n_exons = rng.randint(5, 30)
        events = []
        for i in range(rng.randint(3, 12)):
            ev_rng = random.Random(seed + 7000 + i * 41)
            psi_normal = ev_rng.uniform(0.1, 0.9)
            psi_tumor = ev_rng.uniform(0.1, 0.9)
            delta_psi = psi_tumor - psi_normal

            events.append({
                "event_id": f"SPLICE_{gene}_{i+1:03d}",
                "splice_type": ev_rng.choice(splice_types),
                "exon_involved": f"exon_{ev_rng.randint(2, n_exons - 1)}",
                "psi_normal": round(psi_normal, 3),
                "psi_tumor": round(psi_tumor, 3),
                "delta_psi": round(delta_psi, 3),
                "statistically_significant": abs(delta_psi) > 0.15,
                "affects_epitope": ev_rng.random() > 0.6,
                "affects_surface_domain": ev_rng.random() > 0.7,
                "spliceosomal_factor": ev_rng.choice([
                    "SRSF1", "SRSF3", "hnRNPA1", "RBFOX2", "QKI",
                    "PTBP1", "ESRP1", "MBNL1", "RBM10",
                ]),
            })

        epitope_affecting = [e for e in events if e["affects_epitope"]]
        surface_affecting = [e for e in events if e["affects_surface_domain"]]

        return {
            "gene": gene,
            "analysis_type": "alternative_splicing",
            "data_source": "TCGA SpliceSeq / rMATS simulation",
            "total_exons": n_exons,
            "splice_events": events,
            "significant_events": sum(1 for e in events if e["statistically_significant"]),
            "epitope_affecting_events": len(epitope_affecting),
            "surface_domain_events": len(surface_affecting),
            "therapeutic_risk": (
                "HIGH: Tumor-specific isoform may lack CAR-T binding epitope"
                if len(epitope_affecting) > 2 else
                "MODERATE: Some isoform heterogeneity detected"
                if len(epitope_affecting) > 0 else
                "LOW: Stable splicing across tumor/normal"
            ),
        }

    # ─── RNA Editing Profiling ───────────────────────────────────────────────

    def rna_editing_analysis(self, gene: str) -> dict:
        """
        Profile A-to-I and C-to-U RNA editing events. Identifies post-
        transcriptional modifications that could alter protein sequence
        without genomic mutations.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 8000)

        editing_enzymes = ["ADAR1", "ADAR2", "APOBEC1", "APOBEC3A", "APOBEC3B"]

        sites = []
        n_sites = rng.randint(2, 15)
        for i in range(n_sites):
            s_rng = random.Random(seed + 8000 + i * 53)
            edit_type = s_rng.choice(["A-to-I", "C-to-U"])
            editing_level = s_rng.uniform(0.01, 0.8)

            sites.append({
                "site_id": f"EDIT_{gene}_{i+1:03d}",
                "position": s_rng.randint(100, 5000),
                "edit_type": edit_type,
                "editing_level_normal": round(s_rng.uniform(0.01, 0.5), 3),
                "editing_level_tumor": round(editing_level, 3),
                "region": s_rng.choice(["CDS", "3UTR", "5UTR", "intron", "Alu element"]),
                "amino_acid_change": s_rng.random() > 0.7,
                "enzyme": s_rng.choice(editing_enzymes),
                "functional_impact": s_rng.choice([
                    "synonymous", "missense", "creates stop codon",
                    "alters miRNA binding", "affects splicing",
                ]),
                "clinical_relevance": s_rng.choice(["high", "moderate", "low"]),
            })

        hyper_edited = sum(1 for s in sites if s["editing_level_tumor"] > 0.5)

        return {
            "gene": gene,
            "analysis_type": "rna_editing",
            "data_source": "REDIportal / DARNED simulation",
            "total_editing_sites": len(sites),
            "editing_sites": sites,
            "hyper_edited_sites": hyper_edited,
            "coding_changes": sum(1 for s in sites if s["amino_acid_change"]),
            "dominant_editor": max(
                set(s["enzyme"] for s in sites),
                key=lambda e: sum(1 for s in sites if s["enzyme"] == e),
            ),
            "neoepitope_potential": (
                "RNA editing creates potential neoepitopes for immune recognition"
                if any(s["amino_acid_change"] and s["editing_level_tumor"] > 0.3 for s in sites)
                else "No significant coding-level RNA editing detected"
            ),
        }

    # ─── Circular RNA Detection ──────────────────────────────────────────────

    def circular_rna_analysis(self, gene: str) -> dict:
        """
        Detect and characterize circular RNAs (circRNAs) derived from
        the target gene locus. circRNAs can act as miRNA sponges and
        regulate target expression.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 9000)

        n_circrnas = rng.randint(1, 8)
        circrnas = []
        for i in range(n_circrnas):
            c_rng = random.Random(seed + 9000 + i * 67)
            abundance = c_rng.uniform(0.1, 50.0)
            linear_ratio = c_rng.uniform(0.01, 2.0)

            mirna_targets = c_rng.sample(
                ["miR-21", "miR-155", "miR-29a", "miR-34a", "miR-let-7",
                 "miR-200c", "miR-122", "miR-145", "miR-16", "miR-221"],
                k=c_rng.randint(1, 5)
            )

            circrnas.append({
                "circ_id": f"circ_{gene}_{i+1:04d}",
                "backsplice_junction": f"exon{c_rng.randint(2,10)}-exon{c_rng.randint(3,15)}",
                "abundance_rpm": round(abundance, 2),
                "circular_linear_ratio": round(linear_ratio, 3),
                "is_abundant": abundance > 10,
                "sponged_mirnas": mirna_targets,
                "n_mirna_binding_sites": c_rng.randint(1, 20),
                "stability_half_life_hours": round(c_rng.uniform(12, 96), 1),
                "tumor_enriched": c_rng.random() > 0.5,
                "rna_binding_proteins": c_rng.sample(
                    ["AGO2", "IGF2BP1", "HuR", "FMRP", "QKI"], k=c_rng.randint(1, 3)
                ),
            })

        return {
            "gene": gene,
            "analysis_type": "circular_rna",
            "data_source": "circBase / CIRCpedia simulation",
            "total_circrnas": len(circrnas),
            "circular_rnas": circrnas,
            "abundant_circrnas": sum(1 for c in circrnas if c["is_abundant"]),
            "tumor_enriched": sum(1 for c in circrnas if c["tumor_enriched"]),
            "mirna_sponge_activity": (
                "High sponge activity may upregulate target through miRNA sequestration"
                if any(c["n_mirna_binding_sites"] > 10 for c in circrnas)
                else "Moderate circRNA-mediated regulation"
            ),
        }

    # ─── Competitive Endogenous RNA Network ──────────────────────────────────

    def cerna_network_analysis(self, gene: str) -> dict:
        """
        Map the competitive endogenous RNA (ceRNA) network around the target.
        Identifies lncRNAs and pseudogenes that compete for shared miRNAs.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 10000)

        shared_mirnas = rng.sample(
            ["miR-21", "miR-155", "miR-29a", "miR-34a", "let-7a",
             "miR-200c", "miR-122", "miR-145", "miR-16", "miR-221",
             "miR-15a", "miR-17", "miR-19b", "miR-93", "miR-106b"],
            k=rng.randint(3, 8)
        )

        cerna_partners = []
        n_partners = rng.randint(5, 15)
        for i in range(n_partners):
            p_rng = random.Random(seed + 10000 + i * 79)
            partner_type = p_rng.choice(["lncRNA", "pseudogene", "mRNA", "circRNA"])
            partner_mirnas = p_rng.sample(shared_mirnas, k=p_rng.randint(1, min(3, len(shared_mirnas))))

            cerna_partners.append({
                "partner_id": f"ceRNA_{gene}_{i+1}",
                "partner_type": partner_type,
                "shared_mirnas": partner_mirnas,
                "n_shared_mres": p_rng.randint(1, 8),
                "correlation_with_target": round(p_rng.uniform(-0.3, 0.9), 3),
                "expression_in_tumor": round(p_rng.uniform(0.1, 15.0), 2),
                "regulatory_direction": "positive" if p_rng.random() > 0.3 else "negative",
                "therapeutic_relevance": p_rng.choice([
                    "potential biomarker", "druggable target",
                    "resistance mechanism", "prognostic indicator", "none",
                ]),
            })

        positive_regulators = [p for p in cerna_partners if p["regulatory_direction"] == "positive"]

        return {
            "gene": gene,
            "analysis_type": "cerna_network",
            "data_source": "starBase / miRTarBase",
            "shared_mirnas": shared_mirnas,
            "n_cerna_partners": len(cerna_partners),
            "cerna_partners": cerna_partners,
            "positive_regulators": len(positive_regulators),
            "network_complexity": (
                "dense" if len(cerna_partners) > 10 else
                "moderate" if len(cerna_partners) > 5 else "sparse"
            ),
            "therapeutic_implications": (
                "Dense ceRNA network may buffer against antigen downregulation"
                if len(positive_regulators) > 3 else
                "Sparse ceRNA network — target expression may be more volatile"
            ),
        }

    # ─── Allele-Specific Expression ──────────────────────────────────────────

    def allele_specific_expression(self, gene: str) -> dict:
        """
        Analyze allele-specific expression (ASE) to detect monoallelic
        expression, imprinting, or loss of heterozygosity at the target locus.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 11000)

        n_het_snps = rng.randint(2, 10)
        snp_data = []
        for i in range(n_het_snps):
            s_rng = random.Random(seed + 11000 + i * 83)
            ref_count = s_rng.randint(20, 500)
            alt_count = s_rng.randint(20, 500)
            total = ref_count + alt_count
            allelic_ratio = ref_count / total

            snp_data.append({
                "snp_id": f"rs{s_rng.randint(1000000, 99999999)}",
                "position": s_rng.randint(1000, 200000),
                "ref_allele": s_rng.choice(["A", "C", "G", "T"]),
                "alt_allele": s_rng.choice(["A", "C", "G", "T"]),
                "ref_count": ref_count,
                "alt_count": alt_count,
                "allelic_ratio": round(allelic_ratio, 3),
                "is_imbalanced": abs(allelic_ratio - 0.5) > 0.2,
                "p_value_binomial": round(s_rng.uniform(0.0001, 0.5), 4),
                "region": s_rng.choice(["exonic", "intronic", "3UTR", "5UTR"]),
            })

        imbalanced = [s for s in snp_data if s["is_imbalanced"]]
        mean_ratio = sum(s["allelic_ratio"] for s in snp_data) / len(snp_data) if snp_data else 0.5

        return {
            "gene": gene,
            "analysis_type": "allele_specific_expression",
            "data_source": "GTEx / TCGA ASE data",
            "heterozygous_snps": len(snp_data),
            "snp_data": snp_data,
            "imbalanced_snps": len(imbalanced),
            "mean_allelic_ratio": round(mean_ratio, 3),
            "monoallelic_expression": mean_ratio > 0.8 or mean_ratio < 0.2,
            "loh_detected": len(imbalanced) > len(snp_data) * 0.7,
            "imprinting_status": (
                "potentially imprinted" if mean_ratio > 0.85 else
                "biallelic expression"
            ),
            "clinical_implication": (
                "LOH may reduce antigen density — monitor for heterogeneous loss"
                if len(imbalanced) > len(snp_data) * 0.5
                else "Balanced biallelic expression supports stable antigen display"
            ),
        }

    # ─── Immune Deconvolution from Bulk RNA-seq ──────────────────────────────

    def immune_deconvolution(self, gene: str) -> dict:
        """
        Deconvolve immune cell type proportions from bulk RNA-seq data
        using CIBERSORT/xCell-style methodology. Estimates TME composition.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 12000)

        cell_types = {
            "CD8+ T cells": rng.uniform(0.01, 0.25),
            "CD4+ T cells (non-Treg)": rng.uniform(0.02, 0.2),
            "Tregs": rng.uniform(0.01, 0.1),
            "B cells": rng.uniform(0.01, 0.15),
            "NK cells": rng.uniform(0.01, 0.1),
            "M1 macrophages": rng.uniform(0.02, 0.15),
            "M2 macrophages": rng.uniform(0.03, 0.2),
            "Dendritic cells": rng.uniform(0.01, 0.08),
            "Mast cells": rng.uniform(0.005, 0.05),
            "Neutrophils": rng.uniform(0.01, 0.1),
            "Eosinophils": rng.uniform(0.001, 0.03),
            "Monocytes": rng.uniform(0.02, 0.12),
            "MDSCs": rng.uniform(0.01, 0.15),
            "Plasma cells": rng.uniform(0.005, 0.08),
            "CAFs": rng.uniform(0.05, 0.25),
            "Endothelial cells": rng.uniform(0.02, 0.1),
        }

        total = sum(cell_types.values())
        cell_fractions = {k: round(v / total, 4) for k, v in cell_types.items()}

        cd8_fraction = cell_fractions.get("CD8+ T cells", 0)
        treg_fraction = cell_fractions.get("Tregs", 0)
        cd8_treg_ratio = round(cd8_fraction / max(treg_fraction, 0.001), 2)

        m1_fraction = cell_fractions.get("M1 macrophages", 0)
        m2_fraction = cell_fractions.get("M2 macrophages", 0)
        m1_m2_ratio = round(m1_fraction / max(m2_fraction, 0.001), 2)

        immune_score = round(sum(
            cell_fractions.get(ct, 0)
            for ct in ["CD8+ T cells", "CD4+ T cells (non-Treg)", "NK cells",
                        "M1 macrophages", "Dendritic cells"]
        ), 4)

        suppressive_score = round(sum(
            cell_fractions.get(ct, 0)
            for ct in ["Tregs", "M2 macrophages", "MDSCs"]
        ), 4)

        return {
            "gene": gene,
            "analysis_type": "immune_deconvolution",
            "data_source": "CIBERSORT / xCell / TIMER",
            "cell_fractions": cell_fractions,
            "key_ratios": {
                "cd8_treg_ratio": cd8_treg_ratio,
                "m1_m2_ratio": m1_m2_ratio,
            },
            "immune_activation_score": immune_score,
            "immunosuppression_score": suppressive_score,
            "tme_phenotype": (
                "immune-inflamed" if immune_score > 0.15 else
                "immune-excluded" if immune_score > 0.08 else
                "immune-desert"
            ),
            "cart_favorable": cd8_treg_ratio > 2.0 and m1_m2_ratio > 0.8,
            "recommendations": [
                "High Treg infiltration — consider anti-CD25 conditioning"
                if treg_fraction > 0.05 else "Treg levels manageable",
                "M2-skewed TME — consider CSF1R inhibitor combination"
                if m1_m2_ratio < 0.5 else "Balanced macrophage polarization",
                "MDSC barrier — consider ATRA or anti-CXCR2"
                if cell_fractions.get("MDSCs", 0) > 0.08 else "MDSC levels acceptable",
            ],
        }

    # ─── Fusion Transcript Detection ─────────────────────────────────────────

    def fusion_transcript_detection(self, gene: str) -> dict:
        """
        Detect fusion transcripts involving the target gene.
        Gene fusions can create novel antigens or disrupt expression.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 11000)

        partner_genes = [
            "ABL1", "ALK", "ROS1", "RET", "NTRK1", "FGFR1", "FGFR2",
            "BRAF", "MET", "EGFR", "PDGFRA", "KIT", "BCR", "ETV6",
            "EWSR1", "FLI1", "PAX3", "FOXO1", "MYB", "RUNX1",
        ]

        n_fusions = rng.randint(0, 4)
        fusions = []
        for i in range(n_fusions):
            f_rng = random.Random(seed + 11000 + i * 73)
            partner = f_rng.choice([p for p in partner_genes if p != gene])
            is_5prime = f_rng.random() > 0.5
            breakpoint_exon = f_rng.randint(1, 25)

            fusions.append({
                "fusion_id": f"FUS_{gene}_{partner}_{i+1}",
                "gene_5prime": gene if is_5prime else partner,
                "gene_3prime": partner if is_5prime else gene,
                "breakpoint_5prime": f"exon_{breakpoint_exon}",
                "breakpoint_3prime": f"exon_{f_rng.randint(1, 20)}",
                "junction_reads": f_rng.randint(5, 500),
                "spanning_reads": f_rng.randint(2, 200),
                "in_frame": f_rng.random() > 0.3,
                "reciprocal_detected": f_rng.random() > 0.7,
                "known_oncogenic": f_rng.random() > 0.6,
                "creates_neoantigen": f_rng.random() > 0.5,
                "preserves_target_epitope": f_rng.random() > 0.4,
                "frequency_in_cohort": round(f_rng.uniform(0.01, 0.15), 3),
            })

        return {
            "gene": gene,
            "analysis_type": "fusion_transcript_detection",
            "data_source": "STAR-Fusion / Arriba simulation",
            "total_fusions_detected": len(fusions),
            "fusion_details": fusions,
            "oncogenic_fusions": sum(1 for f in fusions if f["known_oncogenic"]),
            "neoantigen_generating": sum(1 for f in fusions if f["creates_neoantigen"]),
            "epitope_preserved": sum(1 for f in fusions if f["preserves_target_epitope"]),
            "cart_impact": (
                "Fusion may disrupt target epitope — verify scFv binding"
                if any(not f["preserves_target_epitope"] for f in fusions)
                else "No fusions detected affecting target epitope"
                if not fusions else "All detected fusions preserve target epitope"
            ),
        }

    # ─── RNA Velocity Trajectory ─────────────────────────────────────────────

    def rna_velocity_trajectory(self, gene: str) -> dict:
        """
        Compute RNA velocity vectors for the target gene across cell states.
        Predicts future transcriptional state transitions.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 12000)

        cell_states = [
            "quiescent", "proliferating", "differentiating",
            "apoptotic", "senescent", "stem-like", "mesenchymal",
            "immune-evasive",
        ]

        velocity_vectors = []
        for state in cell_states:
            s_rng = random.Random(seed + 12000 + hash(state))
            spliced = s_rng.uniform(0, 10)
            unspliced = s_rng.uniform(0, 5)
            velocity = unspliced - spliced * s_rng.uniform(0.1, 0.5)

            velocity_vectors.append({
                "cell_state": state,
                "spliced_expression": round(spliced, 3),
                "unspliced_expression": round(unspliced, 3),
                "velocity": round(velocity, 3),
                "direction": "upregulating" if velocity > 0 else "downregulating",
                "confidence": round(s_rng.uniform(0.3, 1.0), 3),
                "cell_fraction": round(s_rng.uniform(0.02, 0.3), 3),
            })

        total_frac = sum(v["cell_fraction"] for v in velocity_vectors)
        for v in velocity_vectors:
            v["normalized_fraction"] = round(v["cell_fraction"] / total_frac, 3)

        upregulating = [v for v in velocity_vectors if v["direction"] == "upregulating"]
        downregulating = [v for v in velocity_vectors if v["direction"] == "downregulating"]

        return {
            "gene": gene,
            "analysis_type": "rna_velocity_trajectory",
            "data_source": "scVelo / velocyto simulation",
            "velocity_vectors": velocity_vectors,
            "states_upregulating": len(upregulating),
            "states_downregulating": len(downregulating),
            "net_velocity": round(
                sum(v["velocity"] * v["normalized_fraction"] for v in velocity_vectors), 3
            ),
            "trajectory_insight": (
                "Target expression trending upward across cell states"
                if len(upregulating) > len(downregulating) else
                "Target expression trending downward — potential antigen loss"
                if len(downregulating) > len(upregulating) else
                "Mixed velocity dynamics"
            ),
        }

    # ─── Transcript Isoform Switching ────────────────────────────────────────

    def isoform_switching_analysis(self, gene: str) -> dict:
        """
        Detect transcript isoform switching events between tumor and normal.
        Isoform switches may alter surface epitopes targeted by CAR-T.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 13000)

        n_isoforms = rng.randint(3, 12)
        isoforms = []
        for i in range(n_isoforms):
            i_rng = random.Random(seed + 13000 + i * 59)
            tumor_usage = i_rng.uniform(0, 1)
            normal_usage = i_rng.uniform(0, 1)

            isoforms.append({
                "isoform_id": f"{gene}-{i_rng.randint(200, 299)}",
                "n_exons": i_rng.randint(3, 30),
                "coding_length_aa": i_rng.randint(100, 1500),
                "tumor_usage": round(tumor_usage, 3),
                "normal_usage": round(normal_usage, 3),
                "usage_switch": round(tumor_usage - normal_usage, 3),
                "has_signal_peptide": i_rng.random() > 0.5,
                "has_transmembrane": i_rng.random() > 0.4,
                "preserves_epitope": i_rng.random() > 0.3,
                "nmd_sensitive": i_rng.random() > 0.7,
            })

        total_tumor = sum(iso["tumor_usage"] for iso in isoforms)
        total_normal = sum(iso["normal_usage"] for iso in isoforms)
        for iso in isoforms:
            iso["tumor_proportion"] = round(iso["tumor_usage"] / max(total_tumor, 0.01), 3)
            iso["normal_proportion"] = round(iso["normal_usage"] / max(total_normal, 0.01), 3)

        dominant_tumor = max(isoforms, key=lambda x: x["tumor_usage"])
        dominant_normal = max(isoforms, key=lambda x: x["normal_usage"])

        return {
            "gene": gene,
            "analysis_type": "isoform_switching",
            "data_source": "IsoformSwitchAnalyzeR / SUPPA2 simulation",
            "total_isoforms": len(isoforms),
            "isoforms": isoforms,
            "dominant_tumor_isoform": dominant_tumor["isoform_id"],
            "dominant_normal_isoform": dominant_normal["isoform_id"],
            "isoform_switch_detected": dominant_tumor["isoform_id"] != dominant_normal["isoform_id"],
            "epitope_risk": (
                "CRITICAL: Dominant tumor isoform lacks target epitope"
                if not dominant_tumor["preserves_epitope"] else
                "Safe: Dominant tumor isoform preserves target epitope"
            ),
            "surface_isoforms": sum(
                1 for iso in isoforms if iso["has_transmembrane"] and iso["tumor_usage"] > 0.1
            ),
        }

    # ─── Ribosome Profiling ──────────────────────────────────────────────────

    def ribosome_profiling(self, gene: str) -> dict:
        """
        Ribo-seq analysis measuring translational efficiency.
        Determines if mRNA expression correlates with protein output.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 14000)

        mrna_levels = {"tumor": round(rng.uniform(1, 20), 2), "normal": round(rng.uniform(0.5, 10), 2)}
        ribo_density = {"tumor": round(rng.uniform(0.5, 15), 2), "normal": round(rng.uniform(0.3, 8), 2)}
        te = {
            "tumor": round(ribo_density["tumor"] / max(mrna_levels["tumor"], 0.01), 3),
            "normal": round(ribo_density["normal"] / max(mrna_levels["normal"], 0.01), 3),
        }

        uorf_count = rng.randint(0, 5)
        ires_present = rng.random() > 0.7
        kozak = rng.choice(["strong", "moderate", "weak"])

        codon_usage = {
            "optimal_codons": round(rng.uniform(0.3, 0.9), 3),
            "rare_codons": round(rng.uniform(0.01, 0.2), 3),
            "cai": round(rng.uniform(0.5, 1.0), 3),
        }

        return {
            "gene": gene,
            "analysis_type": "ribosome_profiling",
            "data_source": "Ribo-seq / polysome profiling simulation",
            "mrna_levels": mrna_levels,
            "ribosome_density": ribo_density,
            "translation_efficiency": te,
            "te_ratio": round(te["tumor"] / max(te["normal"], 0.01), 2),
            "uorf_count": uorf_count,
            "ires_present": ires_present,
            "kozak_strength": kozak,
            "codon_usage": codon_usage,
            "insight": (
                "High TE in tumor — protein abundance confirms mRNA"
                if te["tumor"] > 1.5 else
                "Low TE — mRNA may overestimate protein levels"
                if te["tumor"] < 0.5 else "Moderate TE"
            ),
        }

    # ─── Transcription Factor Activity ───────────────────────────────────────

    def transcription_factor_activity(self, gene: str) -> dict:
        """
        Infer transcription factor activities regulating the target gene.
        Uses VIPER/DoRothEA-style regulon analysis.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 15000)

        tfs = [
            "MYC", "TP53", "STAT3", "NF-kB", "HIF1A", "E2F1",
            "AP-1", "CREB", "SP1", "ETS1", "GATA3", "FOXP3",
            "RUNX1", "PAX5", "IRF4", "NFAT", "YY1", "KLF4",
        ]

        n_reg = rng.randint(4, 12)
        selected_tfs = rng.sample(tfs, k=min(n_reg, len(tfs)))
        regulon_results = []

        for tf in selected_tfs:
            t_rng = random.Random(seed + 15000 + hash(tf))
            activity = t_rng.uniform(-3, 3)
            regulon_results.append({
                "tf": tf,
                "activity_score": round(activity, 3),
                "direction": "activating" if activity > 0 else "repressing",
                "regulon_size": t_rng.randint(20, 500),
                "p_value": round(t_rng.uniform(0.001, 0.05), 4),
                "binding_at_promoter": t_rng.random() > 0.4,
                "druggable": t_rng.random() > 0.5,
                "known_oncogene": tf in ["MYC", "STAT3", "HIF1A", "E2F1"],
            })

        regulon_results.sort(key=lambda x: abs(x["activity_score"]), reverse=True)
        top_act = next((r for r in regulon_results if r["direction"] == "activating"), None)
        top_rep = next((r for r in regulon_results if r["direction"] == "repressing"), None)

        return {
            "gene": gene,
            "analysis_type": "tf_activity",
            "data_source": "DoRothEA / VIPER simulation",
            "regulon_analysis": regulon_results,
            "total_regulators": len(regulon_results),
            "activators": sum(1 for r in regulon_results if r["direction"] == "activating"),
            "repressors": sum(1 for r in regulon_results if r["direction"] == "repressing"),
            "top_activator": top_act["tf"] if top_act else "none",
            "top_repressor": top_rep["tf"] if top_rep else "none",
            "druggable_regulators": sum(1 for r in regulon_results if r["druggable"]),
        }

    # ─── Long-Read Isoform Analysis ──────────────────────────────────────────

    def long_read_isoform_analysis(self, gene: str) -> dict:
        """
        Full-length transcript isoform analysis using PacBio/ONT long-read
        sequencing. Detects novel isoforms missed by short-read RNA-seq.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 16000)

        n_known = rng.randint(3, 15)
        n_novel = rng.randint(1, 8)

        isoforms = []
        for i in range(n_known + n_novel):
            i_rng = random.Random(seed + 16000 + i * 61)
            is_novel = i >= n_known
            length = i_rng.randint(500, 10000)

            isoforms.append({
                "isoform_id": f"{gene}-LR-{'N' if is_novel else 'K'}{i+1:02d}",
                "novel": is_novel,
                "length_bp": length,
                "n_exons": i_rng.randint(2, 30),
                "cds_intact": i_rng.random() > 0.2,
                "polyA_site": i_rng.choice(["canonical", "alternative", "internal"]),
                "tumor_reads": i_rng.randint(1, 500),
                "normal_reads": i_rng.randint(0, 200),
                "contains_target_domain": i_rng.random() > 0.4,
                "surface_localized": i_rng.random() > 0.5 if i_rng.random() > 0.2 else False,
            })

        novel_surface = [
            iso for iso in isoforms
            if iso["novel"] and iso["surface_localized"] and iso["contains_target_domain"]
        ]

        return {
            "gene": gene,
            "analysis_type": "long_read_isoform",
            "data_source": "PacBio Iso-Seq / ONT direct RNA simulation",
            "known_isoforms": n_known,
            "novel_isoforms": n_novel,
            "total_isoforms": len(isoforms),
            "isoform_details": isoforms,
            "novel_surface_isoforms": len(novel_surface),
            "tumor_specific_novel": sum(
                1 for iso in isoforms
                if iso["novel"] and iso["tumor_reads"] > 10 and iso["normal_reads"] < 2
            ),
            "discovery_insight": (
                f"Found {len(novel_surface)} novel surface isoforms — potential new epitopes"
                if novel_surface else
                "No targetable novel surface isoforms detected"
            ),
        }
