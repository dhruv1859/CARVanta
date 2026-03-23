# CARVanta — Model Card

## Model Details

| Field | Value |
|-------|-------|
| **Model Name** | CARVanta v4 Adaptive Scoring Engine |
| **Version** | v4 |
| **Architecture** | Ensemble: Random Forest (200 trees) + XGBoost Classifier + XGBoost Regression Ranker |
| **Training Framework** | scikit-learn 1.x, XGBoost |
| **License** | Proprietary (CARVanta) |
| **Contact** | CARVanta AI Platform Team |
| **Last Updated** | 2026-03 |

## Intended Use

### Primary Use
AI-assisted ranking and viability assessment of antigen targets for CAR-T cell therapy development.

### Intended Users
- Biotech researchers evaluating CAR-T therapy targets
- Pharmaceutical R&D teams prioritizing antigen candidates
- Academic immunology labs exploring novel targets
- Bioinformatics pipeline integrations

### Out-of-Scope Uses
- **Not a clinical diagnostic tool** — CARVanta scores should NOT be used as the sole basis for clinical decisions
- **Not FDA-cleared** — Results are for research use only (RUO)
- **Not validated for pediatric populations** specifically

## Training Data

### Dataset Composition

| Layer | Rows | Unique Antigens | Source |
|-------|------|-----------------|--------|
| Validated | ~3,000 | ~50 | TCGA, GTEx, Human Protein Atlas, ClinicalTrials.gov |
| Computationally Derived | ~117,000 | ~16,000 | Synthetic generation from real gene symbols + expression distributions |

### Feature Engineering (9 Features)
1. `tumor_specificity` — Tumor vs normal expression ratio
2. `normal_expression_risk` — Normal tissue expression level (safety signal)
3. `safety_margin` — 1 − normal_expression_risk
4. `stability_score` — Expression consistency across samples
5. `literature_support` — Published clinical evidence strength
6. `immunogenicity_score` — Immune recognition potential
7. `surface_accessibility` — Membrane localization probability
8. `clinical_boost` — Log-normalized clinical trial count
9. `composite_score` — Weighted combination of above features

### Data Limitations
- **Synthetic expansion**: ~97% of training rows are computationally derived, not from direct experimental measurement
- **Cancer type coverage**: 12 cancer types represented; rare cancers underrepresented
- **Temporal bias**: Expression data reflects available TCGA/GTEx cohorts, which may not represent all populations
- **Gene symbol mapping**: Some antigens use common names (e.g., "HER2") that map to multiple gene symbols

## Performance Metrics

### Classifier (Viable vs Non-Viable)

| Metric | 5-Fold CV Mean ± Std |
|--------|---------------------|
| Accuracy | 0.9993 ± 0.0002 |
| Precision | 0.9967 ± 0.0003 |
| Recall | 0.9994 ± 0.0008 |
| F1-Score | 0.9981 ± 0.0005 |
| ROC-AUC | 1.0000 ± 0.0000 |

### FDA Target Validation

| Target | CVS Score | Tier | Status |
|--------|-----------|------|--------|
| CD19 | 0.945 | Tier 1 | ✅ PASS |
| BCMA | 0.943 | Tier 1 | ✅ PASS |
| CD22 | 0.927 | Tier 1 | ✅ PASS |
| GPRC5D | 0.936 | Tier 1 | ✅ PASS |

### Known Limitations in Benchmark
- **CVS Rule-Based accuracy**: 66.2% — lower than ML because CVS formula assigns moderate scores to some non-viable targets (e.g., HER2 at 0.752)
- **ML Model accuracy**: 89.2% — better at discriminating viable from non-viable
- **False Positives**: CD30, TEM1, MUC16, FGFR2, CD44V6, PDGFRA, CD7 (non-viable targets scored as viable by CVS)

## Ethical Considerations

### Bias Assessment
- **Population bias**: Training data derived primarily from Western cohorts (TCGA); genomic variation in non-European populations may not be fully represented
- **Target bias**: Well-studied antigens (CD19, BCMA) have more real data and thus higher confidence; novel targets rely more on synthetic features
- **Confirmation bias**: Known FDA-approved targets are explicitly curated in the training data with high viability labels, which may inflate apparent model performance

### Fairness
- The model does not use demographic features (age, sex, race) directly
- Cancer type distribution in training data is not uniform — common cancers are overrepresented

### Safety
- CARVanta includes safety scoring (normal tissue expression risk, off-tumor toxicity prediction)
- Drug interaction checking flags antigens with existing approved therapies
- All scores should be validated by domain experts before use in therapy design

## Recommendations

1. **Always consult domain experts** before using CARVanta scores for preclinical decisions
2. **Verify with primary sources** — cross-reference scores with TCGA/GTEx/HPA directly
3. **Monitor for antigen loss** — some targets (e.g., CD19) can be lost after prior therapy
4. **Consider combination strategies** — single-antigen targeting has known failure modes
5. **Report discrepancies** — if CARVanta scores conflict with known biology, report for model improvement
