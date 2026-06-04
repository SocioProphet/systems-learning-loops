#!/usr/bin/env python3
"""Validate institutional-learning receipt structure.

This validator enforces receipt discipline without judging claim truth. A receipt
is valid when it preserves the learning-control chain: sources, claims, patterns,
countermeasures, authority surface, gates, teaching references, reobservation,
and explicit claim boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"ERROR: pyyaml required. Install with: pip install pyyaml ({exc})")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT_GLOB = ROOT / "kb" / "receipts"

ALLOWED_STATUSES = {"provisional", "active", "superseded", "revoked"}
REQUIRED_TOP_LEVEL_FIELDS = [
    "receipt_id",
    "status",
    "date",
    "lesson_summary",
    "source_refs",
    "claim_refs",
    "pattern_refs",
    "countermeasure_refs",
    "authority_surface",
    "gate_refs",
    "teaching_refs",
    "reobservation_plan",
    "claim_boundary",
]
REQUIRED_AUTHORITY_FIELDS = ["repo", "artifact"]
REQUIRED_REOBSERVATION_FIELDS = [
    "confirming_signal",
    "weakening_signal",
    "supersession_trigger",
    "review_cadence",
]


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"receipt must be a mapping: {path}")
    return data


def check(check_id: str, passed: bool, diagnostics: list[str] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "passed": bool(passed), "diagnostics": diagnostics or []}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def validate_receipt(path: Path) -> list[dict[str, Any]]:
    data = load_yaml(path)
    receipt_id = str(data.get("receipt_id", path.name))
    results: list[dict[str, Any]] = []

    missing = [field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in data]
    results.append(check(f"{path.name}:required-fields", not missing, missing))

    results.append(check(
        f"{path.name}:receipt-id-prefix",
        isinstance(data.get("receipt_id"), str) and data["receipt_id"].startswith("il.receipt."),
        [] if isinstance(data.get("receipt_id"), str) and data["receipt_id"].startswith("il.receipt.") else ["receipt_id must start with il.receipt."],
    ))

    status = data.get("status")
    results.append(check(
        f"{path.name}:status",
        status in ALLOWED_STATUSES,
        [] if status in ALLOWED_STATUSES else [f"status must be one of {sorted(ALLOWED_STATUSES)}"],
    ))

    for field in ["lesson_summary", "claim_boundary"]:
        results.append(check(
            f"{path.name}:{field}",
            _nonempty_string(data.get(field)),
            [] if _nonempty_string(data.get(field)) else [f"{field} must be a non-empty string"],
        ))

    for field in ["source_refs", "claim_refs", "pattern_refs", "countermeasure_refs", "gate_refs", "teaching_refs"]:
        results.append(check(
            f"{path.name}:{field}",
            _nonempty_list(data.get(field)),
            [] if _nonempty_list(data.get(field)) else [f"{field} must be a non-empty list of strings"],
        ))

    authority = data.get("authority_surface", {})
    authority_diagnostics: list[str] = []
    if not isinstance(authority, dict):
        authority_diagnostics.append("authority_surface must be a mapping")
    else:
        for field in REQUIRED_AUTHORITY_FIELDS:
            if not _nonempty_string(authority.get(field)):
                authority_diagnostics.append(f"authority_surface.{field} is required")
        if not (authority.get("gate") or authority.get("supporting_artifacts")):
            authority_diagnostics.append("authority_surface must include gate or supporting_artifacts")
    results.append(check(f"{path.name}:authority-surface", not authority_diagnostics, authority_diagnostics))

    reobs = data.get("reobservation_plan", {})
    reobs_diagnostics: list[str] = []
    if not isinstance(reobs, dict):
        reobs_diagnostics.append("reobservation_plan must be a mapping")
    else:
        for field in REQUIRED_REOBSERVATION_FIELDS:
            if not _nonempty_string(reobs.get(field)):
                reobs_diagnostics.append(f"reobservation_plan.{field} is required")
    results.append(check(f"{path.name}:reobservation-plan", not reobs_diagnostics, reobs_diagnostics))

    source_refs = set(data.get("source_refs", []) if isinstance(data.get("source_refs"), list) else [])
    gate_refs = set(data.get("gate_refs", []) if isinstance(data.get("gate_refs"), list) else [])
    if source_refs and gate_refs:
        shared_or_same_repo = bool(source_refs & gate_refs) or any(str(g).split(":", 1)[0] in {str(s).split(":", 1)[0] for s in source_refs} for g in gate_refs)
        results.append(check(
            f"{path.name}:gate-source-coherence",
            shared_or_same_repo,
            [] if shared_or_same_repo else ["gate_refs should share at least one authority repo with source_refs"],
        ))

    return results


def discover_receipts(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(path) for path in paths]
    return sorted(DEFAULT_RECEIPT_GLOB.glob("*.receipt.yaml"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    receipt_paths = discover_receipts(args.paths)
    if not receipt_paths:
        raise SystemExit("ERROR: no receipt files found")

    results: list[dict[str, Any]] = []
    for path in receipt_paths:
        results.extend(validate_receipt(path))

    passed = all(item["passed"] for item in results)
    print(json.dumps({"validator": "systems-learning-loops.learning-receipts.validator.v1", "passed": passed, "receipts": [str(path) for path in receipt_paths], "results": results}, indent=2, sort_keys=True))
    print(("PASS" if passed else "FAIL") + ": learning receipts")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
