#!/usr/bin/env python3
"""Generate or update the coordinate/readout diagnostic baseline artifact.

This script intentionally does not invent empirical baseline values.

Modes:
  1. Scaffold-only: emits analytic invariants with empirical fields set to null.
  2. Import: reads a prior coordinate-basis baseline JSON containing selectivity,
     balance metric, and provenance, then emits a complete baseline artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DIAGNOSTIC = Path("experiments/coordinate_readout_cipher_diagnostic.py")
CONVENTION = Path("kb/conventions/GF4-V4-iota-v0.convention.yaml")
BOUNDARY = Path("kb/patterns/coordinate-readout-cipher-experiment-claim-boundary.md")
BASELINE_ID = "coordinate-readout-cipher-v0-baseline"
CLAIM_ID = "COORD_READOUT_INVOLUTION_001"


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return json.dumps(value)


def load_import(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def build_baseline(imported: dict[str, Any] | None = None) -> dict[str, Any]:
    if imported is None:
        selectivity = None
        balance_metric = None
        run_ref = None
        provenance = {
            "code_hash": None,
            "data_hash": None,
            "convention_hash": sha256(CONVENTION),
            "baseline_receipt_hash": None,
        }
        status = "scaffold_pending_empirical_import"
    else:
        selectivity = imported["coordinate_basis_selectivity"]
        balance_metric = imported["coordinate_basis_balance_metric"]
        run_ref = imported.get("run_ref") or imported.get("receipt_hash")
        imported_provenance = imported.get("provenance", {})
        provenance = {
            "code_hash": imported_provenance.get("code_hash") or sha256(DIAGNOSTIC),
            "data_hash": imported_provenance.get("data_hash"),
            "convention_hash": imported_provenance.get("convention_hash") or sha256(CONVENTION),
            "baseline_receipt_hash": imported_provenance.get("baseline_receipt_hash") or run_ref,
        }
        status = "complete_imported_empirical_baseline"

    artifact = {
        "artifact_class": "computational_diagnostic_baseline",
        "status": status,
        "baseline_id": BASELINE_ID,
        "claim_id": CLAIM_ID,
        "diagnostic_ref": str(DIAGNOSTIC),
        "convention_ref": str(CONVENTION),
        "boundary_ref": str(BOUNDARY),
        "coordinate_basis": {
            "involution_error": {
                "value": 0.0,
                "determination": "analytic",
                "rationale": "V4 translations tau_a(x)=x+a are involutions in characteristic 2: a+a=0.",
            },
            "selectivity": {
                "value": selectivity,
                "determination": "empirical_import_required" if imported is None else "empirical_imported",
                "run_ref": run_ref,
                "rationale": "Coordinate-basis selectivity must come from the baseline run; it is not fixed by field axioms alone.",
            },
            "balance_metric": {
                "value": balance_metric,
                "determination": "empirical_import_required" if imported is None else "empirical_imported",
                "null_centroid_analytic": [0.5, 0.5],
                "run_ref": run_ref,
                "rationale": "Analytic null centroid is fixed, but baseline balance metric must be imported or replayed with provenance.",
            },
        },
        "provenance": provenance,
        "nonclaims": [
            "This artifact does not claim a positive or negative diagnostic outcome.",
            "This artifact is not theorem-facing evidence.",
            "Scaffold mode does not produce protocol_valid true for the corrected diagnostic.",
        ],
    }
    artifact["artifact_hash"] = sha256_json(artifact)
    return artifact


def emit_yaml(data: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(emit_yaml(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(emit_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
    else:
        lines.append(f"{prefix}{yaml_scalar(data)}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate coordinate/readout baseline artifact.")
    parser.add_argument("--import-json", type=Path, help="Prior coordinate-basis baseline JSON to import.")
    parser.add_argument("--out", type=Path, help="Output YAML path. Defaults to stdout.")
    args = parser.parse_args()

    artifact = build_baseline(load_import(args.import_json))
    text = "\n".join(emit_yaml(artifact)) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
