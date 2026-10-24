import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "gri_cli.py"
EXAMPLES = ROOT / "cli_examples"

errors = []


def run_json(filename):
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "score",
            str(EXAMPLES / filename),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        errors.append(
            f"{filename}: CLI exited {result.returncode}: "
            f"{result.stderr.strip()}"
        )
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        errors.append(
            f"{filename}: invalid JSON output: {exc}"
        )
        return None


def assert_close(label, actual, expected, tolerance=5e-10):
    if actual is None:
        errors.append(
            f"{label}: expected {expected}, got None"
        )
        return

    if abs(float(actual) - float(expected)) > tolerance:
        errors.append(
            f"{label}: expected {expected:.10f}, "
            f"got {float(actual):.10f}"
        )


# ------------------------------------------------------------
# F11
# ------------------------------------------------------------

f11 = run_json("F11.json")

if f11:
    assert_close(
        "F11 composite",
        f11["summary"]["candidate_composite"],
        1.0,
    )

    if f11["summary"]["composite_status"] != "CANDIDATE":
        errors.append("F11 composite should be CANDIDATE")

    assert_close(
        "F11 coverage",
        f11["summary"]["coverage"],
        1.0,
    )

    if f11["summary"]["breadth_count"] != 2:
        errors.append("F11 breadth should be 2")

    scores = {
        row["dimension"]: row["candidate_score"]
        for row in f11["dimensions"]
    }

    assert_close("F11 D2", scores.get("D2"), 1.0)
    assert_close("F11 D7", scores.get("D7"), 1.0)


# ------------------------------------------------------------
# Privacy
# ------------------------------------------------------------

privacy = run_json("Privacy.json")

if privacy:
    assert_close(
        "Privacy composite",
        privacy["summary"]["candidate_composite"],
        0.9351285176,
    )

    if (
        privacy["summary"]["composite_status"]
        != "CANDIDATE"
    ):
        errors.append(
            "Privacy composite should be CANDIDATE"
        )

    assert_close(
        "Privacy coverage",
        privacy["summary"]["coverage"],
        1.0,
    )

    if privacy["summary"]["breadth_count"] != 4:
        errors.append("Privacy breadth should be 4")

    scores = {
        row["dimension"]: row["candidate_score"]
        for row in privacy["dimensions"]
    }

    assert_close("Privacy D1", scores.get("D1"), 1.0)
    assert_close("Privacy D3", scores.get("D3"), 1.0)
    assert_close(
        "Privacy D5",
        scores.get("D5"),
        0.8515500000,
    )
    assert_close(
        "Privacy D6",
        scores.get("D6"),
        0.8889640704,
    )

    interpretation = privacy["interpretation"]

    forbidden_true = [
        "probability_of_harm",
        "probability_of_attack_success",
        "clinical_probability",
        "population_prevalence",
        "d6_anchor_universal",
    ]

    for key in forbidden_true:
        if interpretation.get(key) is not False:
            errors.append(
                f"Privacy safeguard {key} must be false"
            )


# ------------------------------------------------------------
# Binary evidence withholding
# ------------------------------------------------------------

binary = run_json("BinaryWithheld.json")

if binary:
    summary = binary["summary"]

    if summary["candidate_composite"] is not None:
        errors.append(
            "Binary-only case must not receive composite"
        )

    if summary["composite_status"] != "WITHHELD":
        errors.append(
            "Binary-only composite must be WITHHELD"
        )

    assert_close(
        "Binary coverage",
        summary["coverage"],
        0.0,
    )

    if (
        summary["positive_magnitude_unresolved"]
        != ["D1"]
    ):
        errors.append(
            "Binary D1 must be positive-magnitude unresolved"
        )

    row = binary["dimensions"][0]

    if row["candidate_score"] is not None:
        errors.append(
            "Binary demonstration must not receive point score"
        )

    if (
        row["v2_score_status"]
        != "POSITIVE_MAGNITUDE_UNRESOLVED"
    ):
        errors.append(
            "Binary demonstration status incorrect"
        )


# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("GRI v2 CLI TEST SUITE")
print("=" * 60)
print("Headline cases tested: 2")
print("Withholding cases tested: 1")
print(f"Errors: {len(errors)}")

if errors:
    print()
    print("ERRORS")

    for error in errors:
        print(" -", error)

    print()
    print("STATUS: FAIL")
    sys.exit(1)

print()
print("F11 reproduction: PASS")
print("Privacy reproduction: PASS")
print("Binary-evidence withholding: PASS")
print("Machine-readable JSON: PASS")
print("Interpretation safeguards: PASS")
print()
print("STATUS: PASS")
