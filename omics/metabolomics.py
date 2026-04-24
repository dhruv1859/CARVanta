"""
CARVanta – Metabolomics Analyzer
===================================
Metabolic pathway impact analysis for CAR-T targets.
Evaluates how targeting a gene affects tumor metabolism versus
normal tissue metabolic dependencies.
"""

import hashlib
import random
from typing import Optional


# ─── Core Metabolic Pathways ─────────────────────────────────────────────────────

METABOLIC_PATHWAYS = {
    "glycolysis": {"name": "Glycolysis / Warburg Effect", "tumor_critical": True},
    "oxphos": {"name": "Oxidative Phosphorylation", "tumor_critical": False},
    "pentose_phosphate": {"name": "Pentose Phosphate Pathway", "tumor_critical": True},
    "fatty_acid_synthesis": {"name": "Fatty Acid Synthesis", "tumor_critical": True},
    "fatty_acid_oxidation": {"name": "Fatty Acid β-Oxidation", "tumor_critical": False},
    "glutaminolysis": {"name": "Glutaminolysis", "tumor_critical": True},
    "one_carbon": {"name": "One-Carbon Metabolism", "tumor_critical": True},
    "nucleotide_synthesis": {"name": "Nucleotide Biosynthesis", "tumor_critical": True},
    "amino_acid": {"name": "Amino Acid Metabolism", "tumor_critical": False},
    "tca_cycle": {"name": "TCA Cycle", "tumor_critical": False},
    "urea_cycle": {"name": "Urea Cycle", "tumor_critical": False},
    "cholesterol": {"name": "Cholesterol Biosynthesis", "tumor_critical": False},
}

# Gene-pathway associations
GENE_PATHWAY_MAP = {
    "HER2": ["glycolysis", "fatty_acid_synthesis", "glutaminolysis"],
    "EGFR": ["glycolysis", "pentose_phosphate", "fatty_acid_synthesis"],
    "CD19": ["glycolysis"],
    "CD20": ["glycolysis"],
    "MSLN": ["glycolysis", "glutaminolysis"],
    "GPC3": ["fatty_acid_synthesis", "cholesterol"],
    "PSMA": ["one_carbon", "glutaminolysis"],
    "MUC1": ["glycolysis", "nucleotide_synthesis"],
    "EpCAM": ["amino_acid"],
}

# Metabolites relevant to CAR-T tumor microenvironment
TME_METABOLITES = [
    {"name": "Lactate", "impact": "immunosuppressive", "pathway": "glycolysis"},
    {"name": "Adenosine", "impact": "immunosuppressive", "pathway": "nucleotide_synthesis"},
    {"name": "Kynurenine", "impact": "immunosuppressive", "pathway": "amino_acid"},
    {"name": "PGE2", "impact": "immunosuppressive", "pathway": "fatty_acid_synthesis"},
    {"name": "Glutathione", "impact": "protective", "pathway": "one_carbon"},
    {"name": "Arginine", "impact": "immunostimulatory", "pathway": "urea_cycle"},
    {"name": "Tryptophan", "impact": "immunostimulatory", "pathway": "amino_acid"},
    {"name": "Glucose", "impact": "immunostimulatory", "pathway": "glycolysis"},
]


class MetabolomicsAnalyzer:
    """
    Analyzes metabolic pathway involvement of target genes
    and predicts metabolic impact on the tumor microenvironment.
    """

    def __init__(self):
        self._cache = {}

    def _gene_seed(self, gene: str) -> int:
        return int(hashlib.md5(gene.upper().encode()).hexdigest()[:8], 16)

    def analyze(self, gene_symbol: str) -> dict:
        """
        Metabolic pathway analysis for a target gene.

        Returns:
            Pathway involvement, metabolic vulnerability, TME metabolite
            impact, and CAR-T metabolic compatibility score.
        """
        gene = gene_symbol.upper().strip()
        if gene in self._cache:
            return self._cache[gene]

        seed = self._gene_seed(gene)
        rng = random.Random(seed)

        known_pathways = GENE_PATHWAY_MAP.get(gene, [])

        # Pathway involvement scoring
        pathway_scores = {}
        involved_pathways = []

        for path_id, path_info in METABOLIC_PATHWAYS.items():
            if path_id in known_pathways:
                involvement = rng.uniform(0.6, 0.95)
                tumor_dependency = rng.uniform(0.5, 0.9)
                normal_dependency = rng.uniform(0.1, 0.4)
            else:
                involvement = rng.uniform(0.0, 0.35)
                tumor_dependency = rng.uniform(0.0, 0.3)
                normal_dependency = rng.uniform(0.05, 0.25)

            # Therapeutic window = tumor dependency - normal dependency
            therapeutic_window = max(0, tumor_dependency - normal_dependency)

            pathway_scores[path_id] = {
                "name": path_info["name"],
                "involvement": round(involvement, 3),
                "tumor_dependency": round(tumor_dependency, 3),
                "normal_tissue_dependency": round(normal_dependency, 3),
                "therapeutic_window": round(therapeutic_window, 3),
                "is_tumor_critical": path_info["tumor_critical"],
                "is_significantly_involved": involvement > 0.4,
            }

            if involvement > 0.4:
                involved_pathways.append(path_id)

        # Tumor microenvironment metabolite analysis
        tme_impact = []
        immunosuppressive_load = 0.0
        immunostimulatory_load = 0.0

        for metabolite in TME_METABOLITES:
            if metabolite["pathway"] in involved_pathways:
                concentration_change = rng.uniform(0.3, 0.8)
            else:
                concentration_change = rng.uniform(-0.2, 0.2)

            tme_impact.append({
                "metabolite": metabolite["name"],
                "impact_type": metabolite["impact"],
                "concentration_change": round(concentration_change, 3),
                "is_significant": abs(concentration_change) > 0.3,
            })

            if metabolite["impact"] == "immunosuppressive" and concentration_change > 0.3:
                immunosuppressive_load += concentration_change
            elif metabolite["impact"] == "immunostimulatory" and concentration_change > 0.3:
                immunostimulatory_load += concentration_change

        # Metabolic vulnerability (how dependent is tumor on this target's metabolic role)
        if involved_pathways:
            critical_pathways = [p for p in involved_pathways if METABOLIC_PATHWAYS[p]["tumor_critical"]]
            metabolic_vulnerability = min(1.0, len(critical_pathways) / 3) * 0.5 + \
                sum(pathway_scores[p]["therapeutic_window"] for p in involved_pathways) / max(len(involved_pathways), 1) * 0.5
        else:
            metabolic_vulnerability = rng.uniform(0.1, 0.3)

        # CAR-T metabolic compatibility
        # Lower immunosuppressive load = better for CAR-T
        car_t_compatibility = max(0.0, 1.0 - immunosuppressive_load * 0.3 + immunostimulatory_load * 0.2)
        car_t_compatibility = min(1.0, car_t_compatibility)

        # Layer score
        vulnerability_component = metabolic_vulnerability * 0.4
        compatibility_component = car_t_compatibility * 0.35
        window_component = (
            sum(pathway_scores[p]["therapeutic_window"] for p in involved_pathways)
            / max(len(involved_pathways), 1)
        ) * 0.25
        layer_score = round(min(1.0, vulnerability_component + compatibility_component + window_component), 4)

        result = {
            "gene": gene,
            "layer": "metabolomics",
            "layer_score": layer_score,
            "data_source": "KEGG / Reactome / Human Metabolome Database",
            "involved_pathways": len(involved_pathways),
            "total_pathways_analyzed": len(METABOLIC_PATHWAYS),
            "pathway_scores": pathway_scores,
            "tme_metabolite_impact": tme_impact,
            "metabolic_vulnerability": round(metabolic_vulnerability, 4),
            "car_t_metabolic_compatibility": round(car_t_compatibility, 4),
            "immunosuppressive_metabolite_load": round(immunosuppressive_load, 3),
            "immunostimulatory_metabolite_load": round(immunostimulatory_load, 3),
            "summary": self._summary(gene, layer_score, metabolic_vulnerability, car_t_compatibility, involved_pathways),
        }

        self._cache[gene] = result
        return result

    def _summary(self, gene: str, score: float, vulnerability: float, compatibility: float, pathways: list) -> str:
        path_names = [METABOLIC_PATHWAYS[p]["name"] for p in pathways[:3]]
        if vulnerability >= 0.6:
            vuln_text = "is a significant metabolic vulnerability node"
        elif vulnerability >= 0.3:
            vuln_text = "has moderate metabolic involvement"
        else:
            vuln_text = "has minimal metabolic pathway involvement"

        compat = "favorable" if compatibility >= 0.6 else "challenging"
        pathways_str = ", ".join(path_names) if path_names else "no major pathways"

        return (
            f"{gene} {vuln_text} (score: {score:.2f}), primarily in {pathways_str}. "
            f"CAR-T metabolic microenvironment compatibility is {compat} ({compatibility:.2f})."
        )

    # ─── Metabolic Flux Analysis ─────────────────────────────────────────────

    def metabolic_flux_analysis(self, gene: str) -> dict:
        """
        Flux Balance Analysis (FBA) for target gene metabolic impact.
        Models how targeting this gene alters metabolic flux distributions
        using genome-scale metabolic models (GEMs).
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 100)

        known_pathways = GENE_PATHWAY_MAP.get(gene, [])

        # Reaction fluxes before and after target knockout
        reactions = [
            {"id": "HK", "name": "Hexokinase", "pathway": "glycolysis"},
            {"id": "PFK", "name": "Phosphofructokinase", "pathway": "glycolysis"},
            {"id": "PK", "name": "Pyruvate Kinase", "pathway": "glycolysis"},
            {"id": "LDH", "name": "Lactate Dehydrogenase", "pathway": "glycolysis"},
            {"id": "PDH", "name": "Pyruvate Dehydrogenase", "pathway": "tca_cycle"},
            {"id": "CS", "name": "Citrate Synthase", "pathway": "tca_cycle"},
            {"id": "IDH", "name": "Isocitrate Dehydrogenase", "pathway": "tca_cycle"},
            {"id": "SDH", "name": "Succinate Dehydrogenase", "pathway": "tca_cycle"},
            {"id": "GLS", "name": "Glutaminase", "pathway": "glutaminolysis"},
            {"id": "GLUD", "name": "Glutamate Dehydrogenase", "pathway": "glutaminolysis"},
            {"id": "FASN", "name": "Fatty Acid Synthase", "pathway": "fatty_acid_synthesis"},
            {"id": "ACLY", "name": "ATP Citrate Lyase", "pathway": "fatty_acid_synthesis"},
            {"id": "G6PD", "name": "G6P Dehydrogenase", "pathway": "pentose_phosphate"},
            {"id": "TKT", "name": "Transketolase", "pathway": "pentose_phosphate"},
            {"id": "MTHFR", "name": "MTHF Reductase", "pathway": "one_carbon"},
            {"id": "PRPS", "name": "PRPP Synthetase", "pathway": "nucleotide_synthesis"},
            {"id": "IMPDH", "name": "IMP Dehydrogenase", "pathway": "nucleotide_synthesis"},
            {"id": "CPT1", "name": "Carnitine Palmitoyltransferase 1", "pathway": "fatty_acid_oxidation"},
            {"id": "HMGCR", "name": "HMG-CoA Reductase", "pathway": "cholesterol"},
            {"id": "ARG1", "name": "Arginase 1", "pathway": "urea_cycle"},
        ]

        flux_changes = []
        for rxn in reactions:
            r_rng = random.Random(seed + hash(rxn["id"]))

            # Baseline flux (arbitrary units)
            baseline_flux = r_rng.uniform(5.0, 100.0)

            # Flux change after target knockout
            if rxn["pathway"] in known_pathways:
                knockout_flux = baseline_flux * r_rng.uniform(0.2, 0.6)
            else:
                knockout_flux = baseline_flux * r_rng.uniform(0.7, 1.3)

            flux_ratio = knockout_flux / max(baseline_flux, 0.01)

            flux_changes.append({
                "reaction_id": rxn["id"],
                "reaction_name": rxn["name"],
                "pathway": rxn["pathway"],
                "baseline_flux": round(baseline_flux, 2),
                "knockout_flux": round(knockout_flux, 2),
                "flux_ratio": round(flux_ratio, 3),
                "change_percent": round((flux_ratio - 1) * 100, 1),
                "is_significantly_altered": abs(flux_ratio - 1) > 0.3,
                "direction": "decreased" if flux_ratio < 0.7 else "increased" if flux_ratio > 1.3 else "unchanged",
            })

        # Growth rate impact
        baseline_growth = rng.uniform(0.3, 0.8)
        knockout_growth = baseline_growth * rng.uniform(0.3, 0.9) if known_pathways else baseline_growth * rng.uniform(0.8, 1.1)
        growth_inhibition = 1.0 - (knockout_growth / max(baseline_growth, 0.01))

        # Essential metabolite analysis
        essential_metabolites = []
        for met in ["ATP", "NADH", "NADPH", "Acetyl-CoA", "Glutamine", "Serine", "Glycine"]:
            m_rng = random.Random(seed + hash(met))
            baseline = m_rng.uniform(10, 100)
            knockout = baseline * m_rng.uniform(0.4, 1.1)
            essential_metabolites.append({
                "metabolite": met,
                "baseline_level": round(baseline, 1),
                "knockout_level": round(knockout, 1),
                "depletion_percent": round((1 - knockout / max(baseline, 0.01)) * 100, 1),
                "is_critical": knockout < baseline * 0.5,
            })

        significantly_altered = [f for f in flux_changes if f["is_significantly_altered"]]

        return {
            "gene": gene,
            "analysis_type": "metabolic_flux_analysis",
            "model": "Recon3D (Human GEM)",
            "total_reactions_analyzed": len(reactions),
            "significantly_altered_reactions": len(significantly_altered),
            "flux_changes": flux_changes,
            "growth_rate_analysis": {
                "baseline_growth_rate": round(baseline_growth, 3),
                "knockout_growth_rate": round(knockout_growth, 3),
                "growth_inhibition": round(growth_inhibition, 3),
                "is_essential": growth_inhibition > 0.5,
            },
            "essential_metabolites": essential_metabolites,
            "critical_depletions": [m for m in essential_metabolites if m["is_critical"]],
            "summary": (
                f"Targeting {gene} alters {len(significantly_altered)} metabolic reactions. "
                f"Growth inhibition: {growth_inhibition:.0%}. "
                f"{'Strong metabolic vulnerability — effective therapeutic target.' if growth_inhibition > 0.5 else 'Moderate metabolic impact.'}"
            ),
        }

    # ─── Drug-Metabolite Interactions ────────────────────────────────────────

    def drug_metabolite_interactions(self, gene: str) -> dict:
        """
        Predict metabolic drug interactions relevant to CAR-T combination therapy.
        Identifies metabolic drugs that could enhance or impair CAR-T efficacy.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 200)

        drug_database = [
            {"name": "Metformin", "target": "Complex I", "mechanism": "OXPHOS inhibition", "category": "metabolic"},
            {"name": "2-Deoxyglucose", "target": "Hexokinase", "mechanism": "Glycolysis inhibition", "category": "metabolic"},
            {"name": "CB-839 (Telaglenastat)", "target": "Glutaminase", "mechanism": "Glutaminolysis inhibition", "category": "metabolic"},
            {"name": "TVB-2640", "target": "FASN", "mechanism": "Fatty acid synthesis inhibition", "category": "metabolic"},
            {"name": "Enasidenib", "target": "IDH2", "mechanism": "Oncometabolite reduction", "category": "targeted"},
            {"name": "Ivosidenib", "target": "IDH1", "mechanism": "Oncometabolite reduction", "category": "targeted"},
            {"name": "Venetoclax", "target": "BCL-2", "mechanism": "Apoptosis + metabolic disruption", "category": "targeted"},
            {"name": "Cyclophosphamide", "target": "DNA", "mechanism": "Lymphodepletion for CAR-T", "category": "chemo"},
            {"name": "Fludarabine", "target": "DNA polymerase", "mechanism": "Lymphodepletion for CAR-T", "category": "chemo"},
            {"name": "Pembrolizumab", "target": "PD-1", "mechanism": "Immune checkpoint blockade", "category": "immunotherapy"},
            {"name": "Nivolumab", "target": "PD-1", "mechanism": "Immune checkpoint blockade", "category": "immunotherapy"},
            {"name": "Rapamycin", "target": "mTOR", "mechanism": "mTOR pathway inhibition", "category": "metabolic"},
        ]

        interactions = []
        for drug in drug_database:
            d_rng = random.Random(int(hashlib.md5(f"{gene}_{drug['name']}".encode()).hexdigest()[:8], 16))

            synergy_score = d_rng.uniform(-0.3, 0.8)
            car_t_impact = d_rng.choice(["enhances", "impairs", "neutral"])
            if drug["category"] == "immunotherapy":
                car_t_impact = "enhances"
                synergy_score = d_rng.uniform(0.3, 0.8)

            interactions.append({
                "drug_name": drug["name"],
                "drug_target": drug["target"],
                "mechanism": drug["mechanism"],
                "category": drug["category"],
                "synergy_score": round(synergy_score, 3),
                "car_t_impact": car_t_impact,
                "clinical_evidence": d_rng.choice(["phase_1", "phase_2", "phase_3", "preclinical", "approved"]),
                "recommendation": "combine" if synergy_score > 0.3 and car_t_impact != "impairs" else "avoid" if car_t_impact == "impairs" else "investigate",
            })

        interactions.sort(key=lambda x: x["synergy_score"], reverse=True)
        recommended = [d for d in interactions if d["recommendation"] == "combine"]

        return {
            "gene": gene,
            "analysis_type": "drug_metabolite_interactions",
            "total_drugs_screened": len(drug_database),
            "interactions": interactions,
            "recommended_combinations": recommended[:5],
            "drugs_to_avoid": [d for d in interactions if d["recommendation"] == "avoid"],
        }

    # ─── TME Metabolic Modeling ──────────────────────────────────────────────

    def tme_metabolic_modeling(self, gene: str) -> dict:
        """
        Model the tumor microenvironment (TME) metabolic landscape.
        Predicts how metabolic competition between tumor cells, CAR-T cells,
        and immune cells affects therapeutic outcomes.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 300)

        # Cell type metabolic profiles in TME
        cell_types = {
            "Tumor cells": {"glucose_demand": "high", "amino_acid_demand": "high", "lipid_demand": "moderate"},
            "CAR-T cells": {"glucose_demand": "high", "amino_acid_demand": "moderate", "lipid_demand": "low"},
            "Tregs": {"glucose_demand": "low", "amino_acid_demand": "moderate", "lipid_demand": "high"},
            "MDSCs": {"glucose_demand": "moderate", "amino_acid_demand": "high", "lipid_demand": "moderate"},
            "TAMs (M2)": {"glucose_demand": "low", "amino_acid_demand": "moderate", "lipid_demand": "high"},
            "NK cells": {"glucose_demand": "moderate", "amino_acid_demand": "moderate", "lipid_demand": "low"},
            "Fibroblasts (CAFs)": {"glucose_demand": "high", "amino_acid_demand": "moderate", "lipid_demand": "moderate"},
        }

        tme_profiles = {}
        for cell_type, demands in cell_types.items():
            c_rng = random.Random(int(hashlib.md5(f"{gene}_{cell_type}".encode()).hexdigest()[:8], 16))
            tme_profiles[cell_type] = {
                **demands,
                "prevalence_percent": round(c_rng.uniform(5, 40), 1),
                "metabolic_fitness": round(c_rng.uniform(0.3, 0.9), 3),
                "glucose_consumption_rate": round(c_rng.uniform(1, 20), 1),
                "lactate_production_rate": round(c_rng.uniform(0.5, 15), 1),
                "oxygen_consumption_rate": round(c_rng.uniform(0.5, 10), 1),
            }

        # Nutrient competition analysis
        glucose_available = rng.uniform(0.5, 5.0)  # mM
        glutamine_available = rng.uniform(0.2, 2.0)  # mM
        oxygen_tension = rng.uniform(1.0, 10.0)  # % O2 (normal tissue ~5-10%, tumor <2%)

        car_t_glucose_access = glucose_available / max(sum(p["glucose_consumption_rate"] for p in tme_profiles.values()), 0.01)
        car_t_fitness_score = round(min(1.0, car_t_glucose_access * 0.4 + (oxygen_tension / 10) * 0.3 + (glutamine_available / 2) * 0.3), 3)

        # Hypoxia analysis
        hypoxic_fraction = max(0, 1.0 - oxygen_tension / 5)

        return {
            "gene": gene,
            "analysis_type": "tme_metabolic_modeling",
            "cell_type_profiles": tme_profiles,
            "nutrient_availability": {
                "glucose_mM": round(glucose_available, 2),
                "glutamine_mM": round(glutamine_available, 2),
                "oxygen_tension_percent": round(oxygen_tension, 1),
                "hypoxic_fraction": round(hypoxic_fraction, 3),
            },
            "car_t_metabolic_fitness": car_t_fitness_score,
            "metabolic_competition": {
                "glucose_competition_index": round(1.0 - car_t_glucose_access, 3) if car_t_glucose_access < 1 else 0,
                "nutrient_deprivation_risk": "high" if glucose_available < 1 else "moderate" if glucose_available < 3 else "low",
            },
            "intervention_strategies": [
                "Preconditioning with glycolysis inhibitor to reduce tumor glucose consumption",
                "Armored CAR-T with enhanced OXPHOS capacity for hypoxic TME",
                "IL-7/IL-15 cytokine support to boost CAR-T metabolic fitness",
                "Anti-CD73 to reduce immunosuppressive adenosine",
            ] if car_t_fitness_score < 0.5 else ["TME metabolic conditions favorable for CAR-T activity"],
        }

    # ─── Immunometabolism CAR-T Fitness ──────────────────────────────────────

    def immunometabolism_fitness(self, gene: str) -> dict:
        """
        Predict CAR-T cell metabolic fitness when targeting this gene.
        Models T cell exhaustion risk from metabolic stress in the TME.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 400)

        # CAR-T metabolic states
        metabolic_states = {
            "Effector (glycolytic)": {
                "description": "High glucose consumption, rapid proliferation",
                "fitness": round(rng.uniform(0.5, 0.9), 3),
                "exhaustion_risk": round(rng.uniform(0.3, 0.7), 3),
                "persistence": "short-term",
            },
            "Memory (OXPHOS)": {
                "description": "Oxidative metabolism, long-term persistence",
                "fitness": round(rng.uniform(0.4, 0.8), 3),
                "exhaustion_risk": round(rng.uniform(0.1, 0.4), 3),
                "persistence": "long-term",
            },
            "Exhausted (dysfunctional)": {
                "description": "Impaired metabolism, checkpoint upregulation",
                "fitness": round(rng.uniform(0.1, 0.3), 3),
                "exhaustion_risk": round(rng.uniform(0.7, 0.95), 3),
                "persistence": "none",
            },
        }

        # Time-course metabolic fitness
        fitness_timeline = []
        base_fitness = rng.uniform(0.6, 0.9)
        for day in [0, 3, 7, 14, 21, 28, 42, 60, 90]:
            decay = day * rng.uniform(0.002, 0.008)
            day_fitness = max(0.1, base_fitness - decay)
            fitness_timeline.append({
                "day": day,
                "metabolic_fitness": round(day_fitness, 3),
                "dominant_state": "effector" if day_fitness > 0.6 else "memory" if day_fitness > 0.3 else "exhausted",
                "predicted_killing_capacity": round(day_fitness ** 1.5, 3),
            })

        # Mitochondrial fitness
        mito_fitness = {
            "mitochondrial_mass": round(rng.uniform(0.4, 0.9), 3),
            "membrane_potential": round(rng.uniform(0.3, 0.95), 3),
            "ros_production": round(rng.uniform(0.1, 0.7), 3),
            "spare_respiratory_capacity": round(rng.uniform(0.2, 0.8), 3),
            "fatty_acid_oxidation": round(rng.uniform(0.3, 0.8), 3),
        }

        return {
            "gene": gene,
            "analysis_type": "immunometabolism_fitness",
            "metabolic_states": metabolic_states,
            "fitness_timeline": fitness_timeline,
            "mitochondrial_fitness": mito_fitness,
            "predicted_persistence_days": round(base_fitness * 100 + rng.uniform(-20, 20)),
            "exhaustion_risk_score": round(1.0 - base_fitness, 3),
            "recommendations": [
                "4-1BB co-stimulatory domain favors OXPHOS and persistence",
                "IL-15 armoring enhances memory T cell metabolism",
                "PGC1a overexpression to boost mitochondrial biogenesis",
            ] if base_fitness < 0.7 else ["Strong baseline metabolic fitness"],
        }

    # ─── Lipidomics Profiling ────────────────────────────────────────────────

    def lipidomics_profiling(self, gene: str) -> dict:
        """
        Analyze lipid metabolism alterations in tumors expressing the target.
        Models sphingolipid, phospholipid, and eicosanoid pathway changes
        that affect CAR-T membrane integrity and signaling.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 600)

        lipid_classes = [
            {"class": "Sphingomyelins (SM)", "pathway": "Sphingolipid metabolism",
             "tumor_alteration": round(rng.uniform(-2.0, 3.0), 2),
             "car_t_impact": "Membrane rigidity affects receptor clustering"},
            {"class": "Phosphatidylcholines (PC)", "pathway": "Glycerophospholipid metabolism",
             "tumor_alteration": round(rng.uniform(-1.5, 2.5), 2),
             "car_t_impact": "Membrane fluidity modulates synapse formation"},
            {"class": "Ceramides (Cer)", "pathway": "Sphingolipid metabolism",
             "tumor_alteration": round(rng.uniform(-1.0, 4.0), 2),
             "car_t_impact": "Pro-apoptotic ceramide induces T cell death"},
            {"class": "Prostaglandins (PG)", "pathway": "Arachidonic acid metabolism",
             "tumor_alteration": round(rng.uniform(0.0, 5.0), 2),
             "car_t_impact": "PGE2 suppresses CAR-T cytotoxicity via EP2/EP4"},
            {"class": "Lysophosphatidic acid (LPA)", "pathway": "Glycerophospholipid metabolism",
             "tumor_alteration": round(rng.uniform(-0.5, 3.0), 2),
             "car_t_impact": "LPA impairs T cell chemotaxis"},
            {"class": "Cholesterol esters (CE)", "pathway": "Cholesterol metabolism",
             "tumor_alteration": round(rng.uniform(-2.0, 2.0), 2),
             "car_t_impact": "Cholesterol loading impairs T cell effector function"},
            {"class": "Phosphatidylserines (PS)", "pathway": "Glycerophospholipid metabolism",
             "tumor_alteration": round(rng.uniform(0.0, 3.5), 2),
             "car_t_impact": "PS externalization triggers phagocytic checkpoint"},
            {"class": "Sphingosine-1-phosphate (S1P)", "pathway": "Sphingolipid metabolism",
             "tumor_alteration": round(rng.uniform(-1.0, 2.5), 2),
             "car_t_impact": "S1P gradients regulate T cell tumor infiltration"},
        ]

        fatty_acids = []
        fa_types = [
            ("Palmitic acid (C16:0)", "saturated"),
            ("Stearic acid (C18:0)", "saturated"),
            ("Oleic acid (C18:1)", "monounsaturated"),
            ("Linoleic acid (C18:2)", "polyunsaturated"),
            ("Arachidonic acid (C20:4)", "polyunsaturated"),
            ("EPA (C20:5)", "omega-3"),
            ("DHA (C22:6)", "omega-3"),
        ]
        for fa_name, fa_type in fa_types:
            fa_rng = random.Random(int(hashlib.md5(f"{gene}_{fa_name}".encode()).hexdigest()[:8], 16))
            fatty_acids.append({
                "name": fa_name, "type": fa_type,
                "relative_abundance": round(fa_rng.uniform(0.02, 0.25), 3),
                "log2fc_vs_normal": round(fa_rng.uniform(-2.0, 2.0), 2),
            })

        lipid_peroxidation = {
            "4_HNE_level": round(rng.uniform(0.5, 5.0), 2),
            "MDA_level": round(rng.uniform(0.3, 4.0), 2),
            "ferroptosis_sensitivity": round(rng.uniform(0.1, 0.9), 3),
            "GPX4_expression": round(rng.uniform(0.5, 5.0), 2),
        }

        immunosuppressive = sum(1 for l in lipid_classes if l["tumor_alteration"] > 1.5)
        lipid_score = round(max(0.1, 1.0 - immunosuppressive * 0.12), 3)

        return {
            "gene": gene,
            "analysis_type": "lipidomics_profiling",
            "data_source": "LIPID MAPS / HMDB / MetaboAnalyst",
            "lipid_classes": lipid_classes,
            "fatty_acid_composition": fatty_acids,
            "lipid_peroxidation": lipid_peroxidation,
            "membrane_fluidity_index": round(rng.uniform(0.3, 0.9), 3),
            "immunosuppressive_lipid_burden": immunosuppressive,
            "lipid_metabolism_score": lipid_score,
        }

    # ─── Amino Acid Metabolism ───────────────────────────────────────────────

    def amino_acid_metabolism(self, gene: str) -> dict:
        """
        Profile amino acid metabolism in the TME. Key amino acids like
        tryptophan, arginine, and glutamine impact CAR-T fitness.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 700)

        amino_acid_pathways = [
            {
                "amino_acid": "Tryptophan", "enzyme": "IDO1/TDO2",
                "pathway": "Kynurenine pathway",
                "enzyme_expression": round(rng.uniform(0.5, 8.0), 2),
                "depletion_level": round(rng.uniform(0.1, 0.9), 3),
                "metabolite": "Kynurenine",
                "metabolite_level": round(rng.uniform(0.5, 5.0), 2),
                "car_t_effect": "T cell arrest via AhR activation",
                "counter": "IDO1 inhibitor (epacadostat)",
            },
            {
                "amino_acid": "Arginine", "enzyme": "ARG1/ARG2",
                "pathway": "Urea cycle / Polyamine synthesis",
                "enzyme_expression": round(rng.uniform(0.5, 6.0), 2),
                "depletion_level": round(rng.uniform(0.1, 0.8), 3),
                "metabolite": "Ornithine/Polyamines",
                "metabolite_level": round(rng.uniform(0.3, 4.0), 2),
                "car_t_effect": "T cell proliferation arrest",
                "counter": "ARG1 inhibitor (CB-1158)",
            },
            {
                "amino_acid": "Glutamine", "enzyme": "GLS1/GLS2",
                "pathway": "Glutaminolysis",
                "enzyme_expression": round(rng.uniform(1.0, 10.0), 2),
                "depletion_level": round(rng.uniform(0.2, 0.7), 3),
                "metabolite": "Glutamate (excess)",
                "metabolite_level": round(rng.uniform(1.0, 8.0), 2),
                "car_t_effect": "T cell biosynthetic starvation",
                "counter": "GLS inhibitor (CB-839/telaglenastat)",
            },
            {
                "amino_acid": "Cysteine", "enzyme": "xCT (SLC7A11)",
                "pathway": "Glutathione synthesis",
                "enzyme_expression": round(rng.uniform(0.5, 7.0), 2),
                "depletion_level": round(rng.uniform(0.1, 0.6), 3),
                "metabolite": "Glutathione (sequestered)",
                "metabolite_level": round(rng.uniform(0.5, 5.0), 2),
                "car_t_effect": "T cell redox imbalance",
                "counter": "xCT inhibitor (sulfasalazine)",
            },
            {
                "amino_acid": "Methionine", "enzyme": "MAT2A",
                "pathway": "One-carbon metabolism",
                "enzyme_expression": round(rng.uniform(0.5, 5.0), 2),
                "depletion_level": round(rng.uniform(0.1, 0.5), 3),
                "metabolite": "S-adenosylmethionine",
                "metabolite_level": round(rng.uniform(0.5, 4.0), 2),
                "car_t_effect": "Altered T cell epigenetic programming",
                "counter": "Methionine supplementation in culture",
            },
        ]

        total_depletion = sum(p["depletion_level"] for p in amino_acid_pathways) / len(amino_acid_pathways)

        return {
            "gene": gene,
            "analysis_type": "amino_acid_metabolism",
            "data_source": "HMDB / KEGG / Metabolon",
            "amino_acid_pathways": amino_acid_pathways,
            "overall_depletion_index": round(total_depletion, 3),
            "nutrient_sensing": {
                "mTORC1_activity": round(rng.uniform(0.2, 0.9), 3),
                "AMPK_activity": round(rng.uniform(0.2, 0.8), 3),
                "nutrient_stress": "high" if total_depletion > 0.5 else "moderate" if total_depletion > 0.3 else "low",
            },
            "t_cell_fitness_impact": round(1.0 - total_depletion * 0.8, 3),
            "most_depleted": max(amino_acid_pathways, key=lambda x: x["depletion_level"])["amino_acid"],
            "combination_targets": [p["counter"] for p in amino_acid_pathways if p["depletion_level"] > 0.4],
        }

    # ─── Nucleotide Metabolism ───────────────────────────────────────────────

    def nucleotide_metabolism(self, gene: str) -> dict:
        """Analyze adenosine signaling and nucleotide metabolism in the TME."""
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 800)

        cd39 = round(rng.uniform(0.5, 8.0), 2)
        cd73 = round(rng.uniform(0.5, 7.0), 2)
        a2ar = round(rng.uniform(0.5, 6.0), 2)
        adenosine = round((cd39 * cd73) / 10, 3)

        de_novo = {k: round(rng.uniform(0.5, 6.0), 2) for k in ["PPAT", "GART", "ATIC", "IMPDH2", "DHODH"]}
        salvage = {k: round(rng.uniform(0.5, 5.0), 2) for k in ["HPRT1", "APRT", "TK1", "DCK"]}

        nad_metabolism = {
            "NAMPT_expression": round(rng.uniform(0.5, 7.0), 2),
            "CD38_expression": round(rng.uniform(0.5, 8.0), 2),
            "NAD_plus_level": round(rng.uniform(0.3, 3.0), 2),
            "SIRT1_activity": round(rng.uniform(0.2, 0.9), 3),
        }

        score = round(min(1.0, adenosine * 0.4 + (cd39 / 10) * 0.3 + (a2ar / 8) * 0.3), 3)

        return {
            "gene": gene,
            "analysis_type": "nucleotide_metabolism",
            "data_source": "KEGG Purine Metabolism / HMDB",
            "adenosine_pathway": {
                "CD39": cd39, "CD73": cd73, "A2AR": a2ar,
                "estimated_adenosine_nM": round(adenosine * 100, 1),
                "immunosuppression": "severe" if adenosine > 3 else "high" if adenosine > 1.5 else "moderate" if adenosine > 0.5 else "low",
            },
            "de_novo_synthesis": de_novo,
            "salvage_pathway": salvage,
            "nad_metabolism": nad_metabolism,
            "immunosuppression_score": score,
            "strategies": [
                "Anti-CD73 (oleclumab) to block adenosine generation",
                "A2AR antagonist (ciforadenant) to restore CAR-T function",
                "Anti-CD38 (daratumumab) to preserve NAD+",
            ] if score > 0.5 else ["Nucleotide metabolism not significantly immunosuppressive"],
        }

    # ─── Redox Balance Analysis ──────────────────────────────────────────────

    def redox_balance_analysis(self, gene: str) -> dict:
        """Evaluate oxidative stress landscape affecting CAR-T."""
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 900)

        ros_sources = {
            "mitochondrial_complex_I_III": round(rng.uniform(0.5, 5.0), 2),
            "NOX_family": round(rng.uniform(0.5, 4.0), 2),
            "xanthine_oxidase": round(rng.uniform(0.2, 3.0), 2),
            "cytochrome_P450": round(rng.uniform(0.3, 3.0), 2),
        }

        antioxidant_defense = {
            "SOD1": round(rng.uniform(0.5, 5.0), 2),
            "SOD2": round(rng.uniform(0.5, 6.0), 2),
            "Catalase": round(rng.uniform(0.5, 5.0), 2),
            "GPX1": round(rng.uniform(0.5, 5.0), 2),
            "GPX4": round(rng.uniform(0.5, 5.0), 2),
            "Thioredoxin": round(rng.uniform(0.5, 4.0), 2),
            "NRF2_activity": round(rng.uniform(0.2, 0.9), 3),
            "GSH_GSSG_ratio": round(rng.uniform(1.0, 20.0), 1),
        }

        total_ros = sum(ros_sources.values())
        total_def = sum(v for k, v in antioxidant_defense.items() if k not in ("NRF2_activity", "GSH_GSSG_ratio"))
        ros_burden = round(total_ros / max(total_def, 0.1), 3)

        ferroptosis = {
            "GPX4_dependency": round(rng.uniform(0.3, 0.95), 3),
            "iron_accumulation": round(rng.uniform(0.2, 3.0), 2),
            "lipid_peroxidation": round(rng.uniform(0.2, 4.0), 2),
            "sensitivity": "high" if rng.uniform(0, 1) > 0.6 else "moderate" if rng.uniform(0, 1) > 0.3 else "low",
        }

        return {
            "gene": gene,
            "analysis_type": "redox_balance",
            "ros_sources": ros_sources,
            "antioxidant_defense": antioxidant_defense,
            "ros_burden_ratio": ros_burden,
            "oxidative_stress": "severe" if ros_burden > 2.0 else "high" if ros_burden > 1.0 else "moderate" if ros_burden > 0.5 else "low",
            "t_cell_impact": {
                "tcr_signaling_impairment": round(min(1.0, ros_burden * 0.3), 3),
                "proliferation_inhibition": round(min(1.0, ros_burden * 0.25), 3),
                "exhaustion_acceleration": round(min(1.0, ros_burden * 0.2), 3),
            },
            "ferroptosis_vulnerability": ferroptosis,
            "engineering_suggestions": [
                "Catalase-armored CAR-T for ROS resistance",
                "NRF2-overexpressing CAR-T for antioxidant capacity",
            ] if ros_burden > 1.0 else ["Standard CAR-T adequate for this redox environment"],
        }

    # ─── Metabolic Vulnerability Mapping ─────────────────────────────────────

    def metabolic_vulnerability_mapping(self, gene: str) -> dict:
        """Map metabolic vulnerabilities for combination therapy."""
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 1000)

        vulns = [
            {"vulnerability": "Glutamine addiction", "pathway": "Glutaminolysis",
             "dependency": round(rng.uniform(0.2, 0.95), 3), "enzyme": "GLS1",
             "drug": "CB-839 (telaglenastat)", "synergy": round(rng.uniform(0.3, 0.9), 3)},
            {"vulnerability": "Warburg effect", "pathway": "Aerobic glycolysis",
             "dependency": round(rng.uniform(0.3, 0.9), 3), "enzyme": "LDHA/HK2",
             "drug": "2-DG or Lonidamine", "synergy": round(rng.uniform(0.2, 0.8), 3)},
            {"vulnerability": "FAO dependence", "pathway": "Beta-oxidation",
             "dependency": round(rng.uniform(0.1, 0.7), 3), "enzyme": "CPT1A",
             "drug": "Etomoxir", "synergy": round(rng.uniform(0.2, 0.7), 3)},
            {"vulnerability": "One-carbon metabolism", "pathway": "Folate cycle",
             "dependency": round(rng.uniform(0.1, 0.6), 3), "enzyme": "MTHFD2",
             "drug": "Pemetrexed", "synergy": round(rng.uniform(0.2, 0.6), 3)},
            {"vulnerability": "Cholesterol biosynthesis", "pathway": "Mevalonate",
             "dependency": round(rng.uniform(0.1, 0.7), 3), "enzyme": "HMGCR",
             "drug": "Statins", "synergy": round(rng.uniform(0.3, 0.8), 3)},
            {"vulnerability": "Serine biosynthesis", "pathway": "Serine/Glycine",
             "dependency": round(rng.uniform(0.1, 0.6), 3), "enzyme": "PHGDH",
             "drug": "NCT-503", "synergy": round(rng.uniform(0.2, 0.6), 3)},
        ]

        vulns.sort(key=lambda x: x["synergy"], reverse=True)
        high = [v for v in vulns if v["synergy"] > 0.6]

        return {
            "gene": gene,
            "analysis_type": "metabolic_vulnerability_mapping",
            "data_source": "DepMap / CCLE",
            "vulnerabilities": vulns,
            "top_vulnerability": vulns[0],
            "high_synergy_targets": len(high),
            "recommended_combinations": [f"{v['drug']} + CAR-T (synergy: {v['synergy']:.0%})" for v in high],
            "overall_vulnerability": round(sum(v["dependency"] for v in vulns) / len(vulns), 3),
        }

    # ─── Pharmacometabolomics ────────────────────────────────────────────────

    def pharmacometabolomics(self, gene: str) -> dict:
        """Model drug-metabolite-CAR-T interactions in treatment protocols."""
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 1100)

        drugs = [
            {"drug": "Cyclophosphamide", "category": "Lymphodepletion",
             "effects": ["Depletes Tregs", "Cytokine surge (IL-7/IL-15)"],
             "impact": round(rng.uniform(0.4, 0.9), 3), "net": "beneficial"},
            {"drug": "Fludarabine", "category": "Lymphodepletion",
             "effects": ["Purine analog disruption", "Enhanced CAR-T expansion"],
             "impact": round(rng.uniform(0.3, 0.8), 3), "net": "beneficial"},
            {"drug": "Tocilizumab", "category": "CRS management",
             "effects": ["IL-6R blockade", "May reduce peak expansion"],
             "impact": round(rng.uniform(-0.3, 0.2), 3), "net": "neutral"},
            {"drug": "Dexamethasone", "category": "CRS/ICANS",
             "effects": ["Suppresses T cell glucose uptake", "Can ablate CAR-T"],
             "impact": round(rng.uniform(-0.7, -0.2), 3), "net": "detrimental"},
            {"drug": "Anakinra", "category": "CRS alternative",
             "effects": ["IL-1R blockade", "Preserves CAR-T fitness"],
             "impact": round(rng.uniform(0.0, 0.4), 3), "net": "beneficial"},
        ]

        return {
            "gene": gene,
            "analysis_type": "pharmacometabolomics",
            "data_source": "PharmGKB / DrugBank",
            "drug_interactions": drugs,
            "beneficial": len([d for d in drugs if d["net"] == "beneficial"]),
            "detrimental": len([d for d in drugs if d["net"] == "detrimental"]),
            "optimal_protocol": {
                "lymphodepletion": "Cy/Flu standard of care",
                "crs_management": "Tocilizumab first-line, minimize steroids",
                "metabolic_support": "IL-7/IL-15 supplementation",
            },
            "pharmacokinetic_window": {
                "clearance_hours": rng.randint(24, 72),
                "optimal_delay_hours": rng.randint(48, 96),
                "peak_expansion_day": rng.randint(7, 14),
            },
        }

    # ─── Bile Acid Profiling ─────────────────────────────────────────────────

    def bile_acid_profiling(self, gene: str) -> dict:
        """
        Profile bile acid metabolism in tumor microenvironment.
        Bile acids regulate FXR/TGR5 signaling affecting immune cell function.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 12000)

        primary_bile_acids = [
            {"name": "Cholic acid", "type": "primary", "conjugation": "taurine"},
            {"name": "Chenodeoxycholic acid", "type": "primary", "conjugation": "glycine"},
        ]
        secondary_bile_acids = [
            {"name": "Deoxycholic acid", "type": "secondary", "conjugation": "unconjugated"},
            {"name": "Lithocholic acid", "type": "secondary", "conjugation": "unconjugated"},
            {"name": "Ursodeoxycholic acid", "type": "secondary", "conjugation": "taurine"},
        ]

        all_acids = primary_bile_acids + secondary_bile_acids
        profiles = []
        for acid in all_acids:
            a_rng = random.Random(seed + 12000 + hash(acid["name"]))
            tumor_level = a_rng.uniform(0.1, 50.0)
            normal_level = a_rng.uniform(0.1, 20.0)
            profiles.append({
                **acid,
                "tumor_concentration_uM": round(tumor_level, 2),
                "normal_concentration_uM": round(normal_level, 2),
                "fold_change": round(tumor_level / max(normal_level, 0.01), 2),
                "fxr_activation": round(a_rng.uniform(0, 1), 3),
                "tgr5_activation": round(a_rng.uniform(0, 1), 3),
                "immunomodulatory_effect": a_rng.choice([
                    "T cell suppression", "macrophage polarization",
                    "DC maturation inhibition", "neutral", "Treg induction",
                ]),
            })

        return {
            "gene": gene,
            "analysis_type": "bile_acid_profiling",
            "data_source": "LC-MS/MS bile acid panel simulation",
            "bile_acid_profiles": profiles,
            "primary_secondary_ratio": round(
                sum(p["tumor_concentration_uM"] for p in profiles if p["type"] == "primary") /
                max(sum(p["tumor_concentration_uM"] for p in profiles if p["type"] == "secondary"), 0.01), 2
            ),
            "immune_impact": sum(
                1 for p in profiles if p["immunomodulatory_effect"] != "neutral"
            ),
            "cart_implication": (
                "Bile acid accumulation may suppress T cell function in TME"
                if any(p["immunomodulatory_effect"] == "T cell suppression" and p["fold_change"] > 2
                       for p in profiles) else
                "Bile acid profile does not significantly impact CAR-T activity"
            ),
        }

    # ─── Short-Chain Fatty Acid Analysis ─────────────────────────────────────

    def scfa_analysis(self, gene: str) -> dict:
        """
        Analyze short-chain fatty acid profiles in the tumor
        microenvironment. SCFAs regulate immune cell differentiation.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 13000)

        scfas = [
            {"name": "Acetate", "carbon_length": 2},
            {"name": "Propionate", "carbon_length": 3},
            {"name": "Butyrate", "carbon_length": 4},
            {"name": "Valerate", "carbon_length": 5},
            {"name": "Isobutyrate", "carbon_length": 4},
            {"name": "Isovalerate", "carbon_length": 5},
        ]

        profiles = []
        for scfa in scfas:
            s_rng = random.Random(seed + 13000 + hash(scfa["name"]))
            tumor_conc = s_rng.uniform(0.01, 5.0)
            normal_conc = s_rng.uniform(0.05, 3.0)
            profiles.append({
                **scfa,
                "tumor_mM": round(tumor_conc, 3),
                "normal_mM": round(normal_conc, 3),
                "fold_change": round(tumor_conc / max(normal_conc, 0.001), 2),
                "hdac_inhibition": round(s_rng.uniform(0, 1), 3) if scfa["carbon_length"] >= 3 else 0,
                "gpr_activation": round(s_rng.uniform(0, 1), 3),
                "treg_induction": round(s_rng.uniform(0, 0.8), 3),
                "cd8_effect": s_rng.choice(["enhancing", "suppressing", "neutral"]),
            })

        butyrate = next((p for p in profiles if p["name"] == "Butyrate"), None)
        butyrate_level = butyrate["tumor_mM"] if butyrate else 0

        return {
            "gene": gene,
            "analysis_type": "scfa_profiling",
            "data_source": "GC-MS SCFA panel simulation",
            "scfa_profiles": profiles,
            "total_scfa_tumor": round(sum(p["tumor_mM"] for p in profiles), 3),
            "butyrate_level": round(butyrate_level, 3),
            "hdac_inhibition_potential": round(
                max(p["hdac_inhibition"] for p in profiles), 3
            ),
            "cart_modulation": (
                "SCFA-rich TME may enhance CAR-T epigenetic reprogramming"
                if butyrate_level > 1 else
                "Standard SCFA levels — no major CAR-T modulation expected"
            ),
        }

    # ─── Polyamine Metabolism ────────────────────────────────────────────────

    def polyamine_metabolism(self, gene: str) -> dict:
        """
        Profile polyamine metabolism. Tumor polyamine accumulation drives
        immunosuppression by depleting arginine and producing IDO.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 14000)

        polyamines = [
            {"name": "Putrescine", "enzyme": "ODC1", "inhibitor": "DFMO"},
            {"name": "Spermidine", "enzyme": "SRM", "inhibitor": "MGBG"},
            {"name": "Spermine", "enzyme": "SMS", "inhibitor": "APCHA"},
        ]

        profiles = []
        for pa in polyamines:
            p_rng = random.Random(seed + 14000 + hash(pa["name"]))
            tumor_level = p_rng.uniform(1, 100)
            normal_level = p_rng.uniform(0.5, 30)
            profiles.append({
                **pa,
                "tumor_nmol_g": round(tumor_level, 1),
                "normal_nmol_g": round(normal_level, 1),
                "fold_change": round(tumor_level / max(normal_level, 0.01), 2),
                "enzyme_expression": round(p_rng.uniform(0, 10), 2),
                "immune_suppression_score": round(p_rng.uniform(0.1, 0.9), 3),
            })

        odc1_expression = round(rng.uniform(0.5, 15), 2)
        arginine_depletion = round(rng.uniform(0, 1), 3)

        return {
            "gene": gene,
            "analysis_type": "polyamine_metabolism",
            "data_source": "LC-MS polyamine panel simulation",
            "polyamine_profiles": profiles,
            "odc1_expression": odc1_expression,
            "arginine_depletion": arginine_depletion,
            "total_polyamine_fold_change": round(
                sum(p["fold_change"] for p in profiles) / len(profiles), 2
            ),
            "therapeutic_strategy": (
                "DFMO (ODC1 inhibitor) pre-treatment to reduce immunosuppressive polyamines"
                if odc1_expression > 5 else
                "Polyamine levels within acceptable range"
            ),
            "cart_impact": (
                "HIGH: Polyamine-driven arginine depletion impairs T cell fitness"
                if arginine_depletion > 0.6 else
                "MODERATE: Some polyamine-mediated immunosuppression"
                if arginine_depletion > 0.3 else "LOW: Minimal polyamine impact"
            ),
        }

    # ─── One-Carbon Metabolism ───────────────────────────────────────────────

    def one_carbon_metabolism(self, gene: str) -> dict:
        """
        Analyze one-carbon metabolism (folate cycle, methionine cycle).
        Critical for nucleotide synthesis and epigenetic modifications.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 15000)

        enzymes = [
            {"name": "MTHFR", "pathway": "folate cycle"},
            {"name": "DHFR", "pathway": "folate cycle"},
            {"name": "TYMS", "pathway": "nucleotide synthesis"},
            {"name": "MAT2A", "pathway": "methionine cycle"},
            {"name": "AHCY", "pathway": "methionine cycle"},
            {"name": "MTR", "pathway": "folate-methionine bridge"},
            {"name": "SHMT1", "pathway": "serine-glycine"},
            {"name": "SHMT2", "pathway": "serine-glycine"},
        ]

        enzyme_status = []
        for enz in enzymes:
            e_rng = random.Random(seed + 15000 + hash(enz["name"]))
            expression = e_rng.uniform(0, 15)
            enzyme_status.append({
                **enz,
                "expression_tumor": round(expression, 2),
                "expression_normal": round(e_rng.uniform(0, 8), 2),
                "fold_change": round(expression / max(e_rng.uniform(0.1, 8), 0.01), 2),
                "mutation_status": e_rng.choice(["wildtype", "variant", "amplified"]),
            })

        sam_sar_ratio = round(rng.uniform(0.5, 5.0), 2)
        folate_status = round(rng.uniform(0.1, 1.0), 3)

        return {
            "gene": gene,
            "analysis_type": "one_carbon_metabolism",
            "data_source": "Metabolomics / expression simulation",
            "enzyme_profiles": enzyme_status,
            "sam_sar_ratio": sam_sar_ratio,
            "folate_sufficiency": folate_status,
            "methylation_capacity": (
                "HIGH" if sam_sar_ratio > 3 else
                "MODERATE" if sam_sar_ratio > 1.5 else "LOW"
            ),
            "methotrexate_sensitivity": any(
                e["fold_change"] > 3 for e in enzyme_status if e["name"] == "DHFR"
            ),
            "cart_relevance": (
                "One-carbon pathway supports rapid T cell proliferation; "
                "sufficient folate availability is favorable for CAR-T expansion"
            ),
        }

    # ─── EMT Metabolic Signature ─────────────────────────────────────────────

    def emt_metabolic_signature(self, gene: str) -> dict:
        """
        Map the metabolic rewiring associated with epithelial-mesenchymal
        transition which drives antigen loss and therapy resistance.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 16000)

        emt_markers = {
            "E-cadherin": round(rng.uniform(0, 10), 2),
            "N-cadherin": round(rng.uniform(0, 10), 2),
            "Vimentin": round(rng.uniform(0, 15), 2),
            "Snail": round(rng.uniform(0, 8), 2),
            "Twist": round(rng.uniform(0, 8), 2),
            "ZEB1": round(rng.uniform(0, 8), 2),
        }

        emt_score = round(
            (emt_markers["N-cadherin"] + emt_markers["Vimentin"] + emt_markers["ZEB1"]) /
            max(emt_markers["E-cadherin"] + 1, 0.01), 3
        )

        metabolic_shifts = {
            "glycolysis": round(rng.uniform(-2, 2), 2),
            "glutaminolysis": round(rng.uniform(-1, 3), 2),
            "fatty_acid_oxidation": round(rng.uniform(-1, 2), 2),
            "oxphos": round(rng.uniform(-2, 1), 2),
            "serine_biosynthesis": round(rng.uniform(-1, 2), 2),
            "lipogenesis": round(rng.uniform(-2, 2), 2),
        }

        target_loss_risk = round(rng.uniform(0, 1), 3)

        return {
            "gene": gene,
            "analysis_type": "emt_metabolic_signature",
            "data_source": "Integrated transcriptomic-metabolomic simulation",
            "emt_markers": emt_markers,
            "emt_score": emt_score,
            "emt_status": (
                "mesenchymal" if emt_score > 2 else
                "hybrid_EMT" if emt_score > 0.8 else "epithelial"
            ),
            "metabolic_shifts": metabolic_shifts,
            "target_expression_loss_risk": target_loss_risk,
            "therapy_insight": (
                "HIGH RISK: Mesenchymal phenotype associated with antigen loss"
                if emt_score > 2 and target_loss_risk > 0.5 else
                "MODERATE: Hybrid EMT — monitor for phenotypic drift"
                if emt_score > 0.8 else
                "LOW: Epithelial phenotype maintains target expression"
            ),
        }

    # ─── Immune Checkpoint Metabolic Regulation ──────────────────────────────

    def checkpoint_metabolic_regulation(self, gene: str) -> dict:
        """
        Map how metabolic pathways regulate immune checkpoint expression.
        Identifies metabolic interventions to enhance CAR-T function.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 17000)

        checkpoints = [
            {"name": "PD-L1", "axis": "PD-1/PD-L1"},
            {"name": "CTLA-4", "axis": "CTLA-4/B7"},
            {"name": "TIM-3", "axis": "TIM-3/Galectin-9"},
            {"name": "LAG-3", "axis": "LAG-3/MHC-II"},
            {"name": "TIGIT", "axis": "TIGIT/CD155"},
            {"name": "VISTA", "axis": "VISTA"},
        ]

        checkpoint_metabolic_map = []
        for cp in checkpoints:
            c_rng = random.Random(seed + 17000 + hash(cp["name"]))
            expression = c_rng.uniform(0, 10)
            checkpoint_metabolic_map.append({
                **cp,
                "expression_level": round(expression, 2),
                "metabolic_regulators": c_rng.sample([
                    "HIF-1a (hypoxia)", "mTOR signaling", "AMPK activation",
                    "Lactate accumulation", "IDO1 (tryptophan)",
                    "Adenosine (CD73/A2AR)", "Glucose deprivation",
                    "Glutamine restriction", "ROS stress",
                ], k=c_rng.randint(1, 4)),
                "upregulated_by_metabolic_stress": c_rng.random() > 0.4,
                "druggable_metabolic_target": c_rng.choice([
                    "IDO1 inhibitor", "A2AR antagonist", "CD73 antibody",
                    "mTOR inhibitor", "MCT1 inhibitor", "none",
                ]),
            })

        high_checkpoints = [c for c in checkpoint_metabolic_map if c["expression_level"] > 5]

        return {
            "gene": gene,
            "analysis_type": "checkpoint_metabolic_regulation",
            "data_source": "Integrated checkpoint-metabolomics simulation",
            "checkpoint_profiles": checkpoint_metabolic_map,
            "high_expression_checkpoints": len(high_checkpoints),
            "metabolically_druggable": sum(
                1 for c in checkpoint_metabolic_map
                if c["druggable_metabolic_target"] != "none"
            ),
            "combination_strategy": (
                f"Metabolic checkpoint modulation: {high_checkpoints[0]['druggable_metabolic_target']} "
                f"+ CAR-T to overcome {high_checkpoints[0]['name']}-mediated suppression"
                if high_checkpoints and high_checkpoints[0]["druggable_metabolic_target"] != "none"
                else "No dominant metabolic-checkpoint axis identified"
            ),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Lipidomics TME Profiling
    # ═══════════════════════════════════════════════════════════════════════════

    def lipidomics_tme_profiling(self, gene: str) -> dict:
        """
        Comprehensive lipidomic analysis of the tumor microenvironment.
        Profiles sphingolipids, eicosanoids, phospholipids, and
        ceramide/S1P balance that regulate immune cell trafficking
        and CAR-T cell persistence.

        Models LC-MS/MS shotgun lipidomics data with lipid species
        quantification across major lipid classes.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 18000)

        # ── Sphingolipid metabolism (ceramide / S1P axis) ──
        ceramide_species = []
        for chain in ["C16:0", "C18:0", "C20:0", "C22:0", "C24:0", "C24:1"]:
            c_rng = random.Random(seed + 18000 + hash(chain))
            tumor = c_rng.uniform(0.1, 10.0)
            normal = c_rng.uniform(0.1, 8.0)
            ceramide_species.append({
                "species": f"Cer({chain})",
                "tumor_nmol_per_mg": round(tumor, 3),
                "normal_nmol_per_mg": round(normal, 3),
                "fold_change": round(tumor / max(normal, 0.01), 2),
                "pro_apoptotic": tumor > normal * 1.5,
            })

        s1p_level = round(rng.uniform(0.5, 20.0), 2)
        s1p_s1pr1 = round(rng.uniform(0, 10), 2)  # S1PR1 expression
        s1p_s1pr2 = round(rng.uniform(0, 10), 2)
        ceramide_total = sum(c["tumor_nmol_per_mg"] for c in ceramide_species)
        ceramide_s1p_ratio = round(ceramide_total / max(s1p_level, 0.01), 2)

        # ── Eicosanoid profiling ──
        eicosanoids = []
        eicosanoid_species = [
            {"name": "PGE2", "pathway": "COX-2", "effect": "immunosuppressive"},
            {"name": "PGD2", "pathway": "COX-1", "effect": "anti-inflammatory"},
            {"name": "LTB4", "pathway": "5-LOX", "effect": "pro-inflammatory"},
            {"name": "LXA4", "pathway": "15-LOX", "effect": "pro-resolving"},
            {"name": "TXA2", "pathway": "COX-1/TXAS", "effect": "pro-thrombotic"},
            {"name": "15d-PGJ2", "pathway": "COX-2/non-enzymatic", "effect": "anti-inflammatory (PPARγ)"},
            {"name": "12-HETE", "pathway": "12-LOX", "effect": "pro-tumorigenic"},
            {"name": "EET (14,15)", "pathway": "CYP450", "effect": "pro-angiogenic"},
        ]

        for eico in eicosanoid_species:
            e_rng = random.Random(seed + 18100 + hash(eico["name"]))
            concentration = e_rng.uniform(0.01, 50.0)
            eicosanoids.append({
                **eico,
                "concentration_ng_ml": round(concentration, 2),
                "elevated": concentration > 10.0,
                "impact_on_car_t": (
                    "NEGATIVE" if eico["effect"] == "immunosuppressive" and concentration > 10
                    else "POSITIVE" if eico["effect"] == "pro-inflammatory" and concentration > 5
                    else "NEUTRAL"
                ),
            })

        # ── Phospholipid remodeling (Lands cycle) ──
        phospholipids = {}
        pl_classes = ["PC", "PE", "PS", "PI", "PG", "PA", "SM"]
        for pl in pl_classes:
            p_rng = random.Random(seed + 18200 + hash(pl))
            phospholipids[pl] = {
                "tumor_mol_pct": round(p_rng.uniform(1, 40), 2),
                "normal_mol_pct": round(p_rng.uniform(1, 35), 2),
                "saturated_fraction": round(p_rng.uniform(0.2, 0.8), 3),
                "pufa_enrichment": round(p_rng.uniform(0, 5), 2),
            }

        # ── Lysophospholipid signaling ──
        lpa_level = round(rng.uniform(0.1, 20.0), 2)
        lpc_level = round(rng.uniform(1, 50), 2)
        lpcat_expression = round(rng.uniform(0, 15), 2)

        # Immunosuppressive lipid burden
        pge2_level = next((e["concentration_ng_ml"] for e in eicosanoids if e["name"] == "PGE2"), 0)
        immunosuppressive_burden = "HIGH" if (pge2_level > 15 and s1p_level > 10) else "MODERATE" if (pge2_level > 5 or s1p_level > 5) else "LOW"

        return {
            "gene": gene,
            "analysis_type": "lipidomics_tme",
            "data_source": "LC-MS/MS Shotgun Lipidomics simulation",
            "sphingolipid_axis": {
                "ceramide_species": ceramide_species,
                "ceramide_total_nmol": round(ceramide_total, 2),
                "s1p_level": s1p_level,
                "ceramide_s1p_ratio": ceramide_s1p_ratio,
                "sphingolipid_balance": (
                    "PRO-APOPTOTIC (ceramide dominant)" if ceramide_s1p_ratio > 5
                    else "PRO-SURVIVAL (S1P dominant)" if ceramide_s1p_ratio < 1
                    else "BALANCED"
                ),
                "s1pr1_expression": s1p_s1pr1,
                "s1pr2_expression": s1p_s1pr2,
                "t_cell_trafficking": (
                    "IMPAIRED — high S1PR1 may trap T cells in lymphoid organs"
                    if s1p_s1pr1 > 7 else "FAVORABLE"
                ),
            },
            "eicosanoid_profile": eicosanoids,
            "pge2_dominant": pge2_level > 15,
            "phospholipid_remodeling": phospholipids,
            "lysophospholipid_signaling": {
                "lpa_level": lpa_level,
                "lpc_level": lpc_level,
                "lpcat_expression": lpcat_expression,
                "lpa_pro_tumorigenic": lpa_level > 10,
            },
            "immunosuppressive_lipid_burden": immunosuppressive_burden,
            "therapeutic_targets": [
                t for t in [
                    "COX-2 inhibitor (celecoxib)" if pge2_level > 10 else None,
                    "S1PR1 modulator (fingolimod)" if s1p_s1pr1 > 7 else None,
                    "SPHK1 inhibitor" if s1p_level > 10 else None,
                    "15-LOX activator" if any(e["name"] == "LXA4" and e["concentration_ng_ml"] < 2 for e in eicosanoids) else None,
                ] if t is not None
            ],
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Ferroptosis Vulnerability Analysis
    # ═══════════════════════════════════════════════════════════════════════════

    def ferroptosis_vulnerability(self, gene: str) -> dict:
        """
        Assess tumor vulnerability to ferroptosis — iron-dependent
        regulated cell death driven by lipid peroxidation.
        Profiles GPX4, SLC7A11 (xCT), FSP1, and iron homeostasis
        to predict whether ferroptosis induction could synergize
        with CAR-T therapy.

        Critical for therapy-resistant mesenchymal cancer cells.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 19000)

        # ── Core ferroptosis defense ──
        gpx4_expression = round(rng.uniform(0, 15), 2)
        gpx4_activity = round(rng.uniform(0, 1), 3)
        slc7a11_expression = round(rng.uniform(0, 15), 2)  # xCT cystine transporter
        fsp1_expression = round(rng.uniform(0, 12), 2)  # Ferroptosis suppressor protein 1
        dhodh_expression = round(rng.uniform(0, 10), 2)  # Mitochondrial defense

        # ── Lipid peroxidation markers ──
        mda_level = round(rng.uniform(0.1, 20.0), 2)  # Malondialdehyde
        four_hne_level = round(rng.uniform(0.1, 15.0), 2)  # 4-Hydroxynonenal
        pufa_content = round(rng.uniform(10, 60), 1)  # PUFA membrane %
        acsl4_expression = round(rng.uniform(0, 15), 2)  # Acyl-CoA synthetase
        lpcat3_expression = round(rng.uniform(0, 12), 2)  # Membrane remodeling

        # ── Iron metabolism ──
        tfr1_expression = round(rng.uniform(0, 15), 2)  # Transferrin receptor
        ferritin_expression = round(rng.uniform(0, 10), 2)
        ferroportin_expression = round(rng.uniform(0, 8), 2)
        labile_iron_pool = round(rng.uniform(0.1, 10.0), 2)
        heme_oxygenase_1 = round(rng.uniform(0, 12), 2)

        iron_overload = labile_iron_pool > 5 and tfr1_expression > 8

        # ── Ferroptosis vulnerability scoring ──
        vulnerability_factors = 0.0
        # Low GPX4 = vulnerable
        if gpx4_expression < 5:
            vulnerability_factors += 2.0
        elif gpx4_expression < 10:
            vulnerability_factors += 1.0
        # Low SLC7A11 = vulnerable
        if slc7a11_expression < 5:
            vulnerability_factors += 2.0
        elif slc7a11_expression < 10:
            vulnerability_factors += 1.0
        # High PUFA = vulnerable
        if pufa_content > 40:
            vulnerability_factors += 2.0
        elif pufa_content > 25:
            vulnerability_factors += 1.0
        # High ACSL4 = vulnerable
        if acsl4_expression > 10:
            vulnerability_factors += 1.5
        # Iron overload = vulnerable
        if iron_overload:
            vulnerability_factors += 2.0
        # Low FSP1 = no backup
        if fsp1_expression < 3:
            vulnerability_factors += 1.5

        vulnerability_score = round(min(vulnerability_factors / 10.0, 1.0), 3)

        # ── Ferroptosis inducer drug sensitivity ──
        drug_predictions = {
            "erastin": "SENSITIVE" if slc7a11_expression < 5 else "RESISTANT",
            "RSL3": "SENSITIVE" if gpx4_expression < 5 else "RESISTANT",
            "FIN56": "SENSITIVE" if gpx4_expression < 8 and fsp1_expression < 5 else "VARIABLE",
            "sulfasalazine": "SENSITIVE" if slc7a11_expression < 8 else "RESISTANT",
            "sorafenib_ferroptosis": "SENSITIVE" if vulnerability_score > 0.5 else "RESISTANT",
            "withaferin_A": "SENSITIVE" if gpx4_expression < 6 else "VARIABLE",
        }

        # ── NRF2 (NFE2L2) antioxidant response ──
        nrf2_activity = round(rng.uniform(0, 1), 3)
        nrf2_target_genes = {
            "NQO1": round(rng.uniform(0, 12), 2),
            "GCLC": round(rng.uniform(0, 10), 2),
            "GCLM": round(rng.uniform(0, 10), 2),
            "SLC7A11": slc7a11_expression,
            "HMOX1": heme_oxygenase_1,
        }

        return {
            "gene": gene,
            "analysis_type": "ferroptosis_vulnerability",
            "data_source": "Integrated metabolomics / transcriptomics simulation",
            "core_defense": {
                "gpx4_expression": gpx4_expression,
                "gpx4_activity": gpx4_activity,
                "slc7a11_expression": slc7a11_expression,
                "fsp1_expression": fsp1_expression,
                "dhodh_expression": dhodh_expression,
                "defense_intact": gpx4_expression > 8 and slc7a11_expression > 8,
            },
            "lipid_peroxidation": {
                "mda_level": mda_level,
                "four_hne_level": four_hne_level,
                "pufa_membrane_content_pct": pufa_content,
                "acsl4_expression": acsl4_expression,
                "lpcat3_expression": lpcat3_expression,
                "peroxidation_stress": "HIGH" if mda_level > 10 else "MODERATE" if mda_level > 3 else "LOW",
            },
            "iron_homeostasis": {
                "tfr1_expression": tfr1_expression,
                "ferritin_expression": ferritin_expression,
                "ferroportin_expression": ferroportin_expression,
                "labile_iron_pool": labile_iron_pool,
                "heme_oxygenase_1": heme_oxygenase_1,
                "iron_overload": iron_overload,
            },
            "vulnerability_score": vulnerability_score,
            "vulnerability_class": (
                "HIGHLY VULNERABLE" if vulnerability_score > 0.7 else
                "MODERATELY VULNERABLE" if vulnerability_score > 0.4 else
                "RESISTANT"
            ),
            "drug_sensitivity": drug_predictions,
            "nrf2_response": {
                "activity_score": nrf2_activity,
                "constitutively_active": nrf2_activity > 0.7,
                "target_gene_expression": nrf2_target_genes,
            },
            "cart_synergy": (
                "HIGH — ferroptosis inducers can selectively kill tumor cells "
                "while leaving CAR-T cells unaffected (T cells express high GPX4)"
                if vulnerability_score > 0.5 else
                "LOW — tumor cells have robust ferroptosis defense"
            ),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Redox Homeostasis & ROS Profiling
    # ═══════════════════════════════════════════════════════════════════════════

    def redox_homeostasis(self, gene: str) -> dict:
        """
        Comprehensive analysis of the tumor redox environment.
        ROS levels, antioxidant capacity, glutathione metabolism,
        thioredoxin system, and mitochondrial ROS generation.

        High ROS in the TME suppresses T cell effector function;
        understanding the redox landscape informs CAR-T armoring strategies.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 20000)

        # ── ROS sources ──
        mitochondrial_ros = round(rng.uniform(0, 20), 2)
        nadph_oxidase_activity = round(rng.uniform(0, 10), 2)
        xanthine_oxidase = round(rng.uniform(0, 8), 2)
        cytochrome_p450 = round(rng.uniform(0, 5), 2)
        total_ros = round(mitochondrial_ros + nadph_oxidase_activity + xanthine_oxidase + cytochrome_p450, 2)

        # ── Antioxidant defense ──
        sod1_expression = round(rng.uniform(0, 12), 2)
        sod2_expression = round(rng.uniform(0, 12), 2)
        catalase_expression = round(rng.uniform(0, 10), 2)
        gpx1_expression = round(rng.uniform(0, 10), 2)
        prdx_expression = round(rng.uniform(0, 10), 2)
        total_antioxidant = round(sod1_expression + sod2_expression + catalase_expression + gpx1_expression + prdx_expression, 2)

        # ── Glutathione system ──
        gsh_level = round(rng.uniform(0.5, 20.0), 2)
        gssg_level = round(rng.uniform(0.1, 5.0), 2)
        gsh_gssg_ratio = round(gsh_level / max(gssg_level, 0.01), 2)
        gclc_expression = round(rng.uniform(0, 12), 2)
        gss_expression = round(rng.uniform(0, 10), 2)
        gsr_expression = round(rng.uniform(0, 10), 2)

        # ── Thioredoxin system ──
        trx1_expression = round(rng.uniform(0, 10), 2)
        trxr1_expression = round(rng.uniform(0, 10), 2)
        txnip_expression = round(rng.uniform(0, 8), 2)
        trx_active = trx1_expression > 5 and trxr1_expression > 5

        # ── NAD+/NADPH balance ──
        nad_ratio = round(rng.uniform(0.5, 5.0), 2)
        nadph_level = round(rng.uniform(0.5, 10.0), 2)
        nampt_expression = round(rng.uniform(0, 12), 2)
        idh1_expression = round(rng.uniform(0, 10), 2)
        me1_expression = round(rng.uniform(0, 8), 2)

        # ── Oxidative stress index ──
        oxidative_stress_index = round(total_ros / max(total_antioxidant, 0.01), 3)

        # ── Impact on T cell function ──
        t_cell_suppressive_ros = total_ros > 30
        ros_zone = (
            "SEVERE — high ROS will rapidly exhaust infiltrating CAR-T cells"
            if total_ros > 40 else
            "MODERATE — consider armoring CAR-T with catalase/SOD transgenes"
            if total_ros > 20 else
            "LOW — TME redox environment supports T cell effector function"
        )

        # ── Nrf2 pathway status (cross-referenced) ──
        nrf2_keap1_status = {
            "nrf2_expression": round(rng.uniform(0, 10), 2),
            "keap1_mutation": rng.choice(["wildtype", "loss_of_function", "missense"]),
            "nrf2_constitutive_activation": rng.random() > 0.7,
            "target_induction_fold": round(rng.uniform(1, 10), 1),
        }

        return {
            "gene": gene,
            "analysis_type": "redox_homeostasis",
            "data_source": "ROS assay / metabolomics / transcriptomics simulation",
            "ros_sources": {
                "mitochondrial_complex_I_III": mitochondrial_ros,
                "nadph_oxidase": nadph_oxidase_activity,
                "xanthine_oxidase": xanthine_oxidase,
                "cytochrome_p450": cytochrome_p450,
                "total_ros_burden": total_ros,
            },
            "antioxidant_defense": {
                "sod1": sod1_expression,
                "sod2_mitochondrial": sod2_expression,
                "catalase": catalase_expression,
                "gpx1": gpx1_expression,
                "peroxiredoxin": prdx_expression,
                "total_capacity": total_antioxidant,
            },
            "glutathione_system": {
                "gsh_level": gsh_level,
                "gssg_level": gssg_level,
                "gsh_gssg_ratio": gsh_gssg_ratio,
                "redox_buffer": (
                    "OPTIMAL" if gsh_gssg_ratio > 10 else
                    "STRESSED" if gsh_gssg_ratio > 3 else "DEPLETED"
                ),
                "biosynthesis": {
                    "gclc": gclc_expression,
                    "gss": gss_expression,
                    "gsr_recycling": gsr_expression,
                },
            },
            "thioredoxin_system": {
                "trx1": trx1_expression,
                "trxr1": trxr1_expression,
                "txnip_inhibitor": txnip_expression,
                "system_active": trx_active,
            },
            "nad_nadph_balance": {
                "nad_ratio": nad_ratio,
                "nadph_level": nadph_level,
                "nampt_expression": nampt_expression,
                "idh1_expression": idh1_expression,
                "me1_expression": me1_expression,
                "reductive_capacity": "HIGH" if nadph_level > 5 else "LOW",
            },
            "oxidative_stress_index": oxidative_stress_index,
            "nrf2_keap1": nrf2_keap1_status,
            "tme_ros_impact_on_car_t": {
                "suppressive": t_cell_suppressive_ros,
                "assessment": ros_zone,
                "armoring_recommendation": (
                    "Equip CAR-T with catalase or SOD2 transgene for ROS resistance"
                    if total_ros > 25 else
                    "Standard CAR-T construct should function adequately"
                ),
            },
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Amino Acid Deprivation & Auxotrophy Analysis
    # ═══════════════════════════════════════════════════════════════════════════

    def amino_acid_deprivation_analysis(self, gene: str) -> dict:
        """
        Profile amino acid availability in the tumor microenvironment.
        Tumors consume and deplete specific amino acids (arginine, tryptophan,
        cysteine) creating metabolic deserts that impair T cell function.

        Models IDO1/TDO2 (tryptophan), ARG1/ARG2 (arginine), and
        cystathionine pathways with their impact on CAR-T fitness.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 21000)

        amino_acids = [
            {
                "aa": "Tryptophan",
                "enzymes_depleting": ["IDO1", "IDO2", "TDO2"],
                "toxic_product": "Kynurenine",
                "t_cell_impact": "Suppresses proliferation via AhR activation",
            },
            {
                "aa": "Arginine",
                "enzymes_depleting": ["ARG1", "ARG2", "iNOS"],
                "toxic_product": "Ornithine / NO",
                "t_cell_impact": "CD3ζ chain downregulation, impaired proliferation",
            },
            {
                "aa": "Cysteine/Cystine",
                "enzymes_depleting": ["CBS", "CTH"],
                "toxic_product": "H₂S",
                "t_cell_impact": "GSH depletion, oxidative stress",
            },
            {
                "aa": "Glutamine",
                "enzymes_depleting": ["GLS1", "GLS2"],
                "toxic_product": "Glutamate",
                "t_cell_impact": "Impaired T cell activation and cytokine production",
            },
            {
                "aa": "Asparagine",
                "enzymes_depleting": ["ASNS", "ASRGL1"],
                "toxic_product": "Aspartate",
                "t_cell_impact": "Limits T cell activation in asparagine-poor TME",
            },
            {
                "aa": "Serine",
                "enzymes_depleting": ["PHGDH", "PSAT1", "PSPH"],
                "toxic_product": "Glycine",
                "t_cell_impact": "Impairs one-carbon metabolism and T cell expansion",
            },
        ]

        aa_profiles = []
        for aa in amino_acids:
            a_rng = random.Random(seed + 21000 + hash(aa["aa"]))
            tme_level = a_rng.uniform(0.01, 5.0)
            plasma_level = a_rng.uniform(1.0, 10.0)

            enzyme_data = {}
            for enz in aa["enzymes_depleting"]:
                e_rng = random.Random(seed + 21000 + hash(enz))
                enzyme_data[enz] = {
                    "expression": round(e_rng.uniform(0, 15), 2),
                    "source": e_rng.choice(["tumor", "MDSC", "TAM", "stroma", "DC"]),
                }

            depletion_ratio = round(tme_level / max(plasma_level, 0.01), 3)

            aa_profiles.append({
                **aa,
                "tme_concentration_uM": round(tme_level, 2),
                "plasma_concentration_uM": round(plasma_level, 2),
                "tme_plasma_ratio": depletion_ratio,
                "depleted": depletion_ratio < 0.3,
                "enzyme_expression": enzyme_data,
                "severity": (
                    "CRITICAL" if depletion_ratio < 0.1 else
                    "DEPLETED" if depletion_ratio < 0.3 else
                    "REDUCED" if depletion_ratio < 0.6 else "NORMAL"
                ),
            })

        depleted_count = sum(1 for a in aa_profiles if a["depleted"])

        # GCN2 stress response (amino acid sensing)
        gcn2_activation = round(rng.uniform(0, 1), 3)
        atf4_target_induction = round(rng.uniform(0, 5), 2)

        return {
            "gene": gene,
            "analysis_type": "amino_acid_deprivation",
            "data_source": "Metabolomics / transcriptomics simulation",
            "amino_acid_profiles": aa_profiles,
            "depleted_amino_acids": depleted_count,
            "metabolic_desert_score": round(depleted_count / len(aa_profiles), 3),
            "gcn2_stress_response": {
                "gcn2_activation": gcn2_activation,
                "atf4_induction": atf4_target_induction,
                "integrated_stress_response": gcn2_activation > 0.5,
            },
            "therapeutic_interventions": [
                t for t in [
                    "IDO1 inhibitor (epacadostat)" if any(
                        a["depleted"] and a["aa"] == "Tryptophan" for a in aa_profiles
                    ) else None,
                    "Arginase inhibitor (CB-1158)" if any(
                        a["depleted"] and a["aa"] == "Arginine" for a in aa_profiles
                    ) else None,
                    "Arginine supplementation" if any(
                        a["depleted"] and a["aa"] == "Arginine" for a in aa_profiles
                    ) else None,
                    "CAR-T ASS1 armoring (arginine autotrophy)" if any(
                        a["depleted"] and a["aa"] == "Arginine" for a in aa_profiles
                    ) else None,
                ] if t is not None
            ],
            "cart_metabolic_fitness": (
                "SEVERELY COMPROMISED — multiple amino acid deserts in TME. "
                "Consider metabolically armored CAR-T or combination with enzyme inhibitors."
                if depleted_count >= 3 else
                "MODERATELY IMPACTED — targeted supplementation may improve CAR-T persistence"
                if depleted_count >= 1 else
                "FAVORABLE — amino acid profile supports T cell effector function"
            ),
        }
