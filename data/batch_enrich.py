"""
Batch enrich the top 60 CAR-T targets with real API data.
This pre-warms the cache so scores are real on first visit.
Takes ~3-5 minutes due to API rate limiting.
"""
import sys, time
sys.path.insert(0, r"C:\Users\dhruv\CARVanta")

from features.tumor_features import generate_features
from scoring.cvs_engine import compute_cvs

# Top 60 targets: FDA-approved + all known clinical trial targets + key oncogenes
PRIORITY_TARGETS = [
    # FDA-approved CAR-T targets
    "CD19", "BCMA",
    # Late-stage clinical trial targets
    "CD22", "CD20", "GPRC5D", "HER2", "GD2", "EGFR", "MSLN", "CLDN18",
    "FLT3", "CD33", "CD123", "GPC3", "ROR1", "DLL3", "CD70", "B7H3",
    "PSMA", "MUC1", "EPCAM", "FOLR1", "IL13RA2", "SLAMF7", "CD38",
    # Important oncogenes/tumor suppressors (should score low — not surface)
    "TP53", "KRAS", "BRAF", "PTEN", "MYC",
    # Additional promising targets in early trials
    "CD30", "CD7", "CD5", "NKG2D", "TROP2", "NECTIN4", "CD44",
    "CEACAM5", "TIM3", "LAG3", "PD1", "PDL1", "CTLA4",
    # Hematologic targets
    "CD138", "CD37", "CD4", "CD8A", "CLEC12A", "CLL1",
    # Solid tumor targets
    "CA9", "VEGFR2", "FGFR2", "MET", "ALK", "ROS1", "NTRK1",
    "AXL", "TYRO3", "MERTK",
]

print("Batch enriching %d targets with real data..." % len(PRIORITY_TARGETS))
print("Each target queries GTEx + UniProt + ClinicalTrials.gov")
print()

results = []
for i, gene in enumerate(PRIORITY_TARGETS, 1):
    t0 = time.time()
    features = generate_features(gene)
    cvs = compute_cvs(features)
    elapsed = time.time() - t0

    apis = features.get("data_provenance", {}).get("apis_used", [])
    membrane = features.get("is_membrane_protein", "?")
    sa = features.get("surface_accessibility", 0)

    results.append((gene, cvs["CVS"], cvs["tier"], apis, membrane, sa))

    status = ", ".join(apis) if apis else "base only"
    print("[%2d/%d] %-12s  CVS=%.3f  %-28s  membrane=%-5s  (%s) %.1fs" % (
        i, len(PRIORITY_TARGETS), gene, cvs["CVS"], cvs["tier"],
        str(membrane), status, elapsed
    ))

    # Small delay to be respectful to APIs
    if elapsed < 0.5 and i < len(PRIORITY_TARGETS):
        time.sleep(0.3)

print()
print("=" * 70)
print("DONE — %d targets enriched and cached" % len(results))

# Show top 10
results.sort(key=lambda x: x[1], reverse=True)
print("\nTop 10 by CVS:")
for i, (gene, cvs, tier, apis, mem, sa) in enumerate(results[:10], 1):
    fda = " [FDA]" if gene in ("CD19", "BCMA") else ""
    print("  %2d. %-12s  %.3f  %s%s" % (i, gene, cvs, tier, fda))

# Show bottom 5
print("\nBottom 5 (should be intracellular/poor targets):")
for gene, cvs, tier, apis, mem, sa in results[-5:]:
    print("  %-12s  %.3f  %s  membrane=%s  surface=%.2f" % (gene, cvs, tier, mem, sa))
