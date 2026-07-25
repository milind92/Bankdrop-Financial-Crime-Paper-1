from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "code" / "derived_analysis" / "build_derived_analysis.py"
SPEC = importlib.util.spec_from_file_location("derived_analysis_for_tests", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
derived = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = derived
SPEC.loader.exec_module(derived)



class DerivedAnalysisTests(unittest.TestCase):
    def test_fixture_builds_reconciled_aggregate_statistics(self) -> None:
        corpus = [
            {"note_id": "n1", "source": "s1", "combined_word_count": "3", "combined_text_sha256": "h1", "markdown_present": "1", "ocr_present": "0"},
            {"note_id": "n2", "source": "s1", "combined_word_count": "3", "combined_text_sha256": "h1", "markdown_present": "1", "ocr_present": "0"},
            {"note_id": "n3", "source": "s2", "combined_word_count": "2", "combined_text_sha256": "h2", "markdown_present": "1", "ocr_present": "1"},
            {"note_id": "n4", "source": "s2", "combined_word_count": "0", "combined_text_sha256": "h3", "markdown_present": "0", "ocr_present": "0"},
        ]
        populations, source_by_note, _, metadata = derived.build_populations(corpus)
        presence = {
            "bank_log_sale": {"n1", "n2"},
            "bank_drop_sale": {"n1", "n2", "n3"},
        }
        labels = {
            "bank_log_sale": "Bank log",
            "bank_drop_sale": "Bank drop",
        }
        duplicate_rows = derived.build_duplicate_sensitivity(
            presence, labels, populations
        )
        cooccurrence = derived.build_cooccurrence(
            presence, labels, populations
        )
        by_source, leave_one_out = derived.build_cooccurrence_source_stability(
            presence, labels, populations, source_by_note
        )
        source_normalized = derived.build_source_normalized(
            presence, labels, populations, source_by_note, corpus
        )

        self.assertEqual(
            {name: len(rows) for name, rows in populations.items()},
            {"full_screened": 4, "exact_text_unique_sensitivity": 3},
        )
        self.assertEqual(metadata["exact_duplicate_excess_records_n"], 1)
        self.assertEqual(metadata["zero_combined_word_records_n"], 1)
        self.assertEqual(len(duplicate_rows), 2)
        self.assertEqual(len(cooccurrence), 2)
        self.assertEqual(len(by_source), 4)
        self.assertEqual(len(leave_one_out), 4)
        self.assertEqual(len(source_normalized), 8)
        self.assertTrue(
            all(
                int(row["n11_both_present"])
                + int(row["n10_a_only"])
                + int(row["n01_b_only"])
                + int(row["n00_neither"])
                == int(row["source_denominator_n"])
                for row in by_source
            )
        )
        full = next(
            row for row in cooccurrence if row["population"] == "full_screened"
        )
        self.assertEqual(
            sum(
                int(full[field])
                for field in (
                    "n11_both_present",
                    "n10_a_only",
                    "n01_b_only",
                    "n00_neither",
                )
            ),
            4,
        )
        self.assertEqual(int(full["n11_both_present"]), 2)
        self.assertEqual(
            int(full["n10_a_only"]) + int(full["n01_b_only"]), 1
        )

    def test_structural_typology_aml_pairs_are_excluded(self) -> None:
        populations = {"full_screened": {"n1"}}
        original_labels = derived.POPULATION_LABELS
        try:
            derived.POPULATION_LABELS = {"full_screened": "fixture"}
            rows = derived.build_aml_crosswalk(
                {"bank_log_sale": {"n1"}, "bank_drop_sale": {"n1"}},
                {"bank_log_sale": "Bank log", "bank_drop_sale": "Bank drop"},
                {"bank_log_plus_email_access": {"n1"}},
                {"bank_log_plus_email_access": "Bank log plus email"},
                populations,
            )
        finally:
            derived.POPULATION_LABELS = original_labels

        observed = {
            (row["typology_code"], row["aml_candidate"])
            for row in rows
        }
        self.assertNotIn(
            ("bank_log_sale", "bank_log_plus_email_access"),
            observed,
        )
        self.assertIn(
            ("bank_drop_sale", "bank_log_plus_email_access"),
            observed,
        )

    def test_service_group_uses_unique_record_union(self) -> None:
        populations = {"full_screened": {"n1", "n2", "n3"}}
        original_labels = derived.POPULATION_LABELS
        try:
            derived.POPULATION_LABELS = {"full_screened": "fixture"}
            rows = derived.build_service_chain(
                {
                    "bank_log_sale": {"n1", "n2"},
                    "email_access_takeover": {"n2", "n3"},
                },
                populations,
            )
        finally:
            derived.POPULATION_LABELS = original_labels
        account_access = next(row for row in rows if row["stage"] == "account_access")
        self.assertEqual(account_access["unique_records_present_n"], 3)


if __name__ == "__main__":
    unittest.main()
