import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "results" / "GRI_v2_candidate_dimensions.csv"
OUTPUT = ROOT / "validation" / "ceiling_diagnostic.txt"

scores = []
methods = []
dimensions = []

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        raw = row["candidate_score"].strip()

        if not raw:
            continue

        value = float(raw)

        scores.append(value)
        methods.append(row["normalization_method"])
        dimensions.append(row["dimension"])


n = len(scores)
ceiling = sum(v == 1.0 for v in scores)
high = sum(v >= 0.9 for v in scores)

binary_ceiling = 0

with INPUT.open("r", encoding="utf-8", newline="") as f:
    for row in csv.DictReader(f):

        raw = row["candidate_score"].strip()

        if (
            raw
            and float(raw) == 1.0
            and row["normalization_method"]
            == "BINARY_DEMONSTRATION"
        ):
            binary_ceiling += 1


lines = [
    "GRI v2 CEILING DIAGNOSTIC",
    "=" * 45,
    f"Scored dimension observations: {n}",
    f"Exact 1.0 observations: {ceiling}",
    f"Exact ceiling fraction: {ceiling / n:.4f}",
    f">=0.9 observations: {high}",
    f">=0.9 fraction: {high / n:.4f}",
    f"Binary-demonstration ceiling observations: {binary_ceiling}",
    "",
    "Scores by dimension:"
]

for dimension, count in sorted(Counter(dimensions).items()):
    lines.append(f" - {dimension}: {count}")

lines += [
    "",
    "Interpretation:",
    "A high ceiling fraction indicates limited discrimination among severe cases.",
    "Binary demonstration establishes capability but does not quantify magnitude.",
    "Binary demonstration should therefore not automatically be treated as a calibrated maximum-risk observation."
]

text = "\n".join(lines)

OUTPUT.write_text(text, encoding="utf-8")

print(text)
print()
print(f"Output: {OUTPUT}")
print("STATUS: PASS")
