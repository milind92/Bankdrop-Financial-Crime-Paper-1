from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    path = REPOSITORY_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


phase2 = load_module(
    "bank_drop_phase2_for_tests",
    "code/phase2_image_ocr/run_phase2_ocr.py",
)


class Phase1ImageVerificationTests(unittest.TestCase):
    def test_resolved_row_requires_matching_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            image = vault / "assets" / "evidence.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"first-version")
            expected_hash = phase2.file_sha256(image)
            row = {
                "image_resolution_status": "resolved",
                "image_relative_path": "assets/evidence.png",
                "image_sha256": expected_hash,
            }

            resolved = phase2.resolve_phase1_image_row(row, vault)
            self.assertIsNotNone(resolved)
            assert resolved is not None
            self.assertEqual(resolved.relative_path, "assets/evidence.png")
            self.assertEqual(resolved.sha256, expected_hash)

            image.write_bytes(b"changed-after-phase-one")
            with self.assertRaisesRegex(RuntimeError, "no longer matches"):
                phase2.resolve_phase1_image_row(row, vault)
    def test_new_phase1_schema_requires_a_recorded_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            image = vault / "evidence.png"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"evidence")
            row = {"image_resolution_status": "resolved", "image_relative_path": "evidence.png"}
            with self.assertRaisesRegex(RuntimeError, "without image_sha256"):
                phase2.resolve_phase1_image_row(row, vault)


    def test_legacy_basename_fallback_refuses_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            for folder in ("a", "b"):
                image = vault / folder / "same.png"
                image.parent.mkdir(parents=True)
                image.write_bytes(folder.encode("ascii"))
            row = {"image_exists_in_vault_root": "1", "image_name": "same.png"}
            self.assertIsNone(
                phase2.resolve_phase1_image_row(row, vault, phase2.build_png_index(vault))
            )

    def test_safe_vault_path_rejects_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            with self.assertRaisesRegex(ValueError, "escapes"):
                phase2.safe_vault_path("../../outside.png", vault)


class OcrCacheTests(unittest.TestCase):
    def test_reuse_requires_exact_hash_config_and_self_consistent_key(self) -> None:
        image_hash = "a" * 64
        config_hash = "b" * 64
        valid = {
            "image_name": "name-does-not-identify-cache.png",
            "image_sha256": image_hash,
            "ocr_config_sha256": config_hash,
            "ocr_cache_key": phase2.ocr_cache_key(image_hash, config_hash),
            "ocr_status": "ok",
            "ocr_text": "verified text",
        }
        wrong_config = dict(valid)
        wrong_config["ocr_config_sha256"] = "c" * 64
        legacy_basename_only = {
            "image_name": "name-does-not-identify-cache.png",
            "image_sha256": image_hash,
            "ocr_status": "ok",
            "ocr_text": "stale text",
        }
        malformed_hash = {
            "image_sha256": "not-a-sha",
            "ocr_config_sha256": config_hash,
            "ocr_cache_key": "not-a-key",
            "ocr_status": "ok",
            "ocr_text": "unsafe cache text",
        }
        error_row = dict(valid)
        error_row["ocr_status"] = "error"

        cache = phase2.build_reusable_ocr_cache(
            [wrong_config, legacy_basename_only, error_row, malformed_hash, valid]
        )
        self.assertEqual(list(cache), [(image_hash, config_hash)])
        self.assertEqual(cache[(image_hash, config_hash)]["ocr_text"], "verified text")


class NoteAggregationTests(unittest.TestCase):
    def test_repeated_ocr_blocks_are_deduplicated_by_image_sha(self) -> None:
        corpus = [
            {
                "note_id": "note-1",
                "relative_path": "notes/one.md",
                "source": "source",
                "collection_date": "2026-01-01",
                "word_count": "10",
                "image_ref_count": "3",
            }
        ]
        joined = [
            {
                "note_id": "note-1",
                "image_relative_path": "a/one.png",
                "image_sha256": "1" * 64,
                "ocr_status": "ok",
                "ocr_word_count": "2",
                "ocr_char_count": "10",
                "ocr_text": "same text",
            },
            {
                "note_id": "note-1",
                "image_relative_path": "b/copy.png",
                "image_sha256": "1" * 64,
                "ocr_status": "ok",
                "ocr_word_count": "2",
                "ocr_char_count": "10",
                "ocr_text": "same text",
            },
            {
                "note_id": "note-1",
                "image_relative_path": "c/empty.png",
                "image_sha256": "2" * 64,
                "ocr_status": "empty",
                "ocr_word_count": "0",
                "ocr_char_count": "0",
                "ocr_text": "",
            },
        ]

        result = phase2.build_note_ocr_rows(corpus, joined)[0]
        self.assertEqual(result["ocr_image_count"], 3)
        self.assertEqual(result["ocr_ok_image_count"], 2)
        self.assertEqual(result["ocr_unique_image_count"], 2)
        self.assertEqual(result["ocr_unique_ok_image_count"], 1)
        self.assertEqual(result["ocr_duplicate_ref_count"], 1)
        self.assertEqual(result["ocr_word_count"], 2)
        self.assertEqual(str(result["joined_ocr_text"]).count("same text"), 1)


if __name__ == "__main__":
    unittest.main()
