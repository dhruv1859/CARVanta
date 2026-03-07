"""Verify CARVanta v4 adaptive rankings produce different results per cancer type."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from features.tumor_features import precompute_scores_for_cancer, precompute_all_scores

print("=" * 65)
print("  CARVanta v4 — Ranking Verification")
print("=" * 65)

cancers = ["Leukemia", "Melanoma", "Glioblastoma", "Breast Cancer", "Myeloma"]

for cancer in cancers:
    results = precompute_scores_for_cancer(cancer)[:5]
    print(f"\n  === {cancer.upper()} TOP 5 ===")
    for r in results:
        print(f"    {r['antigen']:>12s}  Score={r['CVS']:.3f}  ML={r['ml_score']:.3f}  {r['tier']}")

print(f"\n  === GLOBAL TOP 5 ===")
global_results = precompute_all_scores()[:5]
for r in global_results:
    print(f"    {r['antigen']:>12s}  Score={r['CVS']:.3f}  ML={r['ml_score']:.3f}  {r['tier']}")

top_per_cancer = {}
for c in cancers:
    top_per_cancer[c] = precompute_scores_for_cancer(c)[0]["antigen"]

print(f"\n  --- Diversity Check ---")
for c, top in top_per_cancer.items():
    print(f"    {c:>20s}  #1 = {top}")

unique_tops = len(set(top_per_cancer.values()))
print(f"\n  Unique top-1 antigens: {unique_tops}/{len(cancers)}")
if unique_tops > 1:
    print("  PASS: Different cancer types produce different top targets!")
else:
    print("  FAIL: Same antigen is #1 for all cancer types")

print("\n" + "=" * 65)
