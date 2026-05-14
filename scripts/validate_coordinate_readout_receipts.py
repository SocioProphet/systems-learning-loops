#!/usr/bin/env python3
"""Validate coordinate/readout diagnostic receipt semantics.

This checker enforces the outcome semantics defined in:

    kb/patterns/coordinate-readout-diagnostic-outcomes.md

It intentionally checks receipt structure and outcome consistency only. It does
not run the diagnostic and does not assert that any diagnostic outcome occurred.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "coordinate-readout" / "valid"
INVALID_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "coordinate-readout" / "invalid"

ALLOWED_OUTCOMES = {
    "protocol_incomplete",
    "falsified_directional",
    "weak_support",
    "empirical_pair_confirmed",
}
POSITIVE_OUTCOMES = {"weak_support", "empirical_pair_confirmed"}
REQUIRED_POSITIVE_METRICS = {
    "selectivity_lift_vs_coordinate",
    "balance_metric_corrected",
    "balance_metric_coordinate",
    "involution_error",
    "tolerance",
    "confirmation_threshold",
}
REQUIRED_FALSIFICATION_STATUS = {
    "selectivity_lift_vs_coordinate",
    "selectivity_threshold",
    "selectivity_passed",
    "balance_metric_corrected",
    "balance_metric_coordinate",
    "balance_passed",
    "involution_error",
    "involution_tolerance",
    "involution_passed",
}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path}: expected JSON object")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_number(value: Any, field: str) -> float:
    require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} must be numeric")
    return float(value)


def statuses(receipt: dict[str, Any]) -> tuple[bool, str]:
    status_block = receipt.get("statuses")
    require(isinstance(status_block, dict), "missing statuses object")
    protocol_valid = status_block.get("protocol_valid")
    outcome = status_block.get("prediction_outcome")
    require(isinstance(protocol_valid, bool), "statuses.protocol_valid must be boolean")
    require(isinstance(outcome, str) and outcome in ALLOWED_OUTCOMES, "invalid statuses.prediction_outcome")
    return protocol_valid, outcome


def validate_positive(receipt: dict[str, Any], outcome: str) -> None:
    require("positive_outcome_metrics" in receipt, f"{outcome} requires positive_outcome_metrics")
    require("falsification_evidence" not in receipt, f"{outcome} must not include falsification_evidence")
    metrics = receipt["positive_outcome_metrics"]
    require(isinstance(metrics, dict), "positive_outcome_metrics must be object")
    missing = REQUIRED_POSITIVE_METRICS - set(metrics)
    require(not missing, f"positive_outcome_metrics missing {sorted(missing)}")

    lift = require_number(metrics["selectivity_lift_vs_coordinate"], "selectivity_lift_vs_coordinate")
    corrected_balance = require_number(metrics["balance_metric_corrected"], "balance_metric_corrected")
    coordinate_balance = require_number(metrics["balance_metric_coordinate"], "balance_metric_coordinate")
    involution_error = require_number(metrics["involution_error"], "involution_error")
    tolerance = require_number(metrics["tolerance"], "tolerance")
    threshold = require_number(metrics["confirmation_threshold"], "confirmation_threshold")

    require(corrected_balance <= coordinate_balance, "positive outcome requires balance non-regression")
    require(involution_error <= tolerance, "positive outcome requires involution tolerance pass")
    require(threshold == 5.0, "v0 confirmation threshold must be 5")
    if outcome == "weak_support":
        require(lift > 1.0, "weak_support requires lift > 1")
        require(lift < threshold, "weak_support requires lift < confirmation threshold")
    elif outcome == "empirical_pair_confirmed":
        require(lift >= threshold, "empirical_pair_confirmed requires lift >= confirmation threshold")


def validate_falsification(receipt: dict[str, Any]) -> None:
    require("falsification_evidence" in receipt, "falsified_directional requires falsification_evidence")
    require("positive_outcome_metrics" not in receipt, "falsified_directional must not include positive_outcome_metrics")
    evidence = receipt["falsification_evidence"]
    require(isinstance(evidence, dict), "falsification_evidence must be object")

    triggering = evidence.get("triggering_conditions")
    require(isinstance(triggering, list) and triggering, "triggering_conditions must be non-empty list")
    require(all(isinstance(item, str) for item in triggering), "triggering_conditions entries must be strings")

    status = evidence.get("all_conditions_status")
    require(isinstance(status, dict), "all_conditions_status must be object")
    missing = REQUIRED_FALSIFICATION_STATUS - set(status)
    require(not missing, f"all_conditions_status missing {sorted(missing)}")

    lift = require_number(status["selectivity_lift_vs_coordinate"], "selectivity_lift_vs_coordinate")
    selectivity_threshold = require_number(status["selectivity_threshold"], "selectivity_threshold")
    corrected_balance = require_number(status["balance_metric_corrected"], "balance_metric_corrected")
    coordinate_balance = require_number(status["balance_metric_coordinate"], "balance_metric_coordinate")
    involution_error = require_number(status["involution_error"], "involution_error")
    involution_tolerance = require_number(status["involution_tolerance"], "involution_tolerance")

    require(selectivity_threshold == 1.0, "falsification selectivity threshold must be 1")
    require(isinstance(status["selectivity_passed"], bool), "selectivity_passed must be boolean")
    require(isinstance(status["balance_passed"], bool), "balance_passed must be boolean")
    require(isinstance(status["involution_passed"], bool), "involution_passed must be boolean")

    expected_selectivity_passed = lift > selectivity_threshold
    expected_balance_passed = corrected_balance <= coordinate_balance
    expected_involution_passed = involution_error <= involution_tolerance
    require(status["selectivity_passed"] == expected_selectivity_passed, "selectivity_passed mismatch")
    require(status["balance_passed"] == expected_balance_passed, "balance_passed mismatch")
    require(status["involution_passed"] == expected_involution_passed, "involution_passed mismatch")
    require(status["involution_passed"] is True, "falsified_directional requires involution_passed true")

    expected_triggers: list[str] = []
    if not expected_selectivity_passed:
        expected_triggers.append("selectivity_lift_vs_coordinate <= 1")
    if not expected_balance_passed:
        expected_triggers.append("balance_metric_corrected > balance_metric_coordinate")
    require(sorted(triggering) == sorted(expected_triggers), "triggering_conditions must match failed prediction conditions exactly")
    require(expected_triggers, "falsified_directional requires at least one prediction-condition failure")


def validate_protocol_incomplete(receipt: dict[str, Any]) -> None:
    require("positive_outcome_metrics" not in receipt, "protocol_incomplete must not include positive_outcome_metrics")
    require("falsification_evidence" not in receipt, "protocol_incomplete must not include falsification_evidence")
    reasons = receipt.get("protocol_failure_reasons")
    require(isinstance(reasons, list) and reasons, "protocol_incomplete requires non-empty protocol_failure_reasons")
    require(all(isinstance(item, str) for item in reasons), "protocol_failure_reasons entries must be strings")


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(receipt.get("evidence_class") == "computational_diagnostic", "evidence_class must be computational_diagnostic")
    protocol_valid, outcome = statuses(receipt)

    if not protocol_valid:
        require(outcome == "protocol_incomplete", "protocol_valid=false requires protocol_incomplete")
        validate_protocol_incomplete(receipt)
        return

    require(outcome != "protocol_incomplete", "protocol_valid=true cannot be protocol_incomplete")
    if outcome in POSITIVE_OUTCOMES:
        validate_positive(receipt, outcome)
    elif outcome == "falsified_directional":
        validate_falsification(receipt)
    else:
        raise ValidationError(f"unsupported protocol-valid outcome: {outcome}")


def validate_path(path: Path, expect_valid: bool) -> None:
    try:
        validate_receipt(load_json(path))
    except ValidationError as exc:
        if expect_valid:
            raise ValidationError(f"{path}: expected valid receipt, got {exc}") from exc
        print(f"ok: rejected {path} ({exc})")
        return
    if not expect_valid:
        raise ValidationError(f"{path}: invalid fixture unexpectedly passed")
    print(f"ok: accepted {path}")


def validate_fixtures() -> None:
    valid_paths = sorted(VALID_FIXTURE_DIR.glob("*.json"))
    invalid_paths = sorted(INVALID_FIXTURE_DIR.glob("*.json"))
    require(valid_paths, f"no valid fixtures found in {VALID_FIXTURE_DIR}")
    require(invalid_paths, f"no invalid fixtures found in {INVALID_FIXTURE_DIR}")
    for path in valid_paths:
        validate_path(path, expect_valid=True)
    for path in invalid_paths:
        validate_path(path, expect_valid=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate coordinate/readout diagnostic receipt semantics")
    parser.add_argument("receipt", nargs="?", help="Optional single receipt JSON to validate")
    parser.add_argument("--expect-invalid", action="store_true", help="Expect the single receipt to fail validation")
    args = parser.parse_args()

    try:
        if args.receipt:
            validate_path(Path(args.receipt), expect_valid=not args.expect_invalid)
        else:
            validate_fixtures()
    except ValidationError as exc:
        print(f"ERR: {exc}", file=sys.stderr)
        return 2
    print("OK: coordinate/readout receipt validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
