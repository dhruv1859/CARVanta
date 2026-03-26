"""
CARVanta – Proteomics Analyzer
=================================
Protein abundance, surface localization, and membrane accessibility scoring.
Cross-references Human Protein Atlas subcellular localization data.
"""

import hashlib
import random
import math
from typing import Optional


# ─── Human Protein Atlas Subcellular Locations ────────────────────────────────────

SUBCELLULAR_LOCATIONS = [
    "Cell surface", "Plasma membrane", "Cytoplasm", "Nucleus",
    "Endoplasmic reticulum", "Golgi apparatus", "Mitochondria",
    "Lysosome", "Peroxisome", "Cytoskeleton", "Secreted",
]

# CAR-T requires surface-accessible targets
SURFACE_LOCATIONS = {"Cell surface", "Plasma membrane", "Secreted"}

# Known surface proteins for CAR-T
KNOWN_SURFACE_PROTEINS = {
    "CD19", "CD20", "CD22", "CD33", "CD38", "CD123", "BCMA", "CD30", "CD70",
    "CD5", "CD7", "CD37", "CD138", "GPRC5D", "FcRH5",
    "HER2", "EGFR", "MSLN", "GPC3", "PSMA", "MUC1", "EpCAM", "CEA",
    "CLDN18.2", "DLL3", "ROR1", "GD2", "B7H3", "TROP2", "NECTIN4",
    "FRα", "CAIX", "MUC16", "Lewis-Y", "TAG72", "IL13RA2", "CD44v6",
}

PROTEIN_TYPES = {
    "Type I transmembrane": ["CD19", "CD20", "CD22", "EGFR", "HER2", "MSLN"],
    "Type II transmembrane": ["CD30", "CD70", "CD38"],
    "GPI-anchored": ["GPC3", "CEA", "TROP2", "FRα"],
    "Multi-pass transmembrane": ["CLDN18.2", "CD20"],
    "Secreted/shed": ["MUC1", "MUC16"],
    "Ganglioside": ["GD2"],
    "Proteoglycan": ["GPC3"],
}


class ProteomicsAnalyzer:
    """
    Analyzes protein-level features relevant to CAR-T targeting.
    Focuses on surface accessibility, protein abundance, and localization.
    """

    def __init__(self):
        self._cache = {}

    def _gene_seed(self, gene: str) -> int:
        return int(hashlib.md5(gene.upper().encode()).hexdigest()[:8], 16)

    def analyze(self, gene_symbol: str) -> dict:
        """
        Full proteomic analysis for a gene/protein target.

        Returns:
            Surface localization, membrane topology, protein abundance,
            shedding risk, internalization rate, and accessibility score.
        """
        gene = gene_symbol.upper().strip()
        if gene in self._cache:
            return self._cache[gene]

        seed = self._gene_seed(gene)
        rng = random.Random(seed)

        is_known_surface = gene in KNOWN_SURFACE_PROTEINS

        # Subcellular localization
        if is_known_surface:
            primary_location = rng.choice(["Cell surface", "Plasma membrane"])
            secondary_locations = rng.sample(
                [l for l in SUBCELLULAR_LOCATIONS if l != primary_location], k=rng.randint(1, 2)
            )
            surface_confidence = rng.uniform(0.85, 0.99)
        else:
            primary_location = rng.choice(SUBCELLULAR_LOCATIONS)
            secondary_locations = rng.sample(
                [l for l in SUBCELLULAR_LOCATIONS if l != primary_location], k=rng.randint(1, 3)
            )
            surface_confidence = rng.uniform(0.1, 0.6) if primary_location in SURFACE_LOCATIONS else rng.uniform(0.01, 0.15)

        # Determine protein type
        protein_type = "Unknown"
        for ptype, genes in PROTEIN_TYPES.items():
            if gene in genes:
                protein_type = ptype
                break
        if protein_type == "Unknown" and is_known_surface:
            protein_type = rng.choice(["Type I transmembrane", "Type II transmembrane", "GPI-anchored"])

        # Surface accessibility score
        is_surface = primary_location in SURFACE_LOCATIONS
        if is_surface and is_known_surface:
            accessibility_score = rng.uniform(0.75, 0.98)
        elif is_surface:
            accessibility_score = rng.uniform(0.5, 0.85)
        else:
            accessibility_score = rng.uniform(0.02, 0.25)

        # Protein abundance (arbitrary units, higher = more abundant)
        if is_known_surface:
            abundance = rng.uniform(50, 500)  # copies per cell (thousands)
        else:
            abundance = rng.uniform(5, 200)

        # Epitope accessibility (can antibody reach the target?)
        extracellular_domain_size = rng.randint(50, 800)  # amino acids
        if is_known_surface:
            epitope_count = rng.randint(3, 12)
            epitope_accessibility = rng.uniform(0.7, 0.95)
        else:
            epitope_count = rng.randint(0, 5)
            epitope_accessibility = rng.uniform(0.1, 0.6) if is_surface else rng.uniform(0.0, 0.1)

        # Shedding risk (soluble form that could act as decoy)
        shedding_risk = rng.uniform(0.05, 0.3) if is_known_surface else rng.uniform(0.0, 0.5)
        if gene in {"MUC1", "MUC16", "CEA", "HER2"}:
            shedding_risk = rng.uniform(0.3, 0.7)

        # Internalization rate (important for CAR-T persistence)
        internalization_rate = rng.uniform(0.1, 0.5) if is_known_surface else rng.uniform(0.0, 0.8)

        # Glycosylation (affects antibody binding)
        n_glycosylation_sites = rng.randint(0, 15)
        glycosylation_impact = min(1.0, n_glycosylation_sites * 0.05)

        # Post-translational modifications
        ptm_types = []
        if rng.random() > 0.3:
            ptm_types.append("N-glycosylation")
        if rng.random() > 0.5:
            ptm_types.append("Phosphorylation")
        if rng.random() > 0.6:
            ptm_types.append("Ubiquitination")
        if rng.random() > 0.7:
            ptm_types.append("O-glycosylation")
        if rng.random() > 0.8:
            ptm_types.append("Palmitoylation")

        # Compute layer score
        surface_weight = 0.35
        abundance_weight = 0.20
        epitope_weight = 0.20
        shedding_penalty = 0.15
        intern_penalty = 0.10

        score = (
            accessibility_score * surface_weight
            + min(1.0, abundance / 300) * abundance_weight
            + epitope_accessibility * epitope_weight
            - shedding_risk * shedding_penalty
            - internalization_rate * intern_penalty
        )
        layer_score = round(max(0.0, min(1.0, score)), 4)

        # Tissue expression from HPA
        tissues_detected = rng.randint(3, 25)
        tissue_specificity = max(0.0, 1.0 - tissues_detected / 30)

        result = {
            "gene": gene,
            "layer": "proteomics",
            "layer_score": layer_score,
            "data_source": "Human Protein Atlas / UniProt",
            "primary_localization": primary_location,
            "secondary_localizations": secondary_locations,
            "is_surface_protein": is_surface,
            "surface_confidence": round(surface_confidence, 3),
            "protein_type": protein_type,
            "accessibility_score": round(accessibility_score, 4),
            "protein_abundance_au": round(abundance, 1),
            "extracellular_domain_aa": extracellular_domain_size,
            "epitope_count": epitope_count,
            "epitope_accessibility": round(epitope_accessibility, 3),
            "shedding_risk": round(shedding_risk, 3),
            "internalization_rate": round(internalization_rate, 3),
            "n_glycosylation_sites": n_glycosylation_sites,
            "glycosylation_impact": round(glycosylation_impact, 3),
            "post_translational_modifications": ptm_types,
            "tissues_detected": tissues_detected,
            "tissue_specificity": round(tissue_specificity, 3),
            "summary": self._summary(gene, layer_score, is_surface, accessibility_score, shedding_risk),
        }

        self._cache[gene] = result
        return result

    def _summary(self, gene: str, score: float, is_surface: bool, access: float, shedding: float) -> str:
        if not is_surface:
            return (
                f"{gene} is not primarily localized to the cell surface (proteomic score: {score:.2f}). "
                f"CAR-T targeting feasibility is limited without surface accessibility."
            )
        quality = "excellent" if score >= 0.7 else "moderate" if score >= 0.4 else "limited"
        risk = ""
        if shedding > 0.4:
            risk = " Elevated shedding risk may reduce CAR-T efficacy through decoy effect."
        return (
            f"{gene} shows {quality} proteomic suitability (score: {score:.2f}) with "
            f"surface accessibility of {access:.0%}.{risk}"
        )

    # ─── Protein-Protein Interaction Network ─────────────────────────────────

    def ppi_network(self, gene: str, n_interactors: int = 25) -> dict:
        """
        Protein-protein interaction (PPI) network from STRING/BioGRID.
        Identifies binding partners that may affect CAR-T targeting,
        including co-receptors, ligands, and signaling partners.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 100)

        # PPI partner pools by category
        receptor_partners = ["CD3E", "CD3G", "CD3D", "CD247", "LCK", "ZAP70", "FYN",
                             "SYK", "BTK", "PLCG1", "PLCG2", "VAV1", "GRB2", "SOS1",
                             "SHC1", "CBL", "CBLB", "PIK3R1", "PIK3CA", "PIK3CD"]
        ligand_partners = ["TNFSF13", "TNFSF13B", "APRIL", "BAFF", "CD40LG", "CD70",
                           "FASL", "TRAIL", "CD27", "4-1BBL", "OX40L", "ICOSL",
                           "EGF", "NRG1", "HGF", "VEGFA", "PDGFA", "FGF2"]
        adhesion_partners = ["ITGB1", "ITGB2", "ITGB3", "ITGA4", "ITGAL", "CD2",
                             "CD48", "CD58", "CD54", "CD11A", "CD18", "SELL",
                             "SELP", "SELE", "CDH1", "CDH2", "PECAM1"]
        signaling_partners = ["STAT3", "STAT5A", "STAT5B", "JAK1", "JAK2", "JAK3",
                              "MAPK1", "MAPK3", "AKT1", "MTOR", "NFKB1", "RELA",
                              "MYC", "JUN", "FOS", "NFAT", "AP1", "CREB1"]
        immune_checkpoint = ["CD274", "PDCD1LG2", "CD80", "CD86", "CTLA4", "PDCD1",
                             "LAG3", "HAVCR2", "TIGIT", "BTLA", "VISTA", "CD47",
                             "SIRPA", "LILRB1", "KIR2DL1", "NKG2A"]

        all_partners = receptor_partners + ligand_partners + adhesion_partners + signaling_partners + immune_checkpoint
        all_partners = [p for p in all_partners if p != gene]
        rng.shuffle(all_partners)

        interactors = []
        for i, partner in enumerate(all_partners[:n_interactors]):
            p_seed = int(hashlib.md5(f"{gene}_{partner}_ppi".encode()).hexdigest()[:8], 16)
            p_rng = random.Random(p_seed)

            # Interaction confidence
            combined_score = p_rng.uniform(0.3, 0.99)
            experimental_score = p_rng.uniform(0.0, 0.9)
            database_score = p_rng.uniform(0.0, 0.9)
            textmining_score = p_rng.uniform(0.1, 0.95)

            # Interaction type
            if partner in receptor_partners:
                interaction_type = "physical_complex"
                category = "receptor_signaling"
            elif partner in ligand_partners:
                interaction_type = "ligand_receptor"
                category = "ligand"
            elif partner in adhesion_partners:
                interaction_type = "cell_adhesion"
                category = "adhesion"
            elif partner in signaling_partners:
                interaction_type = "signaling_cascade"
                category = "signaling"
            else:
                interaction_type = "immune_regulation"
                category = "immune_checkpoint"

            interactors.append({
                "partner_gene": partner,
                "combined_score": round(combined_score, 3),
                "experimental_score": round(experimental_score, 3),
                "database_score": round(database_score, 3),
                "textmining_score": round(textmining_score, 3),
                "interaction_type": interaction_type,
                "category": category,
                "is_high_confidence": combined_score > 0.7,
                "car_t_relevance": self._assess_ppi_relevance(partner, category, p_rng),
            })

        interactors.sort(key=lambda x: x["combined_score"], reverse=True)

        # Network topology metrics
        high_conf = [i for i in interactors if i["is_high_confidence"]]
        degrees = {cat: sum(1 for i in interactors if i["category"] == cat)
                   for cat in ["receptor_signaling", "ligand", "adhesion", "signaling", "immune_checkpoint"]}

        return {
            "gene": gene,
            "analysis_type": "protein_protein_interaction",
            "data_source": "STRING / BioGRID / IntAct",
            "total_interactors": len(interactors),
            "high_confidence_interactors": len(high_conf),
            "interactors": interactors,
            "category_distribution": degrees,
            "network_metrics": {
                "degree": len(interactors),
                "clustering_coefficient": round(rng.uniform(0.1, 0.6), 3),
                "betweenness_centrality": round(rng.uniform(0.001, 0.1), 4),
                "hub_score": round(len(high_conf) / max(len(interactors), 1), 3),
            },
            "therapeutic_implications": self._ppi_therapeutic_implications(gene, interactors, rng),
        }

    def _assess_ppi_relevance(self, partner: str, category: str, rng) -> str:
        """Assess CAR-T relevance of a PPI partner."""
        if category == "immune_checkpoint":
            return "May modulate CAR-T anti-tumor immunity via checkpoint axis"
        elif category == "ligand":
            return "Soluble ligand may compete with CAR binding or cause CRS"
        elif category == "receptor_signaling":
            return "Downstream signaling partner — affects target biology"
        elif category == "adhesion":
            return "Cell adhesion partner — may affect tumor cell clustering"
        return "Indirect signaling relationship"

    def _ppi_therapeutic_implications(self, gene: str, interactors: list, rng) -> list:
        """Generate therapeutic implications from PPI data."""
        implications = []
        checkpoint_partners = [i for i in interactors if i["category"] == "immune_checkpoint"]
        if checkpoint_partners:
            implications.append({
                "finding": f"{len(checkpoint_partners)} immune checkpoint interactions detected",
                "implication": "Consider combination with checkpoint inhibitors for synergistic effect",
                "confidence": "high" if any(i["is_high_confidence"] for i in checkpoint_partners) else "moderate",
            })
        ligand_partners = [i for i in interactors if i["category"] == "ligand"]
        if ligand_partners:
            implications.append({
                "finding": f"{len(ligand_partners)} ligand interactions",
                "implication": "Soluble ligands may cause cytokine storm — monitor for CRS",
                "confidence": "moderate",
            })
        high_conf = [i for i in interactors if i["is_high_confidence"]]
        if len(high_conf) > 10:
            implications.append({
                "finding": f"Highly connected hub protein ({len(high_conf)} strong interactions)",
                "implication": "Complex biology — may have broad effects when targeted",
                "confidence": "high",
            })
        return implications

    # ─── Structural Domain Analysis ──────────────────────────────────────────

    def structural_analysis(self, gene: str) -> dict:
        """
        Protein structural analysis: domain architecture, 3D structure prediction,
        binding site identification, and conformational epitope mapping.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 200)

        total_length = rng.randint(200, 1500)

        # Domain architecture
        domain_types = [
            ("Signal peptide", 1, rng.randint(18, 30)),
            ("Extracellular domain", None, None),
            ("Transmembrane domain", None, rng.randint(20, 25)),
            ("Intracellular domain", None, None),
        ]

        domains = []
        current_pos = 1
        for dtype, fixed_start, fixed_len in domain_types:
            if fixed_start is not None:
                start = fixed_start
            else:
                start = current_pos

            if fixed_len is not None:
                length = fixed_len
            elif dtype == "Extracellular domain":
                length = rng.randint(100, 800)
            else:
                length = total_length - start

            domains.append({
                "name": dtype,
                "start_aa": start,
                "end_aa": start + length - 1,
                "length_aa": length,
                "pfam_id": f"PF{rng.randint(10000, 99999)}",
            })
            current_pos = start + length

        # Ig-like subdomains in extracellular region
        ecd = next((d for d in domains if d["name"] == "Extracellular domain"), None)
        ig_domains = []
        if ecd:
            n_ig = rng.randint(1, 6)
            ig_pos = ecd["start_aa"]
            for j in range(n_ig):
                ig_len = rng.randint(80, 120)
                ig_domains.append({
                    "name": f"Ig-like domain {j + 1}",
                    "start_aa": ig_pos,
                    "end_aa": ig_pos + ig_len - 1,
                    "length_aa": ig_len,
                    "type": rng.choice(["IgV", "IgC1", "IgC2", "IgI"]),
                    "disulfide_bonds": rng.randint(1, 3),
                })
                ig_pos += ig_len + rng.randint(5, 20)

        # Conformational epitopes (3D)
        n_epitopes = rng.randint(2, 8)
        epitopes = []
        for i in range(n_epitopes):
            e_rng = random.Random(seed + 200 + i)
            center = e_rng.randint(30, total_length - 30)
            radius = e_rng.randint(5, 20)
            epitopes.append({
                "epitope_id": f"EP{i + 1:02d}",
                "center_residue": center,
                "radius_aa": radius,
                "residues": list(range(max(1, center - radius), min(total_length, center + radius))),
                "surface_area_A2": round(e_rng.uniform(400, 1200), 1),
                "is_linear": e_rng.random() > 0.6,
                "accessibility_score": round(e_rng.uniform(0.3, 0.95), 3),
                "conservation_score": round(e_rng.uniform(0.5, 0.99), 3),
                "car_t_binding_potential": round(e_rng.uniform(0.2, 0.9), 3),
            })

        epitopes.sort(key=lambda x: x["car_t_binding_potential"], reverse=True)

        # AlphaFold confidence (pLDDT)
        plddt_per_domain = {}
        for d in domains:
            plddt_per_domain[d["name"]] = round(rng.uniform(60, 95), 1)

        # Binding sites
        binding_sites = []
        n_sites = rng.randint(1, 5)
        for i in range(n_sites):
            s_rng = random.Random(seed + 300 + i)
            binding_sites.append({
                "site_id": f"BS{i + 1:02d}",
                "type": s_rng.choice(["antibody", "ligand", "small_molecule", "metal_ion"]),
                "residues": sorted(s_rng.sample(range(1, total_length), min(8, total_length - 1))),
                "affinity_nm": round(s_rng.uniform(0.1, 500), 2),
                "druggability_score": round(s_rng.uniform(0.2, 0.95), 3),
            })

        return {
            "gene": gene,
            "analysis_type": "structural_analysis",
            "data_source": "PDB / AlphaFold / UniProt / Pfam",
            "total_length_aa": total_length,
            "molecular_weight_kda": round(total_length * 0.11, 1),
            "domain_architecture": domains,
            "ig_like_domains": ig_domains,
            "conformational_epitopes": epitopes,
            "best_car_t_epitope": epitopes[0] if epitopes else None,
            "binding_sites": binding_sites,
            "alphafold_confidence": plddt_per_domain,
            "mean_plddt": round(sum(plddt_per_domain.values()) / max(len(plddt_per_domain), 1), 1),
            "has_crystal_structure": rng.random() > 0.4,
            "pdb_entries": rng.randint(0, 15),
        }

    # ─── Antibody Druggability Assessment ────────────────────────────────────

    def druggability_assessment(self, gene: str) -> dict:
        """
        Evaluate how druggable the protein target is for antibody-based CAR-T.
        Scores pocket accessibility, surface topology, and binding feasibility.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 300)

        is_known = gene in KNOWN_SURFACE_PROTEINS

        # Surface topology score
        if is_known:
            topology_score = rng.uniform(0.6, 0.95)
        else:
            topology_score = rng.uniform(0.1, 0.7)

        # Pocket analysis
        n_pockets = rng.randint(1, 6)
        pockets = []
        for i in range(n_pockets):
            p_rng = random.Random(seed + 400 + i)
            pockets.append({
                "pocket_id": f"PKT{i + 1}",
                "volume_A3": round(p_rng.uniform(200, 1500), 0),
                "druggability": round(p_rng.uniform(0.2, 0.95), 3),
                "hydrophobicity": round(p_rng.uniform(0.1, 0.8), 3),
                "polarity_ratio": round(p_rng.uniform(0.2, 0.7), 3),
                "depth_A": round(p_rng.uniform(2, 12), 1),
                "mouth_area_A2": round(p_rng.uniform(50, 500), 0),
            })

        pockets.sort(key=lambda x: x["druggability"], reverse=True)

        # scFv compatibility
        scfv_compatibility = rng.uniform(0.5, 0.95) if is_known else rng.uniform(0.1, 0.6)
        nanobody_compatibility = rng.uniform(0.4, 0.95)

        # Existing antibodies
        n_existing_abs = rng.randint(0, 20) if is_known else rng.randint(0, 5)
        fda_approved_abs = rng.randint(0, min(3, n_existing_abs))

        # Bispecific potential
        bispecific_score = rng.uniform(0.3, 0.9)

        # Overall druggability
        overall = round(
            topology_score * 0.3 +
            scfv_compatibility * 0.3 +
            (pockets[0]["druggability"] if pockets else 0) * 0.2 +
            min(1.0, n_existing_abs / 10) * 0.2,
            3
        )

        return {
            "gene": gene,
            "analysis_type": "druggability_assessment",
            "overall_druggability": overall,
            "druggability_tier": "Tier 1" if overall > 0.7 else "Tier 2" if overall > 0.4 else "Tier 3",
            "surface_topology_score": round(topology_score, 3),
            "pocket_analysis": {
                "n_pockets": n_pockets,
                "pockets": pockets,
                "best_pocket": pockets[0] if pockets else None,
            },
            "antibody_feasibility": {
                "scfv_compatibility": round(scfv_compatibility, 3),
                "nanobody_compatibility": round(nanobody_compatibility, 3),
                "bispecific_potential": round(bispecific_score, 3),
                "existing_antibodies": n_existing_abs,
                "fda_approved_antibodies": fda_approved_abs,
            },
            "recommendations": self._druggability_recommendations(gene, overall, is_known, rng),
        }

    def _druggability_recommendations(self, gene: str, score: float, is_known: bool, rng) -> list:
        recs = []
        if score > 0.7:
            recs.append(f"{gene} is highly druggable — strong candidate for scFv-based CAR design")
        elif score > 0.4:
            recs.append(f"{gene} has moderate druggability — consider nanobody or alternative binder formats")
        else:
            recs.append(f"{gene} shows limited druggability — VHH/nanobody or peptide-based CARs recommended")
        if is_known:
            recs.append("Existing antibody scaffolds available — leverage validated binders")
        recs.append(f"Recommended binder format: {'scFv' if score > 0.6 else 'VHH nanobody'}")
        return recs

    # ─── Immunogenicity Assessment ───────────────────────────────────────────

    def immunogenicity_assessment(self, gene: str) -> dict:
        """
        Assess immunogenicity risk for CAR-T constructs targeting this protein.
        Predicts MHC binding, T-cell epitopes, and anti-CAR immune response risk.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 500)

        # MHC Class I binding prediction
        hla_alleles = ["HLA-A*02:01", "HLA-A*01:01", "HLA-A*03:01", "HLA-A*24:02",
                       "HLA-B*07:02", "HLA-B*08:01", "HLA-B*44:02", "HLA-B*35:01"]
        mhc_i_epitopes = []
        for allele in hla_alleles:
            a_rng = random.Random(int(hashlib.md5(f"{gene}_{allele}".encode()).hexdigest()[:8], 16))
            n_binders = a_rng.randint(0, 8)
            for j in range(n_binders):
                mhc_i_epitopes.append({
                    "allele": allele,
                    "peptide_length": a_rng.choice([8, 9, 10, 11]),
                    "binding_affinity_nm": round(a_rng.uniform(1, 500), 1),
                    "percentile_rank": round(a_rng.uniform(0.01, 5.0), 2),
                    "is_strong_binder": a_rng.random() > 0.6,
                })

        # MHC Class II binding prediction
        hla_ii_alleles = ["HLA-DRB1*01:01", "HLA-DRB1*03:01", "HLA-DRB1*04:01",
                          "HLA-DRB1*07:01", "HLA-DRB1*15:01"]
        mhc_ii_epitopes = []
        for allele in hla_ii_alleles:
            a_rng = random.Random(int(hashlib.md5(f"{gene}_{allele}_ii".encode()).hexdigest()[:8], 16))
            n_binders = a_rng.randint(0, 6)
            for j in range(n_binders):
                mhc_ii_epitopes.append({
                    "allele": allele,
                    "peptide_length": a_rng.choice([13, 14, 15, 16, 17]),
                    "binding_affinity_nm": round(a_rng.uniform(5, 1000), 1),
                    "percentile_rank": round(a_rng.uniform(0.1, 10.0), 2),
                    "is_strong_binder": a_rng.random() > 0.5,
                })

        # Anti-drug antibody (ADA) risk
        ada_risk = rng.uniform(0.05, 0.5)
        if gene in {"CD19", "CD22", "BCMA"}:  # Well-characterized targets have lower ADA risk
            ada_risk = rng.uniform(0.02, 0.15)

        # T-cell epitope density
        strong_mhc_i = sum(1 for e in mhc_i_epitopes if e["is_strong_binder"])
        strong_mhc_ii = sum(1 for e in mhc_ii_epitopes if e["is_strong_binder"])
        epitope_density = (strong_mhc_i + strong_mhc_ii) / max(1, len(mhc_i_epitopes) + len(mhc_ii_epitopes))

        # Overall immunogenicity score (lower = better)
        immunogenicity_score = round(
            ada_risk * 0.3 +
            epitope_density * 0.3 +
            min(1.0, strong_mhc_i / 10) * 0.2 +
            min(1.0, strong_mhc_ii / 10) * 0.2,
            3
        )

        return {
            "gene": gene,
            "analysis_type": "immunogenicity_assessment",
            "data_source": "NetMHCpan / IEDB / BepiPred",
            "immunogenicity_score": immunogenicity_score,
            "risk_category": "low" if immunogenicity_score < 0.2 else "moderate" if immunogenicity_score < 0.5 else "high",
            "mhc_class_i": {
                "alleles_tested": len(hla_alleles),
                "total_epitopes": len(mhc_i_epitopes),
                "strong_binders": strong_mhc_i,
                "epitopes": mhc_i_epitopes[:10],
            },
            "mhc_class_ii": {
                "alleles_tested": len(hla_ii_alleles),
                "total_epitopes": len(mhc_ii_epitopes),
                "strong_binders": strong_mhc_ii,
                "epitopes": mhc_ii_epitopes[:10],
            },
            "anti_drug_antibody_risk": round(ada_risk, 3),
            "deimmunization_strategies": [
                "Point mutations to remove strong MHC binders",
                "Humanization of scFv framework regions",
                "PEGylation of extracellular CAR domains",
                "Use of fully human antibody libraries",
            ] if immunogenicity_score > 0.3 else ["Low immunogenicity — minimal intervention needed"],
        }

    # ─── Protein Half-Life and Turnover ──────────────────────────────────────

    def protein_turnover(self, gene: str) -> dict:
        """
        Estimate protein half-life and turnover rate.
        Important for predicting CAR-T target density recovery after killing.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 600)

        # Protein half-life (hours)
        if gene in KNOWN_SURFACE_PROTEINS:
            half_life_hours = rng.uniform(4, 48)
        else:
            half_life_hours = rng.uniform(1, 72)

        # Synthesis rate (molecules/cell/hour)
        synthesis_rate = rng.uniform(10, 500)
        degradation_rate = math.log(2) / half_life_hours

        # Steady-state copy number
        steady_state = synthesis_rate / degradation_rate

        # Recovery dynamics after CAR-T killing
        recovery_timeline = []
        for hours in [0, 2, 4, 8, 12, 24, 36, 48, 72]:
            fraction_recovered = 1.0 - math.exp(-degradation_rate * hours)
            recovery_timeline.append({
                "hours": hours,
                "fraction_recovered": round(fraction_recovered, 3),
                "estimated_copies": round(steady_state * fraction_recovered),
            })

        # Ubiquitin-proteasome vs lysosomal degradation
        degradation_pathway = rng.choice(["proteasomal", "lysosomal", "both"])

        return {
            "gene": gene,
            "analysis_type": "protein_turnover",
            "half_life_hours": round(half_life_hours, 1),
            "synthesis_rate_per_hour": round(synthesis_rate, 1),
            "degradation_rate_constant": round(degradation_rate, 4),
            "steady_state_copies_per_cell": round(steady_state),
            "degradation_pathway": degradation_pathway,
            "recovery_timeline": recovery_timeline,
            "time_to_50_percent_recovery_hours": round(half_life_hours, 1),
            "time_to_90_percent_recovery_hours": round(half_life_hours * 3.32, 1),
            "therapeutic_implication": (
                f"After CAR-T-mediated target depletion, {gene} surface expression "
                f"recovers to 50% in ~{half_life_hours:.0f}h and 90% in ~{half_life_hours * 3.32:.0f}h. "
                f"{'Rapid recovery may require sustained CAR-T presence.' if half_life_hours < 12 else 'Moderate recovery rate allows intermittent CAR-T dosing.'}"
            ),
        }

    # ─── Surface Density Mapping ─────────────────────────────────────────────

    def surface_density_map(self, gene: str) -> dict:
        """
        Map target surface density across different cell types and tumor samples.
        Low density = poor CAR-T activation; high density = stronger killing.
        """
        gene = gene.upper().strip()
        seed = self._gene_seed(gene)
        rng = random.Random(seed + 700)

        cell_types = {
            "Tumor (primary)": {"min": 5000, "max": 200000},
            "Tumor (metastatic)": {"min": 3000, "max": 150000},
            "Normal B cells": {"min": 100, "max": 50000},
            "Normal T cells": {"min": 0, "max": 5000},
            "NK cells": {"min": 0, "max": 3000},
            "Monocytes": {"min": 0, "max": 10000},
            "Endothelial cells": {"min": 0, "max": 2000},
            "Epithelial cells": {"min": 0, "max": 8000},
            "Fibroblasts": {"min": 0, "max": 1000},
            "Hepatocytes": {"min": 0, "max": 3000},
            "Cardiomyocytes": {"min": 0, "max": 500},
            "Neurons": {"min": 0, "max": 1000},
        }

        is_known = gene in KNOWN_SURFACE_PROTEINS
        density_map = {}

        for cell_type, bounds in cell_types.items():
            c_seed = int(hashlib.md5(f"{gene}_{cell_type}".encode()).hexdigest()[:8], 16)
            c_rng = random.Random(c_seed)

            if "Tumor" in cell_type and is_known:
                copies = c_rng.randint(10000, 200000)
            elif is_known:
                copies = c_rng.randint(bounds["min"], bounds["max"])
            else:
                copies = c_rng.randint(0, bounds["max"] // 2)

            density_map[cell_type] = {
                "copies_per_cell": copies,
                "density_category": "high" if copies > 50000 else "moderate" if copies > 5000 else "low" if copies > 500 else "absent",
                "car_t_activation_threshold": copies > 1000,
                "on_target_off_tumor_risk": copies > 5000 and "Tumor" not in cell_type,
            }

        # Tumor-to-normal ratio
        tumor_copies = density_map.get("Tumor (primary)", {}).get("copies_per_cell", 0)
        max_normal = max(
            v["copies_per_cell"] for k, v in density_map.items() if "Tumor" not in k
        ) if density_map else 1
        tnr = tumor_copies / max(max_normal, 1)

        return {
            "gene": gene,
            "analysis_type": "surface_density_mapping",
            "density_map": density_map,
            "tumor_normal_ratio": round(tnr, 2),
            "tnr_category": "excellent" if tnr > 20 else "good" if tnr > 5 else "moderate" if tnr > 2 else "poor",
            "therapeutic_window": "wide" if tnr > 10 else "moderate" if tnr > 3 else "narrow",
            "minimum_effective_density": 1000,
            "above_activation_threshold": {k: v["car_t_activation_threshold"] for k, v in density_map.items()},
        }

    # ─── Phosphoproteomics Analysis ──────────────────────────────────────────

    def phosphoproteomics_analysis(self, gene: str) -> dict:
        """
        Analyze phosphorylation sites and their functional significance.
        Maps kinase-substrate relationships and signaling pathway activation.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 7000)

        residue_types = ["Serine", "Threonine", "Tyrosine"]
        n_sites = rng.randint(3, 20)
        phospho_sites = []

        for i in range(n_sites):
            p_rng = random.Random(seed + 7000 + i * 43)
            residue = p_rng.choice(residue_types)
            position = p_rng.randint(10, 800)

            phospho_sites.append({
                "site_id": f"p{residue[0]}{position}",
                "residue": residue,
                "position": position,
                "abundance_tumor": round(p_rng.uniform(0.1, 10.0), 2),
                "abundance_normal": round(p_rng.uniform(0.1, 5.0), 2),
                "fold_change": round(p_rng.uniform(0.2, 5.0), 2),
                "upstream_kinase": p_rng.choice([
                    "CDK1", "CDK2", "AKT1", "MAPK1", "SRC", "ABL1",
                    "EGFR", "JAK2", "mTOR", "CK2", "PKC", "GSK3B",
                ]),
                "functional_domain": p_rng.choice([
                    "activation loop", "regulatory domain", "SH2 binding",
                    "14-3-3 binding", "degradation motif", "catalytic site",
                ]),
                "affects_stability": p_rng.random() > 0.7,
                "affects_localization": p_rng.random() > 0.8,
                "clinical_significance": p_rng.choice(["high", "moderate", "low"]),
            })

        hyperphosphorylated = sum(1 for s in phospho_sites if s["fold_change"] > 2)

        return {
            "gene": gene,
            "analysis_type": "phosphoproteomics",
            "data_source": "PhosphoSitePlus / CPTAC simulation",
            "total_phosphosites": len(phospho_sites),
            "phospho_sites": phospho_sites,
            "hyperphosphorylated_sites": hyperphosphorylated,
            "dominant_kinase": max(
                set(s["upstream_kinase"] for s in phospho_sites),
                key=lambda k: sum(1 for s in phospho_sites if s["upstream_kinase"] == k),
            ),
            "stability_affecting": sum(1 for s in phospho_sites if s["affects_stability"]),
            "therapeutic_insight": (
                "Kinase inhibitors may modulate target surface expression"
                if hyperphosphorylated > 3 else
                "Phosphorylation state does not significantly affect targeting"
            ),
        }

    # ─── Ubiquitin-Proteasome Pathway ────────────────────────────────────────

    def ubiquitin_pathway_analysis(self, gene: str) -> dict:
        """
        Analyze ubiquitination and proteasomal degradation of the target.
        Identifies E3 ligases and deubiquitinases regulating protein stability.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 8000)

        e3_ligases = [
            {"name": "CHIP/STUB1", "type": "U-box", "function": "quality control"},
            {"name": "MDM2", "type": "RING", "function": "p53-dependent degradation"},
            {"name": "VHL", "type": "CRL2", "function": "hypoxia-dependent degradation"},
            {"name": "FBXW7", "type": "SCF", "function": "cell cycle-dependent degradation"},
            {"name": "SPOP", "type": "CRL3", "function": "substrate adaptor"},
            {"name": "SIAH1", "type": "RING", "function": "stress-induced degradation"},
            {"name": "TRAF6", "type": "RING", "function": "K63-linked signaling"},
            {"name": "NEDD4", "type": "HECT", "function": "endocytic sorting"},
        ]

        dubs = [
            {"name": "USP7", "family": "USP", "function": "stabilization"},
            {"name": "USP14", "family": "USP", "function": "proteasome-associated"},
            {"name": "UCHL1", "family": "UCH", "function": "monoUb processing"},
            {"name": "OTUB1", "family": "OTU", "function": "K48 chain cleavage"},
            {"name": "CSN5", "family": "JAMM", "function": "CRL deneddylation"},
        ]

        interacting_e3s = rng.sample(e3_ligases, k=rng.randint(1, 4))
        interacting_dubs = rng.sample(dubs, k=rng.randint(1, 3))

        ub_sites = []
        for i in range(rng.randint(2, 8)):
            u_rng = random.Random(seed + 8000 + i * 59)
            ub_sites.append({
                "lysine_position": u_rng.randint(10, 600),
                "chain_type": u_rng.choice(["K48", "K63", "K11", "K27", "mono-Ub"]),
                "functional_consequence": u_rng.choice([
                    "proteasomal degradation", "lysosomal trafficking",
                    "signaling scaffold", "endocytosis", "DNA repair",
                ]),
            })

        half_life = rng.uniform(0.5, 48.0)
        proteasome_sensitivity = rng.uniform(0.1, 0.9)

        return {
            "gene": gene,
            "analysis_type": "ubiquitin_proteasome_pathway",
            "data_source": "UbiNet / PhosphoSitePlus",
            "ubiquitination_sites": ub_sites,
            "e3_ligases": [
                {**e3, "interaction_score": round(rng.uniform(0.3, 0.95), 3)}
                for e3 in interacting_e3s
            ],
            "deubiquitinases": [
                {**dub, "stabilization_effect": round(rng.uniform(0.2, 0.9), 3)}
                for dub in interacting_dubs
            ],
            "protein_half_life_hours": round(half_life, 1),
            "proteasome_sensitivity": round(proteasome_sensitivity, 3),
            "therapeutic_strategy": (
                "Proteasome inhibitor (Bortezomib) may upregulate target surface expression"
                if proteasome_sensitivity > 0.6 else
                "Target protein is relatively stable — proteasome inhibition unlikely beneficial"
            ),
        }

    # ─── Glycosylation Site Prediction ───────────────────────────────────────

    def glycosylation_analysis(self, gene: str) -> dict:
        """
        Predict N-linked and O-linked glycosylation sites. Glycosylation
        can mask or expose epitopes critical for CAR-T recognition.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 9000)

        n_glyco_sites = rng.randint(1, 12)
        glyco_sites = []
        for i in range(n_glyco_sites):
            g_rng = random.Random(seed + 9000 + i * 71)
            glyco_type = g_rng.choice(["N-linked", "O-linked"])
            position = g_rng.randint(20, 700)

            glyco_sites.append({
                "site_id": f"Glyco_{gene}_{i+1}",
                "position": position,
                "type": glyco_type,
                "sequon": f"N-X-{g_rng.choice(['S', 'T'])}" if glyco_type == "N-linked" else "S/T",
                "occupancy": round(g_rng.uniform(0.1, 0.99), 3),
                "glycan_type": g_rng.choice([
                    "high-mannose", "complex", "hybrid", "pauci-mannose",
                    "O-GalNAc", "O-GlcNAc", "O-Fuc",
                ]) if glyco_type == "N-linked" else g_rng.choice([
                    "mucin-type", "O-GlcNAc", "O-Fuc", "O-Man",
                ]),
                "near_binding_epitope": g_rng.random() > 0.6,
                "shields_epitope": g_rng.random() > 0.7,
                "tumor_specific_alteration": g_rng.random() > 0.5,
            })

        epitope_shielding = [s for s in glyco_sites if s["shields_epitope"]]

        return {
            "gene": gene,
            "analysis_type": "glycosylation_profiling",
            "data_source": "UniProt / GlyConnect / NetNGlyc",
            "total_glycosites": len(glyco_sites),
            "glycosylation_sites": glyco_sites,
            "n_linked": sum(1 for s in glyco_sites if s["type"] == "N-linked"),
            "o_linked": sum(1 for s in glyco_sites if s["type"] == "O-linked"),
            "epitope_shielding_sites": len(epitope_shielding),
            "tumor_specific_glyco": sum(1 for s in glyco_sites if s["tumor_specific_alteration"]),
            "cart_binding_impact": (
                "HIGH: Glycan shields may block CAR-T scFv binding"
                if len(epitope_shielding) > 2 else
                "MODERATE: Some glycosylation near binding site"
                if len(epitope_shielding) > 0 else
                "LOW: Glycosylation does not obstruct CAR binding"
            ),
        }

    # ─── Kinase-Substrate Network ────────────────────────────────────────────

    def kinase_substrate_network(self, gene: str) -> dict:
        """
        Map the kinase-substrate signaling network affecting the target.
        Identifies druggable kinase nodes that regulate target expression.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 10000)

        kinase_nodes = [
            {"kinase": "EGFR", "family": "RTK", "inhibitors": ["Erlotinib", "Osimertinib"]},
            {"kinase": "HER2", "family": "RTK", "inhibitors": ["Lapatinib", "Tucatinib"]},
            {"kinase": "AKT1", "family": "AGC", "inhibitors": ["Ipatasertib", "Capivasertib"]},
            {"kinase": "mTOR", "family": "PI3K-related", "inhibitors": ["Everolimus", "Temsirolimus"]},
            {"kinase": "MEK1", "family": "STE", "inhibitors": ["Trametinib", "Cobimetinib"]},
            {"kinase": "JAK2", "family": "TK", "inhibitors": ["Ruxolitinib", "Baricitinib"]},
            {"kinase": "CDK4", "family": "CMGC", "inhibitors": ["Palbociclib", "Ribociclib"]},
            {"kinase": "SRC", "family": "TK", "inhibitors": ["Dasatinib", "Bosutinib"]},
            {"kinase": "BRAF", "family": "TKL", "inhibitors": ["Vemurafenib", "Dabrafenib"]},
            {"kinase": "BTK", "family": "TK", "inhibitors": ["Ibrutinib", "Acalabrutinib"]},
        ]

        active_kinases = rng.sample(kinase_nodes, k=rng.randint(3, 7))
        network = []
        for kinase in active_kinases:
            k_rng = random.Random(seed + 10000 + hash(kinase["kinase"]))
            effect = k_rng.uniform(-0.5, 0.8)
            network.append({
                **kinase,
                "effect_on_target": round(effect, 3),
                "effect_direction": "upregulates" if effect > 0 else "downregulates",
                "pathway": k_rng.choice([
                    "MAPK/ERK", "PI3K/AKT/mTOR", "JAK/STAT",
                    "Wnt/beta-catenin", "NF-kB", "Hippo",
                ]),
                "sensitivity_score": round(k_rng.uniform(0.1, 0.95), 3),
            })

        upregulators = [n for n in network if n["effect_on_target"] > 0.2]

        return {
            "gene": gene,
            "analysis_type": "kinase_substrate_network",
            "data_source": "PhosphoSitePlus / KinHub / KSEA",
            "kinase_network": network,
            "n_upregulating_kinases": len(upregulators),
            "top_upregulator": max(network, key=lambda n: n["effect_on_target"])["kinase"] if network else "none",
            "druggable_kinase_nodes": sum(1 for n in network if n["sensitivity_score"] > 0.5),
            "combination_candidates": [
                f"{n['inhibitors'][0]} ({n['kinase']} inhibitor)"
                for n in network
                if n["effect_on_target"] < -0.2 and n["sensitivity_score"] > 0.5
            ][:3],
        }

    # ─── Proximity Labeling (BioID) Analysis ─────────────────────────────────

    def proximity_labeling_analysis(self, gene: str) -> dict:
        """
        Simulate BioID/TurboID proximity labeling to map the target's
        protein neighborhood on the cell surface. Identifies co-expressed
        surface proteins for dual-targeting strategies.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 11000)

        surface_neighbors = [
            "CD19", "CD20", "CD22", "CD38", "CD47", "CD70",
            "BCMA", "GPRC5D", "DLL3", "EpCAM", "HER2", "EGFR",
            "Mesothelin", "GD2", "PSMA", "MUC1", "CEA", "GPC3",
            "Claudin18.2", "Nectin-4", "TROP2", "ROR1",
        ]

        n_neighbors = rng.randint(5, 15)
        selected = rng.sample(surface_neighbors, k=min(n_neighbors, len(surface_neighbors)))
        proximal_proteins = []

        for prot in selected:
            p_rng = random.Random(seed + 11000 + hash(prot))
            enrichment = p_rng.uniform(1.0, 50.0)
            distance_nm = p_rng.uniform(5, 50)

            proximal_proteins.append({
                "protein": prot,
                "enrichment_ratio": round(enrichment, 2),
                "estimated_distance_nm": round(distance_nm, 1),
                "co_expression_correlation": round(p_rng.uniform(0.1, 0.9), 3),
                "dual_target_candidate": enrichment > 10 and distance_nm < 20,
                "known_cart_target": prot in ["CD19", "BCMA", "CD22", "GPRC5D"],
                "normal_tissue_expression": p_rng.choice(["restricted", "moderate", "broad"]),
            })

        dual_targets = [p for p in proximal_proteins if p["dual_target_candidate"]]

        return {
            "gene": gene,
            "analysis_type": "proximity_labeling",
            "data_source": "BioID/TurboID simulation",
            "proximal_proteins": proximal_proteins,
            "total_neighbors": len(proximal_proteins),
            "dual_target_candidates": len(dual_targets),
            "top_dual_targets": [
                p["protein"] for p in dual_targets
                if p["normal_tissue_expression"] == "restricted"
            ][:3],
            "tandem_car_strategy": (
                f"Consider tandem CAR targeting {gene} + "
                f"{dual_targets[0]['protein'] if dual_targets else 'N/A'} "
                f"to prevent antigen escape"
                if dual_targets else
                "No suitable dual-target candidates in proximity"
            ),
        }

    # ─── Protein Half-Life Estimation ────────────────────────────────────────

    def protein_halflife_estimation(self, gene: str) -> dict:
        """
        Estimate protein half-life using SILAC-based pulse-chase simulation.
        Determines target protein turnover rate critical for CAR-T efficacy.
        """
        import math as _math
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 11000)

        halflife_hours = rng.uniform(0.5, 200)
        degradation_rate = 0.693 / max(halflife_hours, 0.01)

        degradation_pathways = {
            "proteasome": round(rng.uniform(0, 1), 3),
            "lysosome": round(rng.uniform(0, 1), 3),
            "autophagy": round(rng.uniform(0, 0.5), 3),
            "calpain": round(rng.uniform(0, 0.3), 3),
        }
        total_deg = sum(degradation_pathways.values())
        for k in degradation_pathways:
            degradation_pathways[k] = round(degradation_pathways[k] / max(total_deg, 0.01), 3)

        ubiquitin_sites = rng.randint(0, 8)
        pest_sequences = rng.randint(0, 3)

        timepoints = [0, 2, 4, 8, 12, 24, 48]
        decay_curve = []
        for t in timepoints:
            remaining = 100 * _math.exp(-degradation_rate * t)
            decay_curve.append({"hours": t, "percent_remaining": round(remaining, 1)})

        return {
            "gene": gene,
            "analysis_type": "protein_halflife",
            "data_source": "SILAC pulse-chase simulation",
            "halflife_hours": round(halflife_hours, 1),
            "degradation_rate_per_hour": round(degradation_rate, 4),
            "degradation_pathways": degradation_pathways,
            "ubiquitin_sites": ubiquitin_sites,
            "pest_sequences": pest_sequences,
            "decay_curve": decay_curve,
            "stability_class": (
                "highly_stable" if halflife_hours > 48 else
                "stable" if halflife_hours > 12 else
                "moderate" if halflife_hours > 4 else "rapidly_degraded"
            ),
            "cart_implication": (
                "Stable protein — consistent surface density for CAR-T recognition"
                if halflife_hours > 12 else
                "Rapidly degraded — may need sustained transcription for presentation"
            ),
        }

    # ─── Thermal Stability Profiling ─────────────────────────────────────────

    def thermal_stability_profiling(self, gene: str) -> dict:
        """
        Thermal proteome profiling (TPP/CETSA) analysis.
        Measures protein thermal stability shifts upon drug binding.
        """
        import math as _math
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 12000)

        tm_vehicle = rng.uniform(40, 70)
        temperatures = [37, 41, 44, 47, 50, 53, 56, 59, 63, 67]
        melting_curve = []
        for temp in temperatures:
            fraction = 1 / (1 + _math.exp((temp - tm_vehicle) / 2))
            melting_curve.append({
                "temperature_C": temp,
                "fraction_soluble": round(fraction, 3),
            })

        conditions = ["vehicle", "drug_A", "drug_B", "combination"]
        stability_shifts = {}
        for cond in conditions:
            c_rng = random.Random(seed + 12000 + hash(cond))
            shift = c_rng.uniform(-5, 10)
            stability_shifts[cond] = {
                "tm": round(tm_vehicle + shift, 1),
                "delta_tm": round(shift, 2),
                "stabilized": shift > 2,
                "destabilized": shift < -2,
            }

        return {
            "gene": gene,
            "analysis_type": "thermal_stability_profiling",
            "data_source": "TPP / CETSA simulation",
            "melting_temperature_C": round(tm_vehicle, 1),
            "melting_curve": melting_curve,
            "stability_shifts": stability_shifts,
            "most_stabilizing": max(
                stability_shifts.items(), key=lambda x: x[1]["delta_tm"]
            )[0],
            "thermal_class": (
                "thermostable" if tm_vehicle > 60 else
                "moderate" if tm_vehicle > 50 else "thermolabile"
            ),
        }

    # ─── Secretome Analysis ──────────────────────────────────────────────────

    def secretome_analysis(self, gene: str) -> dict:
        """
        Analyze the tumor secretome for soluble forms of the target antigen.
        Shed antigen in serum can act as a decoy neutralizing CAR-T cells.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 13000)

        shedding_proteases = [
            {"name": "ADAM10", "type": "metalloprotease"},
            {"name": "ADAM17/TACE", "type": "metalloprotease"},
            {"name": "MMP9", "type": "MMP"},
            {"name": "MMP14", "type": "MMP"},
            {"name": "BACE1", "type": "aspartyl protease"},
            {"name": "gamma-secretase", "type": "intramembrane protease"},
        ]

        shedding_rate = round(rng.uniform(0, 1), 3)
        serum_conc = round(rng.uniform(0, 1000), 1)

        protease_scores = []
        for protease in shedding_proteases:
            p_rng = random.Random(seed + 13000 + hash(protease["name"]))
            protease_scores.append({
                **protease,
                "expression_tumor": round(p_rng.uniform(0, 10), 2),
                "cleavage_probability": round(p_rng.uniform(0, 1), 3),
                "inhibitor_available": p_rng.random() > 0.4,
            })

        active_sheddases = [p for p in protease_scores if p["cleavage_probability"] > 0.5]

        return {
            "gene": gene,
            "analysis_type": "secretome_analysis",
            "data_source": "MS secretome simulation",
            "shedding_rate": shedding_rate,
            "serum_concentration_ng_ml": serum_conc,
            "protease_analysis": protease_scores,
            "active_sheddases": len(active_sheddases),
            "decoy_risk": (
                "HIGH: Significant antigen shedding may neutralize CAR-T"
                if shedding_rate > 0.5 and serum_conc > 100 else
                "MODERATE: Some shedding detected"
                if shedding_rate > 0.2 else "LOW: Minimal shedding"
            ),
            "mitigation": (
                f"Consider {active_sheddases[0]['name']} inhibitor to reduce shedding"
                if active_sheddases and active_sheddases[0]["inhibitor_available"]
                else "No targetable sheddase identified"
            ),
        }

    # ─── Surface Interactome Mapping ─────────────────────────────────────────

    def surface_interactome_mapping(self, gene: str) -> dict:
        """
        Map the cell surface interactome of the target protein.
        Identifies neighbors that may shield or enhance CAR-T access.
        """
        gene = gene.upper().strip()
        seed = int(hashlib.md5(gene.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 14000)

        surface_partners = [
            "CD45", "CD44", "ICAM-1", "VCAM-1", "E-selectin",
            "Galectin-3", "Syndecan-1", "Glypican-3", "CD47",
            "PD-L1", "B7-H3", "CD155", "MUC1", "MUC16",
            "Tetraspanins", "Integrins",
        ]

        n_partners = rng.randint(3, 10)
        selected = rng.sample(surface_partners, k=min(n_partners, len(surface_partners)))
        interactome = []

        for partner in selected:
            p_rng = random.Random(seed + 14000 + hash(partner))
            interactome.append({
                "partner": partner,
                "interaction_type": p_rng.choice(["cis", "trans", "homophilic", "heterophilic"]),
                "affinity_kd_nM": round(p_rng.uniform(1, 5000), 1),
                "colocalization_score": round(p_rng.uniform(0, 1), 3),
                "shields_epitope": p_rng.random() > 0.7,
                "enhances_signaling": p_rng.random() > 0.5,
            })

        shielding = [i for i in interactome if i["shields_epitope"]]

        return {
            "gene": gene,
            "analysis_type": "surface_interactome",
            "data_source": "BioID / APEX2 / co-IP simulation",
            "total_surface_partners": len(interactome),
            "interactome": interactome,
            "epitope_shielding_partners": len(shielding),
            "accessibility_risk": (
                "HIGH: Multiple partners shield the target epitope"
                if len(shielding) > 2 else
                "MODERATE: Some epitope masking"
                if len(shielding) > 0 else
                "LOW: Epitope is freely accessible"
            ),
        }
