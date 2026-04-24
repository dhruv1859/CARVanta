"""
CARVanta – Multi-Omics API Router
====================================
FastAPI router exposing the Multi-Omics Intelligence Engine endpoints.
"""

from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from typing import Optional, List
import os

from omics.integrator import MultiOmicsIntegrator

router = APIRouter(prefix="/api/v5/omics", tags=["Multi-Omics Intelligence"])

# Shared integrator instance
_integrator = MultiOmicsIntegrator()


@router.get("/analyze/{gene}")
def analyze_gene(
    gene: str,
    cancer_type: Optional[str] = Query(None, description="TCGA cancer type code (e.g., BRCA, LUAD)"),
):
    """
    Full multi-omics integrated analysis for a single gene.
    Returns scores from all 5 omics layers + mutation analysis,
    the integrated MOTS score, tier classification, and recommendations.
    """
    try:
        result = _integrator.analyze(gene, cancer_type)
        return result
    except Exception as e:
        return {"error": str(e), "gene": gene}


@router.get("/compare")
def compare_genes(
    genes: str = Query(..., description="Comma-separated gene symbols (e.g., CD19,CD22,BCMA)"),
    cancer_type: Optional[str] = Query(None, description="TCGA cancer type code"),
):
    """
    Compare multiple genes using multi-omics integration.
    Returns ranked comparison with MOTS scores.
    """
    gene_list = [g.strip() for g in genes.split(",") if g.strip()]
    if not gene_list:
        return {"error": "No genes provided"}
    if len(gene_list) > 10:
        return {"error": "Maximum 10 genes allowed per comparison"}

    try:
        result = _integrator.analyze_multiple(gene_list, cancer_type)
        return result
    except Exception as e:
        return {"error": str(e)}


@router.get("/layer/{layer}/{gene}")
def get_layer_detail(
    layer: str,
    gene: str,
    cancer_type: Optional[str] = Query(None),
):
    """
    Get detailed results from a specific omics layer.
    Layers: transcriptomics, proteomics, epigenomics, metabolomics, single_cell, mutations
    """
    gene = gene.upper().strip()
    layer = layer.lower().strip()

    try:
        if layer == "transcriptomics":
            return _integrator.transcriptomics.analyze(gene, cancer_type)
        elif layer == "proteomics":
            return _integrator.proteomics.analyze(gene)
        elif layer == "epigenomics":
            return _integrator.epigenomics.analyze(gene)
        elif layer == "metabolomics":
            return _integrator.metabolomics.analyze(gene)
        elif layer == "single_cell":
            return _integrator.single_cell.analyze(gene, cancer_type)
        elif layer == "mutations":
            return _integrator.mutations.analyze(gene)
        else:
            return {"error": f"Unknown layer: {layer}. Valid: transcriptomics, proteomics, epigenomics, metabolomics, single_cell, mutations"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/transcriptomics/heatmap")
def get_expression_heatmap(
    genes: str = Query(..., description="Comma-separated gene symbols"),
):
    """Get expression heatmap data for multiple genes across TCGA types."""
    gene_list = [g.strip() for g in genes.split(",") if g.strip()]
    if not gene_list:
        return {"error": "No genes provided"}

    try:
        return _integrator.transcriptomics.get_expression_heatmap(gene_list)
    except Exception as e:
        return {"error": str(e)}


@router.get("/transcriptomics/de/{gene}/{cancer_type}")
def get_differential_expression(gene: str, cancer_type: str):
    """Get detailed differential expression for a specific gene-cancer pair."""
    try:
        return _integrator.transcriptomics.get_differential_expression(gene, cancer_type)
    except Exception as e:
        return {"error": str(e)}


@router.get("/weights")
def get_weights():
    """Get current layer weights used for MOTS computation."""
    return {
        "weights": _integrator.weights,
        "description": {
            "transcriptomics": "RNA-seq expression analysis weight",
            "proteomics": "Protein surface localization weight",
            "epigenomics": "Epigenetic stability weight",
            "metabolomics": "Metabolic pathway impact weight",
            "single_cell": "Single-cell heterogeneity weight",
            "mutations": "Mutation landscape weight",
        },
    }
