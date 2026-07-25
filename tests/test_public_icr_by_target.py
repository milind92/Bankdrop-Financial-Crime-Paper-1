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

    def test_withdrawn_validation_status_is_committed(self) -> None:
        path = ROOT / "outputs" / "human_validation" / "HUMAN_VALIDATION_STATUS.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("withdrawn", text.casefold())
        self.assertIn("14 internal", text)
        self.assertFalse((path.parent / "human_icr_by_target.csv").exists())


if __name__ == "__main__":
    unittest.main()
