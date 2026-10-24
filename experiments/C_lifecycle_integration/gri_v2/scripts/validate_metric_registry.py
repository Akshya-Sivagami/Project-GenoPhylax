import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
REGISTRY = ROOT / "spec" / "GRI_v2_metric_registry.csv"

errors = []
warnings = []

with REGISTRY.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

registry = {}

for row in rows:
    metric = row["raw_metric"]

    if metric in registry:
        errors.append(f"Duplicate metric registry entry: {metric}")
    else:
        registry[metric] = row

used = {}

for path in sorted(CASES.glob("*.json")):
    with path.open("r", encoding="utf-8") as f:
        case = json.load(f)

    for record in case["dimensions"]:

        if record.get("status") != "APPLICABLE":
            continue

        metric = record["raw_metric"]
        dimension = record["dimension"]

        if metric not in registry:
            errors.append(
                f'{case["case_id"]}: unregistered metric {metric}'
            )
            continue

        registered_dimension = registry[metric]["dimension"]

        if registered_dimension != dimension:
            errors.append(
                f'{case["case_id"]}: {metric} used as {dimension} '
                f'but registered as {registered_dimension}'
            )

        used.setdefault(metric, set()).add(case["case_id"])

for metric in registry:
    if metric not in used:
        warnings.append(
            f"Registered metric currently unused: {metric}"
        )

print("GRI v2 METRIC REGISTRY VALIDATION")
print("=" * 45)
print(f"Registered metrics: {len(registry)}")
print(f"Used metrics: {len(used)}")
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")

if warnings:
    print("\nWARNINGS")
    for item in warnings:
        print(" -", item)

if errors:
    print("\nERRORS")
    for item in errors:
        print(" -", item)

    print("\nSTATUS: FAIL")
    sys.exit(1)

print("\nSTATUS: PASS")
