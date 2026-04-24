"""
CARVanta Genomics — Figure Generator Engine
=============================================
Publication-ready visualization rendering for genomic analysis results:
variant waterfall (oncoplot), circos genome overview, neoantigen binding
heatmap, TMB/MSI gauge, and protein-domain lollipop plots.

Renders to SVG-compatible data structures for frontend visualization.

Security: Stateless, async-compatible, no file system writes.
API Version: v5
"""

import math
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from genomics.file_processor import VariantRecord, VariantType, GRCH38_CHROMOSOMES

logger = logging.getLogger("carvanta.genomics.figure_generator")

# ──────────────────────────────────────────────────────────────────────
# Constants & Color Palettes
# ──────────────────────────────────────────────────────────────────────

# Oncoplot color scheme (TCGA standard)
VARIANT_COLORS: Dict[str, str] = {
    "missense_variant": "#2ecc71",
    "frameshift_variant": "#9b59b6",
    "stop_gained": "#e74c3c",
    "splice_acceptor_variant": "#f39c12",
    "splice_donor_variant": "#f39c12",
    "inframe_insertion": "#3498db",
    "inframe_deletion": "#1abc9c",
    "start_lost": "#e67e22",
    "stop_lost": "#e67e22",
    "synonymous_variant": "#bdc3c7",
    "intron_variant": "#95a5a6",
    "default": "#7f8c8d",
}

# Chromosome colors (alternating for circos)
CHROMOSOME_COLORS: Dict[str, str] = {
    "chr1": "#1f77b4", "chr2": "#ff7f0e", "chr3": "#2ca02c",
    "chr4": "#d62728", "chr5": "#9467bd", "chr6": "#8c564b",
    "chr7": "#e377c2", "chr8": "#7f7f7f", "chr9": "#bcbd22",
    "chr10": "#17becf", "chr11": "#aec7e8", "chr12": "#ffbb78",
    "chr13": "#98df8a", "chr14": "#ff9896", "chr15": "#c5b0d5",
    "chr16": "#c49c94", "chr17": "#f7b6d2", "chr18": "#c7c7c7",
    "chr19": "#dbdb8d", "chr20": "#9edae5", "chr21": "#393b79",
    "chr22": "#637939", "chrX": "#8c6d31", "chrY": "#843c39",
    "chrM": "#7b4173",
}

# Impact severity colors
IMPACT_COLORS: Dict[str, str] = {
    "HIGH": "#e74c3c",
    "MODERATE": "#f39c12",
    "LOW": "#3498db",
    "MODIFIER": "#95a5a6",
}

# Binding affinity heatmap palette
BINDING_HEATMAP_COLORS = [
    "#1a9850",  # < 50 nM (strong)
    "#91cf60",  # 50-150 nM
    "#d9ef8b",  # 150-300 nM
    "#fee08b",  # 300-500 nM
    "#fc8d59",  # 500-2000 nM
    "#d73027",  # > 2000 nM (non-binder)
]


class FigureType(Enum):
    """Available figure types."""
    WATERFALL = "waterfall"
    CIRCOS = "circos"
    NEOANTIGEN_HEATMAP = "neoantigen_heatmap"
    TMB_GAUGE = "tmb_gauge"
    MSI_GAUGE = "msi_gauge"
    LOLLIPOP = "lollipop"
    RAINFALL = "rainfall"
    SPECTRUM = "mutation_spectrum"


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class FigureData:
    """Rendered figure data for frontend consumption."""
    figure_type: FigureType
    title: str
    width: int = 900
    height: int = 500
    data: Dict[str, Any] = field(default_factory=dict)
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    legend: List[Dict[str, str]] = field(default_factory=list)
    axes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────────────
# Variant Waterfall (Oncoplot)
# ──────────────────────────────────────────────────────────────────────

async def render_variant_waterfall(
    annotated_variants: List[Dict[str, Any]],
    max_genes: int = 30,
    sort_by: str = "frequency",
) -> FigureData:
    """
    Render a variant waterfall plot (oncoplot-style).

    Shows top mutated genes as rows, samples/variants as columns,
    color-coded by variant consequence.

    Args:
        annotated_variants: List of {gene, consequence, impact, ...} dicts
        max_genes: Maximum genes to display
        sort_by: Sorting criterion ("frequency", "impact", "name")

    Returns:
        FigureData with waterfall plot data
    """
    # Aggregate by gene
    gene_data: Dict[str, Dict[str, Any]] = {}
    for v in annotated_variants:
        gene = v.get("gene", "Unknown")
        if not gene:
            continue
        if gene not in gene_data:
            gene_data[gene] = {
                "gene": gene,
                "mutation_count": 0,
                "variants": [],
                "consequence_distribution": {},
                "max_impact": "MODIFIER",
            }
        gene_data[gene]["mutation_count"] += 1
        consequence = v.get("consequence", "unknown")
        gene_data[gene]["consequence_distribution"][consequence] = (
            gene_data[gene]["consequence_distribution"].get(consequence, 0) + 1
        )
        gene_data[gene]["variants"].append({
            "coordinate": v.get("coordinate", ""),
            "consequence": consequence,
            "impact": v.get("impact", "MODIFIER"),
            "protein_change": v.get("protein_change", ""),
            "cosmic_id": v.get("cosmic_id"),
            "is_hotspot": v.get("is_hotspot", False),
            "color": VARIANT_COLORS.get(consequence, VARIANT_COLORS["default"]),
        })

        # Track highest impact
        impact_order = {"HIGH": 4, "MODERATE": 3, "LOW": 2, "MODIFIER": 1}
        current_impact = impact_order.get(v.get("impact", "MODIFIER"), 1)
        stored_impact = impact_order.get(gene_data[gene]["max_impact"], 1)
        if current_impact > stored_impact:
            gene_data[gene]["max_impact"] = v.get("impact", "MODIFIER")

    # Sort genes
    genes_list = list(gene_data.values())
    if sort_by == "frequency":
        genes_list.sort(key=lambda g: g["mutation_count"], reverse=True)
    elif sort_by == "impact":
        impact_order = {"HIGH": 4, "MODERATE": 3, "LOW": 2, "MODIFIER": 1}
        genes_list.sort(key=lambda g: (impact_order.get(g["max_impact"], 0), g["mutation_count"]), reverse=True)
    elif sort_by == "name":
        genes_list.sort(key=lambda g: g["gene"])

    # Limit
    display_genes = genes_list[:max_genes]

    # Build figure data
    rows = []
    for idx, gene_info in enumerate(display_genes):
        row = {
            "index": idx,
            "gene": gene_info["gene"],
            "total_mutations": gene_info["mutation_count"],
            "max_impact": gene_info["max_impact"],
            "impact_color": IMPACT_COLORS.get(gene_info["max_impact"], "#95a5a6"),
            "cells": gene_info["variants"],
            "consequence_breakdown": gene_info["consequence_distribution"],
        }
        rows.append(row)

    # Legend
    legend = [
        {"label": label.replace("_", " ").title(), "color": color}
        for label, color in VARIANT_COLORS.items()
        if label != "default"
    ]

    return FigureData(
        figure_type=FigureType.WATERFALL,
        title="Somatic Variant Landscape (Oncoplot)",
        width=900,
        height=max(400, len(display_genes) * 25 + 100),
        data={
            "rows": rows,
            "total_genes": len(gene_data),
            "displayed_genes": len(display_genes),
            "total_variants": len(annotated_variants),
        },
        legend=legend,
        axes={
            "x": {"label": "Variants", "type": "categorical"},
            "y": {"label": "Genes", "type": "categorical"},
        },
        metadata={"sort_by": sort_by, "max_genes": max_genes},
    )


# ──────────────────────────────────────────────────────────────────────
# Circos-Style Genome Overview
# ──────────────────────────────────────────────────────────────────────

async def render_circos_overview(
    variants: List[VariantRecord],
    annotations: Optional[Dict[str, Dict[str, Any]]] = None,
    include_ideogram: bool = True,
) -> FigureData:
    """
    Render a circos-style genome overview showing variant distribution
    across all chromosomes.

    Layers:
    1. Chromosome ideogram (outer ring)
    2. Variant density histogram (middle ring)
    3. Variant quality scatter (inner ring)
    4. Connection arcs for structural variants (center)

    Returns:
        FigureData with circos plot data
    """
    annotations = annotations or {}

    # Build chromosome data
    chromosomes = []
    total_genome_length = sum(GRCH38_CHROMOSOMES.values())
    cumulative_angle = 0.0
    gap_angle = 1.0  # degrees between chromosomes

    for chrom, length in GRCH38_CHROMOSOMES.items():
        proportion = length / total_genome_length
        arc_angle = proportion * (360.0 - len(GRCH38_CHROMOSOMES) * gap_angle)

        chromosomes.append({
            "name": chrom,
            "length": length,
            "length_mb": round(length / 1_000_000, 1),
            "start_angle": round(cumulative_angle, 2),
            "end_angle": round(cumulative_angle + arc_angle, 2),
            "color": CHROMOSOME_COLORS.get(chrom, "#7f8c8d"),
        })
        cumulative_angle += arc_angle + gap_angle

    # Bin variants by chromosome and position
    bin_size = 5_000_000  # 5 Mb bins
    density_data: Dict[str, List[Dict[str, Any]]] = {}
    variant_points: List[Dict[str, Any]] = []

    for chrom in GRCH38_CHROMOSOMES:
        n_bins = math.ceil(GRCH38_CHROMOSOMES[chrom] / bin_size)
        density_data[chrom] = [
            {"bin": i, "start": i * bin_size, "end": min((i + 1) * bin_size, GRCH38_CHROMOSOMES[chrom]), "count": 0}
            for i in range(n_bins)
        ]

    for variant in variants:
        chrom = variant.chrom
        if chrom not in density_data:
            continue

        # Find bin
        bin_idx = min(variant.pos // bin_size, len(density_data[chrom]) - 1)
        if 0 <= bin_idx < len(density_data[chrom]):
            density_data[chrom][bin_idx]["count"] += 1

        # Quality scatter point
        annot = annotations.get(variant.coordinate_key, {})
        variant_points.append({
            "chrom": chrom,
            "pos": variant.pos,
            "qual": variant.qual,
            "type": variant.variant_type.value,
            "gene": annot.get("gene", ""),
            "impact": annot.get("impact", "MODIFIER"),
            "color": IMPACT_COLORS.get(annot.get("impact", "MODIFIER"), "#95a5a6"),
        })

    # Compute max density for normalization
    max_density = max(
        (bin_info["count"] for bins in density_data.values() for bin_info in bins),
        default=1,
    )

    # Normalize density
    for chrom, bins in density_data.items():
        for bin_info in bins:
            bin_info["normalized"] = round(bin_info["count"] / max(max_density, 1), 4)

    return FigureData(
        figure_type=FigureType.CIRCOS,
        title="Genome-Wide Variant Distribution (Circos)",
        width=700,
        height=700,
        data={
            "chromosomes": chromosomes,
            "density": {k: v for k, v in density_data.items() if any(b["count"] > 0 for b in v)},
            "variants": variant_points[:5000],  # cap for performance
            "max_density": max_density,
            "bin_size_mb": bin_size / 1_000_000,
        },
        legend=[
            {"label": "HIGH impact", "color": IMPACT_COLORS["HIGH"]},
            {"label": "MODERATE impact", "color": IMPACT_COLORS["MODERATE"]},
            {"label": "LOW impact", "color": IMPACT_COLORS["LOW"]},
        ],
        axes={
            "outer": {"label": "Chromosome", "type": "ideogram"},
            "middle": {"label": "Variant Density", "type": "histogram"},
            "inner": {"label": "Variant Quality", "type": "scatter"},
        },
    )


# ──────────────────────────────────────────────────────────────────────
# Neoantigen Binding Heatmap
# ──────────────────────────────────────────────────────────────────────

async def render_neoantigen_heatmap(
    neoantigen_results: Dict[str, Any],
    max_peptides: int = 30,
) -> FigureData:
    """
    Render a heatmap showing neoantigen-HLA binding affinities.

    Rows = peptides (sorted by best IC50)
    Columns = HLA alleles
    Color = IC50 binding affinity (green=strong, red=non-binder)
    """
    candidates = neoantigen_results.get("candidates", [])[:max_peptides]
    hla_alleles = neoantigen_results.get("hla_alleles_tested", [])

    # Build heatmap matrix
    rows = []
    for c in candidates:
        peptide = c.get("peptide", "")
        gene = c.get("gene", "")
        protein_change = c.get("protein_change", "")

        # Build row with IC50 for each HLA allele
        hla_bindings: Dict[str, Dict[str, Any]] = {}
        for binding in c.get("all_hla_bindings", []):
            hla = binding.get("hla", "")
            ic50 = binding.get("ic50", 50000)
            level = binding.get("level", "non_binder")

            # Color mapping
            if ic50 < 50:
                color = BINDING_HEATMAP_COLORS[0]
            elif ic50 < 150:
                color = BINDING_HEATMAP_COLORS[1]
            elif ic50 < 300:
                color = BINDING_HEATMAP_COLORS[2]
            elif ic50 < 500:
                color = BINDING_HEATMAP_COLORS[3]
            elif ic50 < 2000:
                color = BINDING_HEATMAP_COLORS[4]
            else:
                color = BINDING_HEATMAP_COLORS[5]

            hla_bindings[hla] = {
                "ic50": ic50,
                "level": level,
                "color": color,
                "log_ic50": round(math.log10(max(ic50, 1)), 2),
            }

        rows.append({
            "peptide": peptide,
            "gene": gene,
            "protein_change": protein_change,
            "rank": c.get("rank", 0),
            "category": c.get("category", ""),
            "composite_score": c.get("composite_score", 0),
            "immunogenicity": c.get("immunogenicity", 0),
            "bindings": hla_bindings,
        })

    # Legend
    legend = [
        {"label": "< 50 nM (Strong)", "color": BINDING_HEATMAP_COLORS[0]},
        {"label": "50-150 nM", "color": BINDING_HEATMAP_COLORS[1]},
        {"label": "150-300 nM", "color": BINDING_HEATMAP_COLORS[2]},
        {"label": "300-500 nM", "color": BINDING_HEATMAP_COLORS[3]},
        {"label": "500-2000 nM (Weak)", "color": BINDING_HEATMAP_COLORS[4]},
        {"label": "> 2000 nM (Non-binder)", "color": BINDING_HEATMAP_COLORS[5]},
    ]

    return FigureData(
        figure_type=FigureType.NEOANTIGEN_HEATMAP,
        title="Neoantigen-HLA Binding Affinity Landscape",
        width=800,
        height=max(400, len(rows) * 28 + 120),
        data={
            "rows": rows,
            "columns": hla_alleles,
            "total_candidates": len(neoantigen_results.get("candidates", [])),
            "displayed": len(rows),
        },
        legend=legend,
        axes={
            "x": {"label": "HLA Allele", "type": "categorical"},
            "y": {"label": "Neoantigen Peptide", "type": "categorical"},
            "color": {"label": "Predicted IC50 (nM)", "type": "continuous", "scale": "log"},
        },
    )


# ──────────────────────────────────────────────────────────────────────
# TMB Gauge
# ──────────────────────────────────────────────────────────────────────

async def render_tmb_gauge(
    tmb_data: Dict[str, Any],
) -> FigureData:
    """
    Render a gauge visualization for TMB with clinical thresholds.

    Shows:
    - Current TMB value on a semicircular gauge
    - FDA-approved threshold markers (10 mut/Mb)
    - Cancer-type percentile indicator
    - Confidence interval
    """
    tmb_info = tmb_data.get("tmb", {})
    tmb_value = tmb_info.get("per_mb", 0)
    classification = tmb_info.get("classification", "TMB-Low")
    percentile = tmb_info.get("cancer_percentile", 50)
    ci = tmb_info.get("confidence_interval", [0, 0])
    cancer_type = tmb_info.get("panel", "WES")

    # Gauge segments
    max_gauge = 50.0
    gauge_value = min(tmb_value, max_gauge)
    gauge_fraction = gauge_value / max_gauge

    segments = [
        {"label": "TMB-Low", "start": 0, "end": 6, "color": "#3498db", "fraction": 6/max_gauge},
        {"label": "TMB-Intermediate", "start": 6, "end": 10, "color": "#f39c12", "fraction": 4/max_gauge},
        {"label": "TMB-High", "start": 10, "end": 50, "color": "#e74c3c", "fraction": 40/max_gauge},
    ]

    thresholds = [
        {"value": 6, "label": "Intermediate", "position": 6/max_gauge},
        {"value": 10, "label": "FDA TMB-High", "position": 10/max_gauge, "is_primary": True},
        {"value": 20, "label": "Very High", "position": 20/max_gauge},
    ]

    # Needle color based on classification
    needle_color = "#3498db"
    if classification == "TMB-High":
        needle_color = "#e74c3c"
    elif classification == "TMB-Intermediate":
        needle_color = "#f39c12"

    return FigureData(
        figure_type=FigureType.TMB_GAUGE,
        title=f"Tumor Mutational Burden: {tmb_value:.1f} mut/Mb",
        width=500,
        height=350,
        data={
            "value": tmb_value,
            "max_value": max_gauge,
            "fraction": round(gauge_fraction, 4),
            "classification": classification,
            "needle_color": needle_color,
            "segments": segments,
            "thresholds": thresholds,
            "percentile": percentile,
            "confidence_interval": {"low": ci[0], "high": ci[1]},
            "breakdown": tmb_info.get("breakdown", {}),
            "total_mutations": tmb_info.get("total_mutations", 0),
            "coding_mutations": tmb_info.get("coding_mutations", 0),
        },
        annotations=[
            {"text": f"{percentile:.0f}th percentile", "position": "top_right"},
            {"text": tmb_info.get("interpretation", ""), "position": "bottom"},
        ],
        legend=[
            {"label": s["label"], "color": s["color"]} for s in segments
        ],
    )


# ──────────────────────────────────────────────────────────────────────
# Lollipop Plot (Protein Domain Mutation Map)
# ──────────────────────────────────────────────────────────────────────

# Key protein domains for immunotherapy-relevant genes
PROTEIN_DOMAINS: Dict[str, List[Dict[str, Any]]] = {
    "TP53": [
        {"name": "TAD1", "start": 1, "end": 40, "color": "#3498db", "type": "transactivation"},
        {"name": "TAD2", "start": 41, "end": 61, "color": "#2ecc71", "type": "transactivation"},
        {"name": "PRD", "start": 63, "end": 97, "color": "#9b59b6", "type": "proline_rich"},
        {"name": "DBD", "start": 102, "end": 292, "color": "#e74c3c", "type": "DNA_binding"},
        {"name": "TET", "start": 323, "end": 356, "color": "#f39c12", "type": "tetramerization"},
        {"name": "REG", "start": 364, "end": 393, "color": "#1abc9c", "type": "regulatory"},
    ],
    "KRAS": [
        {"name": "G-domain", "start": 1, "end": 166, "color": "#e74c3c", "type": "GTPase"},
        {"name": "Switch I", "start": 30, "end": 38, "color": "#f39c12", "type": "effector_binding"},
        {"name": "Switch II", "start": 59, "end": 76, "color": "#3498db", "type": "GEF_binding"},
        {"name": "HVR", "start": 167, "end": 189, "color": "#9b59b6", "type": "hypervariable"},
    ],
    "EGFR": [
        {"name": "ECD I", "start": 1, "end": 165, "color": "#3498db", "type": "extracellular"},
        {"name": "ECD II", "start": 166, "end": 309, "color": "#2ecc71", "type": "extracellular"},
        {"name": "ECD III", "start": 310, "end": 480, "color": "#9b59b6", "type": "ligand_binding"},
        {"name": "ECD IV", "start": 481, "end": 621, "color": "#1abc9c", "type": "extracellular"},
        {"name": "TM", "start": 622, "end": 644, "color": "#7f8c8d", "type": "transmembrane"},
        {"name": "TK", "start": 696, "end": 961, "color": "#e74c3c", "type": "tyrosine_kinase"},
        {"name": "CTD", "start": 962, "end": 1210, "color": "#f39c12", "type": "C_terminal"},
    ],
    "BRAF": [
        {"name": "RBD", "start": 155, "end": 227, "color": "#3498db", "type": "Ras_binding"},
        {"name": "CRD", "start": 234, "end": 280, "color": "#2ecc71", "type": "cysteine_rich"},
        {"name": "Kinase", "start": 457, "end": 717, "color": "#e74c3c", "type": "kinase"},
    ],
    "PIK3CA": [
        {"name": "ABD", "start": 1, "end": 108, "color": "#3498db", "type": "adaptor_binding"},
        {"name": "RBD", "start": 190, "end": 291, "color": "#2ecc71", "type": "Ras_binding"},
        {"name": "C2", "start": 330, "end": 487, "color": "#9b59b6", "type": "membrane_binding"},
        {"name": "Helical", "start": 525, "end": 696, "color": "#f39c12", "type": "helical"},
        {"name": "Kinase", "start": 697, "end": 1068, "color": "#e74c3c", "type": "kinase"},
    ],
}


async def render_lollipop_plot(
    gene: str,
    variants: List[Dict[str, Any]],
) -> FigureData:
    """
    Render a lollipop plot showing mutations mapped onto protein domains.

    Shows:
    - Protein backbone with colored domain annotations
    - Mutation lollipops with height = frequency/importance
    - Color by consequence type
    """
    domains = PROTEIN_DOMAINS.get(gene, [])
    protein_length = max((d["end"] for d in domains), default=500) if domains else 500

    # Build mutation lollipops
    lollipops = []
    for v in variants:
        protein_change = v.get("protein_change", "")
        if not protein_change:
            continue

        # Extract position from protein change (e.g., R248W → 248)
        import re
        match = re.match(r"[A-Z*](\d+)[A-Z*]", protein_change)
        if not match:
            continue
        aa_pos = int(match.group(1))

        consequence = v.get("consequence", "missense_variant")
        is_hotspot = v.get("is_hotspot", False)

        # Find which domain this falls in
        in_domain = ""
        for domain in domains:
            if domain["start"] <= aa_pos <= domain["end"]:
                in_domain = domain["name"]
                break

        lollipops.append({
            "position": aa_pos,
            "protein_change": protein_change,
            "consequence": consequence,
            "color": VARIANT_COLORS.get(consequence, VARIANT_COLORS["default"]),
            "is_hotspot": is_hotspot,
            "cosmic_id": v.get("cosmic_id", ""),
            "cosmic_frequency": v.get("cosmic_frequency", 0),
            "height": 1.0 + (v.get("cosmic_frequency", 0) * 10),  # Scale by frequency
            "domain": in_domain,
            "tooltip": f"{protein_change} ({consequence.replace('_', ' ')})",
        })

    # Sort by position
    lollipops.sort(key=lambda l: l["position"])

    return FigureData(
        figure_type=FigureType.LOLLIPOP,
        title=f"{gene} — Protein Domain Mutation Map",
        width=900,
        height=350,
        data={
            "gene": gene,
            "protein_length": protein_length,
            "domains": domains,
            "mutations": lollipops,
            "total_mutations": len(lollipops),
            "hotspot_count": sum(1 for l in lollipops if l["is_hotspot"]),
        },
        legend=[
            {"label": d["name"], "color": d["color"]}
            for d in domains
        ],
        axes={
            "x": {"label": "Amino Acid Position", "type": "linear", "max": protein_length},
            "y": {"label": "Mutation Frequency", "type": "linear"},
        },
        metadata={"gene": gene, "protein_length": protein_length},
    )


# ──────────────────────────────────────────────────────────────────────
# Mutation Spectrum (Ti/Tv, Signature)
# ──────────────────────────────────────────────────────────────────────

async def render_mutation_spectrum(
    variants: List[VariantRecord],
) -> FigureData:
    """
    Render a mutation spectrum bar chart showing the distribution
    of base substitution types (6 classes for SNVs).

    Also computes trinucleotide context signature approximation.
    """
    # 6 substitution classes
    substitution_classes = {
        "C>A": 0, "C>G": 0, "C>T": 0,
        "T>A": 0, "T>C": 0, "T>G": 0,
    }

    # Complement mapping
    complement = {"A": "T", "T": "A", "C": "G", "G": "C"}

    for v in variants:
        if v.variant_type != VariantType.SNV:
            continue
        if len(v.ref) != 1 or len(v.alt) != 1:
            continue

        ref = v.ref.upper()
        alt = v.alt.upper()

        # Normalize to pyrimidine context (C or T as reference)
        if ref in ("A", "G"):
            ref = complement.get(ref, ref)
            alt = complement.get(alt, alt)

        key = f"{ref}>{alt}"
        if key in substitution_classes:
            substitution_classes[key] += 1

    total = sum(substitution_classes.values())

    # Substitution colors (COSMIC signature standard)
    class_colors = {
        "C>A": "#1abc9c",
        "C>G": "#2c3e50",
        "C>T": "#e74c3c",
        "T>A": "#bdc3c7",
        "T>C": "#2ecc71",
        "T>G": "#e377c2",
    }

    bars = []
    for sub_class, count in substitution_classes.items():
        fraction = count / max(total, 1)
        bars.append({
            "class": sub_class,
            "count": count,
            "fraction": round(fraction, 4),
            "color": class_colors.get(sub_class, "#7f8c8d"),
        })

    # Ti/Tv ratio
    transitions = substitution_classes.get("C>T", 0) + substitution_classes.get("T>C", 0)
    transversions = (
        substitution_classes.get("C>A", 0) + substitution_classes.get("C>G", 0) +
        substitution_classes.get("T>A", 0) + substitution_classes.get("T>G", 0)
    )
    ti_tv = round(transitions / max(transversions, 1), 3)

    # Dominant signature interpretation
    dominant = max(substitution_classes, key=lambda k: substitution_classes[k])
    if dominant == "C>T":
        signature_note = "C>T dominant — suggestive of aging/clock-like signature (SBS1/SBS5) or APOBEC (if clustered)"
    elif dominant == "C>A":
        signature_note = "C>A dominant — suggestive of tobacco/smoking (SBS4) or oxidative damage (SBS18)"
    elif dominant == "T>C":
        signature_note = "T>C dominant — may indicate AID/APOBEC activity"
    elif dominant == "C>G":
        signature_note = "C>G dominant — suggestive of APOBEC activity (SBS13)"
    else:
        signature_note = "Mixed mutation spectrum"

    return FigureData(
        figure_type=FigureType.SPECTRUM,
        title="Mutation Spectrum",
        width=600,
        height=400,
        data={
            "bars": bars,
            "total_snvs": total,
            "ti_tv_ratio": ti_tv,
            "transitions": transitions,
            "transversions": transversions,
            "dominant_class": dominant,
            "signature_note": signature_note,
        },
        legend=[
            {"label": sub, "color": col} for sub, col in class_colors.items()
        ],
        axes={
            "x": {"label": "Substitution Class", "type": "categorical"},
            "y": {"label": "Count", "type": "linear"},
        },
    )


# ──────────────────────────────────────────────────────────────────────
# Figure Export Orchestrator
# ──────────────────────────────────────────────────────────────────────

async def generate_figure(
    figure_type: str,
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a specific figure type from analysis data.

    Args:
        figure_type: Type of figure to generate
        data: Input data for the figure
        options: Additional rendering options

    Returns:
        Figure data dictionary ready for frontend rendering
    """
    options = options or {}

    if figure_type == "waterfall":
        fig = await render_variant_waterfall(
            data.get("annotated_variants", []),
            max_genes=options.get("max_genes", 30),
        )
    elif figure_type == "circos":
        variants = data.get("variants", [])
        fig = await render_circos_overview(variants)
    elif figure_type == "neoantigen_heatmap":
        fig = await render_neoantigen_heatmap(data)
    elif figure_type == "tmb_gauge":
        fig = await render_tmb_gauge(data)
    elif figure_type == "lollipop":
        gene = data.get("gene", "TP53")
        variants = data.get("variants", [])
        fig = await render_lollipop_plot(gene, variants)
    elif figure_type == "mutation_spectrum":
        variants = data.get("variants", [])
        fig = await render_mutation_spectrum(variants)
    else:
        return {"error": f"Unknown figure type: {figure_type}"}

    return {
        "figure_type": fig.figure_type.value,
        "title": fig.title,
        "width": fig.width,
        "height": fig.height,
        "data": fig.data,
        "annotations": fig.annotations,
        "legend": fig.legend,
        "axes": fig.axes,
        "metadata": fig.metadata,
    }
