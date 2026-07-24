from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def temporary_workspace():
    """Create disposable isolated fixtures."""

    return tempfile.TemporaryDirectory(dir=REPOSITORY_ROOT)


def load_module(name: str, relative_path: str):
    path = REPOSITORY_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


orchestrator = load_module("bank_drop_orchestrator_for_tests", "code/run_reproducible_pipeline.py")
exporter = load_module("bank_drop_exporter_for_tests", "code/export_public_release.py")


def make_repository(root: Path) -> Path:
    repository = root / "repository"
    for step in orchestrator.PIPELINE_STEPS:
        script = repository / step.script
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# fixture\n", encoding="utf-8")
    return repository


class PipelineGuardrailTests(unittest.TestCase):
    def test_missing_vault_is_refused(self) -> None:
        with temporary_workspace() as temporary:
            root = Path(temporary)
            repository = make_repository(root)
            with self.assertRaises(orchestrator.PipelineSafetyError):
                orchestrator.validate_controlled_paths(
                    root / "missing-vault", root / "controlled-output", repository
                )

    def test_output_inside_vault_is_refused(self) -> None:
        with temporary_workspace() as temporary:
            root = Path(temporary)
            repository = make_repository(root)
            vault = root / "vault"
            vault.mkdir()
            with self.assertRaisesRegex(orchestrator.PipelineSafetyError, "inside it"):
                orchestrator.validate_controlled_paths(vault, vault / "outputs", repository)

    def test_complete_outputs_inside_repository_are_refused(self) -> None:
        with temporary_workspace() as temporary:
            root = Path(temporary)
            repository = make_repository(root)
            vault = root / "vault"
            vault.mkdir()
            with self.assertRaisesRegex(orchestrator.PipelineSafetyError, "outside the public repository"):
                orchestrator.validate_controlled_paths(vault, repository / "outputs", repository)

    def test_dry_run_is_ordered_redacted_and_has_no_side_effects(self) -> None:
        with temporary_workspace() as temporary:
            root = Path(temporary)
            repository = make_repository(root)
            vault = root / "vault"
            vault.mkdir()
            output = root / "controlled-output"
            with mock.patch.object(orchestrator.subprocess, "run") as subprocess_run:
                manifest = orchestrator.run_pipeline(
                    vault, output, dry_run=True, repository_root=repository
                )
            subprocess_run.assert_not_called()
            self.assertFalse(output.exists())
            self.assertEqual(
                [step["phase"] for step in manifest["steps"]],
                [step.phase for step in orchestrator.PIPELINE_STEPS],
            )
            serialized = json.dumps(manifest)
            self.assertNotIn(str(vault), serialized)
            self.assertNotIn(str(output), serialized)
            self.assertTrue(all(step["status"] == "planned" for step in manifest["steps"]))
            self.assertTrue(all(len(step["script_sha256"]) == 64 for step in manifest["steps"]))

    def test_subprocess_failure_stops_later_phases(self) -> None:
        with temporary_workspace() as temporary:
            root = Path(temporary)
            repository = make_repository(root)
            vault = root / "vault"
            vault.mkdir()
            output = root / "controlled-output"
            failure = orchestrator.subprocess.CalledProcessError(2, ["python", "phase2"])
            with mock.patch.object(
                orchestrator.subprocess, "run", side_effect=[None, failure]
            ) as subprocess_run:
                with self.assertRaises(orchestrator.subprocess.CalledProcessError):
                    orchestrator.run_pipeline(vault, output, repository_root=repository)
            self.assertEqual(subprocess_run.call_count, 2)


class PublicExporterTests(unittest.TestCase):
    def make_roots(self, temporary: str) -> tuple[Path, Path]:
        root = Path(temporary)
        controlled = root / "controlled"
        repository = root / "repository"
        controlled.mkdir()
        repository.mkdir()
        return controlled, repository

    def test_only_existing_allowlisted_aggregate_is_copied(self) -> None:
        with temporary_workspace() as temporary:
            controlled, repository = self.make_roots(temporary)
            phase1 = controlled / "phase1_markdown_baseline"
            phase1.mkdir()
            safe = phase1 / "source_summary.csv"
            safe.write_text("source,note_count\nS01,3\n", encoding="utf-8")
            blocked = phase1 / "corpus_index.csv"
            blocked.write_text("note_id,text\nn1,raw evidence\n", encoding="utf-8")

            records = exporter.export_public_release(controlled, repository)

            destination = repository / "outputs" / "phase1_aggregate" / "source_summary.csv"
            self.assertEqual(destination.read_bytes(), safe.read_bytes())
            self.assertFalse((repository / "outputs" / "phase1_aggregate" / blocked.name).exists())
            self.assertEqual(len(records), 1)

    def test_allowlisted_csv_with_note_level_field_is_rejected_before_copy(self) -> None:
        with temporary_workspace() as temporary:
            controlled, repository = self.make_roots(temporary)
            source = controlled / "phase1_markdown_baseline" / "source_summary.csv"
            source.parent.mkdir()
            source.write_text("source,note_id,note_count\nS01,n1,1\n", encoding="utf-8")
            with self.assertRaisesRegex(exporter.PublicExportError, "[Nn]ote-level"):
                exporter.export_public_release(controlled, repository)
            self.assertFalse((repository / "outputs").exists())

    def test_allowlisted_content_with_absolute_path_is_rejected(self) -> None:
        with temporary_workspace() as temporary:
            controlled, repository = self.make_roots(temporary)
            source = controlled / "phase1_markdown_baseline" / "PHASE1_CHECKPOINT_SUMMARY.md"
            source.parent.mkdir()
            source.write_text("Controlled input: \x60C:\\Users\\researcher\\vault\x60\n", encoding="utf-8")
            with self.assertRaisesRegex(exporter.PublicExportError, "Absolute controlled path"):
                exporter.export_public_release(controlled, repository)

    def test_https_urls_are_not_mistaken_for_windows_drive_paths(self) -> None:
        with temporary_workspace() as temporary:
            controlled, repository = self.make_roots(temporary)
            source = controlled / "phase1_markdown_baseline" / "PHASE1_CHECKPOINT_SUMMARY.md"
            source.parent.mkdir()
            source.write_text(
                "Reference: https://doi.org/10.1016/j.techsoc.2025.103130\n",
                encoding="utf-8",
            )
            records = exporter.export_public_release(controlled, repository, dry_run=True)
            self.assertEqual(records[0]["status"], "validated")

    def test_export_dry_run_validates_without_writing(self) -> None:
        with temporary_workspace() as temporary:
            controlled, repository = self.make_roots(temporary)
            source = controlled / "phase2_image_ocr" / "ocr_summary_by_source.csv"
            source.parent.mkdir()
            source.write_text("source,ocr_ok_count\nS01,2\n", encoding="utf-8")
            records = exporter.export_public_release(controlled, repository, dry_run=True)
            self.assertEqual(records[0]["status"], "validated")
            self.assertFalse((repository / "outputs").exists())


if __name__ == "__main__":
    unittest.main()
