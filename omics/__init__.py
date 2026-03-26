"""
CARVanta – Multi-Omics Intelligence Engine
=============================================
Package providing multi-layered omics analysis for CAR-T target evaluation.

Layers:
  1. Transcriptomics — RNA-seq expression analysis
  2. Proteomics — Protein abundance & surface localization
  3. Epigenomics — Methylation & histone modification
  4. Metabolomics — Metabolic pathway impact
  5. Single-cell — Expression heterogeneity

Integration:
  - Multi-omics fusion via weighted composite scoring
  - Mutation impact analysis from COSMIC/ClinVar
"""

from omics.transcriptomics import TranscriptomicsAnalyzer
from omics.proteomics import ProteomicsAnalyzer
from omics.epigenomics import EpigenomicsAnalyzer
from omics.metabolomics import MetabolomicsAnalyzer
from omics.single_cell import SingleCellAnalyzer
from omics.integrator import MultiOmicsIntegrator
from omics.mutation_analyzer import MutationAnalyzer

__all__ = [
    "TranscriptomicsAnalyzer",
    "ProteomicsAnalyzer",
    "EpigenomicsAnalyzer",
    "MetabolomicsAnalyzer",
    "SingleCellAnalyzer",
    "MultiOmicsIntegrator",
    "MutationAnalyzer",
]
