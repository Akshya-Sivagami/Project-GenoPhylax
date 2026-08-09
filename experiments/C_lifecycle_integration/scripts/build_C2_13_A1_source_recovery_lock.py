#!/usr/bin/env python3

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

REGISTRY = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "C2_cross_module_evidence_registry.tsv"
)

TIER_FILE = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "C2_evidence_tier_assignments.tsv"
)

LOCK_FILE = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "C2_11_partial_lock_scope.tsv"
)

UNRESOLVED = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "C2_unresolved_evidence_sources.tsv"
)

SUMMARY = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "source_review/C2_13_A1_source_recovery_summary.txt"
)

AUDIT = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "source_review/C2_13_A1_source_recovery_audit.tsv"
)

VALIDATION = ROOT / (
    "experiments/C_lifecycle_integration/evidence_registry/"
    "C2_13_A1_source_recovery_validation.txt"
)

MARKER = ROOT / (
    "experiments/C_lifecycle_integration/markers/"
    "C2_13_A1_SOURCE_RECOVERY.COMPLETE"
)

A1_IDS = ["A1_E01", "A1_E02", "A1_E03", "A1_E04"]

E2_LABEL = "Controlled direct empirical case study"

RATIONALES = {
    "A1_E01": (
        "Direct controlled BWA/ASAN fuzzing evidence from the canonical "
        "preserved campaign; one principal software version/configuration "
        "without meaningful independent replication."
    ),
    "A1_E02": (
        "Two directly observed ASAN-confirmed source-level root causes "
        "within one BWA software audit; distinct root causes do not by "
        "themselves constitute independent replication."
    ),
    "A1_E03": (
        "Direct ASAN-confirmed ksw_extend2 out-of-bounds-read finding in "
        "the recovered controlled BWA audit; not independently replicated."
    ),
    "A1_E04": (
        "Direct ASAN-confirmed mem_aln2sam out-of-bounds-read finding in "
        "the recovered controlled BWA audit; not independently replicated."
    ),
}


def read_tsv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    return fields, rows


def write_tsv(path: Path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    required = [
        REGISTRY,
        TIER_FILE,
        LOCK_FILE,
        UNRESOLVED,
    ]

    for path in required:
        if not path.is_file():
            raise SystemExit(f"ERROR: required file missing: {path}")

    registry_fields, registry_rows = read_tsv(REGISTRY)
    tier_fields, tier_rows = read_tsv(TIER_FILE)
    lock_fields, lock_rows = read_tsv(LOCK_FILE)

    registry = {
        row["evidence_id"]: row
        for row in registry_rows
    }

    tier = {
        row["evidence_id"]: row
        for row in tier_rows
    }

    lock = {
        row["evidence_id"]: row
        for row in lock_rows
    }

    errors = []
    audit_rows = []

    # ---------------------------------------------------------
    # Validate recovered registry state first.
    # ---------------------------------------------------------

    for eid in A1_IDS:
        if eid not in registry:
            errors.append(f"{eid}: missing from C2 registry")
            continue

        if eid not in tier:
            errors.append(f"{eid}: missing from tier table")
            continue

        if eid not in lock:
            errors.append(f"{eid}: missing from lock table")
            continue

        reg = registry[eid]

        if reg.get("source_resolution_status") != "STRONG_CANDIDATE":
            errors.append(
                f"{eid}: expected STRONG_CANDIDATE in regenerated registry, "
                f"found {reg.get('source_resolution_status')!r}"
            )

        source = reg.get("primary_source_file", "")

        if not source.startswith(
            "experiments/A1_memory_audit/provenance/"
        ):
            errors.append(
                f"{eid}: primary source is not recovered A1 provenance: "
                f"{source}"
            )

    # A1 must no longer occur in unresolved registry.
    unresolved_text = UNRESOLVED.read_text(encoding="utf-8")

    for eid in A1_IDS:
        if eid in unresolved_text:
            errors.append(
                f"{eid}: still present in unresolved-source table"
            )

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        raise SystemExit(1)

    # ---------------------------------------------------------
    # Upgrade tier assignments.
    # ---------------------------------------------------------

    for row in tier_rows:
        eid = row["evidence_id"]

        if eid not in A1_IDS:
            continue

        before_source = row.get("source_resolution_status", "")
        before_tier = row.get("evidence_tier", "")
        before_status = row.get("tier_status", "")

        row["source_resolution_status"] = "VERIFIED_EXISTING_SOURCE"
        row["evidence_tier"] = "E2"
        row["tier_label"] = E2_LABEL
        row["tier_status"] = "ASSIGNED"
        row["tier_rationale"] = RATIONALES[eid]

        audit_rows.append(
            {
                "evidence_id": eid,
                "old_source_resolution_status": before_source,
                "new_source_resolution_status": row[
                    "source_resolution_status"
                ],
                "old_evidence_tier": before_tier,
                "new_evidence_tier": row["evidence_tier"],
                "old_tier_status": before_status,
                "new_tier_status": row["tier_status"],
                "c3_eligible": "NO",
                "scope_status": "SOURCE_LOCKED_STANDALONE_NON_GRI",
            }
        )

    # ---------------------------------------------------------
    # Upgrade the existing C2.11 lock table.
    #
    # Important:
    # A1 is now evidence-locked, but remains outside the existing
    # C3/GRI worked cases by explicit methodological scope.
    # ---------------------------------------------------------

    for row in lock_rows:
        eid = row["evidence_id"]

        if eid not in A1_IDS:
            continue

        row["source_resolution_status"] = "VERIFIED_EXISTING_SOURCE"
        row["evidence_tier"] = "E2"
        row["tier_status"] = "ASSIGNED"
        row["c3_eligible"] = "NO"
        row[
            "partial_lock_status"
        ] = "SOURCE_LOCKED_STANDALONE_NON_GRI"

        row["reason"] = (
            "Authoritative A1 provenance recovered and E2 tier assigned; "
            "A1 remains outside the already-validated F11/Privacy C3 and "
            "Base GRI worked cases by explicit scope decision."
        )

    write_tsv(TIER_FILE, tier_fields, tier_rows)
    write_tsv(LOCK_FILE, lock_fields, lock_rows)

    # ---------------------------------------------------------
    # Write A1 recovery audit.
    # ---------------------------------------------------------

    audit_fields = [
        "evidence_id",
        "old_source_resolution_status",
        "new_source_resolution_status",
        "old_evidence_tier",
        "new_evidence_tier",
        "old_tier_status",
        "new_tier_status",
        "c3_eligible",
        "scope_status",
    ]

    write_tsv(AUDIT, audit_fields, audit_rows)

    # ---------------------------------------------------------
    # Validate final tier/lock state.
    # ---------------------------------------------------------

    _, tier_after = read_tsv(TIER_FILE)
    _, lock_after = read_tsv(LOCK_FILE)

    tier_map = {
        row["evidence_id"]: row
        for row in tier_after
    }

    lock_map = {
        row["evidence_id"]: row
        for row in lock_after
    }

    validation_errors = []

    for eid in A1_IDS:
        t = tier_map[eid]
        l = lock_map[eid]

        expected_tier = {
            "source_resolution_status": "VERIFIED_EXISTING_SOURCE",
            "evidence_tier": "E2",
            "tier_status": "ASSIGNED",
        }

        for key, value in expected_tier.items():
            if t.get(key) != value:
                validation_errors.append(
                    f"{eid}: tier {key} expected {value}, "
                    f"found {t.get(key)}"
                )

        if l.get("source_resolution_status") != "VERIFIED_EXISTING_SOURCE":
            validation_errors.append(
                f"{eid}: lock source status incorrect"
            )

        if l.get("evidence_tier") != "E2":
            validation_errors.append(
                f"{eid}: lock tier is not E2"
            )

        if l.get("tier_status") != "ASSIGNED":
            validation_errors.append(
                f"{eid}: lock tier status is not ASSIGNED"
            )

        if l.get("c3_eligible") != "NO":
            validation_errors.append(
                f"{eid}: A1 must remain non-C3 eligible"
            )

        if (
            l.get("partial_lock_status")
            != "SOURCE_LOCKED_STANDALONE_NON_GRI"
        ):
            validation_errors.append(
                f"{eid}: incorrect A1 scope-lock status"
            )

    # No source-pending rows should remain anywhere in tier assignments.
    pending = [
        row["evidence_id"]
        for row in tier_after
        if row.get("tier_status") == "SOURCE_PENDING"
    ]

    if pending:
        validation_errors.append(
            "SOURCE_PENDING rows remain: " + ",".join(pending)
        )

    tier_counts = Counter(
        row["evidence_tier"]
        for row in tier_after
        if row.get("tier_status") == "ASSIGNED"
    )

    assigned_count = sum(
        1
        for row in tier_after
        if row.get("tier_status") == "ASSIGNED"
    )

    c3_eligible_count = sum(
        1
        for row in lock_after
        if row.get("c3_eligible") == "YES"
    )

    a1_scope_excluded_count = sum(
        1
        for row in lock_after
        if row.get("module") == "A1"
        and row.get("c3_eligible") == "NO"
        and row.get("partial_lock_status")
        == "SOURCE_LOCKED_STANDALONE_NON_GRI"
    )

    if assigned_count != 20:
        validation_errors.append(
            f"expected 20 tier-assigned rows, found {assigned_count}"
        )

    if tier_counts.get("E1", 0) != 2:
        validation_errors.append("E1 count changed unexpectedly")

    if tier_counts.get("E2", 0) != 10:
        validation_errors.append(
            f"expected E2 count 10, found {tier_counts.get('E2', 0)}"
        )

    if tier_counts.get("E3", 0) != 1:
        validation_errors.append("E3 count changed unexpectedly")

    if tier_counts.get("E4", 0) != 7:
        validation_errors.append("E4 count changed unexpectedly")

    if c3_eligible_count != 16:
        validation_errors.append(
            f"expected existing C3 eligibility count 16, "
            f"found {c3_eligible_count}"
        )

    if a1_scope_excluded_count != 4:
        validation_errors.append(
            f"expected four source-locked A1 non-GRI rows, "
            f"found {a1_scope_excluded_count}"
        )

    now = datetime.now(timezone.utc).isoformat()

    summary_lines = [
        "C2.13 A1 SOURCE RECOVERY SUMMARY",
        "================================",
        "",
        f"Generated UTC: {now}",
        "",
        "A1 authoritative source rows recovered: 4",
        "A1 tier assignments: E2,E2,E2,E2",
        "",
        f"Total evidence rows: {len(tier_after)}",
        f"Tier-assigned rows: {assigned_count}",
        f"SOURCE_PENDING rows: {len(pending)}",
        "",
        "Evidence tier counts:",
        f"  E1: {tier_counts.get('E1', 0)}",
        f"  E2: {tier_counts.get('E2', 0)}",
        f"  E3: {tier_counts.get('E3', 0)}",
        f"  E4: {tier_counts.get('E4', 0)}",
        f"  E5: {tier_counts.get('E5', 0)}",
        "",
        f"C3-eligible rows retained: {c3_eligible_count}",
        (
            "A1 source-locked but standalone/non-GRI rows: "
            f"{a1_scope_excluded_count}"
        ),
        "",
        "Numerical evidence-tier weights: NOT DEFINED",
        "Existing F11/Privacy Base GRI mathematics: UNCHANGED",
    ]

    SUMMARY.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    validation_lines = [
        "C2.13 A1 SOURCE RECOVERY VALIDATION",
        "===================================",
        "",
        f"Generated UTC: {now}",
        f"Validation errors: {len(validation_errors)}",
    ]

    if validation_errors:
        validation_lines.append("STATUS: FAIL")
        validation_lines.append("")
        validation_lines.extend(
            f"- {error}"
            for error in validation_errors
        )
    else:
        validation_lines.extend(
            [
                "STATUS: PASS",
                "",
                "A1_E01: VERIFIED_EXISTING_SOURCE / E2 / ASSIGNED",
                "A1_E02: VERIFIED_EXISTING_SOURCE / E2 / ASSIGNED",
                "A1_E03: VERIFIED_EXISTING_SOURCE / E2 / ASSIGNED",
                "A1_E04: VERIFIED_EXISTING_SOURCE / E2 / ASSIGNED",
                "",
                "A1 C3 eligibility: NO",
                "A1 role: SOURCE_LOCKED_STANDALONE_NON_GRI",
                "",
                "C3-eligible row count remains: 16",
                "F11/Privacy GRI scope remains unchanged.",
            ]
        )

    VALIDATION.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    if validation_errors:
        for error in validation_errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    marker_lines = [
        "Status: COMPLETE",
        f"UTC: {now}",
        "C2 state: A1_AUTHORITATIVE_SOURCE_RECOVERED",
        "A1 evidence rows recovered: 4",
        "A1 evidence tiers: E2,E2,E2,E2",
        "Tier-assigned evidence rows: 20",
        "Source-pending evidence rows: 0",
        "Existing C3-eligible rows retained: 16",
        "A1 C3 eligibility: NO",
        "A1 role: SOURCE_LOCKED_STANDALONE_NON_GRI",
        "Numerical evidence weights: NOT_DEFINED",
        "Existing F11/Privacy Base GRI: UNCHANGED",
    ]

    MARKER.write_text(
        "\n".join(marker_lines) + "\n",
        encoding="utf-8",
    )

    print("C2.13 A1 source recovery lock generated successfully")
    print(f"Tier-assigned rows: {assigned_count}")
    print(f"SOURCE_PENDING rows: {len(pending)}")
    print(
        "Tier counts: "
        f"E1={tier_counts.get('E1', 0)}, "
        f"E2={tier_counts.get('E2', 0)}, "
        f"E3={tier_counts.get('E3', 0)}, "
        f"E4={tier_counts.get('E4', 0)}, "
        f"E5={tier_counts.get('E5', 0)}"
    )
    print(f"C3-eligible rows retained: {c3_eligible_count}")
    print("A1 role: SOURCE_LOCKED_STANDALONE_NON_GRI")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
