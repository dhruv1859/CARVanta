"""Quick verification test for all CARVanta API endpoints after fixes."""
import requests
import json
import sys

BASE = "http://127.0.0.1:8001"

tests = [
    ("GET",  "/health",                   None),
    ("GET",  "/rank?top_n=3",             None),
    ("GET",  "/api/cancer-types",         None),
    ("POST", "/api/multi-target",         {"antigens": ["CD19", "CD22"]}),
    ("POST", "/api/stratify",             {"antigen_name": "CD19", "cancer_type": "Leukemia"}),
    ("POST", "/api/query",                {"query": "safe targets for leukemia"}),
    ("GET",  "/api/clinical-trials/CD19", None),
    ("GET",  "/api/clinical-trials/HER2", None),
    ("POST", "/score",                    {"antigen_name": "CD19"}),
    ("GET",  "/antigens?search=&limit=10", None),
]

print("=" * 60)
print("  CARVanta API Endpoint Verification")
print("=" * 60)

errors = 0
for method, path, payload in tests:
    try:
        r = requests.request(method, BASE + path, json=payload, timeout=30)
        status = "OK" if r.status_code == 200 else f"ERR {r.status_code}"
        if r.status_code != 200:
            errors += 1
        print(f"  {status:14s} {method:5s} {path}")
    except Exception as e:
        errors += 1
        print(f"  {'TIMEOUT':14s} {method:5s} {path} -> {e}")

# Detailed checks
print()
print("-" * 60)
print("  Detailed Verification")
print("-" * 60)

# Check antigen ordering
r = requests.get(f"{BASE}/antigens?search=&limit=10", timeout=10)
antigens = r.json().get("antigens", [])
print(f"  First 5 antigens: {antigens[:5]}")
if antigens and antigens[0] == "CD19":
    print("  >>> Antigen ordering: PASS (CD19 first)")
else:
    print("  >>> Antigen ordering: FAIL")
    errors += 1

# Check score endpoint has new fields
r = requests.post(f"{BASE}/score", json={"antigen_name": "CD19"}, timeout=30)
data = r.json()
has_radar = "radar_chart_data" in data
has_safety = "safety_profile" in data
has_safety_insight = "safety_insight" in data
print(f"  Radar chart data: {'PASS' if has_radar else 'FAIL'}")
print(f"  Safety profile:   {'PASS' if has_safety else 'FAIL'}")
print(f"  Safety insight:   {'PASS' if has_safety_insight else 'FAIL'}")
if not (has_radar and has_safety and has_safety_insight):
    errors += 1

# Check AI insight is NOT generic
insight = data.get("ai_insight", "")
if "CD19" in insight:
    print(f"  AI insight mentions antigen name: PASS")
else:
    print(f"  AI insight antigen-specific: FAIL (no antigen name in insight)")
    errors += 1

# Check synergy has AI insight + correct keys
r = requests.post(f"{BASE}/api/multi-target", json={"antigens": ["CD19", "CD22"]}, timeout=30)
syn = r.json()
has_comp = syn.get("complementarity_score", 0) > 0
has_cov = syn.get("coverage_score", 0) > 0
has_agg = syn.get("aggregate_safety", 0) > 0
has_syn_ai = bool(syn.get("ai_insight", ""))
has_per = len(syn.get("per_antigen", [])) > 0
print(f"  Synergy complementarity: {'PASS' if has_comp else 'FAIL'} ({syn.get('complementarity_score', 0)})")
print(f"  Synergy coverage:        {'PASS' if has_cov else 'FAIL'} ({syn.get('coverage_score', 0)})")
print(f"  Synergy agg safety:      {'PASS' if has_agg else 'FAIL'} ({syn.get('aggregate_safety', 0)})")
print(f"  Synergy AI insight:      {'PASS' if has_syn_ai else 'FAIL'}")
print(f"  Synergy per-antigen:     {'PASS' if has_per else 'FAIL'}")
if not all([has_comp, has_cov, has_agg, has_syn_ai, has_per]):
    errors += 1

# Check stratification has correct keys
r = requests.post(f"{BASE}/api/stratify", json={"antigen_name": "CD19", "cancer_type": "Leukemia"}, timeout=30)
strat = r.json()
has_nsub = strat.get("n_subgroups", 0) > 0
has_elig = strat.get("overall_eligibility", "") != "" and strat.get("overall_eligibility") != "N/A"
has_subgroups = len(strat.get("subgroups", [])) > 0
has_strat_ai = bool(strat.get("ai_insight", ""))
print(f"  Strat subgroups:    {'PASS' if has_nsub else 'FAIL'} ({strat.get('n_subgroups', 0)})")
print(f"  Strat eligibility:  {'PASS' if has_elig else 'FAIL'} ({strat.get('overall_eligibility', '')})")
print(f"  Strat subgp list:   {'PASS' if has_subgroups else 'FAIL'}")
print(f"  Strat AI insight:   {'PASS' if has_strat_ai else 'FAIL'}")
if not all([has_nsub, has_elig, has_subgroups, has_strat_ai]):
    errors += 1

# Check clinical trials differ per antigen
r1 = requests.get(f"{BASE}/api/clinical-trials/CD19", timeout=30)
r2 = requests.get(f"{BASE}/api/clinical-trials/HER2", timeout=30)
ct1 = r1.json()
ct2 = r2.json()
trials_differ = ct1.get("total_trials", 0) != ct2.get("total_trials", 0)
print(f"  Clinical trials differ: {'PASS' if trials_differ else 'FAIL'} (CD19={ct1.get('total_trials')}, HER2={ct2.get('total_trials')})")
if not trials_differ:
    errors += 1

print()
print("=" * 60)
if errors == 0:
    print("  ALL TESTS PASSED!")
else:
    print(f"  {errors} CHECK(S) FAILED")
print("=" * 60)

sys.exit(0 if errors == 0 else 1)
