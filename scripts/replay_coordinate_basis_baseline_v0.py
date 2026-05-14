#!/usr/bin/env python3
"""Replay the canonical coordinate-basis baseline v0.

This script produces a computational_diagnostic_baseline receipt under:

  kb/conventions/coordinate-basis-baseline-v0.convention.yaml

It is deterministic for a fixed --generated-at value and does not invent
empirical values. Selectivity and balance are computed from the declared
synthetic fixture over all 16 points in GF(4)^2.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

HASH_ALGORITHM = "sha256"
BASELINE_ID = "coordinate-readout-cipher-v0-baseline"
CLAIM_ID = "COORD_READOUT_INVOLUTION_001"
CONVENTION_ID = "coordinate-basis-baseline-v0"
CONVENTION = Path("kb/conventions/coordinate-basis-baseline-v0.convention.yaml")
DIAGNOSTIC = Path("experiments/coordinate_readout_cipher_diagnostic.py")
BOUNDARY = Path("kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md")
FIELD = (0, 1, 2, 3)
NONZERO = (1, 2, 3)
NAMES = {0: "0", 1: "1", 2: "alpha", 3: "alpha+1"}
READOUTS = (("L_1", 1, 1), ("L_alpha", 2, 2))
EXPECTED_MUL_TABLE = (
    (0, 0, 0, 0),
    (0, 1, 2, 3),
    (0, 2, 3, 1),
    (0, 3, 1, 2),
)


def sha_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def sha_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def add(x: int, y: int) -> int:
    return x ^ y


def mul(x: int, y: int) -> int:
    x0, x1 = x & 1, (x >> 1) & 1
    y0, y1 = y & 1, (y >> 1) & 1
    c0 = x0 & y0
    c1 = (x0 & y1) ^ (x1 & y0)
    c2 = x1 & y1
    return (c0 ^ c2) | ((c1 ^ c2) << 1)


def multiplication_table() -> list[list[int]]:
    return [[mul(x, y) for y in FIELD] for x in FIELD]


def assert_gf4_table() -> None:
    actual = tuple(tuple(row) for row in multiplication_table())
    if actual != EXPECTED_MUL_TABLE:
        raise AssertionError(f"GF(4) multiplication table mismatch: {actual!r}")


def iota(x: int) -> list[float]:
    return [float(x & 1), float((x >> 1) & 1)]


def readout(m: int, x: int, y: int) -> int:
    return add(mul(m, x), y)


def tau(a: int, x: int) -> int:
    return add(x, a)


def pairs() -> list[tuple[int, int]]:
    return [(x, y) for x in FIELD for y in FIELD]


def mean(points: Iterable[list[float]]) -> list[float]:
    points = list(points)
    if not points:
        raise ValueError("cannot average empty point set")
    return [sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)]


def nd(p: list[float], q: list[float]) -> float:
    return math.sqrt((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) / math.sqrt(2.0)


def coordinate_delta(a: int, m: int) -> list[float]:
    return mean([
        [
            iota(readout(m, tau(a, x), y))[0] - iota(readout(m, x, y))[0],
            iota(readout(m, tau(a, x), y))[1] - iota(readout(m, x, y))[1],
        ]
        for x, y in pairs()
    ])


def selectivity(m: int, target_multiplier: int) -> dict[str, Any]:
    margins: list[float] = []
    per_mask: dict[str, Any] = {}
    for a in NONZERO:
        delta = coordinate_delta(a, m)
        target = iota(mul(target_multiplier, a))
        correct = nd(delta, target)
        incorrect = min(nd(delta, iota(mul(target_multiplier, b))) for b in NONZERO if b != a)
        margin = incorrect - correct
        margins.append(margin)
        per_mask[NAMES[a]] = {
            "observed_displacement": delta,
            "intended_translation_label": target,
            "correct_distance": correct,
            "incorrect_distance": incorrect,
            "selectivity_margin": margin,
        }
    return {"selectivity": sum(margins) / len(margins), "per_mask": per_mask}


def centroid(m: int) -> list[float]:
    return mean([iota(readout(m, x, y)) for x, y in pairs()])


def balance(m: int) -> float:
    return nd(centroid(m), [0.5, 0.5])


def v4_involution_error() -> float:
    failures = 0
    total = 0
    for a in NONZERO:
        for x in FIELD:
            total += 1
            if tau(a, tau(a, x)) != x:
                failures += 1
    return failures / total if total else 1.0


def fixture() -> dict[str, Any]:
    return {
        "fixture_id": "coordinate-basis-baseline-synthetic-v0",
        "field": "GF(4)=F2[alpha]/(alpha^2+alpha+1)",
        "element_order": [NAMES[x] for x in FIELD],
        "fixture_domain": "GF(4)^2",
        "enumeration": "lexicographic_over_element_order",
        "sample_points": [[NAMES[x], NAMES[y]] for x, y in pairs()],
        "randomness": "none",
        "seed": None,
    }


def receipt(generated_at: str | None = None) -> dict[str, Any]:
    assert_gf4_table()
    generated_at = generated_at or dt.datetime.now(dt.timezone.utc).isoformat()
    results = {
        name: {
            "m": NAMES[m],
            "target_multiplier": NAMES[t],
            "selectivity": selectivity(m, t),
            "balance_metric": balance(m),
        }
        for name, m, t in READOUTS
    }
    result: dict[str, Any] = {
        "artifact_class": "computational_diagnostic_baseline_receipt",
        "evidence_class": "computational_diagnostic_baseline",
        "hash_algorithm": HASH_ALGORITHM,
        "baseline_id": BASELINE_ID,
        "claim_id": CLAIM_ID,
        "convention_id": CONVENTION_ID,
        "diagnostic_ref": str(DIAGNOSTIC),
        "fixture": fixture(),
        "gf4_multiplication_table_verified": True,
        "coordinate_basis_selectivity": sum(v["selectivity"]["selectivity"] for v in results.values()) / len(results),
        "coordinate_basis_balance_metric": sum(v["balance_metric"] for v in results.values()) / len(results),
        "coordinate_basis_involution_error": v4_involution_error(),
        "value_provenance": {
            "coordinate_basis_selectivity": "replayed",
            "coordinate_basis_balance_metric": "replayed",
            "coordinate_basis_involution_error": "analytic",
            "null_centroid": "analytic",
        },
        "readout_results": results,
        "input_hashes": {
            "code_hash": sha_file(Path(__file__)),
            "diagnostic_code_hash": sha_file(DIAGNOSTIC),
            "data_hash": sha_json(fixture()),
            "convention_hash": sha_file(CONVENTION),
            "boundary_hash": sha_file(BOUNDARY),
        },
        "generated_at": generated_at,
        "time_standard": "UTC_ISO_8601",
        "nonclaims": [
            "This baseline receipt is not the corrected readout result.",
            "This baseline receipt is not a prediction outcome.",
            "This baseline receipt is not a null hypothesis.",
            "This baseline receipt is not theorem-facing evidence.",
        ],
    }
    result["output_hashes"] = {"baseline_receipt_hash": sha_json(result)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay coordinate-basis baseline v0.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generated-at", default=None, help="UTC ISO-8601 timestamp to pin receipt generation.")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt(args.generated_at), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
