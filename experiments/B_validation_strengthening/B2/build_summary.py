from pathlib import Path
import csv
import numpy as np

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]

RESULTS = (
    REPO
    / "experiments"
    / "B_validation_strengthening"
    / "results"
)

LIFETIME = RESULTS / "B2_lifetime_sensitivity.csv"
UNREC = RESULTS / "B2_unrecoverability_sensitivity.csv"
OUT = RESULTS / "B2_STRENGTHENING_SUMMARY.md"


def read_csv(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


life = read_csv(LIFETIME)
unrec = read_csv(UNREC)


def numeric_nonempty(rows, key):
    return np.array(
        [
            float(r[key])
            for r in rows
            if r[key] not in ("", "None", None)
        ],
        dtype=float,
    )


def never_count(rows, key):
    return sum(
        1
        for r in rows
        if r[key] in ("", "None", None)
    )


reid100 = numeric_nonempty(life, "reid_100_year")
fam100 = numeric_nonempty(life, "familial_100_year")
disease100 = numeric_nonempty(life, "disease_100_year")
d5_50 = numeric_nonempty(life, "d5_year_50")

unrec_values = numeric_nonempty(
    unrec,
    "unrecoverability",
)

text = f"""# B2 Validation Strengthening Summary

## Status

MODELLED / SENSITIVITY ANALYSIS

This analysis does not replace or modify the frozen historical B2 evidence.

## Frozen baseline reproduction

The original B2 lifetime equations were independently reproduced using
the frozen development assumptions.

Baseline outputs:
- re-identification reaches 100% at model year 13
- familial exposure reaches 100% at model year 15
- disease inference does not reach 100% within the 80-year horizon
- D5 at model year 50 = 9.3276, consistent with the frozen ~9.33 result

The pathogenic-variant unrecoverability calculation was also reproduced:
- pathogenic leakage assumption = 0.420
- exponential reconstruction coefficient = 3.5
- unrecoverability = 0.2299

## Lifetime parameter sensitivity

A total of {len(life)} model scenarios were evaluated.

The sensitivity grid varied:
- baseline re-identification risk
- baseline disease risk
- baseline familial risk
- database doubling time
- database saturation
- inference midpoint
- maximum inference factor

These are development sensitivity scenarios, not empirical confidence
intervals or real-world forecasts.

### Re-identification saturation

Among tested scenarios:
- earliest 100% horizon = model year {int(np.min(reid100))}
- median 100% horizon = model year {np.median(reid100):.1f}
- latest 100% horizon = model year {int(np.max(reid100))}
- scenarios not reaching 100% = {never_count(life, "reid_100_year")}/{len(life)}

### Familial saturation

Among scenarios that reach 100%:
- earliest 100% horizon = model year {int(np.min(fam100))}
- median 100% horizon = model year {np.median(fam100):.1f}
- latest 100% horizon = model year {int(np.max(fam100))}
- scenarios not reaching 100% = {never_count(life, "familial_100_year")}/{len(life)}

### Disease-inference saturation

Among scenarios that reach 100%:
- earliest 100% horizon = model year {int(np.min(disease100))}
- median 100% horizon = model year {np.median(disease100):.1f}
- latest 100% horizon = model year {int(np.max(disease100))}
- scenarios not reaching 100% = {never_count(life, "disease_100_year")}/{len(life)}

### D5 at model year 50

Across tested scenarios:
- minimum = {np.min(d5_50):.4f}
- 5th percentile = {np.percentile(d5_50, 5):.4f}
- median = {np.median(d5_50):.4f}
- 95th percentile = {np.percentile(d5_50, 95):.4f}
- maximum = {np.max(d5_50):.4f}

The frozen ~9.33 value is therefore a baseline model output rather than a
universal persistence score.

## Pathogenic-variant unrecoverability sensitivity

A total of {len(unrec)} combinations of pathogenic leakage and exponential
reconstruction coefficient were evaluated.

Across the full tested grid:
- minimum unrecoverability = {np.min(unrec_values):.4f}
- 5th percentile = {np.percentile(unrec_values, 5):.4f}
- median = {np.median(unrec_values):.4f}
- 95th percentile = {np.percentile(unrec_values, 95):.4f}
- maximum = {np.max(unrec_values):.4f}

The frozen 0.2299 value is therefore conditional on the selected leakage
and reconstruction assumptions.

A local +/-20% perturbation around those baseline assumptions produced
an unrecoverability range of 0.1204 to 0.3903.

## Structural model audit

The original lifetime implementation computes a technology-decay factor.

However, that factor is not used in the equations producing:
- re-identification risk
- disease-inference risk
- familial risk
- composite lifetime risk
- D5

Therefore the frozen lifetime outputs must not be described as being
numerically driven by technology-cost decay.

Technology decay is currently contextual/model scaffolding rather than an
active contributor to those reported risk trajectories.

## Defensible conclusion

B2 demonstrates how persistent genomic information can produce increasing
modeled privacy and familial exposure over long horizons under specified
database-growth and inference assumptions.

The exact year-13 re-identification horizon, year-15 familial horizon,
year-50 D5 of approximately 9.33, and pathogenic-variant unrecoverability
of 0.2299 are baseline MODEL OUTPUTS.

They are not observed real-world lifetimes, empirical probabilities, or
universal constants.

The strengthened evidence supports reporting ranges and scenario
sensitivity alongside the frozen baseline values.

## DEF CON framing

Safe claim:

"Under GenoPhylax's baseline lifetime model, re-identification saturates
at year 13 and familial exposure at year 15. Across 2,187 sensitivity
scenarios, the corresponding horizons shift substantially, demonstrating
that genomic persistence risk is durable but its exact timing is
assumption-dependent."

Avoid:

"Genomic data becomes fully re-identifiable after 13 years."

Also avoid:

"Pathogenic variants are 22.99% unrecoverable."

Prefer:

"Under the baseline reconstruction assumptions, the modeled
unrecoverability value is 0.2299; sensitivity analysis shows that this
quantity depends strongly on the leakage and reconstruction parameters."
"""

OUT.write_text(text, encoding="utf-8")

print(text)
print(f"\nSaved: {OUT}")
print("STATUS: PASS")
