#!/usr/bin/env python3

from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".tsv",
    ".csv",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".log",
    ".py",
    ".sh",
}

MAX_CONTENT_BYTES = 2 * 1024 * 1024
MAX_SELECTED_SOURCES = 5


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def safe_read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_CONTENT_BYTES:
            return ""

        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, UnicodeError):
        return ""


def list_repository_files(repo_root: Path, c_root: Path) -> list[Path]:
    files: list[Path] = []

    excluded_directory_names = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    }

    for current_root, directory_names, filenames in os.walk(repo_root):
        current_path = Path(current_root)

        directory_names[:] = [
            directory_name
            for directory_name in directory_names
            if directory_name not in excluded_directory_names
        ]

        try:
            current_path.relative_to(c_root)
            continue
        except ValueError:
            pass

        for filename in filenames:
            path = current_path / filename

            try:
                path.relative_to(repo_root / ".git")
                continue
            except ValueError:
                pass

            if path.is_file():
                files.append(path)

    return sorted(files)


def module_path_bonus(module: str, relative_path_lower: str) -> int:
    patterns = {
        "A1": [
            "a1",
            "bwa",
            "fuzz",
            "afl",
            "asan",
            "memory",
        ],
        "A2": [
            "a2",
            "adversarial",
            "basecalling",
            "deepvariant",
            "perturbation",
            "experiment_",
        ],
        "A3": [
            "a3",
            "clinical_consequence",
            "f11",
            "clinvar",
        ],
        "B1": [
            "b1",
            "graph_amplification",
            "amplification",
        ],
        "B2": [
            "b2",
            "vault",
            "lifetime_risk",
            "unrecoverability",
        ],
        "B3": [
            "b3",
            "authentication",
            "containment",
            "classifier",
        ],
    }

    return sum(
        8
        for pattern in patterns[module]
        if pattern in relative_path_lower
    )


def score_candidate(
    evidence: dict[str, Any],
    relative_path: str,
    content: str,
) -> tuple[int, list[str]]:
    relative_lower = relative_path.lower()
    filename_lower = Path(relative_path).name.lower()
    content_lower = content.lower()

    score = module_path_bonus(
        evidence["module"],
        relative_lower,
    )
    reasons: list[str] = []

    for pattern in evidence["preferred_globs"]:
        if fnmatch.fnmatch(relative_lower, pattern.lower()):
            score += 60
            reasons.append(f"preferred_glob:{pattern}")

    for term in evidence["path_terms"]:
        term_lower = term.lower()

        if term_lower in filename_lower:
            score += 20
            reasons.append(f"filename:{term}")
        elif term_lower in relative_lower:
            score += 10
            reasons.append(f"path:{term}")

    content_matches = 0

    for term in evidence["content_terms"]:
        term_lower = term.lower()

        if term_lower in content_lower:
            content_matches += 1
            score += 14
            reasons.append(f"content:{term}")

    if evidence["content_terms"] and content_matches == len(
        evidence["content_terms"]
    ):
        score += 20
        reasons.append("all_content_terms")

    if any(
        marker in filename_lower
        for marker in (
            "finding",
            "summary",
            "report",
            "validation",
            "audit",
            "result",
            "claim",
        )
    ):
        score += 10
        reasons.append("high_value_filename")

    if Path(relative_path).suffix.lower() in {
        ".tsv",
        ".csv",
        ".json",
    }:
        score += 5
        reasons.append("structured_file")

    if "/scripts/" in f"/{relative_lower}":
        score -= 8
        reasons.append("script_penalty")

    return score, reasons


def evidence_specs() -> list[dict[str, Any]]:
    return [
        {
            "evidence_id": "A1_E01",
            "module": "A1",
            "stage_ids": ["S3", "S10"],
            "asset": "BWA alignment software",
            "threat": "Malformed genomic input triggering memory corruption",
            "mechanism": (
                "Coverage-guided fuzzing of AddressSanitizer-instrumented "
                "BWA 0.7.19"
            ),
            "evidence_type": "experimental",
            "measured_result": "Approximately 2.5 million fuzz executions",
            "numeric_value": 2500000,
            "unit": "executions",
            "direction": "observed",
            "confidence": "high",
            "limitations": (
                "Single principal target version and incomplete program coverage"
            ),
            "claim_scope": "software-test campaign",
            "preferred_globs": [
                "*a1*finding*",
                "*bwa*finding*",
                "*fuzz*summary*",
            ],
            "path_terms": [
                "bwa",
                "fuzz",
                "afl",
                "finding",
                "summary",
            ],
            "content_terms": [
                "2.5 million",
                "bwa",
            ],
        },
        {
            "evidence_id": "A1_E02",
            "module": "A1",
            "stage_ids": ["S3", "S10"],
            "asset": "BWA alignment software",
            "threat": "Memory-safety vulnerability",
            "mechanism": "ASAN-confirmed crash triage",
            "evidence_type": "experimental",
            "measured_result": (
                "54 total crashes, 33 unique crashes and two root causes"
            ),
            "numeric_value": 2,
            "unit": "root causes",
            "direction": "observed",
            "confidence": "high",
            "limitations": (
                "Root causes were established within the project audit; "
                "external CVE assignment was not claimed"
            ),
            "claim_scope": "software-test campaign",
            "preferred_globs": [
                "*a1*finding*",
                "*bwa*finding*",
                "*crash*summary*",
            ],
            "path_terms": [
                "bwa",
                "crash",
                "asan",
                "finding",
            ],
            "content_terms": [
                "54",
                "33",
                "root causes",
            ],
        },
        {
            "evidence_id": "A1_E03",
            "module": "A1",
            "stage_ids": ["S3"],
            "asset": "BWA ksw alignment routine",
            "threat": "Heap buffer overflow",
            "mechanism": "Malformed-input execution reaching ksw_extend2",
            "evidence_type": "experimental",
            "measured_result": "Heap buffer overflow in ksw_extend2 at ksw.c:428",
            "numeric_value": "",
            "unit": "vulnerability",
            "direction": "observed",
            "confidence": "high",
            "limitations": "Exploitability beyond the demonstrated crash was not established",
            "claim_scope": "function-level finding",
            "preferred_globs": [
                "*a1*finding*",
                "*bwa*finding*",
                "*asan*",
            ],
            "path_terms": [
                "bwa",
                "asan",
                "finding",
            ],
            "content_terms": [
                "ksw_extend2",
                "ksw.c:428",
            ],
        },
        {
            "evidence_id": "A1_E04",
            "module": "A1",
            "stage_ids": ["S3"],
            "asset": "BWA SAM-output routine",
            "threat": "Global buffer overflow",
            "mechanism": "Malformed-input execution reaching mem_aln2sam",
            "evidence_type": "experimental",
            "measured_result": "Global overflow in mem_aln2sam at bwamem.c:906",
            "numeric_value": "",
            "unit": "vulnerability",
            "direction": "observed",
            "confidence": "high",
            "limitations": "Exploitability beyond the demonstrated crash was not established",
            "claim_scope": "function-level finding",
            "preferred_globs": [
                "*a1*finding*",
                "*bwa*finding*",
                "*asan*",
            ],
            "path_terms": [
                "bwa",
                "asan",
                "finding",
            ],
            "content_terms": [
                "mem_aln2sam",
                "bwamem.c:906",
            ],
        },
        {
            "evidence_id": "A2_E01",
            "module": "A2",
            "stage_ids": ["S1", "S2"],
            "asset": "Nanopore raw signal and basecalled reads",
            "threat": "Whole-read Gaussian raw-signal perturbation",
            "mechanism": "Controlled Gaussian-noise dose series",
            "evidence_type": "experimental",
            "measured_result": (
                "Seed-42 mean identity declined from 98.79% at GN01 "
                "to 93.89% at GN10"
            ),
            "numeric_value": 93.89,
            "unit": "percent mean identity at GN10",
            "direction": "decrease",
            "confidence": "high",
            "limitations": (
                "One sequencing dataset, one production basecaller and a "
                "limited perturbation family"
            ),
            "claim_scope": "100-read controlled experiment",
            "preferred_globs": [
                "*a2*master*finding*",
                "*experiment_a*finding*",
                "*gaussian*summary*",
            ],
            "path_terms": [
                "gaussian",
                "experiment_a",
                "master_findings",
                "numerical_summary",
            ],
            "content_terms": [
                "98.79",
                "93.89",
            ],
        },
        {
            "evidence_id": "A2_E02",
            "module": "A2",
            "stage_ids": ["S1", "S2"],
            "asset": "Nanopore raw signal and basecalled reads",
            "threat": "Stochastic raw-signal perturbation",
            "mechanism": "Five-seed replication across GN01, GN05 and GN10",
            "evidence_type": "experimental",
            "measured_result": (
                "GN10 mean identity replicated within approximately "
                "93.56% to 93.95%"
            ),
            "numeric_value": 5,
            "unit": "random seeds",
            "direction": "replicated",
            "confidence": "high",
            "limitations": "Replication varied noise realization, not biological sample",
            "claim_scope": "multi-seed technical replication",
            "preferred_globs": [
                "*experiment_b*finding*",
                "*multiseed*finding*",
                "*a2*master*finding*",
            ],
            "path_terms": [
                "multiseed",
                "experiment_b",
                "gaussian",
                "master_findings",
            ],
            "content_terms": [
                "93.56",
                "93.95",
            ],
        },
        {
            "evidence_id": "A2_E03",
            "module": "A2",
            "stage_ids": ["S2", "S3"],
            "asset": "Perturbed nanopore reads",
            "threat": "Basecall degradation while preserving downstream usability",
            "mechanism": "Minimap2 map-ont alignment of the 1,000-read series",
            "evidence_type": "experimental",
            "measured_result": (
                "Approximately 97% remained mapped with mean MAPQ "
                "approximately 55.3 to 55.4"
            ),
            "numeric_value": 97,
            "unit": "percent mapped",
            "direction": "retained",
            "confidence": "high",
            "limitations": (
                "Mapping retention does not establish preservation of all "
                "downstream biological information"
            ),
            "claim_scope": "1,000-read alignment series",
            "preferred_globs": [
                "*a2*master*finding*",
                "*alignment*summary*",
                "*experiment_d*",
            ],
            "path_terms": [
                "alignment",
                "1000",
                "experiment_d",
                "master_findings",
            ],
            "content_terms": [
                "97",
                "55.3",
            ],
        },
        {
            "evidence_id": "A2_E04",
            "module": "A2",
            "stage_ids": ["S1", "S2", "S3"],
            "asset": "Truth-backed nanopore locus evidence",
            "threat": "Target-local signal perturbation",
            "mechanism": "W0 targeted-locus perturbation replicated at L2 and L3",
            "evidence_type": "experimental",
            "measured_result": (
                "L2 and L3 each retained ALT state in 10 of 10 parents; "
                "zero target-state changes"
            ),
            "numeric_value": 0,
            "unit": "changed parents across 20",
            "direction": "no effect",
            "confidence": "high",
            "limitations": (
                "The tested W0 effect did not generalize across these two "
                "additional loci"
            ),
            "claim_scope": "cross-locus replication",
            "preferred_globs": [
                "*cross*locus*finding*",
                "*w0*target*effect*",
                "*a2*master*finding*",
            ],
            "path_terms": [
                "cross_locus",
                "w0_target_effect",
                "master_findings",
                "replication",
            ],
            "content_terms": [
                "0/10",
                "no_effect",
            ],
        },
        {
            "evidence_id": "A3_E01",
            "module": "A3",
            "stage_ids": ["S1", "S2", "S3"],
            "asset": "F11 ALT-supporting nanopore reads",
            "threat": "Target-mapped local raw-signal interpolation",
            "mechanism": (
                "Interpolation over W0, PM2, PM5, PM10 and PM20 signal windows"
            ),
            "evidence_type": "experimental",
            "measured_result": (
                "59 of 70 parent-condition observations changed target state"
            ),
            "numeric_value": 84.2857,
            "unit": "percent changed",
            "direction": "increase",
            "confidence": "high",
            "limitations": (
                "Single individual, pathogenic locus, sequencing run, "
                "basecaller and model"
            ),
            "claim_scope": "single-locus controlled case study",
            "preferred_globs": [
                "*f11*final*",
                "*f11*summary*",
                "*controlled*hybrid*summary*",
            ],
            "path_terms": [
                "f11",
                "controlled",
                "summary",
                "final",
            ],
            "content_terms": [
                "59/70",
                "84.2857",
            ],
        },
        {
            "evidence_id": "A3_E02",
            "module": "A3",
            "stage_ids": ["S3", "S4"],
            "asset": "F11 pathogenic variant evidence",
            "threat": "Target-overlapping local signal attack",
            "mechanism": "PM2 interpolation over target base and two flanking bases",
            "evidence_type": "experimental",
            "measured_result": (
                "All 14 clean-confirmed ALT parents lost ALT state under PM2"
            ),
            "numeric_value": 14,
            "unit": "ALT parents changed out of 14",
            "direction": "suppressed",
            "confidence": "high",
            "limitations": "Controlled single-locus experiment",
            "claim_scope": "parent-level target-state analysis",
            "preferred_globs": [
                "*f11*controlled*summary*",
                "*f11*final*validation*",
                "*f11*attacked*summary*",
            ],
            "path_terms": [
                "f11",
                "controlled",
                "attacked",
                "summary",
                "validation",
            ],
            "content_terms": [
                "pm2",
                "14/14",
            ],
        },
        {
            "evidence_id": "A3_E03",
            "module": "A3",
            "stage_ids": ["S4", "S5"],
            "asset": "Pathogenic F11 heterozygous variant call",
            "threat": "False-negative or missed-variant event",
            "mechanism": (
                "Controlled hybrid pileup and bcftools variant calling "
                "after targeted signal attack"
            ),
            "evidence_type": "experimental",
            "measured_result": (
                "Clean 0/1 call with QUAL 222.201 was lost under PM2, "
                "PM5, PM10 and PM20"
            ),
            "numeric_value": 4,
            "unit": "attack conditions with call loss",
            "direction": "suppressed",
            "confidence": "high",
            "limitations": (
                "Potential clinical interpretation risk only; no real clinical "
                "diagnosis or patient outcome was tested"
            ),
            "claim_scope": "controlled variant-calling workflow",
            "preferred_globs": [
                "*f11*controlled*hybrid*",
                "*f11*final*",
                "*a3*checkpoint*summary*",
            ],
            "path_terms": [
                "f11",
                "controlled_hybrid",
                "checkpoint_summary",
                "variant_calling",
            ],
            "content_terms": [
                "222.201",
                "no_call",
            ],
        },
        {
            "evidence_id": "A3_E04",
            "module": "A3",
            "stage_ids": ["S1", "S2", "S3", "S4"],
            "asset": "F11 pathogenic variant evidence",
            "threat": "Non-target interpolation as confounding mechanism",
            "mechanism": (
                "PM2-sized off-target sham interpolation at least 5,000 "
                "signal samples from the F11 target"
            ),
            "evidence_type": "experimental control",
            "measured_result": (
                "Sham retained 14 of 14 ALT parents, genotype 0/1 and "
                "QUAL 222.202"
            ),
            "numeric_value": 14,
            "unit": "ALT parents retained out of 14",
            "direction": "retained",
            "confidence": "high",
            "limitations": "One off-target sham design within the same read cohort",
            "claim_scope": "target-specific causality control",
            "preferred_globs": [
                "*pm2*off*target*sham*report*",
                "*pm2*off*target*sham*summary*",
                "*f11*sham*",
            ],
            "path_terms": [
                "pm2_off_target_sham",
                "sham_report",
                "sham_summary",
            ],
            "content_terms": [
                "222.202",
                "14/14",
            ],
        },
        {
            "evidence_id": "B1_E01",
            "module": "B1",
            "stage_ids": ["S7", "S8"],
            "asset": "Genomic-sharing population graph",
            "threat": "Familial graph-amplified exposure",
            "mechanism": "Population graph simulation and breach propagation",
            "evidence_type": "simulation",
            "measured_result": (
                "Population graph contained 3,303 nodes, with 1,321 "
                "registered individuals and 786 baseline exposed"
            ),
            "numeric_value": 3303,
            "unit": "graph nodes",
            "direction": "model input",
            "confidence": "medium",
            "limitations": "Synthetic or modelled graph rather than direct platform data",
            "claim_scope": "graph simulation",
            "preferred_globs": [
                "*b1*result*",
                "*amplification*result*",
                "*graph*summary*",
            ],
            "path_terms": [
                "results_log",
                "amplification",
                "graph_model",
            ],
            "content_terms": [
                "3303",
                "1321",
                "786",
            ],
        },
        {
            "evidence_id": "B1_E02",
            "module": "B1",
            "stage_ids": ["S7", "S8"],
            "asset": "Genomic-sharing population graph",
            "threat": "Graph-amplified breach exposure",
            "mechanism": "Calibration to a 493-fold target amplification scenario",
            "evidence_type": "calibrated simulation",
            "measured_result": (
                "Model amplification reached 464.4-fold with 5.8% "
                "calibration error"
            ),
            "numeric_value": 464.4,
            "unit": "fold amplification",
            "direction": "amplified",
            "confidence": "medium",
            "limitations": (
                "Calibration target does not independently validate every "
                "graph assumption"
            ),
            "claim_scope": "calibrated graph model",
            "preferred_globs": [
                "*calibration*",
                "*b1*result*",
                "*amplification*result*",
            ],
            "path_terms": [
                "calibration",
                "results_log",
                "amplification",
            ],
            "content_terms": [
                "464.4",
                "5.8",
            ],
        },
        {
            "evidence_id": "B2_E01",
            "module": "B2",
            "stage_ids": ["S6", "S7"],
            "asset": "Layered genomic vault",
            "threat": "Reconstruction from disclosed semantic layers",
            "mechanism": "Layered vault and unrecoverability model",
            "evidence_type": "model-derived",
            "measured_result": (
                "Adding the pathogenic-variant layer reduced "
                "unrecoverability to 0.044"
            ),
            "numeric_value": 0.044,
            "unit": "unrecoverability score",
            "direction": "decrease",
            "confidence": "medium",
            "limitations": (
                "Unrecoverability is produced by the project model and is "
                "not a formal cryptographic proof"
            ),
            "claim_scope": "vault-model scenario",
            "preferred_globs": [
                "*b2*result*",
                "*vault*result*",
                "*vault*summary*",
            ],
            "path_terms": [
                "vault",
                "unrecoverability",
                "b2_upgrades",
            ],
            "content_terms": [
                "0.044",
                "pathogenic",
            ],
        },
        {
            "evidence_id": "B2_E02",
            "module": "B2",
            "stage_ids": ["S7", "S9"],
            "asset": "Persistently disclosed genomic information",
            "threat": "Time-dependent re-identification",
            "mechanism": "Lifetime genomic-risk simulation",
            "evidence_type": "simulation",
            "measured_result": (
                "Re-identification reached 50% by year 11 and "
                "100% by year 20"
            ),
            "numeric_value": 11,
            "unit": "years to 50 percent re-identification",
            "direction": "increase over time",
            "confidence": "medium",
            "limitations": "Long-term projections depend on model assumptions",
            "claim_scope": "lifetime-risk simulation",
            "preferred_globs": [
                "*lifetime*risk*",
                "*b2*result*",
            ],
            "path_terms": [
                "lifetime_risk",
                "risk",
                "b2",
            ],
            "content_terms": [
                "year 11",
                "year 20",
            ],
        },
        {
            "evidence_id": "B2_E03",
            "module": "B2",
            "stage_ids": ["S8", "S9"],
            "asset": "Familial genomic information",
            "threat": "Persistent familial exposure",
            "mechanism": "Lifetime familial-risk simulation",
            "evidence_type": "simulation",
            "measured_result": "Familial risk reached 100% by year 15",
            "numeric_value": 15,
            "unit": "years to 100 percent familial risk",
            "direction": "increase over time",
            "confidence": "medium",
            "limitations": "Projection depends on the selected model parameters",
            "claim_scope": "lifetime-risk simulation",
            "preferred_globs": [
                "*lifetime*risk*",
                "*b2*result*",
            ],
            "path_terms": [
                "lifetime_risk",
                "familial",
                "b2",
            ],
            "content_terms": [
                "year 15",
                "familial",
            ],
        },
        {
            "evidence_id": "B3_E01",
            "module": "B3",
            "stage_ids": ["S8", "S10"],
            "asset": "Kinship graph exposure boundary",
            "threat": "Graph-originating breach propagation",
            "mechanism": "Graph-aware boundary-isolation simulation",
            "evidence_type": "simulation",
            "measured_result": (
                "Exposure declined from 560 at k=5 to 6 at k=10; "
                "hub-origin containment required k=20"
            ),
            "numeric_value": 6,
            "unit": "exposed nodes at k=10",
            "direction": "decrease",
            "confidence": "medium",
            "limitations": "Containment performance depends on graph construction",
            "claim_scope": "containment simulation",
            "preferred_globs": [
                "*containment*result*",
                "*b3*result*",
                "*containment*",
            ],
            "path_terms": [
                "containment",
                "attack_origin",
                "b3",
            ],
            "content_terms": [
                "560",
                "k=10",
            ],
        },
        {
            "evidence_id": "B3_E02",
            "module": "B3",
            "stage_ids": ["S6", "S10"],
            "asset": "Genomic-platform authentication layer",
            "threat": "Unauthorized platform access",
            "mechanism": "Behavioural authentication classifier",
            "evidence_type": "simulation or benchmark",
            "measured_result": (
                "At threshold 3.8, precision was 0.9737, recall 0.7400, "
                "F1 0.8409 and accuracy 0.9440"
            ),
            "numeric_value": 0.8409,
            "unit": "F1 score",
            "direction": "performance",
            "confidence": "medium",
            "limitations": (
                "Classifier results require interpretation within the "
                "project's generated benchmark setting"
            ),
            "claim_scope": "authentication benchmark",
            "preferred_globs": [
                "*authentication*result*",
                "*classifier*result*",
                "*b3*",
            ],
            "path_terms": [
                "authentication",
                "classifier",
                "containment_auth",
                "b3",
            ],
            "content_terms": [
                "0.9737",
                "0.8409",
            ],
        },
        {
            "evidence_id": "B3_E03",
            "module": "B3",
            "stage_ids": ["S6", "S10"],
            "asset": "Genomic-platform authentication layer",
            "threat": "Missed malicious access",
            "mechanism": "Operational classifier-threshold selection",
            "evidence_type": "design decision",
            "measured_result": (
                "Threshold 3.6 was selected operationally to favour recall"
            ),
            "numeric_value": 3.6,
            "unit": "classifier threshold",
            "direction": "selected",
            "confidence": "medium",
            "limitations": (
                "Operational preference is a design choice rather than a "
                "universally optimal threshold"
            ),
            "claim_scope": "project design decision",
            "preferred_globs": [
                "*authentication*result*",
                "*classifier*result*",
                "*b3*",
            ],
            "path_terms": [
                "authentication",
                "classifier",
                "b3",
            ],
            "content_terms": [
                "3.6",
                "recall",
            ],
        },
    ]


def main() -> int:
    if len(sys.argv) != 9:
        print(
            "Usage: build_C2_cross_module_evidence_registry.py "
            "<repo_root> <c1_schema> <registry_tsv> <registry_json> "
            "<registry_md> <source_audit> <unresolved> <validation>",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(sys.argv[1]).resolve()
    c1_schema_path = Path(sys.argv[2]).resolve()
    registry_tsv = Path(sys.argv[3]).resolve()
    registry_json = Path(sys.argv[4]).resolve()
    registry_md = Path(sys.argv[5]).resolve()
    source_audit = Path(sys.argv[6]).resolve()
    unresolved_file = Path(sys.argv[7]).resolve()
    validation_file = Path(sys.argv[8]).resolve()

    c_root = repo_root / "experiments" / "C_lifecycle_integration"

    with c1_schema_path.open(encoding="utf-8") as handle:
        c1_schema = json.load(handle)

    valid_stage_ids = {
        stage["stage_id"]
        for stage in c1_schema["stages"]
    }

    repository_files = list_repository_files(
        repo_root=repo_root,
        c_root=c_root,
    )

    content_cache: dict[Path, str] = {}

    for path in repository_files:
        if path.suffix.lower() in TEXT_EXTENSIONS:
            content_cache[path] = safe_read_text(path)

    records = evidence_specs()
    errors: list[str] = []
    source_audit_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, Any]] = []

    required_fields = {
        "evidence_id",
        "module",
        "stage_ids",
        "asset",
        "threat",
        "mechanism",
        "evidence_type",
        "measured_result",
        "unit",
        "confidence",
        "limitations",
        "claim_scope",
    }

    evidence_ids = [
        record["evidence_id"]
        for record in records
    ]

    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("Evidence IDs are not unique")

    for record in records:
        missing_fields = required_fields.difference(record)

        if missing_fields:
            errors.append(
                f'{record.get("evidence_id", "UNKNOWN")} missing fields: '
                + ", ".join(sorted(missing_fields))
            )

        invalid_stages = set(record["stage_ids"]).difference(
            valid_stage_ids
        )

        if invalid_stages:
            errors.append(
                f'{record["evidence_id"]} references invalid stages: '
                + ", ".join(sorted(invalid_stages))
            )

        candidates: list[dict[str, Any]] = []

        for path in repository_files:
            relative_path = path.relative_to(repo_root).as_posix()
            content = content_cache.get(path, "")

            score, reasons = score_candidate(
                evidence=record,
                relative_path=relative_path,
                content=content,
            )

            if score > 0:
                candidates.append(
                    {
                        "relative_path": relative_path,
                        "score": score,
                        "reasons": reasons,
                        "size_bytes": path.stat().st_size,
                    }
                )

        candidates.sort(
            key=lambda item: (
                -item["score"],
                item["relative_path"],
            )
        )

        selected = [
            item
            for item in candidates
            if item["score"] >= 28
        ][:MAX_SELECTED_SOURCES]

        if not selected and candidates:
            selected = candidates[:1]

        if not selected:
            resolution_status = "UNRESOLVED"
            source_confidence = "none"
            primary_source = ""
            supporting_sources: list[str] = []
            top_score = 0
        else:
            top_score = selected[0]["score"]
            primary_source = selected[0]["relative_path"]
            supporting_sources = [
                item["relative_path"]
                for item in selected[1:]
            ]

            if top_score >= 95:
                resolution_status = "STRONG_CANDIDATE"
                source_confidence = "high"
            elif top_score >= 60:
                resolution_status = "REVIEW_REQUIRED"
                source_confidence = "medium"
            else:
                resolution_status = "WEAK_CANDIDATE"
                source_confidence = "low"

        record["primary_source_file"] = primary_source
        record["supporting_source_files"] = supporting_sources
        record["source_resolution_status"] = resolution_status
        record["source_confidence"] = source_confidence
        record["source_match_score"] = top_score

        if resolution_status in {
            "UNRESOLVED",
            "WEAK_CANDIDATE",
        }:
            unresolved_rows.append(
                {
                    "evidence_id": record["evidence_id"],
                    "module": record["module"],
                    "measured_result": record["measured_result"],
                    "resolution_status": resolution_status,
                    "primary_source_file": primary_source,
                    "source_match_score": top_score,
                }
            )

        for rank, candidate in enumerate(
            candidates[:10],
            start=1,
        ):
            source_audit_rows.append(
                {
                    "evidence_id": record["evidence_id"],
                    "module": record["module"],
                    "candidate_rank": rank,
                    "candidate_file": candidate["relative_path"],
                    "score": candidate["score"],
                    "size_bytes": candidate["size_bytes"],
                    "match_reasons": " | ".join(candidate["reasons"]),
                    "selected": (
                        "YES"
                        if candidate["relative_path"]
                        in {
                            primary_source,
                            *supporting_sources,
                        }
                        else "NO"
                    ),
                }
            )

    module_counts: dict[str, int] = {}

    for record in records:
        module_counts[record["module"]] = (
            module_counts.get(record["module"], 0) + 1
        )

    expected_modules = {
        "A1",
        "A2",
        "A3",
        "B1",
        "B2",
        "B3",
    }

    missing_modules = expected_modules.difference(module_counts)

    if missing_modules:
        errors.append(
            "Modules missing from evidence registry: "
            + ", ".join(sorted(missing_modules))
        )

    registry_fieldnames = [
        "evidence_id",
        "module",
        "stage_ids",
        "asset",
        "threat",
        "mechanism",
        "evidence_type",
        "measured_result",
        "numeric_value",
        "unit",
        "direction",
        "confidence",
        "claim_scope",
        "limitations",
        "primary_source_file",
        "supporting_source_files",
        "source_resolution_status",
        "source_confidence",
        "source_match_score",
    ]

    with registry_tsv.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=registry_fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()

        for record in records:
            row = {
                key: record.get(key, "")
                for key in registry_fieldnames
            }
            row["stage_ids"] = "|".join(record["stage_ids"])
            row["supporting_source_files"] = "|".join(
                record["supporting_source_files"]
            )
            writer.writerow(row)

    audit_fieldnames = [
        "evidence_id",
        "module",
        "candidate_rank",
        "candidate_file",
        "score",
        "size_bytes",
        "match_reasons",
        "selected",
    ]

    with source_audit.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=audit_fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(source_audit_rows)

    unresolved_fieldnames = [
        "evidence_id",
        "module",
        "measured_result",
        "resolution_status",
        "primary_source_file",
        "source_match_score",
    ]

    with unresolved_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=unresolved_fieldnames,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(unresolved_rows)

    serializable_records: list[dict[str, Any]] = []

    for record in records:
        serializable = {
            key: value
            for key, value in record.items()
            if key
            not in {
                "preferred_globs",
                "path_terms",
                "content_terms",
            }
        }
        serializable_records.append(serializable)

    status = (
        "DRAFT_SOURCE_REVIEW_REQUIRED"
        if unresolved_rows
        else "SOURCE_RESOLUTION_COMPLETE"
    )

    registry_document = {
        "schema_name": "GenoPhylax Cross-Module Evidence Registry",
        "schema_version": "1.0.0-draft",
        "generated_utc": utc_now(),
        "status": status,
        "record_count": len(records),
        "module_counts": module_counts,
        "source_resolution_summary": {
            resolution_status: sum(
                1
                for record in records
                if record["source_resolution_status"]
                == resolution_status
            )
            for resolution_status in {
                "STRONG_CANDIDATE",
                "REVIEW_REQUIRED",
                "WEAK_CANDIDATE",
                "UNRESOLVED",
            }
        },
        "important_qualification": (
            "The source resolver identifies candidate repository evidence. "
            "Candidate files must be reviewed before C2 is declared locked "
            "for final GRI construction."
        ),
        "records": serializable_records,
    }

    with registry_json.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            registry_document,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")

    with registry_md.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            "# Module C2 — Cross-Module Evidence Registry\n\n"
        )
        handle.write("## Status\n\n")
        handle.write(f"`{status}`\n\n")

        handle.write("## Purpose\n\n")
        handle.write(
            "This registry links measured GenoPhylax results to the "
            "canonical lifecycle stages defined in C1. It separates "
            "experimental evidence from simulation, calibration, "
            "model-derived values and project design decisions.\n\n"
        )

        handle.write("## Important source qualification\n\n")
        handle.write(
            "The source paths in this first pass are automatically "
            "resolved candidates. Strong candidates may still require "
            "human inspection before they are locked as authoritative "
            "paper sources. No GenoPhylax Risk Index weights or composite "
            "scores are assigned in C2.\n\n"
        )

        handle.write("## Module coverage\n\n")

        for module in sorted(module_counts):
            handle.write(
                f"- **{module}:** {module_counts[module]} evidence records\n"
            )

        handle.write("\n## Evidence records\n\n")

        for record in records:
            handle.write(
                f'### {record["evidence_id"]} — '
                f'{record["module"]}\n\n'
            )
            handle.write(
                f'**Lifecycle stages:** '
                f'{", ".join(record["stage_ids"])}\n\n'
            )
            handle.write(
                f'**Evidence type:** '
                f'{record["evidence_type"]}\n\n'
            )
            handle.write(
                f'**Asset:** {record["asset"]}\n\n'
            )
            handle.write(
                f'**Threat:** {record["threat"]}\n\n'
            )
            handle.write(
                f'**Mechanism:** {record["mechanism"]}\n\n'
            )
            handle.write(
                f'**Measured result:** '
                f'{record["measured_result"]}\n\n'
            )
            handle.write(
                f'**Evidence confidence:** '
                f'{record["confidence"]}\n\n'
            )
            handle.write(
                f'**Claim scope:** '
                f'{record["claim_scope"]}\n\n'
            )
            handle.write(
                f'**Limitations:** '
                f'{record["limitations"]}\n\n'
            )
            handle.write(
                f'**Candidate source:** '
                f'`{record["primary_source_file"] or "UNRESOLVED"}`\n\n'
            )
            handle.write(
                f'**Source resolution:** '
                f'{record["source_resolution_status"]} '
                f'(score {record["source_match_score"]})\n\n'
            )

    strong_count = sum(
        1
        for record in records
        if record["source_resolution_status"]
        == "STRONG_CANDIDATE"
    )
    review_count = sum(
        1
        for record in records
        if record["source_resolution_status"]
        == "REVIEW_REQUIRED"
    )
    weak_count = sum(
        1
        for record in records
        if record["source_resolution_status"]
        == "WEAK_CANDIDATE"
    )
    unresolved_count = sum(
        1
        for record in records
        if record["source_resolution_status"]
        == "UNRESOLVED"
    )

    validation_lines = [
        "MODULE C2 — EVIDENCE REGISTRY VALIDATION",
        "==========================================",
        f"Generated UTC: {utc_now()}",
        f"Evidence records: {len(records)}",
        f"Unique evidence IDs: {len(set(evidence_ids))}",
        f"Modules represented: {','.join(sorted(module_counts))}",
        f"Strong source candidates: {strong_count}",
        f"Review-required candidates: {review_count}",
        f"Weak source candidates: {weak_count}",
        f"Unresolved sources: {unresolved_count}",
        f"Schema validation errors: {len(errors)}",
    ]

    if errors:
        validation_lines.append("Schema validation status: FAIL")
        validation_lines.append("")
        validation_lines.append("Errors:")
        validation_lines.extend(
            f"- {error}"
            for error in errors
        )
    else:
        validation_lines.append("Schema validation status: PASS")

    validation_lines.extend(
        [
            f"Registry status: {status}",
            "",
            (
                "Interpretation: PASS confirms structural validity and "
                "module coverage. It does not mean every automatically "
                "selected source file has been manually verified."
            ),
        ]
    )

    validation_file.write_text(
        "\n".join(validation_lines) + "\n",
        encoding="utf-8",
    )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("C2 evidence registry generated successfully")
    print(f"Evidence records: {len(records)}")
    print(f"Strong source candidates: {strong_count}")
    print(f"Review-required candidates: {review_count}")
    print(f"Weak source candidates: {weak_count}")
    print(f"Unresolved sources: {unresolved_count}")
    print(f"Registry status: {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
