from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPOSITORY_ROOT / "code" / "verify_repository.py"
SPEC = importlib.util.spec_from_file_location("bankdrop_repository_verifier", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


class PrivacyBoundaryTests(unittest.TestCase):
    def test_https_urls_are_not_mistaken_for_windows_paths(self) -> None:
        self.assertIsNone(verifier.ABSOLUTE_PATH_PATTERN.search("https://doi.org/10.1000/test"))
        windows_path = "controlled: " + "C:" + "\\Users\\analyst\\vault"
        self.assertIsNotNone(verifier.ABSOLUTE_PATH_PATTERN.search(windows_path))
        self.assertIsNotNone(verifier.ABSOLUTE_PATH_PATTERN.search("controlled: /" + "home/analyst/vault"))

    def test_public_csv_note_level_field_is_rejected(self) -> None:
        self.assertEqual(verifier.blocked_public_fields(["source", "note_id", "note_count"]), ["note_id"])
        self.assertEqual(verifier.blocked_public_fields(["code", "unique_text_count"]), [])
        self.assertEqual(verifier.blocked_public_fields(["code", "positive_unique_evidence_rows"]), [])


class ManifestBoundaryTests(unittest.TestCase):
    def test_only_four_deterministic_phases_are_accepted(self) -> None:
        manifest = {"phases": [
            {"phase": "Phase 1", "llm_used": False},
            {"phase": "Phase 2", "llm_used": False},
            {"phase": "Phase 3", "llm_used": False},
            {"phase": "Phase 4", "llm_used": False},
        ]}
        errors: list[str] = []
        verifier.check_manifest(manifest, errors)
        self.assertEqual(errors, [])

        manifest["phases"].append({"phase": "Phase 3b", "llm_used": True})
        errors = []
        verifier.check_manifest(manifest, errors)
        self.assertTrue(any("exactly deterministic Phases 1-4" in error for error in errors))


class ReleaseMetadataTests(unittest.TestCase):
    def test_citation_and_changelog_match_manifest_release(self) -> None:
        errors: list[str] = []
        manifest = verifier.load_manifest(errors)
        checked = verifier.check_release_metadata(manifest, errors)
        self.assertEqual(errors, [])
        self.assertEqual(checked, 5)


class AiDisclosureTests(unittest.TestCase):
    def test_author_provided_disclosure_is_consistent(self) -> None:
        disclosure = (
            "preparation and formatting of the workbook used for the intercoder reliability assessment; "
            "did not generate coding responses; "
            "did not perform literature discovery, citation checking, or the drafting or editing of the manuscript or submission materials"
        )
        manifest = {"ai_authoring_assistance": {"disclosure": disclosure}}
        with mock.patch.object(verifier.Path, "read_text", return_value=disclosure):
            errors: list[str] = []
            checked = verifier.check_ai_authoring_disclosure(manifest, errors)
        self.assertEqual(errors, [])
        self.assertEqual(checked, 4)

        with mock.patch.object(verifier.Path, "read_text", return_value="different wording"):
            errors = []
            verifier.check_ai_authoring_disclosure(manifest, errors)
        self.assertTrue(any("differs" in error for error in errors))


class HumanIcrInvariantTests(unittest.TestCase):
    def make_row(self) -> dict[str, str]:
        return {
            "completion_date": "2026-07-23",
            "coder_count": "2", "coordinator_count": "0",
            "evidence_packet_count": "351", "assessed_target_count": "18",
            "decision_category_count": "5", "paired_units": "1036",
            "exact_agreements": "977", "disagreements": "59",
            "agreement_percent": "94.3", "cohen_kappa": "0.909",
            "krippendorff_alpha_nominal": "0.909",
            "binary_subset_units": "841", "binary_subset_exact_agreements": "812",
            "binary_subset_agreement_percent": "96.6", "binary_subset_cohen_kappa": "0.930",
            "adjudicated_disagreements": "59", "consensus_cases": "59",
            "no_consensus_cases": "0", "final_present": "13", "final_absent": "16",
            "final_ambiguous": "30", "final_insufficient_evidence": "0", "final_out_of_scope": "0",
        }

    def manifest(self) -> dict[str, object]:
        return {"validation": {
            "completion_date": "2026-07-23",
            "coder_count": 2, "coordinator_count": 0, "evidence_packet_count": 351,
            "assessed_target_count": 18, "paired_case_target_units": 1036,
            "exact_agreements": 977, "disagreements": 59,
        }}

    def test_completed_human_icr_contract(self) -> None:
        with mock.patch.object(verifier, "_read_rows", return_value=[self.make_row()]):
            errors: list[str] = []
            verifier.check_human_icr_aggregate(self.manifest(), errors)
        self.assertEqual(errors, [])

    def test_inconsistent_disagreement_count_is_rejected(self) -> None:
        row = self.make_row()
        row["disagreements"] = "58"
        with mock.patch.object(verifier, "_read_rows", return_value=[row]):
            errors: list[str] = []
            verifier.check_human_icr_aggregate(self.manifest(), errors)
        self.assertTrue(any("disagreements" in error or "paired units" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
