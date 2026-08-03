#!/usr/bin/env python3
"""Validate self-improving-loop experience/improvement records (EG-1).

An *experience record* is one trajectory step of the estate's self-improving loop
(the "experience generator": generate -> measure -> keep-if-better). Where the
qualitative learning receipt (validate_learning_receipts.py) preserves the
learning-control chain, this record pins the QUANTITATIVE claim: "the candidate
improved on the baseline".

The teeth (a claim without evidence is not admitted):

  1. An improvement claim MUST carry a measured delta: baseline.value,
     candidate.value, and delta, with delta == candidate.value - baseline.value.
  2. The delta MUST be in the improving direction (higher_better => delta > 0,
     lower_better => delta < 0). A non-improving delta cannot claim improvement.
  3. min-n >= 30 (estate rule, cf. guild-knowledge-network min_n_for_calibrated):
     effective n = min(baseline.n, candidate.n). If n < 30 the record MUST be
     status 'provisional' — it may not claim 'active'. Small samples are flagged,
     not promoted.
  4. Provenance via the estate receipt spine (SHA-256, FIPS 180-4): input_hash is
     recomputed over the improvement block and receipt_hash over the whole record
     (minus receipt_hash); both must match. Tampering with the measured delta after
     the fact breaks the hash and is rejected. Convention mirrors
     prophet-workspace tools/proof-artifact-spine.

Exit non-zero on any failure, so it plugs into the Makefile the same way the
learning-receipts validator does.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GLOB = ROOT / "kb" / "experience"

ALLOWED_STATUSES = {"provisional", "active", "superseded", "revoked"}
ALLOWED_DIRECTIONS = {"higher_better", "lower_better"}
MIN_N = 30  # estate min-n rule; a claim below this may not be promoted past provisional
EPS = 1e-9

REQUIRED_TOP_LEVEL = [
    "record_id",
    "status",
    "date",
    "loop",
    "task",
    "improvement",
    "evidence_refs",
    "evidence_grade",
    "claim_boundary",
    "receipt",
]


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_string(x) for x in value)


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == len("sha256:") + 64


def check(check_id: str, passed: bool, diagnostics: list[str] | None = None) -> dict[str, Any]:
    return {"check_id": check_id, "passed": bool(passed), "diagnostics": diagnostics or []}


def load_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"record must be an object: {path}")
    return data


def _validate_endpoint(imp: dict[str, Any], key: str, diags: list[str]) -> None:
    ep = imp.get(key)
    if not isinstance(ep, dict):
        diags.append(f"improvement.{key} must be an object with value and n")
        return
    if not _is_number(ep.get("value")):
        diags.append(f"improvement.{key}.value must be a number")
    n = ep.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        diags.append(f"improvement.{key}.n must be a non-negative integer")


def validate_record(path: Path) -> list[dict[str, Any]]:
    data = load_record(path)
    name = path.name
    results: list[dict[str, Any]] = []

    missing = [f for f in REQUIRED_TOP_LEVEL if f not in data]
    results.append(check(f"{name}:required-fields", not missing, missing))

    rid = data.get("record_id")
    ok = isinstance(rid, str) and rid.startswith("il.experience.")
    results.append(check(f"{name}:record-id-prefix", ok,
                         [] if ok else ["record_id must start with il.experience."]))

    status = data.get("status")
    results.append(check(f"{name}:status", status in ALLOWED_STATUSES,
                         [] if status in ALLOWED_STATUSES else [f"status must be one of {sorted(ALLOWED_STATUSES)}"]))

    for field in ["task", "claim_boundary", "evidence_grade"]:
        results.append(check(f"{name}:{field}", _nonempty_string(data.get(field)),
                             [] if _nonempty_string(data.get(field)) else [f"{field} must be a non-empty string"]))

    results.append(check(f"{name}:evidence_refs", _nonempty_list(data.get("evidence_refs")),
                         [] if _nonempty_list(data.get("evidence_refs")) else ["evidence_refs must be a non-empty list of strings"]))

    # --- improvement block structure ---
    imp = data.get("improvement")
    struct_diags: list[str] = []
    if not isinstance(imp, dict):
        struct_diags.append("improvement must be an object")
        imp = {}
    else:
        if not _nonempty_string(imp.get("metric")):
            struct_diags.append("improvement.metric must be a non-empty string")
        if imp.get("direction") not in ALLOWED_DIRECTIONS:
            struct_diags.append(f"improvement.direction must be one of {sorted(ALLOWED_DIRECTIONS)}")
        _validate_endpoint(imp, "baseline", struct_diags)
        _validate_endpoint(imp, "candidate", struct_diags)
        if not _is_number(imp.get("delta")):
            struct_diags.append("improvement.delta must be a number (a claim without a measured delta is not admitted)")
    results.append(check(f"{name}:improvement-structure", not struct_diags, struct_diags))

    structurally_ok = not struct_diags

    # --- TOOTH 1: delta is a real, consistent measured delta ---
    if structurally_ok:
        expected = imp["candidate"]["value"] - imp["baseline"]["value"]
        consistent = abs(imp["delta"] - expected) <= EPS
        results.append(check(f"{name}:delta-consistency", consistent,
                             [] if consistent else [f"delta {imp['delta']} != candidate-baseline {expected}"]))

        # --- TOOTH 2: delta is in the improving direction ---
        if imp["direction"] == "higher_better":
            improving = imp["delta"] > 0
        else:
            improving = imp["delta"] < 0
        results.append(check(f"{name}:improving-direction", improving,
                             [] if improving else [f"delta {imp['delta']} is not an improvement for direction {imp['direction']}"]))

        # --- TOOTH 3: min-n >= 30 provisional flag ---
        n_eff = min(imp["baseline"]["n"], imp["candidate"]["n"])
        min_n_ok = n_eff >= MIN_N or status == "provisional"
        results.append(check(f"{name}:min-n-provisional", min_n_ok,
                             [] if min_n_ok else [f"effective n={n_eff} < {MIN_N}: status must be 'provisional', got '{status}'"]))

    # --- TOOTH 4: receipt spine (recomputed SHA-256) ---
    receipt = data.get("receipt")
    receipt_diags: list[str] = []
    if not isinstance(receipt, dict):
        receipt_diags.append("receipt must be an object")
    else:
        if receipt.get("algorithm") != "sha256":
            receipt_diags.append("receipt.algorithm must be 'sha256'")
        if not _is_hash(receipt.get("input_hash")):
            receipt_diags.append("receipt.input_hash must be sha256:<64 hex>")
        if not _is_hash(receipt.get("receipt_hash")):
            receipt_diags.append("receipt.receipt_hash must be sha256:<64 hex>")
        if not receipt_diags and structurally_ok:
            expected_input = _sha256(_canonical(imp))
            if receipt["input_hash"] != expected_input:
                receipt_diags.append("receipt.input_hash does not match sha256(improvement) — measured delta was tampered or mis-hashed")
            body = copy.deepcopy(data)
            body["receipt"].pop("receipt_hash", None)
            expected_receipt = _sha256(_canonical(body))
            if receipt["receipt_hash"] != expected_receipt:
                receipt_diags.append("receipt.receipt_hash does not match sha256(record minus receipt_hash) — record was tampered or mis-hashed")
    results.append(check(f"{name}:receipt-spine", not receipt_diags, receipt_diags))

    return results


def discover(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(p) for p in paths]
    return sorted(DEFAULT_GLOB.glob("*.experience.json"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    record_paths = discover(args.paths)
    if not record_paths:
        raise SystemExit("ERROR: no experience records found")

    results: list[dict[str, Any]] = []
    for path in record_paths:
        results.extend(validate_record(path))

    passed = all(item["passed"] for item in results)
    print(json.dumps({
        "validator": "systems-learning-loops.experience-records.validator.v1",
        "passed": passed,
        "records": [str(p) for p in record_paths],
        "results": results,
    }, indent=2, sort_keys=True))
    print(("PASS" if passed else "FAIL") + ": experience records")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
