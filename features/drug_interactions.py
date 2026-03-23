"""
CARVanta – Drug Interaction Checker v1
========================================
Curated database of antigen-drug interactions for CAR-T therapy planning.
Flags antigens that have existing approved therapies which may compete
with, synergize, or complicate CAR-T cell therapy.

CARVanta-Original: Drug-antigen interaction safety module.

Usage:
    from features.drug_interactions import check_interactions
    result = check_interactions("CD20")
"""


# ─── Curated drug-antigen interactions ──────────────────────────────────────────
# Sources: FDA labels, PubMed reviews, ClinicalTrials.gov
DRUG_INTERACTIONS = {
    "CD19": {
        "drugs": [
            {
                "drug": "Blinatumomab (Blincyto)",
                "type": "BiTE antibody",
                "interaction": "competing",
                "mechanism": "Bispecific T-cell engager also targets CD19; may reduce CD19+ cell pool before CAR-T infusion",
                "clinical_note": "Wash-out period recommended before CAR-T. Prior blinatumomab may cause CD19 antigen loss.",
                "severity": "moderate",
            },
            {
                "drug": "Tafasitamab (Monjuvi)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-CD19 antibody; may deplete target cells and mask CD19 epitope",
                "clinical_note": "Concurrent use not recommended. Sequential use requires monitoring of CD19 expression.",
                "severity": "moderate",
            },
            {
                "drug": "Loncastuximab tesirine (Zynlonta)",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-CD19 antibody-drug conjugate; depletes CD19+ population",
                "clinical_note": "May reduce available target cells for CAR-T.",
                "severity": "moderate",
            },
        ],
        "risk_level": "moderate",
        "summary": "Multiple CD19-targeting therapies exist. Prior exposure may cause antigen loss or reduced target cell pool.",
    },
    "CD20": {
        "drugs": [
            {
                "drug": "Rituximab (Rituxan)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-CD20 depletes B-cells; may reduce CAR-T target cells",
                "clinical_note": "Very common prior therapy. B-cell recovery needed before CD20 CAR-T.",
                "severity": "moderate",
            },
            {
                "drug": "Obinutuzumab (Gazyva)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Type II anti-CD20; enhanced B-cell depletion",
                "clinical_note": "More potent B-cell depletion than rituximab. Longer wash-out needed.",
                "severity": "moderate",
            },
            {
                "drug": "Ofatumumab (Arzerra)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-CD20 targeting different epitope",
                "clinical_note": "Cross-resistance unlikely but monitor CD20 expression post-treatment.",
                "severity": "low",
            },
        ],
        "risk_level": "moderate",
        "summary": "Rituximab is standard-of-care in B-cell lymphoma. CAR-T timing must account for B-cell recovery.",
    },
    "BCMA": {
        "drugs": [
            {
                "drug": "Belantamab mafodotin (Blenrep)",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-BCMA ADC; may reduce BCMA+ myeloma cells",
                "clinical_note": "FDA-withdrawn but was used. Check prior treatment history.",
                "severity": "low",
            },
            {
                "drug": "Teclistamab (Tecvayli)",
                "type": "Bispecific antibody",
                "interaction": "competing",
                "mechanism": "BCMA × CD3 bispecific; directly engages T-cells against BCMA+ cells",
                "clinical_note": "Prior bispecific exposure may impact BCMA expression levels.",
                "severity": "moderate",
            },
            {
                "drug": "Elranatamab (Elrexfio)",
                "type": "Bispecific antibody",
                "interaction": "competing",
                "mechanism": "BCMA × CD3 bispecific T-cell redirector",
                "clinical_note": "Sequential bispecific → CAR-T requires careful scheduling.",
                "severity": "moderate",
            },
        ],
        "risk_level": "moderate",
        "summary": "BCMA is a heavily targeted antigen in myeloma. Multiple competing therapies complicate CAR-T sequencing.",
    },
    "HER2": {
        "drugs": [
            {
                "drug": "Trastuzumab (Herceptin)",
                "type": "Monoclonal antibody",
                "interaction": "synergistic",
                "mechanism": "Anti-HER2 antibody; may sensitize cells but also compete for epitope",
                "clinical_note": "HER2 CAR-T after trastuzumab failure is being explored. Not antagonistic.",
                "severity": "low",
            },
            {
                "drug": "Pertuzumab (Perjeta)",
                "type": "Monoclonal antibody",
                "interaction": "synergistic",
                "mechanism": "Targets different HER2 domain (II); no epitope competition",
                "clinical_note": "May be used concurrently in theory. Clinical data limited.",
                "severity": "low",
            },
            {
                "drug": "Ado-trastuzumab emtansine (Kadcyla)",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-HER2 ADC; cytotoxic payload may deplete HER2+ cells",
                "clinical_note": "Wait for HER2+ cell rebound before CAR-T infusion.",
                "severity": "moderate",
            },
            {
                "drug": "Lapatinib (Tykerb)",
                "type": "Small molecule TKI",
                "interaction": "neutral",
                "mechanism": "Dual EGFR/HER2 tyrosine kinase inhibitor; does not deplete cells",
                "clinical_note": "Can be used concurrently without impacting CAR-T function.",
                "severity": "low",
            },
        ],
        "risk_level": "low",
        "summary": "HER2 has multiple approved therapies. Most are not strongly antagonistic to CAR-T but sequencing matters.",
    },
    "EGFR": {
        "drugs": [
            {
                "drug": "Cetuximab (Erbitux)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-EGFR blocks receptor; may mask epitope from CAR-T",
                "clinical_note": "Epitope masking possible. Use different EGFR domain for CAR construct.",
                "severity": "moderate",
            },
            {
                "drug": "Panitumumab (Vectibix)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Fully human anti-EGFR; similar epitope competition risk",
                "clinical_note": "Same concern as cetuximab. Sequential dosing recommended.",
                "severity": "moderate",
            },
            {
                "drug": "Erlotinib (Tarceva)",
                "type": "Small molecule TKI",
                "interaction": "neutral",
                "mechanism": "Intracellular kinase inhibitor; does not block surface EGFR",
                "clinical_note": "No impact on CAR-T cell binding. Can be used concurrently.",
                "severity": "low",
            },
            {
                "drug": "Osimertinib (Tagrisso)",
                "type": "Small molecule TKI",
                "interaction": "neutral",
                "mechanism": "Third-gen EGFR TKI for T790M mutants; intracellular target",
                "clinical_note": "No direct impact on CAR-T surface recognition.",
                "severity": "low",
            },
        ],
        "risk_level": "moderate",
        "summary": "EGFR is widely expressed in normal tissues, making safety a concern. Multiple approved therapies exist.",
    },
    "CD38": {
        "drugs": [
            {
                "drug": "Daratumumab (Darzalex)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-CD38 depletes CD38+ myeloma cells and also activated T-cells",
                "clinical_note": "Daratumumab kills T-cells expressing CD38 — may reduce CAR-T persistence. Consider CD38-knockout CAR-T.",
                "severity": "high",
            },
            {
                "drug": "Isatuximab (Sarclisa)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-CD38 with distinct epitope; similar T-cell toxicity concern",
                "clinical_note": "Same fratricide risk as daratumumab for CD38 CAR-T.",
                "severity": "high",
            },
        ],
        "risk_level": "high",
        "summary": "CD38 is expressed on activated T-cells — anti-CD38 therapies cause CAR-T fratricide. Major safety concern.",
    },
    "CD33": {
        "drugs": [
            {
                "drug": "Gemtuzumab ozogamicin (Mylotarg)",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-CD33 ADC; depletes CD33+ AML blasts but also normal myeloid cells",
                "clinical_note": "Severe myelosuppression risk. CAR-T after Mylotarg requires bone marrow recovery.",
                "severity": "high",
            },
        ],
        "risk_level": "high",
        "summary": "CD33 targeting causes severe myelosuppression. Very narrow therapeutic window for CAR-T.",
    },
    "CD30": {
        "drugs": [
            {
                "drug": "Brentuximab vedotin (Adcetris)",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-CD30 ADC approved for Hodgkin lymphoma and ALCL",
                "clinical_note": "Prior brentuximab may reduce CD30 expression. Monitor before CAR-T.",
                "severity": "moderate",
            },
        ],
        "risk_level": "moderate",
        "summary": "Brentuximab is first-line for CD30+ lymphomas. Sequencing with CAR-T is feasible.",
    },
    "PSMA": {
        "drugs": [
            {
                "drug": "Lutetium-177 vipivotide tetraxetan (Pluvicto)",
                "type": "Radioligand therapy",
                "interaction": "synergistic",
                "mechanism": "PSMA-targeted radioligand; different mechanism of action from CAR-T",
                "clinical_note": "Sequential use is being explored. Radioligand does not deplete surface PSMA.",
                "severity": "low",
            },
        ],
        "risk_level": "low",
        "summary": "PSMA-targeting radioligand therapy is complementary to CAR-T. Low drug interaction risk.",
    },
    "GD2": {
        "drugs": [
            {
                "drug": "Dinutuximab (Unituxin)",
                "type": "Monoclonal antibody",
                "interaction": "competing",
                "mechanism": "Anti-GD2 antibody approved for neuroblastoma; complement-dependent cytotoxicity",
                "clinical_note": "Severe pain syndrome (neuropathic) is a known side effect. Consider for combination or sequential use.",
                "severity": "moderate",
            },
        ],
        "risk_level": "moderate",
        "summary": "GD2 CAR-T is in clinical trials for neuroblastoma. Dinutuximab is the main competing therapy.",
    },
    "MUC1": {
        "drugs": [
            {
                "drug": "Gatipotuzumab",
                "type": "Monoclonal antibody",
                "interaction": "neutral",
                "mechanism": "Anti-MUC1 antibody targeting tumor-specific glyco-epitope (TA-MUC1)",
                "clinical_note": "Different MUC1 epitope from typical CAR-T targets. Minimal interference.",
                "severity": "low",
            },
        ],
        "risk_level": "low",
        "summary": "MUC1 is broadly expressed. CAR-T safety concerns are primarily about on-target/off-tumor toxicity.",
    },
    "FLT3": {
        "drugs": [
            {
                "drug": "Midostaurin (Rydapt)",
                "type": "Small molecule kinase inhibitor",
                "interaction": "neutral",
                "mechanism": "FLT3 kinase inhibitor; intracellular target, does not block surface FLT3",
                "clinical_note": "No impact on CAR-T binding. Can be used concurrently.",
                "severity": "low",
            },
            {
                "drug": "Gilteritinib (Xospata)",
                "type": "Small molecule kinase inhibitor",
                "interaction": "neutral",
                "mechanism": "Selective FLT3 inhibitor for relapsed AML",
                "clinical_note": "Compatible with CAR-T approaches targeting surface FLT3.",
                "severity": "low",
            },
        ],
        "risk_level": "low",
        "summary": "FLT3 inhibitors are intracellular, so they don't interfere with CAR-T surface binding.",
    },
    "MESOTHELIN": {
        "drugs": [
            {
                "drug": "Anetumab ravtansine",
                "type": "ADC",
                "interaction": "competing",
                "mechanism": "Anti-mesothelin ADC; targets the same surface antigen",
                "clinical_note": "May deplete mesothelin+ cells. Consider as bridge therapy before CAR-T.",
                "severity": "moderate",
            },
        ],
        "risk_level": "moderate",
        "summary": "Mesothelin is a leading solid tumor CAR-T target. ADCs targeting the same antigen may complicate sequencing.",
    },
}


def check_interactions(antigen_name: str) -> dict:
    """
    Check known drug interactions for a given antigen.

    Parameters
    ----------
    antigen_name : str
        Antigen/gene symbol (e.g., 'CD19', 'BCMA', 'HER2')

    Returns
    -------
    dict with drugs, risk_level, summary, and clinical recommendations
    """
    antigen = antigen_name.upper()
    data = DRUG_INTERACTIONS.get(antigen, None)

    if data is None:
        return {
            "antigen": antigen,
            "has_interactions": False,
            "drugs": [],
            "risk_level": "unknown",
            "summary": f"No known drug interactions catalogued for {antigen}. "
                       f"This may indicate a novel target without existing approved therapies.",
            "total_drugs": 0,
            "recommendation": "Proceed with standard CAR-T development pipeline. "
                              "Verify against latest FDA drug labels before clinical use.",
        }

    drugs = data["drugs"]
    risk_level = data["risk_level"]

    # Count by interaction type
    competing = sum(1 for d in drugs if d["interaction"] == "competing")
    synergistic = sum(1 for d in drugs if d["interaction"] == "synergistic")
    neutral = sum(1 for d in drugs if d["interaction"] == "neutral")

    # Generate recommendation
    if risk_level == "high":
        recommendation = (
            f"HIGH RISK: {antigen} has {competing} competing therapies that may cause "
            f"fratricide or severe depletion. Careful sequencing and specialized CAR-T "
            f"engineering (e.g., antigen-knockout CAR-T) may be required."
        )
    elif risk_level == "moderate":
        recommendation = (
            f"MODERATE RISK: {antigen} has {competing} competing therapies. "
            f"Wash-out periods and antigen expression monitoring recommended before CAR-T infusion."
        )
    else:
        recommendation = (
            f"LOW RISK: {antigen} has minimal drug interaction concerns. "
            f"Existing therapies are mostly compatible with CAR-T approaches."
        )

    return {
        "antigen": antigen,
        "has_interactions": True,
        "drugs": drugs,
        "risk_level": risk_level,
        "summary": data["summary"],
        "total_drugs": len(drugs),
        "competing_count": competing,
        "synergistic_count": synergistic,
        "neutral_count": neutral,
        "recommendation": recommendation,
    }


def get_all_interactions() -> dict:
    """Return a summary of all catalogued drug interactions."""
    summary = {}
    total_interactions = 0
    for antigen, data in DRUG_INTERACTIONS.items():
        drug_count = len(data["drugs"])
        total_interactions += drug_count
        summary[antigen] = {
            "risk_level": data["risk_level"],
            "total_drugs": drug_count,
            "summary": data["summary"],
        }
    return {
        "total_antigens_catalogued": len(DRUG_INTERACTIONS),
        "total_interactions": total_interactions,
        "antigens": summary,
    }

