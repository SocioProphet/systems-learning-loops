"""Tests for the coordinate/readout cipher computational diagnostic."""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path

from experiments import coordinate_readout_cipher_diagnostic as diag


class CoordinateReadoutCipherDiagnosticTests(unittest.TestCase):
    def _baseline_file(self, payload: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        with tmp:
            json.dump(payload, tmp)
        return Path(tmp.name)

    def _baseline(self, selectivity: float, balance: float) -> dict:
        return {
            "provided": True,
            "coordinate_basis_involution_error": 0.0,
            "coordinate_basis_selectivity": selectivity,
            "coordinate_basis_balance_metric": balance,
            "provenance": {
                "code_hash": "baseline-code",
                "data_hash": "baseline-data",
                "convention_hash": "baseline-convention",
            },
        }

    def test_gf4_presentation_and_v4_translation_involution(self) -> None:
        self.assertEqual(diag.gf4_mul(2, 2), 3)  # alpha^2 = alpha + 1
        self.assertEqual(diag.gf4_mul(2, 3), 1)
        self.assertEqual(diag.gf4_mul(3, 3), 2)

        for a in diag.NONZERO_ELEMENTS:
            for x in diag.FIELD_ELEMENTS:
                self.assertEqual(diag.tau(a, diag.tau(a, x)), x)

        self.assertEqual(diag.v4_involution_error(), 0.0)

    def test_l_alpha_is_not_treated_as_involution(self) -> None:
        # Boundary correction guard: the affine readout map L_alpha is not the
        # involution being tested. This input witnesses that repeated use of
        # L_alpha-style transformation on the first coordinate would not be id.
        x, y = 1, 1
        once = diag.l_m(2, x, y)
        twice = diag.l_m(2, once, y)
        self.assertNotEqual(twice, x)

    def test_z4_rejection_is_executed_negative_control(self) -> None:
        rejection = diag.z4_rejection()
        self.assertTrue(rejection["z4_rejected"])
        self.assertEqual(rejection["z4_generator_order"], 4)
        self.assertEqual(rejection["v4_nonzero_translation_order"], 2)

    def test_iota_and_analytic_centroid_are_pinned(self) -> None:
        self.assertEqual(diag.iota(0), (0.0, 0.0))
        self.assertEqual(diag.iota(1), (1.0, 0.0))
        self.assertEqual(diag.iota(2), (0.0, 1.0))
        self.assertEqual(diag.iota(3), (1.0, 1.0))

        self.assertEqual(diag.analytic_null_centroid(), (0.5, 0.5))
        self.assertEqual(diag.centroid_for_readout(1), (0.5, 0.5))
        self.assertEqual(diag.centroid_for_readout(2), (0.5, 0.5))
        self.assertEqual(diag.balance_metric(1), 0.0)

    def test_selectivity_uses_group_displacement_not_euclidean_subtraction(self) -> None:
        for a in diag.NONZERO_ELEMENTS:
            self.assertEqual(diag.observed_displacement_for_translation(a, 1), diag.iota(a))

        result = diag.selectivity_for_readout(1, target_multiplier=1)
        self.assertGreater(result["selectivity"], 0.0)

    def test_receipt_carries_boundary_version_and_evidence_class(self) -> None:
        baseline_path = self._baseline_file(self._baseline(selectivity=0.015, balance=1.0))
        receipt = diag.compute_receipt(baseline_path=baseline_path, code_hash="impl-code")

        self.assertEqual(receipt["evidence_class"], "computational_diagnostic")
        self.assertEqual(receipt["boundary_version"]["merge_commit"], diag.BOUNDARY_MERGE_COMMIT)
        self.assertEqual(receipt["construction"]["presentation"], "F2[alpha]/(alpha^2 + alpha + 1)")
        self.assertEqual(receipt["construction"]["mols_pair"], ["L_1", "L_alpha"])
        self.assertEqual(receipt["construction"]["involution_operators"], "V4_translations_tau_a")
        self.assertTrue(receipt["construction"]["z4_rejected"])
        self.assertEqual(receipt["readout_basis"]["embedding"], "iota_GF4_to_F2xF2")
        self.assertEqual(receipt["provenance"]["code_hash"], "impl-code")

    def test_protocol_valid_and_prediction_confirmed_are_separate(self) -> None:
        strong_baseline = self._baseline_file(self._baseline(selectivity=1.0, balance=0.0))
        receipt = diag.compute_receipt(baseline_path=strong_baseline, code_hash="impl-code")

        self.assertTrue(receipt["statuses"]["protocol_valid"])
        self.assertEqual(receipt["statuses"]["prediction_outcome"], "falsified_directional")

    def test_missing_baseline_is_protocol_incomplete_not_prediction_result(self) -> None:
        receipt = diag.compute_receipt(baseline_path=None, code_hash="impl-code")

        self.assertFalse(receipt["statuses"]["protocol_valid"])
        self.assertEqual(receipt["statuses"]["prediction_outcome"], "protocol_incomplete")
        self.assertIsNone(receipt["corrected_run"]["selectivity_lift_vs_coordinate"])

    def test_no_scope_creep_terms_or_theorem_facing_claims(self) -> None:
        source = inspect.getsource(diag)
        forbidden = [
            "Z9",
            "S3",
            "alternative embedding",
            "proves",
            "theorem-facing",
            "A2 track validates",
            "Clay progress",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
