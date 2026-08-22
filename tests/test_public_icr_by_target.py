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

    def test_corrected_revalidation_status_is_committed(self) -> None:
        path = ROOT / "outputs" / "human_validation" / "HUMAN_VALIDATION_STATUS.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("corrected revalidation complete", text.casefold())
        self.assertIn("1,032 paired", text)
        self.assertIn("Human Ethics Protocol 2025/697", text)
        self.assertIn("Ausma Bernot", text)
        self.assertIn("Milind Tiwari", text)
        self.assertTrue((path.parent / "human_icr_by_target.csv").exists())

    def test_committed_target_schema_matches_the_generator(self) -> None:
        path = ROOT / "outputs" / "human_validation" / "human_icr_by_target.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader)
        self.assertEqual(header, list(public_icr.OUTPUT_FIELDS))

        metadata = json.loads(
            (path.parent / "human_icr_target_metadata.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["target_count"], 18)
        self.assertEqual(metadata["paired_units"], 1032)
        self.assertEqual(metadata["adjudicated_disagreements"], 51)
        self.assertEqual(len(metadata["controlled_input_sha256"]), 3)
        self.assertEqual(len(metadata["frozen_coder_workbook_sha256"]), 2)

    def test_markdown_renderer_handles_undefined_reliability_metrics(self) -> None:
        payload = {
            "unreconciled_human_icr": {
                "five_category_metrics": {
                    "n": 40,
                    "agreement_percent": 100.0,
                    "cohen_kappa": None,
                    "krippendorff_alpha_nominal": None,
                },
                "present_absent_subset": {
                    "n": 40,
                    "agreement_percent": 100.0,
                    "cohen_kappa": None,
                },
            }
        }
        row = {field: 0 for field in public_icr.OUTPUT_FIELDS}
        row.update(
            code="vulnerable_group_exploitation",
            target_group="typology",
            paired_units=40,
            exact_agreements=40,
            agreement_percent=100.0,
            agreement_ci95_low_percent=91.238,
            agreement_ci95_high_percent=100.0,
            cohen_kappa="",
            cohen_kappa_bootstrap_ci95_low="",
            cohen_kappa_bootstrap_ci95_high="",
            krippendorff_alpha_nominal="",
            binary_subset_units=40,
            binary_subset_exact_agreements=40,
            binary_subset_agreement_percent=100.0,
            binary_subset_cohen_kappa="",
            binary_subset_gwet_ac1=1.0,
            binary_subset_gwet_ac1_bootstrap_ci95_low=1.0,
            binary_subset_gwet_ac1_bootstrap_ci95_high=1.0,
        )
        rendered = public_icr.render_markdown(payload, [row])
        self.assertIn("NA", rendered)
        self.assertIn("All 0 frozen disagreements", rendered)



if __name__ == "__main__":
    unittest.main()
