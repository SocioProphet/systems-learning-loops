"""Tests for coordinate-basis baseline replay v0."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path("scripts/replay_coordinate_basis_baseline_v0.py")
CONVENTION = Path("kb/conventions/coordinate-basis-baseline-v0.convention.yaml")


def load_module():
    spec = importlib.util.spec_from_file_location("replay_coordinate_basis_baseline_v0", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def convention_multiplication_table() -> tuple[tuple[int, ...], ...]:
    """Parse the committed convention table without adding a YAML dependency."""
    text = CONVENTION.read_text(encoding="utf-8")
    start = text.index("  multiplication_table:")
    end = text.index("\n\ncoordinate_basis:", start)
    block = text[start:end]
    rows: list[tuple[int, ...]] = []
    symbol_to_code = {"0": 0, "1": 1, "alpha": 2, "alpha+1": 3}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        values = stripped.removeprefix("- [").removesuffix("]")
        row = tuple(symbol_to_code[item.strip().strip('"')] for item in values.split(","))
        rows.append(row)
    return tuple(rows)


class CoordinateBasisBaselineReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.replay = load_module()

    def test_gf4_multiplication_table_is_exact(self) -> None:
        self.assertEqual(
            tuple(tuple(row) for row in self.replay.multiplication_table()),
            self.replay.EXPECTED_MUL_TABLE,
        )
        self.replay.assert_gf4_table()

    def test_runtime_multiplication_table_matches_convention_yaml(self) -> None:
        self.assertEqual(
            tuple(tuple(row) for row in self.replay.multiplication_table()),
            convention_multiplication_table(),
        )

    def test_fixture_is_deterministic_all_16_pairs(self) -> None:
        fixture = self.replay.fixture()
        self.assertEqual(fixture["fixture_domain"], "GF(4)^2")
        self.assertEqual(fixture["enumeration"], "lexicographic_over_element_order")
        self.assertEqual(fixture["randomness"], "none")
        self.assertIsNone(fixture["seed"])
        self.assertEqual(len(fixture["sample_points"]), 16)

    def test_replay_receipt_has_required_hash_and_provenance_fields(self) -> None:
        receipt = self.replay.receipt("2026-05-14T18:15:00+00:00")

        self.assertEqual(receipt["artifact_class"], "computational_diagnostic_baseline_receipt")
        self.assertEqual(receipt["evidence_class"], "computational_diagnostic_baseline")
        self.assertEqual(receipt["hash_algorithm"], "sha256")
        self.assertEqual(receipt["convention_id"], "coordinate-basis-baseline-v0")
        self.assertEqual(receipt["time_standard"], "UTC_ISO_8601")
        self.assertTrue(receipt["gf4_multiplication_table_verified"])

        for key in ["code_hash", "data_hash", "convention_hash"]:
            self.assertIn(key, receipt["input_hashes"])
            self.assertIsNotNone(receipt["input_hashes"][key])

        self.assertIn("baseline_receipt_hash", receipt["output_hashes"])
        self.assertIsNotNone(receipt["output_hashes"]["baseline_receipt_hash"])

    def test_metric_values_and_value_provenance_are_explicit(self) -> None:
        receipt = self.replay.receipt("2026-05-14T18:15:00+00:00")

        self.assertEqual(receipt["coordinate_basis_involution_error"], 0.0)
        self.assertEqual(receipt["coordinate_basis_balance_metric"], 0.0)
        self.assertAlmostEqual(receipt["coordinate_basis_selectivity"], -0.09763107293781752)
        self.assertEqual(receipt["value_provenance"]["coordinate_basis_involution_error"], "analytic")
        self.assertEqual(receipt["value_provenance"]["null_centroid"], "analytic")
        self.assertEqual(receipt["value_provenance"]["coordinate_basis_selectivity"], "replayed")
        self.assertEqual(receipt["value_provenance"]["coordinate_basis_balance_metric"], "replayed")

    def test_receipt_is_baseline_not_prediction_outcome(self) -> None:
        receipt = self.replay.receipt("2026-05-14T18:15:00+00:00")
        self.assertNotIn("prediction_outcome", receipt)
        self.assertNotIn("protocol_valid", receipt)
        nonclaims = "\n".join(receipt["nonclaims"])
        self.assertIn("not the corrected readout result", nonclaims)
        self.assertIn("not a prediction outcome", nonclaims)
        self.assertIn("not theorem-facing evidence", nonclaims)


if __name__ == "__main__":
    unittest.main()
