from __future__ import annotations

import importlib.util
import sys
import tempfile
import unicodedata
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


phase1 = load_module(
    "bank_drop_phase1_for_tests",
    "code/phase1_markdown_baseline/extract_phase1.py",
)


class CanonicalNoteIdentityTests(unittest.TestCase):
    def test_note_paths_are_unicode_normalised_posix_and_ids_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            decomposed_folder = "Cafe\u0301"
            note = vault / "Collected Data" / decomposed_folder / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text("Evidence", encoding="utf-8")

            records = list(
                phase1.iter_notes(
                    vault,
                    {"date_patterns": [], "source_root_parts": ["Collected Data"]},
                )
            )
            self.assertEqual(len(records), 1)
            record = records[0]
            expected_path = f"Collected Data/{unicodedata.normalize('NFC', decomposed_folder)}/note.md"
            self.assertEqual(record.relative_path, expected_path)
            self.assertNotIn("\\", record.relative_path)
            self.assertEqual(
                record.note_id,
                phase1.note_id_from_relative_path(expected_path),
            )
            self.assertEqual(
                record.legacy_note_id,
                phase1.sha256_text(record.legacy_relative_path)[:16],
            )
            self.assertEqual(
                phase1.note_id_from_relative_path("folder\\note.md"),
                phase1.note_id_from_relative_path("folder/note.md"),
            )

    def test_term_count_respects_word_boundaries(self) -> None:
        text = "wire wireless rewire WIRE wire-transfer; bank drop, BANK DROP, bank drops"
        self.assertEqual(phase1.term_count(text, "wire"), 3)
        self.assertEqual(phase1.term_count(text, "bank drop"), 2)


class ImageResolutionTests(unittest.TestCase):
    def test_explicit_relative_path_resolves_with_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            note = vault / "notes" / "note.md"
            image = vault / "assets" / "screen shot.png"
            note.parent.mkdir(parents=True)
            image.parent.mkdir(parents=True)
            note.write_text("", encoding="utf-8")
            image.write_bytes(b"png-evidence")

            result = phase1.resolve_image_reference(
                "../assets/screen%20shot.png",
                note,
                vault,
                phase1.build_png_index(vault),
            )
            self.assertEqual(result.status, "resolved")
            self.assertEqual(result.relative_path, "assets/screen shot.png")
            self.assertEqual(result.sha256, phase1.file_sha256(image))
            self.assertIn("note_relative", result.method)

    def test_basename_ambiguity_is_reported_instead_of_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            note = vault / "note.md"
            note.parent.mkdir(parents=True)
            note.write_text("", encoding="utf-8")
            for folder in ("a", "b"):
                image = vault / folder / "duplicate.png"
                image.parent.mkdir(parents=True)
                image.write_bytes(folder.encode("ascii"))

            result = phase1.resolve_image_reference(
                "duplicate.png", note, vault, phase1.build_png_index(vault)
            )
            self.assertEqual(result.status, "ambiguous")
            self.assertEqual(result.candidate_count, 2)
            self.assertEqual(result.sha256, "")

    def test_unsafe_external_and_missing_references_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            vault = Path(temporary) / "vault"
            vault.mkdir()
            note = vault / "note.md"
            note.write_text("", encoding="utf-8")
            self.assertEqual(phase1.resolve_image_reference("../../outside.png", note, vault).status, "unsafe")
            self.assertEqual(phase1.resolve_image_reference("https://example.org/a.png", note, vault).status, "external")
            self.assertEqual(phase1.resolve_image_reference("missing.png", note, vault).status, "missing")


if __name__ == "__main__":
    unittest.main()
