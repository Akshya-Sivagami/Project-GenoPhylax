import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"

D6_DEVELOPMENT_ANCHOR = 1000.0

D4_SCOPE_SCORES = {
    0: 0.0,
    1: 0.3333333333,
    2: 0.6666666667,
    3: 1.0,
}

D7_LEVEL_SCORES = {
    0: 0.0,
    1: 0.3333333333,
    2: 0.6666666667,
    3: 1.0,
}


def clamp(value):
    return max(0.0, min(1.0, float(value)))


def load_metric_registry(path=None):
    if path is None:
        path = SPEC / "GRI_v2_metric_registry.csv"

    registry = {}

    with Path(path).open(
        "r",
        encoding="utf-8",
        newline=""
    ) as f:
        for row in csv.DictReader(f):
            registry[row["raw_metric"]] = row

    return registry


def score_d4(boundary_breach, access_scope_level):
    breach = float(boundary_breach)
    level = int(access_scope_level)

    if breach not in (0.0, 1.0):
        raise ValueError(
            "D4 boundary_breach must be 0 or 1."
        )

    if level not in D4_SCOPE_SCORES:
        raise ValueError(
            "D4 access_scope_level must be 0, 1, 2, or 3."
        )

    return clamp(
        breach * D4_SCOPE_SCORES[level]
    )


def score_d5(
    recoverability_fraction,
    temporal_persistence
):
    recoverability = float(recoverability_fraction)
    persistence = float(temporal_persistence)

    if not 0.0 <= recoverability <= 1.0:
        raise ValueError(
            "D5 recoverability_fraction must be in [0,1]."
        )

    if not 0.0 <= persistence <= 1.0:
        raise ValueError(
            "D5 temporal_persistence must be in [0,1]."
        )

    irreversibility = 1.0 - recoverability

    return clamp(
        (irreversibility + persistence) / 2.0
    )


def score_d6(
    amplification_ratio,
    upper_anchor=D6_DEVELOPMENT_ANCHOR
):
    ratio = float(amplification_ratio)
    anchor = float(upper_anchor)

    if ratio < 1.0:
        raise ValueError(
            "D6 amplification_ratio must be >= 1."
        )

    if anchor <= 1.0:
        raise ValueError(
            "D6 upper anchor must be > 1."
        )

    return clamp(
        math.log10(ratio) / math.log10(anchor)
    )


def score_d7(rubric_level):
    level = int(rubric_level)

    if level not in D7_LEVEL_SCORES:
        raise ValueError(
            "D7 rubric_level must be 0, 1, 2, or 3."
        )

    return D7_LEVEL_SCORES[level]


def score_metric(
    record,
    registry,
    auxiliary=None
):
    auxiliary = auxiliary or {}

    metric = record["raw_metric"]
    dimension = record["dimension"]
    value = record.get("raw_value")

    mapping = registry.get(metric)

    if mapping is None:
        return {
            "candidate_score": None,
            "normalization_method": "UNREGISTERED_METRIC",
            "v2_score_status": "UNSCORED",
        }

    if mapping["dimension"] != dimension:
        return {
            "candidate_score": None,
            "normalization_method": "METRIC_DIMENSION_MISMATCH",
            "v2_score_status": "UNSCORED",
        }

    semantic = mapping["semantic_type"]
    rule = mapping["scoring_rule"]

    if rule == "CONSTRUCT_REVIEW":
        return {
            "candidate_score": None,
            "normalization_method": "CONSTRUCT_REVIEW",
            "v2_score_status": "CONSTRUCT_UNRESOLVED",
        }

    if semantic == "BINARY_DEMONSTRATION":
        try:
            demonstrated = float(value)
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "INVALID_BINARY_VALUE",
                "v2_score_status": "UNSCORED",
            }

        if demonstrated not in (0.0, 1.0):
            return {
                "candidate_score": None,
                "normalization_method": "INVALID_BINARY_VALUE",
                "v2_score_status": "UNSCORED",
            }

        if demonstrated == 1.0:
            return {
                "candidate_score": None,
                "normalization_method": "BINARY_DEMONSTRATION",
                "v2_score_status":
                    "POSITIVE_MAGNITUDE_UNRESOLVED",
            }

        return {
            "candidate_score": None,
            "normalization_method": "BINARY_DEMONSTRATION",
            "v2_score_status": "NO_POSITIVE_DEMONSTRATION",
        }

    if rule == "DIRECT":
        try:
            candidate = clamp(value)
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "INVALID_DIRECT_VALUE",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method": semantic,
            "v2_score_status": "CANDIDATE",
        }

    if rule == "INVERSE":
        try:
            candidate = clamp(
                1.0 - float(value)
            )
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "INVALID_INVERSE_VALUE",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method": semantic,
            "v2_score_status": "CANDIDATE",
        }

    if rule == "D4":
        required = (
            "boundary_breach",
            "access_scope_level",
        )

        if not all(
            key in auxiliary for key in required
        ):
            return {
                "candidate_score": None,
                "normalization_method": "D4_RUBRIC_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        try:
            candidate = score_d4(
                auxiliary["boundary_breach"],
                auxiliary["access_scope_level"],
            )
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "D4_RUBRIC_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method":
                "D4_ACCESSIBILITY_RUBRIC",
            "v2_score_status": "CANDIDATE",
        }

    if rule == "D5":
        required = (
            "recoverability_fraction",
            "temporal_persistence",
        )

        if not all(
            key in auxiliary for key in required
        ):
            return {
                "candidate_score": None,
                "normalization_method":
                    "D5_COMPONENTS_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        try:
            candidate = score_d5(
                auxiliary["recoverability_fraction"],
                auxiliary["temporal_persistence"],
            )
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method":
                    "D5_COMPONENTS_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method":
                "D5_PERSISTENCE_COMPOSITE",
            "v2_score_status": "CANDIDATE",
        }

    if rule == "D6":
        if "amplification_ratio" not in auxiliary:
            return {
                "candidate_score": None,
                "normalization_method": "D6_RATIO_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        try:
            candidate = score_d6(
                auxiliary["amplification_ratio"]
            )
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "D6_RATIO_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method":
                "D6_LOG10_ANCHORED_1000_"
                "SENSITIVITY_CANDIDATE",
            "v2_score_status": "CANDIDATE",
        }

    if rule == "D6_DENOMINATOR_REQUIRED":
        return {
            "candidate_score": None,
            "normalization_method":
                "D6_DENOMINATOR_REQUIRED",
            "v2_score_status": "UNSCORED",
        }

    if rule == "D7":
        if "rubric_level" not in auxiliary:
            return {
                "candidate_score": None,
                "normalization_method": "D7_RUBRIC_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        try:
            candidate = score_d7(
                auxiliary["rubric_level"]
            )
        except (TypeError, ValueError):
            return {
                "candidate_score": None,
                "normalization_method": "D7_RUBRIC_REQUIRED",
                "v2_score_status": "UNSCORED",
            }

        return {
            "candidate_score": candidate,
            "normalization_method":
                "D7_PIPELINE_RUBRIC",
            "v2_score_status": "CANDIDATE",
        }

    return {
        "candidate_score": None,
        "normalization_method": "UNKNOWN_SCORING_RULE",
        "v2_score_status": "UNSCORED",
    }


def aggregate_case(scored_records):
    total = len(scored_records)

    point_scores = []
    unresolved = []
    positive_unresolved = []
    construct_unresolved = []

    for row in scored_records:
        status = row["v2_score_status"]
        candidate = row["candidate_score"]
        dimension = row["dimension"]

        if (
            status == "CANDIDATE"
            and candidate is not None
        ):
            point_scores.append(float(candidate))
            continue

        unresolved.append(dimension)

        if status == "POSITIVE_MAGNITUDE_UNRESOLVED":
            positive_unresolved.append(dimension)

        if status == "CONSTRUCT_UNRESOLVED":
            construct_unresolved.append(dimension)

    coverage = (
        len(point_scores) / total
        if total
        else 0.0
    )

    if unresolved:
        composite = None
        composite_status = "WITHHELD"
    else:
        composite = (
            sum(point_scores) / len(point_scores)
            if point_scores
            else None
        )
        composite_status = (
            "CANDIDATE"
            if composite is not None
            else "WITHHELD"
        )

    return {
        "applicable_dimensions": total,
        "point_scored_dimensions": len(point_scores),
        "coverage": coverage,
        "candidate_composite": composite,
        "composite_status": composite_status,
        "unresolved_dimensions":
            sorted(set(unresolved)),
        "positive_magnitude_unresolved":
            sorted(set(positive_unresolved)),
        "construct_unresolved":
            sorted(set(construct_unresolved)),
    }
