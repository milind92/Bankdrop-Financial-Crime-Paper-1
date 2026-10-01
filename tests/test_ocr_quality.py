from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "bank_drop_ocr_quality_for_tests", ROOT / "code/ocr_quality/assess_ocr_quality.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot import OCR quality procedure")
quality = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = quality
spec.loader.exec_module(quality)


def save_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class OcrQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = ROOT.parents[1] / "outputs" / "paper1_audit_20261001" / f"test_ocr_{uuid.uuid4().hex}"
        self.base.mkdir()
        self.vault = self.base / "vault"
        self.vault.mkdir()
        self.review = self.base / "review"
        self.output = self.base / "scored"
        self.ocr_csv = self.base / "ocr_text_by_image.csv"
        self.joined_csv = self.base / "ocr_joined_image_references.csv"
        config = quality.text_sha("fixture-config")
        ocr_rows = []
        joined_rows = []
        for index, (source, ocr_text) in enumerate((
            ("A", "bank drop"), ("A", "cash ot"), ("A", "hello"), ("B", "transfer")
        ), start=1):
            image = self.vault / f"image-{index}.png"
            image.write_bytes(f"fixture-image-{index}".encode())
            digest = quality.file_sha(image)
            ocr_rows.append({
                "image_relative_path": image.name,
                "image_sha256": digest,
                "ocr_config_sha256": config,
                "ocr_cache_key": quality.text_sha(f"{digest}:{config}"),
                "ocr_status": "ok",
                "ocr_text": ocr_text,
            })
            joined_rows.append({
                "image_resolution_status": "resolved", "image_sha256": digest,
                "source": source,
            })
        save_csv(self.ocr_csv, ocr_rows, list(ocr_rows[0]))
        save_csv(self.joined_csv, joined_rows, list(joined_rows[0]))
        quality.prepare(self.vault, self.ocr_csv, self.joined_csv, self.review,
                        size=3, minimum=1)

    def tearDown(self) -> None:
        if self.base.resolve().is_relative_to(ROOT.parents[1].resolve()):
            shutil.rmtree(self.base)

    def complete_review(self, create_lock: bool = True) -> None:
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        gold_by_image = {"image-1.png": "bank drop", "image-2.png": "cash out", "image-3.png": "hello", "image-4.png": "transfer"}
        for row in rows:
            name = row["image_relative_path"]
            path = self.review / "transcripts" / f"{row['sample_number']}.txt"
            path.write_text(gold_by_image[name], encoding="utf-8")
            row.update({
                "transcript_relative_path": f"transcripts/{row['sample_number']}.txt",
                "transcriber": "Reviewer A", "transcriber_blind_to_ocr": "yes",
                "checker": "Reviewer B", "checker_blind_to_ocr": "yes",
                "transcript_check_status": "agreed", "image_text_legible": "full",
                "transcription_scope": "all_visible_text",
            })
        save_csv(self.review / "ocr_quality_sample.csv", rows, quality.SAMPLE_FIELDS)
        if create_lock:
            quality.lock_transcripts(self.vault, self.ocr_csv, self.joined_csv, self.review)
        for row in rows:
            row["ocr_extraction_adequate"] = "yes"
            row["review_status"] = "complete"
        save_csv(self.review / "ocr_quality_sample.csv", rows, quality.SAMPLE_FIELDS)

    def test_sample_has_known_stratum_probabilities_and_blank_review(self) -> None:
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        self.assertEqual(len(rows), 3)
        self.assertEqual(sorted((row["source_stratum"], row["population_stratum_n"], row["selected_stratum_n"]) for row in rows),
                         [("A", "3", "2"), ("A", "3", "2"), ("B", "1", "1")])
        self.assertTrue(all(row["transcriber"] == "" and row["review_status"] == "pending" for row in rows))

    def test_incomplete_review_fails_without_report(self) -> None:
        with self.assertRaisesRegex(ValueError, "lock is missing"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)
        self.assertFalse(self.output.exists())

    def test_completed_sheet_without_pre_unblinding_lock_fails(self) -> None:
        self.complete_review(create_lock=False)
        with self.assertRaisesRegex(ValueError, "lock is missing"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)
        self.assertFalse(self.output.exists())

    def test_lock_rejects_ocr_adequacy_filled_before_transcript_freeze(self) -> None:
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        rows[0]["ocr_extraction_adequate"] = "yes"
        save_csv(self.review / "ocr_quality_sample.csv", rows, quality.SAMPLE_FIELDS)
        with self.assertRaisesRegex(ValueError, "adequacy must remain blank"):
            quality.lock_transcripts(self.vault, self.ocr_csv, self.joined_csv, self.review)
        self.assertFalse((self.review / "transcript_lock_manifest.json").exists())

    def test_checked_transcripts_produce_bounded_diagnostic(self) -> None:
        self.complete_review()
        report = quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)
        self.assertEqual(report["sample_size"], 3)
        self.assertEqual(report["population_unique_image_hashes"], 4)
        self.assertEqual(report["ocr_extraction_adequacy_weighted_percent"]["yes"], 100.0)
        self.assertEqual(report["image_legibility_weighted_percent"]["full"], 100.0)
        self.assertEqual(len(report["transcript_lock_manifest_sha256"]), 64)
        self.assertIsNotNone(report["word_error_rate_full_legible_weighted"])
        self.assertGreaterEqual(report["word_error_rate_full_legible_weighted"], 0)
        self.assertTrue((self.output / "per_image_ocr_quality_controlled.csv").exists())
        self.assertNotIn("bank drop", (self.output / "ocr_quality_report.json").read_text())

    def test_changed_image_or_review_identity_fails_closed(self) -> None:
        self.complete_review()
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        rows[0]["image_sha256"] = "0" * 64
        save_csv(self.review / "ocr_quality_sample.csv", rows, quality.SAMPLE_FIELDS)
        with self.assertRaisesRegex(ValueError, "sample identity"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)

    def test_changed_blinded_review_copy_fails_closed(self) -> None:
        self.complete_review()
        (self.review / "images" / "sample_001.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "review image changed"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)

    def test_changed_transcript_after_lock_fails_closed(self) -> None:
        self.complete_review()
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        transcript = self.review / rows[0]["transcript_relative_path"]
        transcript.write_text("changed after reveal", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "locked transcript changed"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)
        self.assertFalse(self.output.exists())

    def test_changed_human_review_field_after_lock_fails_closed(self) -> None:
        self.complete_review()
        rows = quality.read_csv(self.review / "ocr_quality_sample.csv", quality.SAMPLE_FIELDS)
        rows[0]["checker"] = "Reviewer C"
        save_csv(self.review / "ocr_quality_sample.csv", rows, quality.SAMPLE_FIELDS)
        with self.assertRaisesRegex(ValueError, "Pre-unblinding review"):
            quality.score(self.vault, self.ocr_csv, self.joined_csv, self.review, self.output)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
