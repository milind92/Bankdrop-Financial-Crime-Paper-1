"""Prepare and validate a controlled, author-reviewed Paper 1 evidence corpus.

The public repository contains this procedure, never the review worksheets or
assembled source text. ``prepare`` makes blank, inventory-bound worksheets;
``build`` fails until every note and image has two decisions, an adjudicated
decision, and every included source-text span has been approved. It then emits
one JSONL unit per eligible note (plus any approved stand-alone image units).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
NOTE_FIELDS = [
    "note_id", "relative_path", "sha256_text", "source_from_path",
    "filename_date", "reviewer_1", "reviewer_1_decision", "reviewer_2",
    "reviewer_2_decision", "final_decision", "adjudicator",
    "adjudication_reason", "record_type", "approved_source", "capture_date",
    "capture_date_basis", "markdown_decision", "markdown_decision_reason",
    "decision_reason",
]
IMAGE_FIELDS = [
    "reference_key", "kind", "note_id", "image_relative_path",
    "image_sha256", "ocr_status", "reference_count", "reviewer_1",
    "reviewer_1_decision", "reviewer_2", "reviewer_2_decision",
    "final_decision", "adjudicator", "adjudication_reason", "decision_reason",
    "assigned_note_id", "approved_source", "capture_date", "capture_date_basis",
]
SEGMENT_FIELDS = [
    "reference_key", "start_char", "end_char", "segment_sha256",
    "reviewer_1", "reviewer_1_decision", "reviewer_2",
    "reviewer_2_decision", "final_decision", "adjudicator",
    "adjudication_reason", "decision_reason",
]
NOTE_TYPES = {
    "source_capture", "mixed_source_and_researcher", "collection_status",
    "researcher_note", "out_of_scope", "unassessable",
}
DATE_BASES = {"source_metadata", "collector_record", "filename_only", "unknown"}


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_text(value: str) -> str:
    return sha_bytes(value.encode("utf-8", errors="replace"))


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path, fields: list[str] | None = None) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if fields and reader.fieldnames != fields:
            raise ValueError(f"Unexpected columns in {path.name}: {reader.fieldnames}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def controlled_path(path: Path, vault: Path | None = None) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("Controlled review and evidence output must be outside the public repository")
    if vault is not None:
        source = vault.resolve()
        if resolved == source or source in resolved.parents:
            raise ValueError("Controlled review and evidence output must be outside the source vault")
    return resolved


def vault_file(vault: Path, relative: str) -> Path:
    canonical = unicodedata.normalize("NFC", relative).replace("\\", "/")
    if not canonical or canonical.startswith("/") or re.match(r"^[A-Za-z]:", canonical):
        raise ValueError("Source path is not vault-relative")
    parts = PurePosixPath(canonical).parts
    if ".." in parts:
        raise ValueError("Source path escapes vault")
    target = vault.joinpath(*parts).resolve()
    if target != vault.resolve() and vault.resolve() not in target.parents:
        raise ValueError("Source path escapes vault")
    return target


def canonical_path(path: Path, vault: Path) -> str:
    return unicodedata.normalize("NFC", path.resolve().relative_to(vault.resolve()).as_posix())


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def inventory(vault: Path, phase1_index: Path, phase2_joined: Path):
    """Recheck all frozen note/image content before permitting any decision."""
    source = vault.resolve()
    if source == ROOT or ROOT in source.parents:
        raise ValueError("Controlled source vault must remain outside the public repository")
    notes = {}
    note_texts = {}
    expected_reference_counts = {}
    for row in read_csv(phase1_index):
        note_id = row["note_id"]
        if not note_id or note_id in notes:
            raise ValueError("Missing or duplicate Phase 1 note ID")
        relative = row["relative_path"]
        path = vault_file(vault, relative)
        text = normalise_newlines(path.read_text(encoding="utf-8", errors="replace"))
        if sha_text(text) != row["sha256_text"].lower():
            raise ValueError(f"Phase 1 note hash mismatch: {note_id}")
        notes[note_id] = {
            "note_id": note_id, "relative_path": relative,
            "sha256_text": row["sha256_text"].lower(),
            "source_from_path": row.get("source", ""),
            "filename_date": row.get("collection_date", ""),
        }
        try:
            expected_reference_counts[note_id] = int(row["image_ref_count"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Phase 1 image-reference count is missing for {note_id}") from exc
        if expected_reference_counts[note_id] < 0:
            raise ValueError(f"Negative Phase 1 image-reference count for {note_id}")
        note_texts[f"markdown:{note_id}"] = text

    images = {}
    ocr_texts = {}
    linked_paths = set()
    referenced_hashes = set()
    seen_reference_indices: dict[str, set[int]] = defaultdict(set)
    for row in read_csv(phase2_joined):
        note_id = row["note_id"]
        if note_id not in notes:
            raise ValueError("Phase 2 image reference is outside Phase 1 corpus")
        try:
            index = int(row["image_index_in_note"])
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Phase 2 image index is missing for {note_id}") from exc
        if index < 1 or index > expected_reference_counts[note_id] or index in seen_reference_indices[note_id]:
            raise ValueError(f"Phase 2 image indices do not match Phase 1 for {note_id}")
        seen_reference_indices[note_id].add(index)
        status = row.get("image_resolution_status", "")
        if status == "resolved":
            relative = row["image_relative_path"]
            image_sha = row["image_sha256"].lower()
            if not SHA_RE.fullmatch(image_sha):
                raise ValueError("Resolved image has invalid SHA-256")
            path = vault_file(vault, relative)
            if not path.is_file() or sha_file(path) != image_sha:
                raise ValueError(f"Resolved image hash mismatch: {relative}")
            linked_paths.add(canonical_path(path, vault))
            referenced_hashes.add(image_sha)
            key = f"linked:{note_id}:{image_sha}"
            ocr_status = row.get("ocr_status", "")
            text = row.get("ocr_text", "")
            config_sha = row.get("ocr_config_sha256", "").lower()
            cache_key = row.get("ocr_cache_key", "").lower()
            if ocr_status in {"ok", "empty"}:
                if not SHA_RE.fullmatch(config_sha) or cache_key != sha_text(f"{image_sha}:{config_sha}"):
                    raise ValueError("Phase 2 OCR cache provenance mismatch")
            if key in images:
                old = images[key]
                old["reference_count"] = str(int(old["reference_count"]) + 1)
                if ocr_texts[key] != text or old["ocr_status"] != ocr_status:
                    raise ValueError("Conflicting OCR for repeated image content")
                if relative < old["image_relative_path"]:
                    old["image_relative_path"] = relative
            else:
                images[key] = {
                    "reference_key": key, "kind": "linked", "note_id": note_id,
                    "image_relative_path": relative, "image_sha256": image_sha,
                    "ocr_status": ocr_status, "reference_count": "1",
                }
                ocr_texts[key] = text
            continue
        key = f"unresolved:{note_id}:{index}"
        if key in images:
            raise ValueError("Duplicate unresolved image reference key")
        images[key] = {
            "reference_key": key, "kind": "unresolved", "note_id": note_id,
            "image_relative_path": "", "image_sha256": "",
            "ocr_status": row.get("ocr_status", "not_local_or_not_processed"),
            "reference_count": "1",
        }

    for note_id, expected in expected_reference_counts.items():
        if len(seen_reference_indices[note_id]) != expected:
            raise ValueError(f"Phase 2 image-reference coverage is incomplete for {note_id}")

    for path in sorted(vault.rglob("*")):
        if not path.is_file() or path.suffix.casefold() != ".png":
            continue
        relative = canonical_path(path, vault)
        if relative in linked_paths:
            continue
        image_sha = sha_file(path)
        key = f"orphan:{relative}"
        images[key] = {
            "reference_key": key, "kind": "orphan", "note_id": "",
            "image_relative_path": relative, "image_sha256": image_sha,
            "ocr_status": "not_in_phase2", "reference_count": "0",
        }
    return notes, note_texts, images, ocr_texts, referenced_hashes


def review_template(rows: dict[str, dict[str, str]], fields: list[str]) -> list[dict[str, str]]:
    return [{field: row.get(field, "") for field in fields} for _, row in sorted(rows.items())]


def prepare(vault: Path, phase1_index: Path, phase2_joined: Path, review_dir: Path) -> dict:
    review_dir = controlled_path(review_dir, vault)
    notes, _, images, _, _ = inventory(vault, phase1_index, phase2_joined)
    if review_dir.exists() and any(review_dir.iterdir()):
        raise ValueError("Review directory is not empty; existing human decisions will not be overwritten")
    review_dir.mkdir(parents=True, exist_ok=True)
    write_csv(review_dir / "note_decisions.csv", review_template(notes, NOTE_FIELDS), NOTE_FIELDS)
    write_csv(review_dir / "image_decisions.csv", review_template(images, IMAGE_FIELDS), IMAGE_FIELDS)
    write_csv(review_dir / "source_segments.csv", [], SEGMENT_FIELDS)
    counts = Counter(row["kind"] for row in images.values())
    metadata = {
        "schema_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase1_index_sha256": sha_file(phase1_index),
        "phase2_joined_sha256": sha_file(phase2_joined),
        "notes_to_review": len(notes),
        "image_decisions_to_review": dict(sorted(counts.items())),
        "status": "blank_review_template",
    }
    (review_dir / "review_inventory.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def check_vote(row: dict[str, str], allowed: set[str], key: str) -> str:
    names = [row.get("reviewer_1", "").strip(), row.get("reviewer_2", "").strip()]
    decisions = [row.get("reviewer_1_decision", "").strip(), row.get("reviewer_2_decision", "").strip()]
    final = row.get("final_decision", "").strip()
    if not all(names) or names[0].casefold() == names[1].casefold():
        raise ValueError(f"Two distinct reviewers are required for {key}")
    if any(value not in allowed for value in (*decisions, final)):
        raise ValueError(f"Incomplete or invalid reviewer decisions for {key}")
    if not row.get("adjudicator", "").strip():
        raise ValueError(f"An adjudicator is required for {key}")
    if (decisions[0] != decisions[1] or final not in decisions) and not row.get("adjudication_reason", "").strip():
        raise ValueError(f"Disagreement or adjudicator override requires a reason for {key}")
    return final


def check_date(row: dict[str, str], key: str) -> str:
    basis = row.get("capture_date_basis", "").strip()
    raw = row.get("capture_date", "").strip()
    if basis not in DATE_BASES:
        raise ValueError(f"Capture-date basis is missing or invalid for {key}")
    if basis in {"unknown", "filename_only"}:
        if raw:
            raise ValueError(f"Unverified capture date must remain blank for {key}")
        return ""
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError as exc:
        raise ValueError(f"Verified capture date is invalid for {key}") from exc


def check_identity(rows: list[dict[str, str]], expected: dict[str, dict[str, str]],
                   key_field: str, identity_fields: list[str]) -> dict[str, dict[str, str]]:
    actual = {}
    for row in rows:
        key = row[key_field]
        if not key or key in actual:
            raise ValueError(f"Blank or duplicate {key_field} in review sheet")
        actual[key] = row
    if set(actual) != set(expected):
        raise ValueError(f"Review inventory differs from frozen {key_field} inventory")
    for key, row in actual.items():
        if any(row.get(field, "") != expected[key].get(field, "") for field in identity_fields):
            raise ValueError(f"Frozen inventory identity was edited for {key}")
    return actual


def supplement_ocr(path: Path | None, image_rows: dict[str, dict[str, str]],
                   approved_configs: set[str]) -> dict[str, str]:
    if path is None:
        return {}
    required = ["image_relative_path", "image_sha256", "ocr_config_sha256", "ocr_cache_key", "ocr_status", "ocr_text"]
    cache = {}
    for row in read_csv(path, required):
        image_sha = row["image_sha256"].lower()
        config_sha = row["ocr_config_sha256"].lower()
        key = f"orphan:{row['image_relative_path']}"
        if key not in image_rows or image_rows[key]["image_sha256"] != image_sha:
            raise ValueError("Supplemental OCR image does not match orphan inventory")
        if (not SHA_RE.fullmatch(config_sha) or config_sha not in approved_configs
                or row["ocr_cache_key"].lower() != sha_text(f"{image_sha}:{config_sha}")):
            raise ValueError("Supplemental OCR cache provenance mismatch")
        if row["ocr_status"] != "ok" or not row["ocr_text"].strip():
            raise ValueError("Supplemental OCR must contain successful nonempty text")
        if key in cache:
            raise ValueError("Duplicate supplemental OCR image")
        cache[key] = row["ocr_text"]
    return cache


def build(vault: Path, phase1_index: Path, phase2_joined: Path,
          review_dir: Path, output_dir: Path, orphan_ocr: Path | None = None) -> dict:
    review_dir = controlled_path(review_dir, vault)
    output_dir = controlled_path(output_dir, vault)
    if review_dir == output_dir or review_dir in output_dir.parents or output_dir in review_dir.parents:
        raise ValueError("Review and evidence output directories must be separate")
    notes, note_texts, images, ocr_texts, referenced_hashes = inventory(vault, phase1_index, phase2_joined)
    frozen = json.loads((review_dir / "review_inventory.json").read_text(encoding="utf-8"))
    if frozen.get("schema_version") != 2 or frozen.get("phase1_index_sha256") != sha_file(phase1_index) or frozen.get("phase2_joined_sha256") != sha_file(phase2_joined):
        raise ValueError("Review template does not match current Phase 1/2 inputs")
    note_rows = check_identity(read_csv(review_dir / "note_decisions.csv", NOTE_FIELDS), notes,
                               "note_id", ["note_id", "relative_path", "sha256_text", "source_from_path", "filename_date"])
    image_rows = check_identity(read_csv(review_dir / "image_decisions.csv", IMAGE_FIELDS), images,
                                "reference_key", ["reference_key", "kind", "note_id", "image_relative_path", "image_sha256", "ocr_status", "reference_count"])
    phase2_configs = {
        row.get("ocr_config_sha256", "").lower()
        for row in read_csv(phase2_joined)
        if row.get("ocr_status") in {"ok", "empty"}
    }
    if orphan_ocr and len(phase2_configs) != 1:
        raise ValueError("Supplemental OCR requires one consistent Phase 2 OCR configuration")
    extra_ocr = supplement_ocr(orphan_ocr, image_rows, phase2_configs)

    units = {}
    for note_id, row in note_rows.items():
        decision = check_vote(row, {"include", "exclude"}, f"note {note_id}")
        record_type = row.get("record_type", "").strip()
        if record_type not in NOTE_TYPES:
            raise ValueError(f"Record type is missing or invalid for note {note_id}")
        if decision == "exclude":
            if not row.get("decision_reason", "").strip():
                raise ValueError(f"Exclusion reason is required for note {note_id}")
            continue
        if record_type not in {"source_capture", "mixed_source_and_researcher"}:
            raise ValueError(f"Non-source record cannot enter evidence corpus: {note_id}")
        source = row.get("approved_source", "").strip()
        if not source:
            raise ValueError(f"Approved source attribution is required for note {note_id}")
        markdown_decision = row.get("markdown_decision", "").strip()
        if markdown_decision not in {"source_spans", "no_source_text", "unassessable"}:
            raise ValueError(f"Markdown provenance decision is required for note {note_id}")
        if markdown_decision != "source_spans" and not row.get("markdown_decision_reason", "").strip():
            raise ValueError(f"Markdown non-inclusion needs a reason for note {note_id}")
        units[note_id] = {
            "note_id": note_id, "relative_path": row["relative_path"],
            "source": source, "collection_date": check_date(row, f"note {note_id}"),
            "date_basis": row["capture_date_basis"], "record_type": record_type,
            "artifacts": [],
        }

    allowed_references = {}
    orphan_standalone = 0
    for key, row in image_rows.items():
        decision = check_vote(row, {"include", "exclude", "unavailable"}, f"image {key}")
        original = images[key]
        if original["kind"] == "unresolved" and decision == "include":
            raise ValueError(f"Unresolved image cannot enter evidence corpus: {key}")
        if decision != "include":
            if not row.get("decision_reason", "").strip():
                raise ValueError(f"Image non-inclusion reason is required for {key}")
            continue
        if original["kind"] == "linked":
            unit_id = original["note_id"]
            if unit_id not in units:
                raise ValueError(f"Included image belongs to excluded note: {key}")
            if original["ocr_status"] != "ok" or not ocr_texts.get(key, "").strip():
                raise ValueError(f"Included image lacks usable, provenance-checked OCR: {key}")
            allowed_references[key] = (unit_id, "image_ocr", ocr_texts[key])
        elif original["kind"] == "orphan":
            if original["image_sha256"] in referenced_hashes:
                raise ValueError(f"Content-duplicate orphan cannot be included twice: {key}")
            if not row.get("decision_reason", "").strip():
                raise ValueError(f"Included orphan needs a source/linkage rationale: {key}")
            assigned = row.get("assigned_note_id", "").strip()
            if assigned:
                if assigned not in units:
                    raise ValueError(f"Orphan assigned to unapproved note: {key}")
                unit_id = assigned
            else:
                unit_id = f"orphan:{original['image_sha256']}"
                if unit_id in units:
                    raise ValueError("Duplicate orphan-content unit")
                source = row.get("approved_source", "").strip()
                if not source:
                    raise ValueError(f"Standalone orphan source attribution is required: {key}")
                units[unit_id] = {
                    "note_id": unit_id, "relative_path": original["image_relative_path"],
                    "source": source, "collection_date": check_date(row, key),
                    "date_basis": row["capture_date_basis"], "record_type": "orphan_image",
                    "artifacts": [],
                }
                orphan_standalone += 1
            if key not in extra_ocr:
                raise ValueError(f"Approved orphan needs provenance-matched supplemental OCR: {key}")
            allowed_references[key] = (unit_id, "image_ocr", extra_ocr[key])
    for note_id in units:
        if note_id in notes:
            key = f"markdown:{note_id}"
            allowed_references[key] = (note_id, "markdown_source_span", note_texts[key])

    segment_rows = read_csv(review_dir / "source_segments.csv", SEGMENT_FIELDS)
    spans_by_ref: dict[str, list[tuple[int, int]]] = defaultdict(list)
    image_refs_with_text = set()
    for index, row in enumerate(segment_rows, start=2):
        key = row["reference_key"]
        if key not in allowed_references:
            raise ValueError(f"Segment row {index} refers to unapproved source: {key}")
        decision = check_vote(row, {"include", "exclude"}, f"segment row {index}")
        if decision == "exclude":
            if not row.get("decision_reason", "").strip():
                raise ValueError(f"Excluded segment needs reason at row {index}")
            continue
        unit_id, kind, source_text = allowed_references[key]
        try:
            start, end = int(row["start_char"]), int(row["end_char"])
        except ValueError as exc:
            raise ValueError(f"Segment offsets invalid at row {index}") from exc
        if start < 0 or end <= start or end > len(source_text):
            raise ValueError(f"Segment offsets out of bounds at row {index}")
        if any(start < old_end and old_start < end for old_start, old_end in spans_by_ref[key]):
            raise ValueError(f"Overlapping source segments for {key}")
        span = source_text[start:end]
        if not span.strip() or sha_text(span) != row["segment_sha256"].lower():
            raise ValueError(f"Source-text segment hash mismatch at row {index}")
        if kind == "markdown_source_span" and re.search(r"!\[\[|!\[[^\]]*\]\(", span):
            raise ValueError(f"Markdown image/embed markup cannot be coded as source text at row {index}")
        spans_by_ref[key].append((start, end))
        units[unit_id]["artifacts"].append({
            "artifact_id": f"{key}:{start}:{end}", "kind": kind,
            "text_sha256": sha_text(span), "text": span,
        })
        if kind == "image_ocr":
            image_refs_with_text.add(key)
    for key in allowed_references:
        if not key.startswith("markdown:") and key not in image_refs_with_text:
            raise ValueError(f"Included image lacks an approved source-text span: {key}")
    for unit_id, unit in units.items():
        if unit_id in note_rows:
            policy = note_rows[unit_id]["markdown_decision"].strip()
            included_markdown = bool(spans_by_ref.get(f"markdown:{unit_id}"))
            if (policy == "source_spans") != included_markdown:
                raise ValueError(f"Approved Markdown spans do not match provenance decision for {unit_id}")
        if not unit["artifacts"]:
            raise ValueError(f"Included unit has no approved source text: {unit_id}")
        unit["artifacts"].sort(key=lambda item: item["artifact_id"])
    if not units:
        raise ValueError("No approved evidence units; refusing an empty substantive analysis")

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "approved_evidence_units.jsonl"
    with evidence_path.open("w", encoding="utf-8", newline="\n") as handle:
        for unit_id in sorted(units):
            handle.write(json.dumps(units[unit_id], ensure_ascii=False, sort_keys=True) + "\n")
    counts = Counter(row["final_decision"] for row in note_rows.values())
    image_counts = Counter((row["kind"], row["final_decision"]) for row in image_rows.values())
    metadata = {
        "schema_version": 2,
        "status": "source_screening_complete_target_validation_pending",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase1_index_sha256": sha_file(phase1_index),
        "phase2_joined_sha256": sha_file(phase2_joined),
        "note_decisions_sha256": sha_file(review_dir / "note_decisions.csv"),
        "image_decisions_sha256": sha_file(review_dir / "image_decisions.csv"),
        "source_segments_sha256": sha_file(review_dir / "source_segments.csv"),
        "supplemental_ocr_sha256": sha_file(orphan_ocr) if orphan_ocr else None,
        "evidence_jsonl_sha256": sha_file(evidence_path),
        "screened_notes": len(notes),
        "note_decisions": dict(sorted(counts.items())),
        "image_decisions": {f"{kind}:{decision}": count for (kind, decision), count in sorted(image_counts.items())},
        "approved_evidence_units": len(units),
        "approved_standalone_orphan_units": orphan_standalone,
        "approved_text_segments": sum(len(unit["artifacts"]) for unit in units.values()),
        "article_ready": False,
    }
    (output_dir / "evidence_build_manifest.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    sub = top.add_subparsers(dest="command", required=True)
    for name in ("prepare", "build"):
        command = sub.add_parser(name)
        command.add_argument("--vault", type=Path, required=True)
        command.add_argument("--phase1-index", type=Path, required=True)
        command.add_argument("--phase2-joined", type=Path, required=True)
        command.add_argument("--review-dir", type=Path, required=True)
        if name == "build":
            command.add_argument("--output-dir", type=Path, required=True)
            command.add_argument("--orphan-ocr", type=Path)
    return top


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.vault, args.phase1_index, args.phase2_joined, args.review_dir)
        else:
            result = build(args.vault, args.phase1_index, args.phase2_joined,
                           args.review_dir, args.output_dir, args.orphan_ocr)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
