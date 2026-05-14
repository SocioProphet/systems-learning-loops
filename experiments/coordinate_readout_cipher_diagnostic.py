"""Coordinate/readout cipher computational diagnostic.

Implements the Issue #3 diagnostic defined by:

    kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md

Evidence class: computational_diagnostic.

This module does not make theorem-facing claims. It computes the pinned
GF(4)/V4 readout diagnostic and produces a receipt that separates protocol
validity from prediction outcome.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

BOUNDARY_PATH = "kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md"
BOUNDARY_MERGE_COMMIT = "4b9a9082765dfe1884bb872e8470e5af2df5d963"
CLAIM_ID = "COORD_READOUT_INVOLUTION_001"
PATTERN = "coordinate-basis-vs-readout-basis-involution"
EVIDENCE_CLASS = "computational_diagnostic"
EXPERIMENT_ID = "coordinate-readout-cipher-v0"
FIELD_ELEMENTS = (0, 1, 2, 3)  # 0, 1, alpha, alpha+1 under F2[alpha]/(alpha^2+alpha+1)
NONZERO_ELEMENTS = (1, 2, 3)
ELEMENT_NAMES = {0: "0", 1: "1", 2: "alpha", 3: "alpha+1"}
EPSILON_FLOOR = 1.0e-12
INVOLUTION_TOLERANCE = 1.0e-12


def gf4_add(x: int, y: int) -> int:
    """GF(4) addition in F2^2 coordinates."""
    return x ^ y


def gf4_mul(x: int, y: int) -> int:
    """GF(4) multiplication with alpha^2 = alpha + 1.

    Elements are encoded as two-bit polynomials b0 + b1*alpha.
    """
    x0, x1 = x & 1, (x >> 1) & 1
    y0, y1 = y & 1, (y >> 1) & 1
    # Raw product: c0 + c1*a + c2*a^2, with a^2 = a + 1.
    c0 = x0 & y0
    c1 = (x0 & y1) ^ (x1 & y0)
    c2 = x1 & y1
    # Add c2*(a+1).
    r0 = c0 ^ c2
    r1 = c1 ^ c2
    return r0 | (r1 << 1)


def iota(x: int) -> tuple[float, float]:
    """Pinned readout embedding GF(4) -> F2^2 subset R^2."""
    return float(x & 1), float((x >> 1) & 1)


def l_m(m: int, x: int, y: int) -> int:
    """Pinned affine MOLS readout L_m(x,y) = m*x + y."""
    return gf4_add(gf4_mul(m, x), y)


def tau(a: int, x: int) -> int:
    """Pinned V4 translation tau_a(x) = x + a."""
    return gf4_add(x, a)


def all_pairs() -> list[tuple[int, int]]:
    return [(x, y) for x in FIELD_ELEMENTS for y in FIELD_ELEMENTS]


def l2_distance(p: tuple[float, float], q: tuple[float, float]) -> float:
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)


def normalized_distance(p: tuple[float, float], q: tuple[float, float]) -> float:
    return l2_distance(p, q) / math.sqrt(2.0)


def mean_vector(points: Iterable[tuple[float, float]]) -> tuple[float, float]:
    points = list(points)
    if not points:
        raise ValueError("cannot average empty point set")
    return sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)


def centroid_for_readout(m: int, sample: list[tuple[int, int]] | None = None) -> tuple[float, float]:
    sample = sample or all_pairs()
    return mean_vector(iota(l_m(m, x, y)) for x, y in sample)


def analytic_null_centroid() -> tuple[float, float]:
    return 0.5, 0.5


def balance_metric(m: int, sample: list[tuple[int, int]] | None = None) -> float:
    return normalized_distance(centroid_for_readout(m, sample), analytic_null_centroid())


def v4_involution_error() -> float:
    failures = 0
    total = 0
    for a in NONZERO_ELEMENTS:
        for x in FIELD_ELEMENTS:
            total += 1
            if tau(a, tau(a, x)) != x:
                failures += 1
    return failures / total if total else 1.0


def z4_rejection() -> dict[str, Any]:
    """Structural Z4 negative control: generator 1 has order 4, not 2."""
    x = 0
    orbit = []
    for _ in range(4):
        x = (x + 1) % 4
        orbit.append(x)
    return {
        "z4_rejected": True,
        "reason": "Z4 generator has order 4; additive GF(4) / V4 translations are all order <= 2.",
        "z4_generator_orbit_from_0": orbit,
        "z4_generator_order": 4,
        "v4_nonzero_translation_order": 2,
    }


def observed_displacement_for_translation(a: int, m: int) -> tuple[float, float]:
    """Mean readout displacement induced by tau_a under the pinned readout.

    We compare L_m(tau_a(x), y) against L_m(x, y), embedded by iota.
    For m=1 this displacement is iota(a); for m=alpha it is iota(alpha*a).
    The canonical diagnostic reports the better of the pinned pair only if it is
    selected before scoring. In v0 the selected readout is L_1, and L_alpha is
    reported for balance/composability but not used for post-hoc selection.
    """
    displacements = []
    for x, y in all_pairs():
        before = iota(l_m(m, x, y))
        after = iota(l_m(m, tau(a, x), y))
        displacements.append((after[0] - before[0], after[1] - before[1]))
    return mean_vector(displacements)


def selectivity_for_readout(m: int) -> dict[str, Any]:
    margins = []
    per_mask: dict[str, Any] = {}
    for a in NONZERO_ELEMENTS:
        delta = observed_displacement_for_translation(a, m)
        target = iota(a)
        correct_distance = normalized_distance(delta, target)
        incorrect_distance = min(
            normalized_distance(delta, iota(b)) for b in NONZERO_ELEMENTS if b != a
        )
        margin = incorrect_distance - correct_distance
        margins.append(margin)
        per_mask[ELEMENT_NAMES[a]] = {
            "observed_displacement": list(delta),
            "intended_translation_label": list(target),
            "correct_distance": correct_distance,
            "incorrect_distance": incorrect_distance,
            "selectivity_margin": margin,
        }
    return {"selectivity": sum(margins) / len(margins), "per_mask": per_mask}


def composability_metric() -> float:
    """Check V4 translation composition tau_a o tau_b = tau_{a+b}."""
    failures = 0
    total = 0
    for a in FIELD_ELEMENTS:
        for b in FIELD_ELEMENTS:
            for x in FIELD_ELEMENTS:
                total += 1
                if tau(a, tau(b, x)) != tau(gf4_add(a, b), x):
                    failures += 1
    return 1.0 - (failures / total if total else 1.0)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_baseline(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "provided": False,
            "coordinate_basis_involution_error": None,
            "coordinate_basis_selectivity": None,
            "coordinate_basis_balance_metric": None,
            "provenance": None,
        }
    return json.loads(path.read_text(encoding="utf-8"))


def classify_outcome(
    protocol_valid: bool,
    corrected_selectivity: float,
    baseline_selectivity: float | None,
    corrected_balance: float,
    baseline_balance: float | None,
    involution_error: float,
) -> tuple[str, float | None]:
    if not protocol_valid or baseline_selectivity is None or baseline_balance is None:
        return "protocol_incomplete", None

    lift = corrected_selectivity / max(abs(baseline_selectivity), EPSILON_FLOOR)
    if (
        lift >= 5.0
        and corrected_balance <= baseline_balance
        and involution_error <= INVOLUTION_TOLERANCE
    ):
        return "empirical_pair_confirmed", lift
    if (
        lift > 1.0
        and corrected_balance <= baseline_balance
        and involution_error <= INVOLUTION_TOLERANCE
    ):
        return "weak_support", lift
    return "falsified_directional", lift


def compute_receipt(
    baseline_path: Path | None = None,
    repo_root: Path | None = None,
    code_hash: str = "UNCOMMITTED",
    generated_at: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or Path.cwd()
    generated_at = generated_at or _dt.datetime.now(_dt.timezone.utc).isoformat()

    baseline = load_baseline(baseline_path)
    baseline_selectivity = baseline.get("coordinate_basis_selectivity")
    baseline_balance = baseline.get("coordinate_basis_balance_metric")

    selected_readout = 1  # L_1 is the predeclared v0 readout for scoring.
    corrected_selectivity = selectivity_for_readout(selected_readout)
    l_alpha_diagnostic = selectivity_for_readout(2)
    corrected_balance = balance_metric(selected_readout)
    involution_error = v4_involution_error()
    z4 = z4_rejection()

    boundary_hash = sha256_file(repo_root / BOUNDARY_PATH)
    readout_basis_block = {
        "embedding": "iota_GF4_to_F2xF2",
        "centroid_definition": "analytic_uniform_GF4xGF4_expectation",
        "centroid_null": [0.5, 0.5],
        "centroid_training_data": "none",
        "normalization": "L2_distance_over_sqrt2",
        "predeclared_before_masks": True,
        "predeclared_before_scores": True,
        "boundary_hash": boundary_hash,
    }
    readout_basis_hash = sha256_json(readout_basis_block)

    protocol_valid = bool(
        z4["z4_rejected"]
        and baseline.get("provided", baseline_path is not None)
        and baseline_selectivity is not None
        and baseline_balance is not None
        and baseline.get("provenance") is not None
        and involution_error <= INVOLUTION_TOLERANCE
        and readout_basis_hash
    )

    outcome_label, observed_lift = classify_outcome(
        protocol_valid,
        corrected_selectivity["selectivity"],
        baseline_selectivity,
        corrected_balance,
        baseline_balance,
        involution_error,
    )

    core_values = {
        "construction": "GF(4) F2[alpha]/(alpha^2+alpha+1), L1/Lalpha",
        "readout_basis": readout_basis_block,
        "corrected_selectivity": corrected_selectivity,
        "l_alpha_diagnostic": l_alpha_diagnostic,
        "balance_metric": corrected_balance,
        "involution_error": involution_error,
        "z4": z4,
        "baseline": baseline,
        "protocol_valid": protocol_valid,
        "outcome_label": outcome_label,
    }

    return {
        "experiment_id": EXPERIMENT_ID,
        "claim_id": CLAIM_ID,
        "pattern": PATTERN,
        "evidence_class": EVIDENCE_CLASS,
        "boundary_version": {
            "path": BOUNDARY_PATH,
            "merge_commit": BOUNDARY_MERGE_COMMIT,
            "sha256": boundary_hash,
        },
        "construction": {
            "field": "GF(4)",
            "presentation": "F2[alpha]/(alpha^2 + alpha + 1)",
            "element_order": [ELEMENT_NAMES[x] for x in FIELD_ELEMENTS],
            "mols_pair": ["L_1", "L_alpha"],
            "selected_readout_for_scoring": "L_1",
            "sensitivity_readouts_reported_not_scored": ["L_alpha"],
            "involution_operators": "V4_translations_tau_a",
            "z4_rejected": z4["z4_rejected"],
        },
        "readout_basis": {**readout_basis_block, "convention_hash": readout_basis_hash},
        "baseline": {
            "coordinate_basis_involution_error": baseline.get("coordinate_basis_involution_error"),
            "coordinate_basis_selectivity": baseline_selectivity,
            "coordinate_basis_balance_metric": baseline_balance,
            "provenance": baseline.get("provenance"),
        },
        "corrected_run": {
            "involution_error": involution_error,
            "selectivity": corrected_selectivity["selectivity"],
            "selectivity_by_mask": corrected_selectivity["per_mask"],
            "selectivity_lift_vs_coordinate": observed_lift,
            "balance_metric": corrected_balance,
            "composability_metric": composability_metric(),
            "l_alpha_diagnostic_not_scored": l_alpha_diagnostic,
            "outcome_label": outcome_label,
        },
        "statuses": {
            "protocol_valid": protocol_valid,
            "prediction_outcome": outcome_label,
        },
        "failure_criteria": {
            "declared": True,
            "involution_error_tolerance": INVOLUTION_TOLERANCE,
            "epsilon_floor": EPSILON_FLOOR,
        },
        "provenance": {
            "code_hash": code_hash,
            "data_hash": baseline.get("provenance", {}).get("data_hash") if isinstance(baseline.get("provenance"), dict) else None,
            "convention_hash": readout_basis_hash,
            "boundary_hash": boundary_hash,
            "generated_at": generated_at,
            "core_values_hash": sha256_json(core_values),
        },
        "nonclaims": [
            "This computational diagnostic does not prove a theorem.",
            "This computational diagnostic does not claim Hodge, BSD, Con(PA), P vs NP, RH/GRH, or Clay progress.",
            "This computational diagnostic is independent of the np-program A2 track.",
            "Cipher terminology is interpretive framing, not a unique interpretation of the transform.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the coordinate/readout cipher diagnostic.")
    parser.add_argument("--baseline", type=Path, help="Baseline JSON with coordinate-basis metrics.")
    parser.add_argument("--out", type=Path, help="Optional output receipt path.")
    parser.add_argument("--code-hash", default="UNCOMMITTED", help="Implementation commit hash.")
    args = parser.parse_args(argv)

    receipt = compute_receipt(baseline_path=args.baseline, code_hash=args.code_hash)
    text = json.dumps(receipt, indent=2, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if receipt["statuses"]["protocol_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
