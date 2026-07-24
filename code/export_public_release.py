"""Export only allowlisted aggregate outputs from a controlled pipeline run.

The exporter never walks the controlled output tree.  Every copy operation is
named below, and each candidate is checked for note-level fields, raw evidence
fields, and absolute controlled paths before any repository file is changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPORTER_VERSION = "1.0.0"


@dataclass(frozen=True)
class PublicExport:
    source: str
    destination: str


def phase_exports(source_folder: str, destination_folder: str, files: Sequence[str]) -> list[PublicExport]:
    return [
        PublicExport(f"{source_folder}/{filename}", f"outputs/{destination_folder}/{filename}")
        for filename in files
    ]


PUBLIC_EXPORTS = tuple(
    phase_exports(
        "phase1_markdown_baseline",
        "phase1_aggregate",
        (
            "source_summary.csv",
            "keyword_summary_by_source.csv",
            "entity_summary_by_source.csv",
            "top_price_amounts.csv",
            "phase1_summary.json",
            "PHASE1_CHECKPOINT_SUMMARY.md",
        ),
    )
    + phase_exports(
        "phase2_image_ocr",
        "phase2_aggregate",
        ("ocr_summary_by_source.csv", "PHASE2_CHECKPOINT_SUMMARY.md"),
    )
    + phase_exports(
        "phase3_typology_coding",
        "phase3_aggregate",
        (
            "typology_summary.csv",
            "typology_summary_by_source.csv",
            "criminal_objective_summary.csv",
            "aml_indicator_summary_by_source.csv",
            "CODEBOOK_PHASE3.md",
            "PHASE3_ANALYTIC_OVERVIEW.md",
            "PHASE3_CHECKPOINT_SUMMARY.md",
        ),
    )
    + phase_exports(
        "phase4_financial_crime_analysis",
        "phase4_aggregate",
        (
            "financial_crime_findings.csv",
            "aml_red_flags_summary.csv",
            "source_profile_summary.csv",
            "FINANCIAL_CRIME_ANALYSIS_REPORT.md",
            "PHASE4_CHECKPOINT_SUMMARY.md",
            "run_metadata.json",
        ),
    )
    + phase_exports(
        "human_validation",
        "human_validation",
        (
            "HUMAN_ICR_COMPLETION.md",
            "validation_code_summary.csv",
            "human_icr_aggregate_summary.csv",
        ),
    )
    + phase_exports(
        "analysis_audit",
        "analysis_audit",
        ("corpus_screening_audit_summary.csv",),
    )
)


BLOCKED_FILENAMES = {
    "corpus_index.csv",
    "image_references.csv",
    "keyword_counts_long.csv",
    "entity_mentions_long.csv",
    "price_mentions.csv",
    "ocr_image_results.csv",
    "ocr_joined_to_notes.csv",
    "ocr_text_by_note.csv",
    "combined_corpus_with_ocr.csv",
    "typology_coding_long.csv",
    "aml_indicator_coding_long.csv",
    "evidence_snippets.csv",
    "validation_sample_index.csv",
    "blinded_coder_sheet_template.csv",
    "adjudication_sheet_template.csv",
    "file_inventory.csv",
    "phase_inventory.csv",
}
BLOCKED_FIELD_TOKENS = {"path", "text", "snippet", "snippets", "evidence"}
BLOCKED_EXACT_FIELDS = {"note_id", "legacy_note_id", "record_id"}
SAFE_AGGREGATE_FIELDS = {
    "unique_text_count",
    "positive_unique_evidence_rows",
    "negative_unique_evidence_rows",
    "evidence_packet_count",
}
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:file://|(?:^|[\s\"'=(\x60])(?:[A-Za-z]:[\\/]|/(?:home|Users|mnt|tmp|var|private)/))",
    re.MULTILINE,
)


class PublicExportError(ValueError):
    """Raised when a candidate does not meet the public-data boundary."""


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def is_within(candidate: Path, parent: Path) -> bool:
    try:
        resolved(candidate).relative_to(resolved(parent))
    except ValueError:
        return False
    return True


def field_is_blocked(field: str) -> bool:
    normalized = field.strip().lstrip("\ufeff").casefold()
    if normalized in SAFE_AGGREGATE_FIELDS:
        return False
    tokens = {token for token in re.split(r"[^a-z0-9]+", normalized) if token}
    return normalized in BLOCKED_EXACT_FIELDS or bool(tokens & BLOCKED_FIELD_TOKENS)


def assert_no_absolute_paths(text: str, source: Path) -> None:
    if ABSOLUTE_PATH_PATTERN.search(text):
        raise PublicExportError(f"Absolute controlled path found in allowlisted file: {source.name}")


def validate_csv(source: Path) -> None:
    with source.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            fields = next(reader)
        except StopIteration as exc:
            raise PublicExportError(f"Allowlisted CSV is empty: {source.name}") from exc
        blocked = [field for field in fields if field_is_blocked(field)]
        if blocked:
            raise PublicExportError(
                f"Note-level or raw-evidence fields in {source.name}: {', '.join(blocked)}"
            )
        for row in reader:
            for value in row:
                assert_no_absolute_paths(value, source)


def walk_json(value: Any, source: Path) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if field_is_blocked(str(key)):
                raise PublicExportError(f"Sensitive JSON key in {source.name}: {key}")
            walk_json(child, source)
    elif isinstance(value, list):
        for child in value:
            walk_json(child, source)
    elif isinstance(value, str):
        assert_no_absolute_paths(value, source)


def validate_json(source: Path) -> None:
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise PublicExportError(f"Invalid JSON in allowlisted file: {source.name}") from exc
    walk_json(payload, source)


def validate_public_candidate(source: Path) -> None:
    if source.name.casefold() in BLOCKED_FILENAMES:
        raise PublicExportError(f"Note-level filename is never exportable: {source.name}")
    if source.is_symlink():
        raise PublicExportError(f"Symlinked output is not exportable: {source.name}")
    suffix = source.suffix.casefold()
    if suffix == ".csv":
        validate_csv(source)
    elif suffix == ".json":
        validate_json(source)
    elif suffix == ".md":
        assert_no_absolute_paths(source.read_text(encoding="utf-8-sig"), source)
    else:
        raise PublicExportError(f"Unsupported public-output type: {source.name}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        shutil.copyfile(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def export_public_release(
    source_output_root: Path,
    repository_root: Path,
    *,
    dry_run: bool = False,
) -> list[dict[str, object]]:
    """Validate and copy all existing allowlisted aggregate outputs."""

    source_output_root = resolved(source_output_root)
    repository_root = resolved(repository_root)
    if not source_output_root.is_dir():
        raise PublicExportError(f"Controlled output root does not exist: {source_output_root}")
    if not repository_root.is_dir():
        raise PublicExportError(f"Repository root does not exist: {repository_root}")
    if source_output_root == repository_root or is_within(source_output_root, repository_root):
        raise PublicExportError("Controlled output root must be outside the public repository")

    candidates: list[tuple[PublicExport, Path, Path]] = []
    for item in PUBLIC_EXPORTS:
        source = source_output_root / Path(item.source)
        destination = repository_root / Path(item.destination)
        if not source.exists():
            continue
        if not source.is_file() or not is_within(source, source_output_root):
            raise PublicExportError(f"Allowlisted source is not a regular contained file: {item.source}")
        if not is_within(destination, repository_root):
            raise PublicExportError(f"Export destination escapes repository: {item.destination}")
        validate_public_candidate(source)
        candidates.append((item, source, destination))

    if not candidates:
        raise PublicExportError("No allowlisted aggregate outputs were found")

    records: list[dict[str, object]] = []
    for item, source, destination in candidates:
        digest = sha256_file(source)
        if not dry_run:
            atomic_copy(source, destination)
        records.append(
            {
                "source": item.source,
                "destination": item.destination,
                "sha256": digest,
                "status": "validated" if dry_run else "copied",
            }
        )
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-output-root", required=True, type=Path, help="Controlled Phases 1--5 output root")
    parser.add_argument("--repository-root", required=True, type=Path, help="Public repository checkout")
    parser.add_argument("--dry-run", action="store_true", help="Validate candidates without copying them")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        records = export_public_release(
            args.source_output_root, args.repository_root, dry_run=args.dry_run
        )
    except PublicExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"exporter_version": EXPORTER_VERSION, "dry_run": args.dry_run, "files": records},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
