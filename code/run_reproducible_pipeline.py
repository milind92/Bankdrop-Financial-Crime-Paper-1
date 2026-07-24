"""Run the deterministic Bank Drop research pipeline against controlled data.

This entrypoint deliberately keeps the source vault and complete intermediate
outputs outside the public repository.  It invokes Phases 1--4 in a fixed order,
fails on the first unsuccessful phase, and records a path-redacted run manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ORCHESTRATOR_VERSION = "1.0.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "pipeline_run_manifest.json"


@dataclass(frozen=True)
class PipelineStep:
    phase: str
    script: str


PIPELINE_STEPS = (
    PipelineStep("phase1_markdown_baseline", "code/phase1_markdown_baseline/run_phase1.py"),
    PipelineStep("phase2_image_ocr", "code/phase2_image_ocr/run_phase2_ocr.py"),
    PipelineStep("phase3_typology_coding", "code/phase3_typology_coding/run_phase3_typology.py"),
    PipelineStep("phase4_financial_crime_analysis", "code/phase4_financial_crime_analysis/run_phase4_analysis.py"),
)


class PipelineSafetyError(ValueError):
    """Raised when controlled paths do not satisfy the safety boundary."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_within(candidate: Path, parent: Path) -> bool:
    try:
        resolved(candidate).relative_to(resolved(parent))
    except ValueError:
        return False
    return True


def validate_controlled_paths(
    vault: Path,
    output_root: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> tuple[Path, Path]:
    """Resolve and validate the non-public input and output locations."""

    vault = resolved(vault)
    output_root = resolved(output_root)
    repository_root = resolved(repository_root)

    if not vault.exists() or not vault.is_dir():
        raise PipelineSafetyError(f"Controlled vault does not exist or is not a directory: {vault}")
    if not repository_root.is_dir():
        raise PipelineSafetyError(f"Repository root does not exist or is not a directory: {repository_root}")
    if output_root.exists() and not output_root.is_dir():
        raise PipelineSafetyError(f"Controlled output root exists but is not a directory: {output_root}")
    if output_root == output_root.parent:
        raise PipelineSafetyError("Filesystem root is not a valid controlled output directory")
    if output_root == vault or is_within(output_root, vault):
        raise PipelineSafetyError("Output root must not be the source vault or a directory inside it")
    if is_within(vault, output_root):
        raise PipelineSafetyError("Source vault must not be contained by the controlled output root")
    if output_root == repository_root or is_within(output_root, repository_root):
        raise PipelineSafetyError(
            "Complete controlled outputs must be outside the public repository; use the exporter for aggregates"
        )
    if vault == repository_root or is_within(vault, repository_root):
        raise PipelineSafetyError("Controlled source vault must be outside the public repository")
    return vault, output_root


def redacted_command(step: PipelineStep) -> list[str]:
    """Return the publishable command description, without machine paths."""

    return ["[PYTHON]", step.script]


def build_environment(vault: Path, output_root: Path, repository_root: Path) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "BANK_DROP_WORKSPACE": str(repository_root),
            "BANK_DROP_VAULT": str(vault),
            "BANK_DROP_OUTPUTS_DIR": str(output_root),
            "BANK_DROP_SOURCE_OUTPUTS_DIR": str(output_root),
            "PYTHONHASHSEED": "0",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def run_pipeline(
    vault: Path,
    output_root: Path,
    *,
    python_executable: str = sys.executable,
    dry_run: bool = False,
    repository_root: Path = REPOSITORY_ROOT,
) -> dict[str, object]:
    """Execute the pipeline and return its redacted controlled run manifest."""

    repository_root = resolved(repository_root)
    vault, output_root = validate_controlled_paths(vault, output_root, repository_root)
    started_at = utc_now()
    steps: list[dict[str, object]] = []
    environment = build_environment(vault, output_root, repository_root)

    for step in PIPELINE_STEPS:
        script_path = repository_root / Path(step.script)
        if not script_path.is_file():
            raise FileNotFoundError(f"Pipeline script is missing: {step.script}")

        step_record: dict[str, object] = {
            "phase": step.phase,
            "command": redacted_command(step),
            "script_sha256": file_sha256(script_path),
            "started_at_utc": utc_now(),
            "status": "planned" if dry_run else "running",
        }
        steps.append(step_record)
        if dry_run:
            step_record["finished_at_utc"] = utc_now()
            continue

        try:
            subprocess.run(
                [python_executable, str(script_path)],
                cwd=repository_root,
                env=environment,
                check=True,
            )
        except subprocess.CalledProcessError:
            step_record["status"] = "failed"
            step_record["finished_at_utc"] = utc_now()
            raise
        step_record["status"] = "completed"
        step_record["finished_at_utc"] = utc_now()

    manifest: dict[str, object] = {
        "orchestrator": "Bank Drop deterministic pipeline",
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "python_version": platform.python_version(),
        "started_at_utc": started_at,
        "finished_at_utc": utc_now(),
        "dry_run": dry_run,
        "fixed_settings": {
            "python_hash_seed": 0,
            "validation_positive_target": 20,
            "validation_negative_target": 40,
            "validation_min_words": 30,
        },
        "path_boundary": {
            "source_vault": "[CONTROLLED_VAULT]",
            "output_root": "[CONTROLLED_OUTPUT_ROOT]",
            "public_repository": "[REPOSITORY_ROOT]",
        },
        "steps": steps,
    }

    if not dry_run:
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / MANIFEST_NAME).write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path, help="Controlled source-vault directory")
    parser.add_argument(
        "--output-root", required=True, type=Path, help="Controlled output directory outside this repository"
    )
    parser.add_argument(
        "--python", default=sys.executable, dest="python_executable", help="Python interpreter for phase subprocesses"
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate paths and print the planned commands only")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manifest = run_pipeline(
            args.vault,
            args.output_root,
            python_executable=args.python_executable,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, PipelineSafetyError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
