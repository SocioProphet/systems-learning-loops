"""Coordinate/readout cipher computational diagnostic.

Implements the Issue #3 diagnostic defined by:

    kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md

Evidence class: computational_diagnostic.

This module does not make theorem-facing claims. It computes the pinned
GF(4)/V4 readout diagnostic and produces a receipt that separates protocol
validity from prediction outcome.

Implementation correction record:
- Incorrect computation: Euclidean after-minus-before under the iota embedding.
- Correct computation: GF(4) group displacement first, then iota embedding:
      delta = iota(L_m(tau_a(x), y) + L_m(x, y))
- Rationale: Euclidean subtraction is not the pinned V4 translation diagnostic
  and cancels under uniform binary coordinates. The corrected computation tests
  the group displacement induced by the V4 translation mask.
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
ALLOWED_EVIDENCE_CLASSES = ("computational_diagnostic",)
EXPERIMENT_ID = "coordinate-readout-cipher-v0"
FIELD_ELEMENTS = (0, 1, 2, 3)  # 0, 1, alpha, alpha+1 under F2[alpha]/(alpha^2+alpha+1)
NONZERO_ELEMENTS = (1, 2, 3)
ELEMENT_NAMES = {0: "0", 1: "1", 2: "alpha", 3: "alpha+1"}
PINNED_READOUTS = (
    {"name": "L_1", "m": 1, "target_multiplier": 1},
    {"name": "L_alpha", "m": 2, "target_multiplier": 2},
)
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
    c0 = x0 & y0
    c1 = (x0 & y1) ^ (x1 & y0)
    c2 = x1 & y1
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


def readout_group_displacement(a: int, m: int, x: int, y: int) -> int:
    """GF(4) displacement of readout after applying tau_a to x.

    This is group displacement in GF(4), not Euclidean after-minus-before under iota.
    The latter cancels under uniform binary coordinates and is not the pinned diagnostic.
    """
    before = l_m(m, x, y)
    after = l_m(m, tau(a, x), y)
    return gf4_add(after, before)


def observed_displacement_for_translation(a: int, m: int) -> tuple[float, float]:
    """Mean embedded GF(4) readout displacement induced by tau_a."""
    displacements = [iota(readout_group_displacement(a, m, x, y)) for x, y in all_pairs()]
    return mean_vector(displacements)


def selectivity_for_readout(m: int, target_multiplier: int) -> dict[str, Any]:
    """Compute v0 selectivity for a predeclared readout."""
    margins = []
    per_mask: dict[str, Any] = {}
    for a in NONZERO_ELEMENTS:
        delta = observed_displacement_for_translation(a, m)
        intended = gf4_mul(target_multiplier, a)
        target = iota(intended)
        incorrect_distance = min(
            normalized_distance(delta, iota(gf4_mul(target_multiplier, b)))
            for b in NONZERO_ELEMENTS
            if b != a
        )
        correct_distance = normalized_distance(delta, target)
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


def pinned_readout_results() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for readout in PINNED_READOUTS:
        results[readout["name"]] = {
            "m": ELEMENT_NAMES[readout["m"]],
            "target_multiplier": ELEMENT_NAMES[readout["target_multiplier"]],
            "selectivity": selectivity_for_readout(readout["m"], readout["target_multiplier"]),
            "balance_metric": balance_metric(readout["m"]),
        }
    return results


def aggregate_selectivity(readout_results: dict[str, Any]) -> float:
    return sum(item["selectivity"]["selectivity"] for item in readout_results.values()) / len(readout_results)


def aggregate_balance(readout_results: dict[str, Any]) -> float:
    return sum(item["balance_metric"] for item in readout_results.values()) / len(readout_results)


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
    loaded = json.loads(path.read_text(encoding="utf-8"))
    loaded.setdefault("provided", True)
    return loaded


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
    if EVIDENCE_CLASS not in ALLOWED_EVIDENCE_CLASSES:
        raise ValueError(f"unsupported evidence class: {EVIDENCE_CLASS}")

    repo_root = repo_root or Path.cwd()
    generated_at = generated_at or _dt.datetime.now(_dt.timezone.utc).isoformat()

    baseline = load_baseline(baseline_path)
    baseline_selectivity = baseline.get("coordinate_basis_selectivity")
    baseline_balance = baseline.get("coordinate_basis_balance_metric")

    readout_results = pinned_readout_results()
    corrected_selectivity = aggregate_selectivity(readout_results)
    corrected_balance = aggregate_balance(readout_results)
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
        boundary_hash
        and z4["z4_rejected"]
        and baseline.get("provided", baseline_path is not None)
        and baseline_selectivity is not None
        and baseline_balance is not None
        and baseline.get("provenance") is not None
        and involution_error <= INVOLUTION_TOLERANCE
        and readout_basis_hash
    )

    outcome_label, observed_lift = classify_outcome(
        protocol_valid,
        corrected_selectivity,
        baseline_selectivity,
        corrected_balance,
        baseline_balance,
        involution_error,
    )

    core_values = {
        "construction": "GF(4) F2[alpha]/(alpha^2+alpha+1), L1/Lalpha",
        "readout_basis": readout_basis_block,
        "readout_results": readout_results,
        "corrected_selectivity": corrected_selectivity,
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
            "pinned_readouts_for_scoring": [item["name"] for item in PINNED_READOUTS],
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
            "selectivity": corrected_selectivity,
            "selectivity_by_readout": readout_results,
            "selectivity_lift_vs_coordinate": observed_lift,
            "balance_metric": corrected_balance,
            "composability_metric": composability_metric(),
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
