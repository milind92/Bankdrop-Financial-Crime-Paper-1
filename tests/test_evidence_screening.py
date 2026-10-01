from __future__ import annotations

import csv
import importlib.util
import json
import os
import shutil
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot import test target")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


screen = load_module("bank_drop_evidence_screen_for_tests", "code/evidence_screening/build_evidence_corpus.py")
phase3 = load_module("bank_drop_phase3_for_screen_tests", "code/phase3_typology_coding/run_phase3_typology.py")
overview = load_module("bank_drop_overview_for_screen_tests", "code/phase3_typology_coding/make_phase3_overview.py")
phase4 = load_module("bank_drop_phase4_for_screen_tests", "code/phase4_financial_crime_analysis/run_phase4_analysis.py")
derived = load_module("bank_drop_derived_for_screen_tests", "code/derived_analysis/build_derived_analysis.py")
revised_pairs = load_module("bank_drop_revised_pairs_for_screen_tests", "code/derived_analysis/build_revised_pair_boundaries.py")
revised_holdout = load_module("bank_drop_revised_holdout_for_screen_tests", "code/human_validation/prepare_revised_holdout.py")


def save_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def approve(row: dict[str, str], decision: str) -> None:
    row.update({
        "reviewer_1": "Reviewer A", "reviewer_1_decision": decision,
        "reviewer_2": "Reviewer B", "reviewer_2_decision": decision,
        "final_decision": decision, "adjudicator": "Reviewer A",
    })


class EvidenceScreeningTests(unittest.TestCase):
    def setUp(self) -> None:
        # Outside the public checkout, matching the production privacy gate.
        self.base = ROOT.parents[1] / "outputs" / "paper1_audit_20261001" / f"test_evidence_{uuid.uuid4().hex}"
        self.base.mkdir()
        self.vault = self.base / "vault"
        self.vault.mkdir()
        self.review = self.base / "review"
        self.output = self.base / "evidence"
        self.note = self.vault / "source.md"
        self.note.write_text("Collector heading\nFullz offer\n", encoding="utf-8")
        self.status_note = self.vault / "status.md"
        self.status_note.write_text("Could not access market", encoding="utf-8")
        self.image_one = self.vault / "crypto.png"
        self.image_two = self.vault / "bank.png"
        self.orphan = self.vault / "unlinked.png"
        self.image_one.write_bytes(b"image-a")
        self.image_two.write_bytes(b"image-b")
        self.orphan.write_bytes(b"unlinked-image")
        self.index = self.base / "corpus_index.csv"
        save_csv(self.index, [
            {"note_id": "n1", "relative_path": "source.md", "sha256_text": screen.sha_text(self.note.read_text()), "source": "Source A", "collection_date": "2026-03-01", "image_ref_count": "2"},
            {"note_id": "n2", "relative_path": "status.md", "sha256_text": screen.sha_text(self.status_note.read_text()), "source": "Source A", "collection_date": "2026-03-01", "image_ref_count": "0"},
        ], ["note_id", "relative_path", "sha256_text", "source", "collection_date", "image_ref_count"])
        self.joined = self.base / "ocr_joined_image_references.csv"
        config = screen.sha_text("test-ocr-config")
        rows = []
        for index, (image, ocr) in enumerate(((self.image_one, "crypto"), (self.image_two, "bank")), start=1):
            image_sha = screen.sha_file(image)
            rows.append({
                "note_id": "n1", "image_index_in_note": str(index),
                "image_resolution_status": "resolved", "image_relative_path": image.name,
                "image_sha256": image_sha, "ocr_config_sha256": config,
                "ocr_cache_key": screen.sha_text(f"{image_sha}:{config}"),
                "ocr_status": "ok", "ocr_text": ocr,
            })
        save_csv(self.joined, rows, list(rows[0]))
        screen.prepare(self.vault, self.index, self.joined, self.review)

    def tearDown(self) -> None:
        if self.base.resolve().is_relative_to(ROOT.parents[1].resolve()):
            shutil.rmtree(self.base)

    def complete_review(self) -> None:
        note_rows = screen.read_csv(self.review / "note_decisions.csv", screen.NOTE_FIELDS)
        for row in note_rows:
            if row["note_id"] == "n1":
                approve(row, "include")
                row.update({"record_type": "mixed_source_and_researcher", "approved_source": "Source A", "capture_date_basis": "filename_only", "markdown_decision": "source_spans"})
            else:
                approve(row, "exclude")
                row.update({"record_type": "collection_status", "decision_reason": "Collector access log"})
        save_csv(self.review / "note_decisions.csv", note_rows, screen.NOTE_FIELDS)

        image_rows = screen.read_csv(self.review / "image_decisions.csv", screen.IMAGE_FIELDS)
        for row in image_rows:
            if row["kind"] == "linked":
                approve(row, "include")
            else:
                approve(row, "exclude")
                row["decision_reason"] = "Provenance not established"
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)

        segment_rows = []
        content = self.note.read_text()
        start = content.index("Fullz offer")
        segments = [("markdown:n1", start, start + len("Fullz offer"), content)]
        for image_row in image_rows:
            if image_row["kind"] == "linked":
                text = "crypto" if image_row["image_relative_path"] == "crypto.png" else "bank"
                segments.append((image_row["reference_key"], 0, len(text), text))
        for key, first, last, source_text in segments:
            row = {field: "" for field in screen.SEGMENT_FIELDS}
            row.update({"reference_key": key, "start_char": str(first), "end_char": str(last), "segment_sha256": screen.sha_text(source_text[first:last])})
            approve(row, "include")
            segment_rows.append(row)
        save_csv(self.review / "source_segments.csv", segment_rows, screen.SEGMENT_FIELDS)

    def test_blank_review_cannot_build(self) -> None:
        with self.assertRaisesRegex(ValueError, "Two distinct reviewers"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)
        self.assertFalse(self.output.exists())

    def test_revised_holdout_requires_approved_plan_and_keeps_short_negatives(self) -> None:
        self.complete_review()
        screen.build(self.vault, self.index, self.joined, self.review, self.output)
        old_output = phase3.PHASE3_OUTPUT
        old_env = os.environ.get("BANK_DROP_EVIDENCE_CORPUS")
        try:
            phase3.PHASE3_OUTPUT = self.base / "phase3"
            os.environ["BANK_DROP_EVIDENCE_CORPUS"] = str(self.output / "approved_evidence_units.jsonl")
            phase3.main()
        finally:
            phase3.PHASE3_OUTPUT = old_output
            if old_env is None:
                os.environ.pop("BANK_DROP_EVIDENCE_CORPUS", None)
            else:
                os.environ["BANK_DROP_EVIDENCE_CORPUS"] = old_env
        human_book = self.base / "human_codebook.md"
        human_book.write_text("Synthetic inclusion and exclusion rules for every target", encoding="utf-8")
        pilot = self.base / "pilot_units.csv"
        save_csv(pilot, [], ["unit_id"])
        frame_dir = self.base / "holdout_frame"
        frame_report = revised_holdout.prepare(
            self.base / "phase3", self.output / "approved_evidence_units.jsonl",
            pilot, human_book, frame_dir,
        )
        self.assertEqual(frame_report["diagnostics"]["short_units"], 1)
        self.assertEqual(frame_report["case_target_frame_n"], 18)
        plan_path = frame_dir / "allocation_plan_template.json"
        with self.assertRaisesRegex(ValueError, "approval date"):
            revised_holdout.draw(
                self.base / "phase3", self.output / "approved_evidence_units.jsonl",
                pilot, human_book, frame_dir, plan_path, self.base / "premature_draw",
            )
        self.assertFalse((self.base / "premature_draw").exists())
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan.update({
            "status": "approved", "precision_rationale": "Synthetic complete-frame census for a gate test.",
            "pilot_exclusions_finalized": True, "target_definitions_frozen": True,
            "approved_by": ["Ausma Bernot", "Milind Tiwari"],
            "approval_date": "2026-10-01", "selection_seed": 12345,
        })
        plan["target_precision_rationale"] = {
            key: "Synthetic census removes sampling variance for this target."
            for key in plan["target_precision_rationale"]
        }
        for allocation in plan["allocations"]:
            allocation["sample_n"] = allocation["frame_n"]
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        report = revised_holdout.draw(
            self.base / "phase3", self.output / "approved_evidence_units.jsonl",
            pilot, human_book, frame_dir, plan_path, self.base / "holdout_sample",
        )
        self.assertEqual(report["sampled_case_target_n"], 18)
        self.assertEqual(report["sampled_short_case_target_n"], 18)
        self.assertFalse(report["article_ready"])
        machine = screen.read_csv(self.base / "holdout_sample" / "coordinator_machine_key.csv")
        coder = screen.read_csv(self.base / "holdout_sample" / "coder_1_blank.csv")
        self.assertEqual({row["inclusion_probability"] for row in machine}, {"1"})
        self.assertTrue(any(row["predicted_present"] == "0" and row["length_band"] == "short" for row in machine))
        self.assertNotIn("predicted_present", coder[0])
        self.assertNotIn("unit_id", coder[0])
        self.assertTrue(all(row["decision"] == "" for row in coder))
        human_book.write_text(human_book.read_text(encoding="utf-8") + " changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "frozen approved evidence"):
            revised_holdout.draw(
                self.base / "phase3", self.output / "approved_evidence_units.jsonl",
                pilot, human_book, frame_dir, plan_path, self.base / "stale_draw",
            )
        self.assertFalse((self.base / "stale_draw").exists())

    def test_revised_holdout_probability_sample_is_reproducible(self) -> None:
        frame = [
            {"unit_id": f"n{i}", "target_type": "typology", "code": "bank_log_sale",
             "predicted_present": "0", "length_band": "short"}
            for i in range(5)
        ]
        groups = revised_holdout.frame_strata(frame)
        key = ("typology", "bank_log_sale", "0", "short")
        selected = revised_holdout.select_rows(groups, {key: 2}, 791)
        self.assertEqual(selected, revised_holdout.select_rows(groups, {key: 2}, 791))
        self.assertEqual(len({row["unit_id"] for row, _, _ in selected}), 2)
        self.assertTrue(all(frame_n == 5 and sample_n == 2 for _, frame_n, sample_n in selected))

    def test_reviewed_segments_preserve_source_and_image_boundaries(self) -> None:
        self.complete_review()
        result = screen.build(self.vault, self.index, self.joined, self.review, self.output)
        self.assertEqual(result["screened_notes"], 2)
        self.assertEqual(result["approved_evidence_units"], 1)
        self.assertEqual(result["approved_text_segments"], 3)
        units, actual_sha = phase3.load_approved_evidence(self.output / "approved_evidence_units.jsonl")
        self.assertEqual(actual_sha, result["evidence_jsonl_sha256"])
        self.assertEqual(units[0].collection_date, "")  # filename-only date is not verified capture date
        self.assertEqual(units[0].markdown_text, "Fullz offer")
        self.assertEqual(phase3.code_artifacts(units[0].artifacts, phase3.CODEBOOK)[0]["fullz_identity_package"], 1)
        self.assertEqual(phase3.code_artifacts(units[0].artifacts, phase3.AML_INDICATORS)[0]["crypto_to_bank_cashout"], 0)
        self.assertGreater(phase3.code_text("crypto\n\nbank", phase3.AML_INDICATORS)[0]["crypto_to_bank_cashout"], 0)

        old_output = phase3.PHASE3_OUTPUT
        old_env = os.environ.get("BANK_DROP_EVIDENCE_CORPUS")
        try:
            phase3.PHASE3_OUTPUT = self.base / "phase3"
            os.environ["BANK_DROP_EVIDENCE_CORPUS"] = str(self.output / "approved_evidence_units.jsonl")
            phase3.main()
        finally:
            phase3.PHASE3_OUTPUT = old_output
            if old_env is None:
                os.environ.pop("BANK_DROP_EVIDENCE_CORPUS", None)
            else:
                os.environ["BANK_DROP_EVIDENCE_CORPUS"] = old_env
        aml_rows = screen.read_csv(self.base / "phase3" / "aml_indicator_coding_long.csv")
        crypto_row = next(row for row in aml_rows if row["aml_indicator"] == "crypto_to_bank_cashout")
        self.assertEqual(crypto_row["present"], "0")
        artifact_rows = screen.read_csv(self.base / "phase3" / "artifact_coding_long.csv")
        self.assertEqual(len(artifact_rows), 3 * (len(phase3.CODEBOOK) + len(phase3.AML_INDICATORS)))
        self.assertEqual(sum(int(row["present"]) for row in artifact_rows
                             if row["target_type"] == "typology" and row["code"] == "fullz_identity_package"), 1)
        self.assertEqual(sum(int(row["present"]) for row in artifact_rows
                             if row["target_type"] == "aml_candidate" and row["code"] == "crypto_to_bank_cashout"), 0)
        metadata = json.loads((self.base / "phase3" / "run_metadata.json").read_text())
        self.assertEqual(metadata["analysis_mode"], "author_reviewed_artifact_bounded_source_text")
        self.assertEqual(metadata["approved_source_artifacts"], 3)
        self.assertEqual(metadata["artifact_coding_rows"], len(artifact_rows))
        pair_report = revised_pairs.build(self.base / "phase3", self.output / "approved_evidence_units.jsonl", self.base / "revised_pairs")
        self.assertFalse(pair_report["article_ready"])
        pair_rows = screen.read_csv(self.base / "revised_pairs" / "revised_typology_pair_boundaries.csv")
        separated = next(row for row in pair_rows if row["scope"] == "all" and
                         {row["code_a"], row["code_b"]} ==
                         {"fullz_identity_package", "crypto_payment_or_conversion"})
        self.assertEqual(separated["units_with_both_codes_n"], "1")
        self.assertEqual(separated["units_with_both_in_same_artifact_n"], "0")
        self.assertEqual(separated["cross_artifact_only_units_n"], "1")
        altered_dir = self.base / "altered_evidence"
        altered_dir.mkdir()
        altered_evidence = altered_dir / "approved_evidence_units.jsonl"
        altered_evidence.write_bytes((self.output / "approved_evidence_units.jsonl").read_bytes() + b"\n")
        shutil.copyfile(self.output / "evidence_build_manifest.json", altered_dir / "evidence_build_manifest.json")
        with self.assertRaisesRegex(ValueError, "evidence corpus hash"):
            revised_pairs.build(self.base / "phase3", altered_evidence, self.base / "tampered_pairs")
        self.assertFalse((self.base / "tampered_pairs").exists())
        old_overview_base = overview.BASE
        old_phase4_input, old_phase4_output = phase4.PHASE3_OUTPUT, phase4.PHASE4_OUTPUT
        try:
            overview.BASE = self.base / "phase3"
            overview.main()
            phase4.PHASE3_OUTPUT = self.base / "phase3"
            phase4.PHASE4_OUTPUT = self.base / "phase4"
            with self.assertRaisesRegex(RuntimeError, "historical mixed-record analysis"):
                phase4.main()
        finally:
            overview.BASE = old_overview_base
            phase4.PHASE3_OUTPUT, phase4.PHASE4_OUTPUT = old_phase4_input, old_phase4_output
        self.assertIn("historical human validation does not validate", (self.base / "phase3" / "PHASE3_ANALYTIC_OVERVIEW.md").read_text())
        with self.assertRaisesRegex(derived.DerivedAnalysisError, "do not yet apply"):
            derived.build_analysis(self.base / "phase3", self.base / "derived")

    def test_changed_note_and_segment_hashes_fail_closed(self) -> None:
        self.complete_review()
        segments = screen.read_csv(self.review / "source_segments.csv", screen.SEGMENT_FIELDS)
        segments[0]["segment_sha256"] = "0" * 64
        save_csv(self.review / "source_segments.csv", segments, screen.SEGMENT_FIELDS)
        with self.assertRaisesRegex(ValueError, "segment hash mismatch"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)
        self.note.write_text("Changed source text", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "note hash mismatch"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

    def test_missing_phase2_reference_cannot_shrink_review_frame(self) -> None:
        rows = screen.read_csv(self.joined)
        save_csv(self.joined, rows[:1], list(rows[0]))
        with self.assertRaisesRegex(ValueError, "reference coverage is incomplete"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

    def test_markdown_provenance_decision_must_match_approved_spans(self) -> None:
        self.complete_review()
        rows = screen.read_csv(self.review / "note_decisions.csv", screen.NOTE_FIELDS)
        rows[0]["markdown_decision"] = "no_source_text"
        rows[0]["markdown_decision_reason"] = "Reviewer rejected note prose"
        save_csv(self.review / "note_decisions.csv", rows, screen.NOTE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Markdown spans do not match"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

    def test_controlled_output_cannot_enter_public_repository(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the public repository"):
            screen.prepare(self.vault, self.index, self.joined, ROOT / "unsafe-review")


if __name__ == "__main__":
    unittest.main()
