import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "validation" / "known_groups_posthoc.json"
SCORES = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "validation" / "known_groups_posthoc_results.csv"

with SPEC.open("r", encoding="utf-8") as f:
    spec = json.load(f)

scores = {}

with SCORES.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):
        if (
            row["v2_score_status"] == "CANDIDATE"
            and row["candidate_score"].strip()
        ):
            scores[(row["case_id"], row["dimension"])] = float(
                row["candidate_score"]
            )

results = []

for comp in spec["comparisons"]:
    lower_key = (comp["lower_case"], comp["dimension"])
    higher_key = (comp["higher_case"], comp["dimension"])

    lower = scores.get(lower_key)
    higher = scores.get(higher_key)

    if lower is None or higher is None:
        passed = False
        status = "UNRESOLVED"
    else:
        passed = lower < higher
        status = "PASS" if passed else "FAIL"

    results.append({
        "comparison_id": comp["comparison_id"],
        "lower_case": comp["lower_case"],
        "higher_case": comp["higher_case"],
        "dimension": comp["dimension"],
        "lower_score": "" if lower is None else f"{lower:.10f}",
        "higher_score": "" if higher is None else f"{higher:.10f}",
        "expected_relation": comp["expected_relation"],
        "status": status,
        "validation_class": "POST_HOC_DIRECTIONAL_SANITY_CHECK"
    })

with OUTPUT.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print("GRI v2 POST-HOC KNOWN-GROUPS SANITY CHECK")
print("=" * 76)
print("IMPORTANT: exploratory/post-hoc; not independent construct validation.")
print()

for row in results:
    print(
        f'{row["comparison_id"]}: '
        f'{row["lower_case"]}={row["lower_score"] or "NA"} '
        f'< {row["higher_case"]}={row["higher_score"] or "NA"} '
        f'-> {row["status"]}'
    )

print()
print(f"Comparisons: {len(results)}")
print(f"Passed: {sum(r['status'] == 'PASS' for r in results)}")
print(f"Output: {OUTPUT}")
