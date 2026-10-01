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
revised_duplicates = load_module("bank_drop_revised_duplicates_for_screen_tests", "code/derived_analysis/build_revised_duplicate_sensitivity.py")
sys.modules["build_revised_duplicate_sensitivity"] = revised_duplicates
revised_descriptives = load_module("bank_drop_revised_descriptives_for_screen_tests", "code/derived_analysis/build_revised_descriptive_tables.py")
revised_holdout = load_module("bank_drop_revised_holdout_for_screen_tests", "code/human_validation/prepare_revised_holdout.py")
revised_close = load_module("bank_drop_revised_close_for_screen_tests", "code/human_validation/close_revised_holdout.py")


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
                row.update({"record_type": "mixed_source_and_researcher", "approved_source": "Source A", "capture_date_basis": "filename_only", "markdown_decision": "source_spans", "decision_reason": "Source marker in synthetic preserved note"})
            else:
                approve(row, "exclude")
                row.update({"record_type": "collection_status", "decision_reason": "Collector access log"})
        save_csv(self.review / "note_decisions.csv", note_rows, screen.NOTE_FIELDS)

        image_rows = screen.read_csv(self.review / "image_decisions.csv", screen.IMAGE_FIELDS)
        for row in image_rows:
            if row["kind"] == "linked":
                approve(row, "include")
                row.update({"approved_source": "Source A", "capture_date_basis": "unknown", "decision_reason": "Visible marker matches synthetic preserved note"})
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

    def test_exact_span_signature_sensitivity_preserves_boundaries(self) -> None:
        first = [{"kind": "image_ocr", "text_sha256": screen.sha_text("a\n\nb")}]
        split = [
            {"kind": "image_ocr", "text_sha256": screen.sha_text("a")},
            {"kind": "image_ocr", "text_sha256": screen.sha_text("b")},
        ]
        self.assertNotEqual(revised_duplicates.signature(first),
                            revised_duplicates.signature(split))
        units = {
            "u1": {"source": "Source A", "signature": revised_duplicates.signature(first), "artifacts": first},
            "u2": {"source": "Source B", "signature": revised_duplicates.signature(first), "artifacts": first},
            "u3": {"source": "Source A", "signature": revised_duplicates.signature(split), "artifacts": split},
        }
        predictions = {
            (unit_id, target_type, code): value
            for unit_id, pair in {"u1": (1, 0), "u2": (1, 0), "u3": (0, 1)}.items()
            for target_type, code, value in (
                ("typology", "bank_drop_sale", pair[0]),
                ("aml_candidate", "crypto_to_bank_cashout", pair[1]),
            )
        }
        rows, sources, report = revised_duplicates.sensitivity_rows(
            units, predictions,
            {"typology": {"bank_drop_sale"}, "aml_candidate": {"crypto_to_bank_cashout"}},
        )
        typology = next(row for row in rows if row["target_type"] == "typology")
        self.assertEqual(typology["approved_positive_units_n"], 2)
        self.assertEqual(typology["positive_signature_groups_n"], 1)
        self.assertEqual(typology["positive_excess_from_exact_repeats_n"], 1)
        self.assertEqual(report["exact_span_signature_groups_n"], 2)
        self.assertEqual(report["cross_source_repeat_signature_groups_n"], 1)
        self.assertEqual(report["approved_span_assignments_n"], 4)
        self.assertEqual(len(sources), 2)
        predictions[("u2", "typology", "bank_drop_sale")] = 0
        with self.assertRaisesRegex(ValueError, "conflicting deterministic predictions"):
            revised_duplicates.sensitivity_rows(
                units, predictions,
                {"typology": {"bank_drop_sale"}, "aml_candidate": {"crypto_to_bank_cashout"}},
            )

    def test_revised_descriptive_source_denominators_and_zero_marginals(self) -> None:
        units = {
            "u1": {"source": "A", "collection_date": "", "artifacts": [
                {"artifact_id": "a1", "kind": "markdown_source_span"}]},
            "u2": {"source": "A", "collection_date": "2026-03-01", "artifacts": [
                {"artifact_id": "a2", "kind": "image_ocr"}]},
            "u3": {"source": "B", "collection_date": "", "artifacts": [
                {"artifact_id": "a3", "kind": "markdown_source_span"}]},
        }
        target_values = {
            ("typology", "a"): {"u1": 1, "u2": 0, "u3": 1},
            ("typology", "b"): {"u1": 1, "u2": 0, "u3": 0},
            ("typology", revised_duplicates.QUALITY_FLAG): {"u1": 0, "u2": 0, "u3": 0},
            ("aml_candidate", "candidate"): {"u1": 0, "u2": 1, "u3": 0},
        }
        run = revised_duplicates.CheckedRun(
            units=units,
            predictions={(unit_id, target_type, code): value
                         for (target_type, code), values in target_values.items()
                         for unit_id, value in values.items()},
            artifact_predictions={(unit_id, unit["artifacts"][0]["artifact_id"],
                                   target_type, code): values[unit_id]
                                  for unit_id, unit in units.items()
                                  for (target_type, code), values in target_values.items()},
            targets={"typology": {"a", "b", revised_duplicates.QUALITY_FLAG},
                     "aml_candidate": {"candidate"}},
            labels={(target_type, code): code for target_type, code in target_values},
            input_sha256={},
            evidence_manifest={"screened_notes": 3,
                               "note_decisions": {"include": 3, "exclude": 0},
                               "approved_standalone_orphan_units": 0,
                               "approved_text_segments": 3,
                               "image_decisions": {}},
            phase3_metadata={},
        )
        tables = revised_descriptives.compute_tables(run)
        coverage = tables["revised_source_coverage_controlled.csv"]
        self.assertEqual(next(row for row in coverage if row["scope"] == "all")
                         ["unknown_or_mixed_unit_date_n"], 2)
        prevalence = tables["revised_target_prevalence_controlled.csv"]
        self.assertEqual(next(row for row in prevalence if row["scope"] == "source"
                              and row["source"] == "A" and row["code"] == "a")
                         ["rule_positive_percent"], "50.000")
        pairs = tables["revised_typology_cooccurrence_controlled.csv"]
        overall = next(row for row in pairs if row["scope"] == "all")
        self.assertEqual((overall["n11_both_n"], overall["n10_a_only_n"],
                          overall["n01_b_only_n"], overall["n00_neither_n"]),
                         (1, 1, 0, 1))
        self.assertEqual(overall["lift"], "1.500000")
        omitted_a = next(row for row in pairs if row["removed_source"] == "A")
        self.assertEqual(omitted_a["jaccard"], "0.000000")
        self.assertEqual(omitted_a["lift"], "")
        self.assertEqual(len(tables["revised_target_prevalence_controlled.csv"]), 9)

    def test_superseded_review_schema_cannot_build(self) -> None:
        inventory_path = self.review / "review_inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["schema_version"] = 2
        inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Review template does not match"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

    def test_capture_dates_and_image_source_are_checked_per_artifact(self) -> None:
        self.complete_review()
        note_rows = screen.read_csv(self.review / "note_decisions.csv", screen.NOTE_FIELDS)
        included = next(row for row in note_rows if row["note_id"] == "n1")
        included.update({
            "capture_date_basis": "source_metadata", "capture_date": "2026-03-01",
            "capture_date_record_locator": "source post timestamp",
        })
        save_csv(self.review / "note_decisions.csv", note_rows, screen.NOTE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Capture-date basis is missing or invalid"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        included["capture_date_basis"] = "collector_record"
        included["capture_date_record_locator"] = ""
        save_csv(self.review / "note_decisions.csv", note_rows, screen.NOTE_FIELDS)
        with self.assertRaisesRegex(ValueError, "contemporaneous record locator"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        included["capture_date_record_locator"] = "capture log A"
        save_csv(self.review / "note_decisions.csv", note_rows, screen.NOTE_FIELDS)
        image_rows = screen.read_csv(self.review / "image_decisions.csv", screen.IMAGE_FIELDS)
        linked = sorted((row for row in image_rows if row["kind"] == "linked"),
                        key=lambda row: row["image_relative_path"])
        linked[0]["approved_source"] = "Different source"
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        with self.assertRaisesRegex(ValueError, "confirmed matching source"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        linked[0]["approved_source"] = "Source A"
        linked[0]["capture_date_basis"] = ""
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Capture-date basis is missing or invalid"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        for row, day in zip(linked, ("2026-03-01", "2026-03-02")):
            row.update({
                "approved_source": "Source A", "capture_date_basis": "collector_record",
                "capture_date": day, "capture_date_record_locator": f"capture log {day}",
            })
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        screen.build(self.vault, self.index, self.joined, self.review, self.output)
        unit = json.loads((self.output / "approved_evidence_units.jsonl").read_text())
        self.assertEqual(unit["collection_date"], "")
        self.assertEqual(unit["date_basis"], "unverified_or_mixed_artifact_dates")
        by_kind = {artifact["artifact_id"]: artifact for artifact in unit["artifacts"]}
        self.assertEqual({artifact["collection_date"] for artifact in by_kind.values()},
                         {"2026-03-01", "2026-03-02"})

        old_output = phase3.PHASE3_OUTPUT
        old_env = os.environ.get("BANK_DROP_EVIDENCE_CORPUS")
        try:
            phase3.PHASE3_OUTPUT = self.base / "phase3_dates"
            os.environ["BANK_DROP_EVIDENCE_CORPUS"] = str(self.output / "approved_evidence_units.jsonl")
            phase3.main()
        finally:
            phase3.PHASE3_OUTPUT = old_output
            if old_env is None:
                os.environ.pop("BANK_DROP_EVIDENCE_CORPUS", None)
            else:
                os.environ["BANK_DROP_EVIDENCE_CORPUS"] = old_env
        artifact_rows = screen.read_csv(self.base / "phase3_dates" / "artifact_coding_long.csv")
        observed = {(row["artifact_id"], row["collection_date"]) for row in artifact_rows}
        self.assertEqual(observed,
                         {(artifact_id, artifact["collection_date"])
                          for artifact_id, artifact in by_kind.items()})
        revised_pairs.build(self.base / "phase3_dates",
                            self.output / "approved_evidence_units.jsonl",
                            self.base / "revised_pairs_dates")

        altered = self.base / "altered_dates"
        altered.mkdir()
        altered_unit = dict(unit)
        altered_unit["collection_date"] = "2026-03-01"
        altered_evidence = altered / "approved_evidence_units.jsonl"
        altered_evidence.write_text(json.dumps(altered_unit) + "\n", encoding="utf-8")
        altered_manifest = json.loads((self.output / "evidence_build_manifest.json").read_text())
        altered_manifest["evidence_jsonl_sha256"] = screen.sha_file(altered_evidence)
        (altered / "evidence_build_manifest.json").write_text(json.dumps(altered_manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unit capture date disagrees"):
            phase3.load_approved_evidence(altered_evidence)

    def test_novel_orphan_requires_ocr_and_matching_source_when_assigned(self) -> None:
        self.complete_review()
        image_rows = screen.read_csv(self.review / "image_decisions.csv", screen.IMAGE_FIELDS)
        orphan = next(row for row in image_rows if row["kind"] == "orphan")
        approve(orphan, "include")
        orphan.update({
            "decision_reason": "Synthetic provenance confirmation",
            "assigned_note_id": "n1", "approved_source": "Different source",
            "capture_date_basis": "unknown",
        })
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Assigned orphan needs confirmed matching source"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        orphan["approved_source"] = "Source A"
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        config = screen.read_csv(self.joined)[0]["ocr_config_sha256"]
        image_sha = orphan["image_sha256"]
        extra = self.base / "orphan_ocr.csv"
        save_csv(extra, [{
            "image_relative_path": orphan["image_relative_path"],
            "image_sha256": image_sha, "ocr_config_sha256": config,
            "ocr_cache_key": screen.sha_text(f"{image_sha}:{config}"),
            "ocr_status": "ok", "ocr_text": "orphan source text",
        }], ["image_relative_path", "image_sha256", "ocr_config_sha256",
            "ocr_cache_key", "ocr_status", "ocr_text"])
        segments = screen.read_csv(self.review / "source_segments.csv", screen.SEGMENT_FIELDS)
        segment = {field: "" for field in screen.SEGMENT_FIELDS}
        segment.update({
            "reference_key": orphan["reference_key"], "start_char": "0",
            "end_char": str(len("orphan source text")),
            "segment_sha256": screen.sha_text("orphan source text"),
        })
        approve(segment, "include")
        segments.append(segment)
        save_csv(self.review / "source_segments.csv", segments, screen.SEGMENT_FIELDS)

        assigned = screen.build(self.vault, self.index, self.joined,
                                self.review, self.output, extra)
        self.assertEqual(assigned["approved_evidence_units"], 1)
        self.assertEqual(assigned["approved_standalone_orphan_units"], 0)
        self.assertEqual(assigned["approved_text_segments"], 4)

        orphan["assigned_note_id"] = ""
        orphan["approved_source"] = "Source B"
        save_csv(self.review / "image_decisions.csv", image_rows, screen.IMAGE_FIELDS)
        standalone = screen.build(self.vault, self.index, self.joined,
                                  self.review, self.base / "standalone_evidence", extra)
        self.assertEqual(standalone["approved_evidence_units"], 2)
        self.assertEqual(standalone["approved_standalone_orphan_units"], 1)

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
        packet_root = self.base / "packets"
        packet_root.mkdir()
        packet_rows = screen.read_csv(self.base / "holdout_sample" / "packet_manifest_template.csv")
        for row in packet_rows:
            packet = packet_root / f"{row['case_id']}.txt"
            packet.write_text("Synthetic approved source evidence only.", encoding="utf-8")
            row.update({
                "packet_file": packet.name, "packet_sha256": screen.sha_file(packet),
                "privacy_reviewer": "Reviewer A", "context_reviewer": "Reviewer B",
                "packet_checked": "yes",
            })
        packet_manifest = self.base / "packet_manifest.csv"
        save_csv(packet_manifest, packet_rows, revised_close.PACKET_FIELDS)
        coder_1_rows = [dict(row) for row in coder]
        coder_2_rows = [dict(row) for row in coder]
        for left, right in zip(coder_1_rows, coder_2_rows):
            decision = "present" if left["code"] == "fullz_identity_package" else "absent"
            left["decision"] = right["decision"] = decision
            if left["code"] == "crypto_to_bank_cashout":
                left["decision"] = "present"
        coder_1_path, coder_2_path = self.base / "coder_1.csv", self.base / "coder_2.csv"
        save_csv(coder_1_path, coder_1_rows, revised_close.CODER_FIELDS)
        save_csv(coder_2_path, coder_2_rows, revised_close.CODER_FIELDS)
        wrong_source_rows = [dict(row) for row in packet_rows]
        wrong_source_rows[0]["source_unit_sha256"] = "0" * 64
        wrong_source_manifest = self.base / "wrong_source_packet_manifest.csv"
        save_csv(wrong_source_manifest, wrong_source_rows, revised_close.PACKET_FIELDS)
        with self.assertRaisesRegex(ValueError, "Packet source-unit hashes differ"):
            revised_close.lock_coders(
                self.base / "holdout_sample", coder_1_path, coder_2_path,
                wrong_source_manifest, packet_root, "Reviewer A", "Reviewer B",
                self.base / "wrong_source_lock",
            )
        self.assertFalse((self.base / "wrong_source_lock").exists())
        lock_dir = self.base / "coder_lock"
        coder_lock = revised_close.lock_coders(
            self.base / "holdout_sample", coder_1_path, coder_2_path,
            packet_manifest, packet_root, "Reviewer A", "Reviewer B", lock_dir,
        )
        self.assertEqual(coder_lock["pre_adjudication_disagreement_n"], 1)
        reference_dir = self.base / "reference_template"
        revised_close.prepare_reference(
            self.base / "holdout_sample", lock_dir, coder_1_path, coder_2_path,
            packet_manifest, packet_root, reference_dir,
        )
        reference_rows = screen.read_csv(reference_dir / "reference_decisions_template.csv")
        for row in reference_rows:
            if not row["final_decision"]:
                row.update({
                    "final_decision": "absent", "adjudicator": "Reviewer C",
                    "rationale": "Separate synthetic spans do not establish this target.",
                })
        reference = self.base / "reference_decisions.csv"
        save_csv(reference, reference_rows, revised_close.REFERENCE_FIELDS)
        reference_lock_dir = self.base / "reference_lock"
        revised_close.lock_reference(
            self.base / "holdout_sample", lock_dir, coder_1_path, coder_2_path,
            packet_manifest, packet_root, reference, reference_lock_dir,
        )
        score_dir = self.base / "holdout_score"
        score = revised_close.score(
            self.base / "holdout_sample", frame_dir, plan_path, lock_dir,
            coder_1_path, coder_2_path, packet_manifest, packet_root,
            reference, reference_lock_dir, score_dir,
        )
        self.assertEqual(score["target_count"], 18)
        self.assertFalse(score["article_ready"])
        performance = screen.read_csv(score_dir / "revised_holdout_performance_controlled.csv")
        fullz = next(row for row in performance if row["code"] == "fullz_identity_package")
        self.assertEqual(fullz["ppv"], "1.0")
        self.assertEqual(fullz["sensitivity"], "1.0")
        self.assertEqual(fullz["ppv_ci95_low"], "1.0")
        self.assertEqual(fullz["sensitivity_ci95_low"], "1.0")
        (packet_root / f"{packet_rows[0]['case_id']}.txt").write_text("Changed packet", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Packet content hash"):
            revised_close.score(
                self.base / "holdout_sample", frame_dir, plan_path, lock_dir,
                coder_1_path, coder_2_path, packet_manifest, packet_root,
                reference, reference_lock_dir, self.base / "changed_packet_score",
            )
        self.assertFalse((self.base / "changed_packet_score").exists())
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

    def test_exact_finite_population_bounds_cover_small_populations(self) -> None:
        from math import comb
        for population_n in range(1, 11):
            for draw_n in range(1, population_n + 1):
                for successes_n in range(population_n + 1):
                    covered = 0
                    for observed in range(max(0, draw_n - population_n + successes_n),
                                          min(draw_n, successes_n) + 1):
                        lower, upper = revised_close.exact_success_bounds(
                            population_n, draw_n, observed, 0, 1,
                        )
                        if lower <= successes_n <= upper:
                            covered += comb(successes_n, observed) * comb(
                                population_n - successes_n, draw_n - observed
                            )
                    self.assertGreaterEqual(20 * covered, 19 * comb(population_n, draw_n))

    def test_revised_score_uses_stratum_weights_and_bounds_nonbinary_reference(self) -> None:
        positive = ("typology", "bank_log_sale", "1", "short")
        negative = ("typology", "bank_log_sale", "0", "long")
        rows = [
            {"target_type": "typology", "code": "bank_log_sale", "stratum": positive,
             "N": 8, "n": 2, "length_band": "short", "coder_1": "present",
             "coder_2": "present", "final": "present"},
            {"target_type": "typology", "code": "bank_log_sale", "stratum": positive,
             "N": 8, "n": 2, "length_band": "short", "coder_1": "present",
             "coder_2": "present", "final": "present"},
            {"target_type": "typology", "code": "bank_log_sale", "stratum": negative,
             "N": 4, "n": 2, "length_band": "long", "coder_1": "present",
             "coder_2": "present", "final": "present"},
            {"target_type": "typology", "code": "bank_log_sale", "stratum": negative,
             "N": 4, "n": 2, "length_band": "long", "coder_1": "absent",
             "coder_2": "absent", "final": "absent"},
        ]
        result = revised_close.score_target(rows)
        self.assertEqual(result["estimated_tp"], 8.0)
        self.assertEqual(result["estimated_fn"], 2.0)
        self.assertEqual(result["sensitivity"], 0.8)
        self.assertLess(result["ppv_ci95_low"], 1.0)
        rows[0]["final"] = "ambiguous"
        bounded = revised_close.score_target(rows)
        self.assertEqual(bounded["reference_status"], "nonbinary_bounds_only")
        self.assertIsNone(bounded["ppv"])
        self.assertIsNotNone(bounded["ppv_ci95_low"])
        rows[0]["final"] = "out_of_scope_record"
        with self.assertRaisesRegex(ValueError, "invalidates"):
            revised_close.score_target(rows)

    def test_two_stratum_ratio_intervals_cover_small_finite_frames(self) -> None:
        from math import comb
        population_n, draw_n = 3, 2
        total_draws = comb(population_n, draw_n) ** 2
        for true_positive_n in range(population_n + 1):
            for false_negative_n in range(population_n + 1):
                ppv_covered = sensitivity_covered_or_suppressed = 0
                for observed_tp in range(max(0, draw_n + true_positive_n - population_n),
                                         min(draw_n, true_positive_n) + 1):
                    for observed_fn in range(max(0, draw_n + false_negative_n - population_n),
                                             min(draw_n, false_negative_n) + 1):
                        weight = (
                            comb(true_positive_n, observed_tp)
                            * comb(population_n - true_positive_n, draw_n - observed_tp)
                            * comb(false_negative_n, observed_fn)
                            * comb(population_n - false_negative_n, draw_n - observed_fn)
                        )
                        rows = []
                        for machine_status, observed in (("1", observed_tp), ("0", observed_fn)):
                            for index in range(draw_n):
                                decision = "present" if index < observed else "absent"
                                rows.append({
                                    "target_type": "typology", "code": "bank_log_sale",
                                    "stratum": ("typology", "bank_log_sale", machine_status, "short"),
                                    "N": population_n, "n": draw_n, "length_band": "short",
                                    "coder_1": decision, "coder_2": decision, "final": decision,
                                })
                        result = revised_close.score_target(rows)
                        actual_ppv = true_positive_n / population_n
                        if result["ppv_ci95_low"] <= actual_ppv <= result["ppv_ci95_high"]:
                            ppv_covered += weight
                        if true_positive_n + false_negative_n:
                            actual_sensitivity = true_positive_n / (true_positive_n + false_negative_n)
                            if (result["sensitivity_ci95_low"] is None
                                    or result["sensitivity_ci95_low"] <= actual_sensitivity
                                    <= result["sensitivity_ci95_high"]):
                                sensitivity_covered_or_suppressed += weight
                self.assertGreaterEqual(20 * ppv_covered, 19 * total_draws)
                if true_positive_n + false_negative_n:
                    self.assertGreaterEqual(
                        20 * sensitivity_covered_or_suppressed, 19 * total_draws
                    )

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
        duplicate_report = revised_duplicates.build(
            self.base / "phase3", self.output / "approved_evidence_units.jsonl",
            self.base / "revised_duplicates",
        )
        self.assertFalse(duplicate_report["article_ready"])
        self.assertEqual(duplicate_report["approved_units_n"], 1)
        self.assertEqual(duplicate_report["exact_span_signature_groups_n"], 1)
        duplicate_rows = screen.read_csv(
            self.base / "revised_duplicates" / "revised_duplicate_sensitivity_controlled.csv"
        )
        self.assertEqual(len(duplicate_rows), 18)
        descriptive_report = revised_descriptives.build(
            self.base / "phase3", self.output / "approved_evidence_units.jsonl",
            self.base / "revised_descriptives",
        )
        self.assertFalse(descriptive_report["article_ready"])
        self.assertEqual(descriptive_report["approved_capture_units_n"], 1)
        coverage_rows = screen.read_csv(
            self.base / "revised_descriptives" / "revised_source_coverage_controlled.csv"
        )
        self.assertEqual(len(coverage_rows), 2)
        self.assertEqual(coverage_rows[0]["unknown_or_mixed_unit_date_n"], "1")
        modality_rows = screen.read_csv(
            self.base / "revised_descriptives" / "revised_modality_contribution_controlled.csv"
        )
        fullz = next(row for row in modality_rows if row["code"] == "fullz_identity_package")
        self.assertEqual(fullz["markdown_only_positive_units_n"], "1")
        altered_phase3 = self.base / "phase3_changed_label"
        shutil.copytree(self.base / "phase3", altered_phase3)
        changed_rows = screen.read_csv(altered_phase3 / "typology_coding_long.csv")
        changed_rows[0]["label"] = "Changed label"
        save_csv(altered_phase3 / "typology_coding_long.csv", changed_rows, list(changed_rows[0]))
        with self.assertRaisesRegex(ValueError, "generated codebook"):
            revised_descriptives.build(altered_phase3,
                                       self.output / "approved_evidence_units.jsonl",
                                       self.base / "changed_label_descriptives")
        self.assertFalse((self.base / "changed_label_descriptives").exists())
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
        with self.assertRaisesRegex(ValueError, "hash-matched"):
            revised_descriptives.build(self.base / "phase3", altered_evidence,
                                       self.base / "tampered_descriptives")
        self.assertFalse((self.base / "tampered_descriptives").exists())
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

    def test_included_source_attribution_needs_recorded_rationale(self) -> None:
        self.complete_review()
        notes = screen.read_csv(self.review / "note_decisions.csv", screen.NOTE_FIELDS)
        included_note = next(row for row in notes if row["final_decision"] == "include")
        included_note["decision_reason"] = ""
        save_csv(self.review / "note_decisions.csv", notes, screen.NOTE_FIELDS)
        with self.assertRaisesRegex(ValueError, "source-attribution rationale"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

        included_note["decision_reason"] = "Visible source marker"
        save_csv(self.review / "note_decisions.csv", notes, screen.NOTE_FIELDS)
        images = screen.read_csv(self.review / "image_decisions.csv", screen.IMAGE_FIELDS)
        included_image = next(row for row in images if row["final_decision"] == "include")
        included_image["decision_reason"] = ""
        save_csv(self.review / "image_decisions.csv", images, screen.IMAGE_FIELDS)
        with self.assertRaisesRegex(ValueError, "source-match rationale"):
            screen.build(self.vault, self.index, self.joined, self.review, self.output)

    def test_controlled_output_cannot_enter_public_repository(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the public repository"):
            screen.prepare(self.vault, self.index, self.joined, ROOT / "unsafe-review")


if __name__ == "__main__":
    unittest.main()
