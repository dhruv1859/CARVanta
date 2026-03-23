"""
CARVanta — Intent Training Data
================================
Reference query-intent pairs used to build the semantic intent classifier.
The SemanticQueryEngine computes embeddings for these at startup and uses
cosine similarity to classify new queries.

Each entry: (query_text, intent_label)

Intent labels:
    - best:          User wants top/highest-scoring antigens
    - worst:         User wants bottom/lowest-scoring antigens
    - filter_cancer: User wants antigens for a specific cancer type
    - filter_safety: User wants safe/low-toxicity antigens
    - compare:       User wants to compare specific antigens
    - count:         User wants to know how many antigens match
    - explain:       User wants explanation about an antigen or score
    - general:       General browsing / no strong intent
"""

INTENT_TRAINING_DATA: list[tuple[str, str]] = [
    # ── BEST (want the top / highest scoring) ─────────────────────────────
    ("best antigens", "best"),
    ("show me the best targets", "best"),
    ("top scoring antigens", "best"),
    ("highest CVS score", "best"),
    ("most viable targets", "best"),
    ("most promising antigens", "best"),
    ("which antigens are the strongest", "best"),
    ("what are the best candidates", "best"),
    ("show the top performers", "best"),
    ("find me the highest ranked targets", "best"),
    ("which targets have the best scores", "best"),
    ("give me the cream of the crop", "best"),
    ("elite antigens", "best"),
    ("leading candidates", "best"),
    ("tier 1 targets", "best"),
    ("highly viable antigens", "best"),
    ("antigens that are performing well", "best"),
    ("most effective car-t targets", "best"),
    ("strongest car-t candidates", "best"),
    ("premier targets for therapy", "best"),
    # Multi-intent: "best + cancer" should still be "best"
    ("best car-t candidates for leukemia", "best"),
    ("best antigens for breast cancer", "best"),
    ("best targets for lung cancer", "best"),
    ("best car-t targets for melanoma", "best"),
    ("top candidates for glioblastoma", "best"),
    ("strongest targets for lymphoma", "best"),
    ("most promising car-t targets for myeloma", "best"),
    ("highest scoring antigens for prostate cancer", "best"),

    # ── WORST (want the bottom / lowest scoring) ──────────────────────────
    ("worst antigens", "worst"),
    ("show me the worst targets", "worst"),
    ("lowest scoring antigens", "worst"),
    ("which antigens should I avoid", "worst"),
    ("targets that are failing", "worst"),
    ("least viable antigens", "worst"),
    ("poorest candidates", "worst"),
    ("antigens with the lowest scores", "worst"),
    ("bottom ranked targets", "worst"),
    ("which antigens are the weakest", "worst"),
    ("show me the bad ones", "worst"),
    ("targets to stay away from", "worst"),
    ("high risk antigens", "worst"),
    ("most dangerous targets", "worst"),
    ("least promising candidates", "worst"),
    ("riskiest antigens", "worst"),
    ("antigens that don't work", "worst"),
    ("what should I not use", "worst"),
    ("which targets have failed", "worst"),
    ("non-viable antigens", "worst"),
    ("antigens that are not recommended", "worst"),
    ("show the losers", "worst"),
    ("least effective targets", "worst"),
    ("tier 4 antigens", "worst"),

    # ── FILTER_CANCER (want antigens for a specific cancer) ───────────────
    ("antigens for breast cancer", "filter_cancer"),
    ("targets for leukemia", "filter_cancer"),
    ("car-t targets for lung cancer", "filter_cancer"),
    ("what works for glioblastoma", "filter_cancer"),
    ("find me targets for melanoma", "filter_cancer"),
    ("antigens effective against lymphoma", "filter_cancer"),
    ("show me options for prostate cancer", "filter_cancer"),
    ("targets specific to ovarian cancer", "filter_cancer"),
    ("what antigens work for brain tumors", "filter_cancer"),
    ("viable targets for colorectal cancer", "filter_cancer"),
    ("myeloma car-t targets", "filter_cancer"),
    ("liver cancer antigens", "filter_cancer"),
    ("pancreatic cancer targets", "filter_cancer"),
    ("kidney cancer options", "filter_cancer"),
    ("bladder cancer candidates", "filter_cancer"),
    ("head and neck cancer targets", "filter_cancer"),
    ("gastric cancer antigens", "filter_cancer"),
    ("thyroid cancer car-t options", "filter_cancer"),
    ("triple negative breast cancer targets", "filter_cancer"),
    ("AML targets", "filter_cancer"),

    # ── FILTER_SAFETY (want safe / low-toxicity targets) ──────────────────
    ("safe antigens", "filter_safety"),
    ("targets with low toxicity", "filter_safety"),
    ("which antigens are the safest", "filter_safety"),
    ("show me non-toxic targets", "filter_safety"),
    ("antigens with minimal off-target effects", "filter_safety"),
    ("safe car-t targets", "filter_safety"),
    ("low risk targets", "filter_safety"),
    ("targets with good safety profile", "filter_safety"),
    ("which antigens have the least side effects", "filter_safety"),
    ("antigens safe for normal tissue", "filter_safety"),
    ("targets with low normal expression", "filter_safety"),
    ("find antigens that won't damage healthy cells", "filter_safety"),
    ("least toxic candidates", "filter_safety"),
    ("antigens with high therapeutic index", "filter_safety"),
    ("targets that spare normal organs", "filter_safety"),
    # Multi-intent: "safe + cancer" should still be "filter_safety"
    ("safe targets for breast cancer", "filter_safety"),
    ("safe antigens for leukemia", "filter_safety"),
    ("low toxicity targets for lung cancer", "filter_safety"),
    ("safe car-t candidates for melanoma", "filter_safety"),
    ("non-toxic antigens for brain tumors", "filter_safety"),
    ("safest targets for lymphoma", "filter_safety"),
    ("targets with good safety for myeloma", "filter_safety"),

    # ── COMPARE (want to compare specific antigens) ───────────────────────
    ("compare CD19 and CD22", "compare"),
    ("which is better CD19 or BCMA", "compare"),
    ("how does HER2 compare to EGFR", "compare"),
    ("CD19 vs CD22", "compare"),
    ("head to head CD19 BCMA", "compare"),
    ("show me the difference between these two targets", "compare"),
    ("put CD19 and mesothelin side by side", "compare"),
    ("compare the scores of these antigens", "compare"),
    ("which target is superior", "compare"),
    ("is CD19 better than CD22 for leukemia", "compare"),

    # ── COUNT (want to know how many match) ───────────────────────────────
    ("how many antigens are in the database", "count"),
    ("how many tier 1 targets exist", "count"),
    ("count of viable antigens", "count"),
    ("how many targets for breast cancer", "count"),
    ("total number of antigens", "count"),
    ("what's the size of the database", "count"),
    ("how many options do I have", "count"),
    ("number of high-risk antigens", "count"),

    # ── EXPLAIN (want explanation about a target) ─────────────────────────
    ("explain CD19 score", "explain"),
    ("why is CD19 ranked so high", "explain"),
    ("what makes BCMA a good target", "explain"),
    ("tell me about HER2", "explain"),
    ("why is this antigen tier 1", "explain"),
    ("break down the CVS score for CD19", "explain"),
    ("what factors contribute to this ranking", "explain"),
    ("explain the safety profile of EGFR", "explain"),
    ("why should I consider this target", "explain"),
    ("what's special about mesothelin", "explain"),

    # ── GENERAL (browsing / no specific intent) ───────────────────────────
    ("show me antigens", "general"),
    ("browse targets", "general"),
    ("list some antigens", "general"),
    ("what antigens are available", "general"),
    ("search the database", "general"),
    ("find targets", "general"),
    ("explore antigens", "general"),
    ("show me the leaderboard", "general"),
    ("give me some recommendations", "general"),
    ("what do you have", "general"),
]

# ── Cancer type reference phrases for fuzzy matching ──────────────────────
CANCER_REFERENCE_PHRASES: dict[str, list[str]] = {
    "Breast Cancer": [
        "breast cancer", "breast", "breast tumor", "triple negative breast",
        "tnbc", "triple-negative", "mammary cancer",
    ],
    "Lung Adenocarcinoma": [
        "lung cancer", "lung", "lung adenocarcinoma", "nsclc",
        "non-small cell lung", "pulmonary cancer",
    ],
    "Glioblastoma": [
        "glioblastoma", "gbm", "brain cancer", "brain tumor",
        "glioma", "brain malignancy",
    ],
    "Prostate Cancer": [
        "prostate cancer", "prostate", "prostatic cancer",
    ],
    "Colorectal Cancer": [
        "colorectal cancer", "colorectal", "colon cancer", "colon",
        "rectal cancer", "bowel cancer",
    ],
    "Ovarian Cancer": [
        "ovarian cancer", "ovarian", "ovary cancer",
    ],
    "Leukemia": [
        "leukemia", "leukaemia", "aml", "all", "cll",
        "acute myeloid leukemia", "blood cancer",
    ],
    "Melanoma": [
        "melanoma", "skin cancer", "cutaneous melanoma",
    ],
    "Liver Cancer": [
        "liver cancer", "liver", "hepatocellular", "hcc",
        "hepatic cancer",
    ],
    "Renal Cancer": [
        "renal cancer", "renal", "kidney cancer", "kidney",
        "renal cell carcinoma",
    ],
    "Gastric Cancer": [
        "gastric cancer", "gastric", "stomach cancer", "stomach",
    ],
    "Pancreatic Cancer": [
        "pancreatic cancer", "pancreatic", "pancreas",
        "pancreatic adenocarcinoma",
    ],
    "Lymphoma": [
        "lymphoma", "dlbcl", "non-hodgkin", "hodgkin",
        "b-cell lymphoma",
    ],
    "Myeloma": [
        "myeloma", "multiple myeloma", "mm", "plasma cell",
    ],
    "Bladder Cancer": [
        "bladder cancer", "bladder", "urothelial cancer",
    ],
    "Head & Neck Cancer": [
        "head and neck", "head & neck", "hnsc",
        "oral cancer", "throat cancer",
    ],
    "Endometrial Cancer": [
        "endometrial cancer", "endometrial", "uterine cancer", "uterine",
    ],
    "Thyroid Cancer": [
        "thyroid cancer", "thyroid", "thyroid carcinoma",
    ],
}

# ── Sort direction reference phrases ──────────────────────────────────────
ASCENDING_PHRASES = [
    "worst", "lowest", "bottom", "weakest", "poorest",
    "least viable", "most toxic", "most dangerous",
    "least safe", "riskiest", "avoid", "failing",
    "should not use", "bad", "don't work", "not recommended",
    "stay away", "non-viable", "high risk targets",
    "tier 4", "least promising", "least effective",
]

DESCENDING_PHRASES = [
    "best", "top", "highest", "strongest", "most viable",
    "most promising", "most effective", "safest",
    "elite", "leading", "premier", "cream of the crop",
    "tier 1", "highly viable", "recommended",
]
