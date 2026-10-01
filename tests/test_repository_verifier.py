from __future__ import annotations

import copy
import importlib.util
import io
import unittest
from contextlib import redirect_stdout
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
    def test_binary_attachment_in_public_repository_is_rejected(self) -> None:
        path = REPOSITORY_ROOT / "outputs" / "phase4_aggregate" / "unapproved.png"
        errors: list[str] = []
        with mock.patch.object(verifier, "repository_files", return_value=[path]):
            verifier.check_excluded_material(errors)
        self.assertTrue(any("Unapproved public file type" in error for error in errors))

    def test_https_urls_are_not_mistaken_for_windows_paths(self) -> None:
        self.assertIsNone(verifier.ABSOLUTE_PATH_PATTERN.search("https://doi.org/10.1000/test"))
        windows_path = "controlled: " + "C:" + "\\Users\\analyst\\vault"
        self.assertIsNotNone(verifier.ABSOLUTE_PATH_PATTERN.search(windows_path))
        self.assertIsNotNone(verifier.ABSOLUTE_PATH_PATTERN.search("controlled: /" + "home/analyst/vault"))

    def test_public_csv_note_level_field_is_rejected(self) -> None:
        self.assertEqual(verifier.blocked_public_fields(["source", "note_id", "note_count"]), ["note_id"])
        self.assertEqual(verifier.blocked_public_fields(["unit_id", "case_id", "duplicate_cluster_hash"]), ["unit_id", "case_id", "duplicate_cluster_hash"])
        self.assertEqual(
            verifier.blocked_public_fields(["packet_file", "packet_sha256", "source_unit_sha256"]),
            ["packet_file", "packet_sha256", "source_unit_sha256"],
        )
        self.assertEqual(verifier.blocked_public_fields(["code", "unique_text_count"]), [])
        self.assertEqual(verifier.blocked_public_fields(["code", "positive_unique_evidence_rows"]), [])


class SyntaxAuditTests(unittest.TestCase):
    def test_python_syntax_audit_does_not_write_bytecode(self) -> None:
        errors: list[str] = []
        with (
            mock.patch.object(verifier, "repository_files", return_value=[MODULE_PATH]),
            mock.patch(
                "py_compile.compile",
                side_effect=AssertionError("syntax audit attempted to write bytecode"),
            ),
        ):
            python_count, json_count = verifier.check_python_and_json(errors)
        self.assertEqual(errors, [])
        self.assertEqual((python_count, json_count), (1, 0))


class TextHashTests(unittest.TestCase):
    def test_public_text_hash_is_independent_of_line_endings(self) -> None:
        lf_text = b"heading,value\nalpha,1\n"
        crlf_text = b"heading,value\r\nalpha,1\r\n"
        cr_text = b"heading,value\ralpha,1\r"

        expected = verifier._sha256_normalized_text_bytes(lf_text)
        self.assertEqual(verifier._sha256_normalized_text_bytes(crlf_text), expected)
        self.assertEqual(verifier._sha256_normalized_text_bytes(cr_text), expected)


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


class JournalSupplementTests(unittest.TestCase):
    def test_committed_journal_supplement_contract_passes(self) -> None:
        errors: list[str] = []
        manifest = verifier.load_manifest(errors)
        checked = verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertGreater(checked, 0)
        self.assertEqual(errors, [])

    def test_primary_denominator_cannot_be_described_as_unique_records(self) -> None:
        manifest = {
            "journal_reproducibility_supplement": {
                "repository_role": "journal-neutral reproducibility supplement",
                "repository_status": "methodological hold pending evidence-only reanalysis",
                "supplement_submission_ready": False,
                "readiness_scope": (
                    "Historical computations are retained for audit; substantive article use "
                    "requires author-reviewed corpus eligibility, image linkage, OCR quality, "
                    "revised analyses, and validation."
                ),
                "manuscript_included": False,
                "primary_analysis_unit": (
                    "screened combined note record representing one unique post"
                ),
                "primary_descriptive_denominator_n": 980,
                "exact_text_sensitivity_denominator_n": 463,
                "external_prevalence_claims_permitted": False,
                "author_confirmation_date": "2026-08-22",
                "journal_specific_items_outside_supplement_scope": [
                    "target journal policy and review model",
                    "final citation and authorship metadata",
                    "manuscript declarations",
                    "rights licence and archival DOI",
                ],
                "files": {},
            }
        }
        errors: list[str] = []
        verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertTrue(any("screened combined note record" in error for error in errors))

    def test_unsupported_independent_aml_review_is_rejected(self) -> None:
        errors: list[str] = []
        manifest = copy.deepcopy(verifier.load_manifest(errors))
        manifest["validation"]["independent_external_aml_review_claimed"] = True
        verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertTrue(any("independent external AML review" in error for error in errors))

    def test_supplement_cannot_be_marked_ready_during_corpus_hold(self) -> None:
        errors: list[str] = []
        manifest = copy.deepcopy(verifier.load_manifest(errors))
        manifest["journal_reproducibility_supplement"][
            "repository_status"
        ] = "submission-ready as a journal-neutral reproducibility supplement"
        manifest["journal_reproducibility_supplement"]["supplement_submission_ready"] = True
        verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertTrue(any("methodological hold" in error for error in errors))

    def test_revised_denominator_cannot_be_claimed_without_author_review(self) -> None:
        errors: list[str] = []
        manifest = copy.deepcopy(verifier.load_manifest(errors))
        manifest["post_release_corpus_audit"]["final_evidence_only_denominator"] = 391
        verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertTrue(any("final_evidence_only_denominator" in error for error in errors))

    def test_legacy_unique_eligible_record_claim_is_rejected(self) -> None:
        errors: list[str] = []
        manifest = copy.deepcopy(verifier.load_manifest(errors))
        manifest["screening_audit"]["eligible_unique_analytic_records"] = 980
        verifier.check_journal_reproducibility_supplement(manifest, errors)
        self.assertTrue(
            any("eligible_unique_analytic_records" in error for error in errors)
        )


class HumanIcrInvariantTests(unittest.TestCase):
    def test_optional_reliability_number_is_parsed_and_validated(self) -> None:
        errors: list[str] = []
        self.assertEqual(
            verifier._optional_number({"cohen_kappa": "0.839"}, "cohen_kappa", errors),
            0.839,
        )
        self.assertEqual(errors, [])
        self.assertIsNone(
            verifier._optional_number({"cohen_kappa": "bad"}, "cohen_kappa", errors)
        )
        self.assertTrue(any("numeric or blank" in error for error in errors))

    def make_row(self) -> dict[str, str]:
        return {
            "completion_date": "2026-07-26",
            "coder_count": "2", "coordinator_count": "0",
            "evidence_packet_count": "313", "assessed_target_count": "18",
            "decision_category_count": "5", "paired_units": "1032",
            "exact_agreements": "981", "disagreements": "51",
            "agreement_percent": "95.1", "cohen_kappa": "0.839378",
            "krippendorff_alpha_nominal": "0.839365",
            "binary_subset_units": "998", "binary_subset_exact_agreements": "979",
            "binary_subset_agreement_percent": "98.1", "binary_subset_cohen_kappa": "0.933155",
            "adjudicated_disagreements": "51", "consensus_cases": "51",
            "no_consensus_cases": "0", "final_present": "22", "final_absent": "29",
            "final_ambiguous": "0", "final_insufficient_evidence": "0", "final_out_of_scope": "0",
        }

    def manifest(self) -> dict[str, object]:
        return {"validation": {
            "completion_date": "2026-07-26",
            "coder_count": 2, "coordinator_count": 0, "evidence_packet_count": 313,
            "assessed_target_count": 18, "paired_case_target_units": 1032,
            "exact_agreements": 981, "disagreements": 51,
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

    def test_committed_target_results_pass_the_target_checker(self) -> None:
        errors: list[str] = []
        manifest = verifier.load_manifest(errors)
        checked = verifier.check_human_icr_by_target(manifest, errors)
        self.assertGreater(checked, 0)
        self.assertEqual(errors, [])

    def test_committed_performance_results_pass_the_performance_checker(self) -> None:
        errors: list[str] = []
        manifest = verifier.load_manifest(errors)
        checked = verifier.check_human_validation_performance(manifest, errors)
        self.assertGreater(checked, 0)
        self.assertEqual(errors, [])

    def test_main_executes_all_human_validation_checkers(self) -> None:
        with (
            mock.patch.object(verifier, "check_human_icr_aggregate", return_value=1) as aggregate,
            mock.patch.object(verifier, "check_human_icr_by_target", return_value=1) as by_target,
            mock.patch.object(
                verifier, "check_human_validation_performance", return_value=1
            ) as performance,
            redirect_stdout(io.StringIO()),
        ):
            result = verifier.main()
        self.assertEqual(result, 0)
        aggregate.assert_called_once()
        by_target.assert_called_once()
        performance.assert_called_once()


if __name__ == "__main__":
    unittest.main()
