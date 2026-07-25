from __future__ import annotations

import csv
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "code" / "human_validation" / "build_public_icr_by_target.py"
)
SPEC = importlib.util.spec_from_file_location("public_icr_for_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
public_icr = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = public_icr
SPEC.loader.exec_module(public_icr)


class PublicICRByTargetTests(unittest.TestCase):
    def test_binary_gwet_ac1_perfect_agreement(self) -> None:
        pairs = [
            ("Present", "Present"),
            ("Present", "Present"),
            ("Absent", "Absent"),
            ("Absent", "Absent"),
        ]
        self.assertEqual(public_icr.gwet_ac1_binary(pairs), 1.0)

    def test_wilson_interval_contains_observed_agreement(self) -> None:
        low, high = public_icr.wilson_interval(49, 56)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        assert low is not None and high is not None
        self.assertLess(low, 49 / 56)
        self.assertGreater(high, 49 / 56)

    def test_committed_target_table_reconciles_to_frozen_totals(self) -> None:
        path = ROOT / "outputs" / "human_validation" / "human_icr_by_target.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 18)
        self.assertEqual(len({row["code"] for row in rows}), 18)
        self.assertEqual(sum(int(row["paired_units"]) for row in rows), 1036)
        self.assertEqual(sum(int(row["exact_agreements"]) for row in rows), 977)
        self.assertEqual(sum(int(row["disagreements"]) for row in rows), 59)
        self.assertEqual(
            sum(int(row["adjudicated_disagreements"]) for row in rows), 59
        )
        self.assertEqual(sum(int(row["final_present"]) for row in rows), 13)
        self.assertEqual(sum(int(row["final_absent"]) for row in rows), 16)
        self.assertEqual(sum(int(row["final_ambiguous"]) for row in rows), 30)
        self.assertEqual(
            sum(int(row["final_insufficient_evidence"]) for row in rows), 0
        )
        self.assertEqual(
            sum(int(row["final_out_of_scope_record"]) for row in rows), 0
        )
        metadata = json.loads(
            (ROOT / "outputs" / "human_validation" / "human_icr_target_metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["target_count"], 18)
        self.assertEqual(metadata["paired_units"], 1036)
        self.assertEqual(metadata["adjudicated_disagreements"], 59)
        self.assertEqual(len(metadata["controlled_input_sha256"]), 3)
        self.assertEqual(len(metadata["frozen_coder_workbook_sha256"]), 2)
        self.assertTrue(
            all(
                len(value) == 64
                for value in metadata["controlled_input_sha256"].values()
            )
        )
        for row in rows:
            self.assertLessEqual(
                float(row["agreement_ci95_low_percent"]),
                float(row["agreement_percent"]),
            )
            self.assertGreaterEqual(
                float(row["agreement_ci95_high_percent"]),
                float(row["agreement_percent"]),
            )
            self.assertTrue(-1 <= float(row["cohen_kappa"]) <= 1)
            self.assertTrue(-1 <= float(row["binary_subset_gwet_ac1"]) <= 1)


if __name__ == "__main__":
    unittest.main()
