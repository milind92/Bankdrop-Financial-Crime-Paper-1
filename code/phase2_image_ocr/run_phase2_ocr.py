"""
Phase 2 image OCR for the Bank Drop Project.

Uses the local Windows OCR engine through the Python ``winrt-*`` packages, or
replays a complete provenance-matched cache when ``BANK_DROP_OCR_CACHE_ONLY=1``. The script verifies Phase 1 image provenance, keys reusable OCR by image content and
OCR configuration, and joins de-duplicated OCR evidence back to notes.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import FileAccessMode, StorageFile
except ImportError as exc:  # Keep pure provenance helpers testable off Windows.
    BitmapDecoder = None
    OcrEngine = None
    FileAccessMode = None
    StorageFile = None
    WINRT_IMPORT_ERROR: ImportError | None = exc
else:
    WINRT_IMPORT_ERROR = None


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
VAULT = Path(os.environ.get("BANK_DROP_VAULT", WORKSPACE / "work" / "bank_drop_project" / "DW Project"))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
PHASE1_OUTPUT = OUTPUTS / "phase1_markdown_baseline"
PHASE2_OUTPUT = OUTPUTS / "phase2_image_ocr"
IMAGE_REFS_CSV = PHASE1_OUTPUT / "image_references.csv"
CORPUS_INDEX_CSV = PHASE1_OUTPUT / "corpus_index.csv"
PIPELINE_VERSION = "2.1.0"
OCR_ENGINE_NAME = "windows.media.ocr"
SHA256_RE = re.compile(r"[0-9a-f]{64}")

OCR_IMAGE_FIELDS = [
    "image_name", "image_path", "image_relative_path", "image_sha256",
    "ocr_config_sha256", "ocr_cache_key", "ocr_engine", "ocr_language",
    "cache_reused", "ocr_status", "ocr_word_count", "ocr_char_count",
    "ocr_text", "error",
]

JOINED_FIELDS = [
    "note_id", "legacy_note_id", "relative_path", "legacy_relative_path",
    "source", "collection_date", "image_index_in_note", "image_ref",
    "image_name", "image_exists_in_vault_root", "image_reference_normalized",
    "image_resolution_status", "image_resolution_method", "image_relative_path",
    "image_sha256", "image_candidate_count", "ocr_config_sha256",
    "ocr_cache_key", "cache_reused", "ocr_status", "ocr_word_count",
    "ocr_char_count", "ocr_text", "error",
]

NOTE_FIELDS = [
    "note_id", "legacy_note_id", "relative_path", "legacy_relative_path",
    "source", "collection_date", "markdown_word_count", "image_ref_count",
    "ocr_image_count", "ocr_ok_image_count", "ocr_unique_image_count",
    "ocr_unique_ok_image_count", "ocr_duplicate_ref_count", "ocr_word_count",
    "ocr_char_count", "joined_ocr_text",
]


@dataclass(frozen=True)
class ResolvedImage:
    relative_path: str
    path: Path
    sha256: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def text_stats(text: str) -> tuple[int, int]:
    words = re.findall(r"\b\w+\b", text or "")
    return len(words), len(text or "")


def canonical_relative_path(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return unicodedata.normalize("NFC", relative)


def safe_vault_path(relative_path: str, vault: Path) -> Path:
    normalized = unicodedata.normalize("NFC", relative_path.strip()).replace("\\", "/")
    if not normalized or "\x00" in normalized:
        raise ValueError("Image relative path is empty or contains a null byte")
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("/"):
        raise ValueError(f"Image path is not vault-relative: {relative_path!r}")
    candidate = vault.joinpath(*PurePosixPath(normalized).parts).resolve()
    try:
        candidate.relative_to(vault.resolve())
    except ValueError as exc:
        raise ValueError(f"Image path escapes the vault: {relative_path!r}") from exc
    return candidate


def build_png_index(vault: Path) -> dict[str, list[Path]]:
    indexed: dict[str, list[Path]] = defaultdict(list)
    for path in vault.rglob("*"):
        if not path.is_file() or path.suffix.casefold() != ".png":
            continue
        resolved = path.resolve()
        try:
            canonical_relative_path(resolved, vault)
        except ValueError:
            continue
        indexed[path.name.casefold()].append(resolved)
    for paths in indexed.values():
        paths.sort(key=lambda item: canonical_relative_path(item, vault))
    return dict(indexed)


def resolve_phase1_image_row(
    row: dict[str, str],
    vault: Path,
    basename_index: dict[str, list[Path]] | None = None,
) -> ResolvedImage | None:
    """Resolve a Phase 1 row, verifying both containment and the recorded SHA."""
    phase1_status = (row.get("image_resolution_status") or "").strip()
    relative_path = (row.get("image_relative_path") or "").strip()
    expected_sha256 = (row.get("image_sha256") or "").strip().casefold()

    if phase1_status and phase1_status != "resolved":
        return None
    if phase1_status == "resolved" and not relative_path:
        raise RuntimeError("Phase 1 marked an image resolved without image_relative_path")
    if phase1_status == "resolved" and not expected_sha256:
        raise RuntimeError("Phase 1 marked an image resolved without image_sha256")
    if expected_sha256 and SHA256_RE.fullmatch(expected_sha256) is None:
        raise RuntimeError(f"Phase 1 recorded an invalid image SHA-256: {expected_sha256!r}")

    if relative_path:
        image_path = safe_vault_path(relative_path, vault)
        if not image_path.is_file() or image_path.suffix.casefold() != ".png":
            raise RuntimeError(f"Phase 1 resolved image is missing: {relative_path}")
    else:
        # Compatibility for old Phase 1 CSVs: a basename is accepted only when
        # globally unique and is never used as an OCR cache key.
        if row.get("image_exists_in_vault_root") != "1":
            return None
        image_name = (row.get("image_name") or "").strip()
        if not image_name:
            return None
        index = basename_index if basename_index is not None else build_png_index(vault)
        candidates = index.get(Path(image_name).name.casefold(), [])
        if len(candidates) != 1:
            return None
        image_path = candidates[0]

    actual_sha256 = file_sha256(image_path)
    if expected_sha256 and actual_sha256.casefold() != expected_sha256:
        raise RuntimeError(
            "Image SHA-256 no longer matches Phase 1 provenance for "
            f"{relative_path or image_path.name}: expected {expected_sha256}, got {actual_sha256}"
        )
    return ResolvedImage(
        relative_path=canonical_relative_path(image_path, vault),
        path=image_path,
        sha256=actual_sha256,
    )


def package_version(distribution: str) -> str:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def engine_language(engine: Any) -> str:
    language = getattr(engine, "recognizer_language", None)
    return str(getattr(language, "language_tag", "") or "")


def build_ocr_configuration(engine: Any) -> dict[str, object]:
    return {
        "pipeline_version": PIPELINE_VERSION,
        "ocr_engine": OCR_ENGINE_NAME,
        "ocr_language": engine_language(engine),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "winrt_package_versions": {
            name: package_version(name)
            for name in (
                "winrt-runtime", "winrt-Windows.Foundation",
                "winrt-Windows.Graphics.Imaging", "winrt-Windows.Media.Ocr",
                "winrt-Windows.Globalization",
                "winrt-Windows.Storage",
            )
        },
    }


def ocr_cache_key(image_sha256: str, ocr_config_sha256: str) -> str:
    return hashlib.sha256(f"{image_sha256}:{ocr_config_sha256}".encode("ascii")).hexdigest()


def build_reusable_ocr_cache(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str], dict[str, str]]:
    """Return complete successful cache rows with self-consistent keys."""
    cache: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        image_sha = (row.get("image_sha256") or "").strip().casefold()
        config_sha = (row.get("ocr_config_sha256") or "").strip().casefold()
        status = (row.get("ocr_status") or "").strip()
        recorded_key = (row.get("ocr_cache_key") or "").strip().casefold()
        if (
            SHA256_RE.fullmatch(image_sha) is None
            or SHA256_RE.fullmatch(config_sha) is None
            or status not in {"ok", "empty"}
        ):
            continue
        expected_key = ocr_cache_key(image_sha, config_sha)
        if recorded_key != expected_key:
            continue
        cache[(image_sha, config_sha)] = row
    return cache


async def ocr_image(path: Path, engine: Any) -> str:
    if StorageFile is None or FileAccessMode is None or BitmapDecoder is None:
        raise RuntimeError(f"Windows OCR dependencies are unavailable: {WINRT_IMPORT_ERROR}")
    storage_file = await StorageFile.get_file_from_path_async(str(path.resolve()))
    stream = await storage_file.open_async(FileAccessMode.READ)
    try:
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        return result.text or ""
    finally:
        stream.close()


def build_note_ocr_rows(
    corpus_rows: list[dict[str, str]],
    joined_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Aggregate OCR per note while de-duplicating repeated content hashes."""
    by_note: dict[str, dict[str, object]] = {}
    seen_by_note: dict[str, set[str]] = defaultdict(set)
    for row in corpus_rows:
        note_id = row.get("note_id", "")
        by_note[note_id] = {
            "note_id": note_id,
            "legacy_note_id": row.get("legacy_note_id", ""),
            "relative_path": row.get("relative_path", ""),
            "legacy_relative_path": row.get("legacy_relative_path", ""),
            "source": row.get("source", ""),
            "collection_date": row.get("collection_date", ""),
            "markdown_word_count": row.get("word_count", 0),
            "image_ref_count": row.get("image_ref_count", 0),
            "ocr_image_count": 0,
            "ocr_ok_image_count": 0,
            "ocr_unique_image_count": 0,
            "ocr_unique_ok_image_count": 0,
            "ocr_duplicate_ref_count": 0,
            "ocr_word_count": 0,
            "ocr_char_count": 0,
            "joined_ocr_text": "",
        }

    for joined in joined_rows:
        note_id = str(joined.get("note_id", ""))
        if note_id not in by_note:
            continue
        aggregate = by_note[note_id]
        aggregate["ocr_image_count"] = int(aggregate["ocr_image_count"]) + 1
        status = str(joined.get("ocr_status", ""))
        if status == "ok":
            aggregate["ocr_ok_image_count"] = int(aggregate["ocr_ok_image_count"]) + 1

        image_sha256 = str(joined.get("image_sha256") or "").strip().casefold()
        content_key = image_sha256 or str(
            joined.get("image_relative_path") or ""
        )
        if not content_key or status == "not_local_or_not_processed":
            continue
        if content_key in seen_by_note[note_id]:
            aggregate["ocr_duplicate_ref_count"] = int(aggregate["ocr_duplicate_ref_count"]) + 1
            continue
        seen_by_note[note_id].add(content_key)
        aggregate["ocr_unique_image_count"] = int(aggregate["ocr_unique_image_count"]) + 1

        if status == "ok":
            aggregate["ocr_unique_ok_image_count"] = int(aggregate["ocr_unique_ok_image_count"]) + 1
            aggregate["ocr_word_count"] = int(aggregate["ocr_word_count"]) + int(joined.get("ocr_word_count") or 0)
            aggregate["ocr_char_count"] = int(aggregate["ocr_char_count"]) + int(joined.get("ocr_char_count") or 0)
            label = str(joined.get("image_relative_path") or joined.get("image_name") or "image")
            block = f"\n\n[OCR: {label}]\n{joined.get('ocr_text', '')}"
            aggregate["joined_ocr_text"] = str(aggregate["joined_ocr_text"]) + block

    return list(by_note.values())


async def main() -> None:
    PHASE2_OUTPUT.mkdir(parents=True, exist_ok=True)
    if not IMAGE_REFS_CSV.exists():
        raise FileNotFoundError(f"Missing Phase 1 image references: {IMAGE_REFS_CSV}")
    if not VAULT.exists():
        raise FileNotFoundError(f"Missing extracted vault: {VAULT}")
    cache_only = os.environ.get("BANK_DROP_OCR_CACHE_ONLY", "").strip() == "1"
    if OcrEngine is None and not cache_only:
        raise RuntimeError(
            f"Windows OCR dependencies are unavailable: {WINRT_IMPORT_ERROR}. "
            "Set BANK_DROP_OCR_CACHE_ONLY=1 only when a complete, provenance-matched OCR cache is present."
        )

    image_refs = read_csv(IMAGE_REFS_CSV)
    corpus_rows = read_csv(CORPUS_INDEX_CSV) if CORPUS_INDEX_CSV.exists() else []
    basename_index = build_png_index(VAULT)

    resolved_refs: list[ResolvedImage | None] = []
    unique_images: dict[str, ResolvedImage] = {}
    resolution_counts: Counter[str] = Counter()
    for ref in image_refs:
        resolved = resolve_phase1_image_row(ref, VAULT, basename_index)
        resolved_refs.append(resolved)
        phase1_status = (ref.get("image_resolution_status") or "").strip()
        status = phase1_status or ("resolved" if resolved is not None else "legacy_unresolved")
        resolution_counts[status] += 1
        if resolved is not None:
            prior = unique_images.get(resolved.relative_path)
            if prior is not None and prior.sha256 != resolved.sha256:
                raise RuntimeError(f"Conflicting hashes for image path: {resolved.relative_path}")
            unique_images[resolved.relative_path] = resolved

    ocr_csv = PHASE2_OUTPUT / "ocr_text_by_image.csv"
    existing_rows = read_csv(ocr_csv) if ocr_csv.exists() else []
    engine = None
    if cache_only:
        config_hashes = {row.get("ocr_config_sha256", "").strip() for row in existing_rows if row.get("ocr_config_sha256", "").strip()}
        if len(config_hashes) != 1:
            raise RuntimeError("Cache-only OCR requires one consistent nonblank OCR configuration hash.")
        ocr_config_sha256 = next(iter(config_hashes))
        languages = {row.get("ocr_language", "").strip() for row in existing_rows if row.get("ocr_language", "").strip()}
        language = next(iter(languages)) if len(languages) == 1 else "cache-recorded"
        ocr_configuration = {"mode": "cache_only", "source_ocr_config_sha256": ocr_config_sha256}
    else:
        engine = OcrEngine.try_create_from_user_profile_languages()
        if engine is None:
            raise RuntimeError("Windows OCR engine is unavailable for the current user profile languages.")
        ocr_configuration = build_ocr_configuration(engine)
        ocr_config_sha256 = stable_json_sha256(ocr_configuration)
        language = engine_language(engine)
    reusable_cache = build_reusable_ocr_cache(existing_rows)
    rows_by_path: dict[str, dict[str, object]] = {}

    relative_paths = sorted(unique_images)
    total = len(relative_paths)
    for index, relative_path in enumerate(relative_paths, start=1):
        resolved = unique_images[relative_path]
        current_sha256 = file_sha256(resolved.path)
        if current_sha256 != resolved.sha256:
            raise RuntimeError(
                "Image changed after Phase 1 verification for "
                f"{resolved.relative_path}: expected {resolved.sha256}, got {current_sha256}"
            )

        cache_tuple = (resolved.sha256.casefold(), ocr_config_sha256.casefold())
        cached = reusable_cache.get(cache_tuple)
        if cached is not None:
            text = cached.get("ocr_text", "")
            word_count, char_count = text_stats(text)
            status = cached.get("ocr_status", "empty")
            error = ""
            cache_reused = 1
        else:
            if cache_only:
                raise RuntimeError(
                    "Cache-only OCR has no provenance-matched row for "
                    f"{resolved.relative_path} ({resolved.sha256})."
                )
            try:
                text = await ocr_image(resolved.path, engine)
                post_ocr_sha256 = file_sha256(resolved.path)
                if post_ocr_sha256 != resolved.sha256:
                    raise RuntimeError(
                        "Image changed while OCR was running for "
                        f"{resolved.relative_path}: expected {resolved.sha256}, got {post_ocr_sha256}"
                    )
                word_count, char_count = text_stats(text)
                status = "ok" if text.strip() else "empty"
                error = ""
            except Exception as exc:
                text = ""
                word_count = 0
                char_count = 0
                status = "error"
                error = f"{type(exc).__name__}: {exc}"
            cache_reused = 0

        cache_key = ocr_cache_key(resolved.sha256, ocr_config_sha256)
        output_row: dict[str, object] = {
            "image_name": resolved.path.name,
            "image_path": str(resolved.path),
            "image_relative_path": resolved.relative_path,
            "image_sha256": resolved.sha256,
            "ocr_config_sha256": ocr_config_sha256,
            "ocr_cache_key": cache_key,
            "ocr_engine": OCR_ENGINE_NAME,
            "ocr_language": language,
            "cache_reused": cache_reused,
            "ocr_status": status,
            "ocr_word_count": word_count,
            "ocr_char_count": char_count,
            "ocr_text": text,
            "error": error,
        }
        rows_by_path[relative_path] = output_row
        if status in {"ok", "empty"}:
            reusable_cache[cache_tuple] = {key: str(value) for key, value in output_row.items()}

        if index % 25 == 0 or index == total:
            print(f"OCR progress: {index}/{total} images")
            write_csv(ocr_csv, [rows_by_path[path] for path in sorted(rows_by_path)], OCR_IMAGE_FIELDS)

    ocr_rows = [rows_by_path[path] for path in sorted(rows_by_path)]
    write_csv(ocr_csv, ocr_rows, OCR_IMAGE_FIELDS)
    ocr_by_path = {str(row["image_relative_path"]): row for row in ocr_rows}

    joined_rows: list[dict[str, object]] = []
    for ref, resolved in zip(image_refs, resolved_refs, strict=True):
        ocr = ocr_by_path.get(resolved.relative_path, {}) if resolved is not None else {}
        image_name = ref.get("image_name", "")
        if not image_name and resolved is not None:
            image_name = resolved.path.name
        resolution_status = (ref.get("image_resolution_status") or "").strip()
        if not resolution_status:
            resolution_status = "resolved" if resolved is not None else "legacy_unresolved"
        joined_rows.append(
            {
                "note_id": ref.get("note_id", ""),
                "legacy_note_id": ref.get("legacy_note_id", ""),
                "relative_path": ref.get("relative_path", ""),
                "legacy_relative_path": ref.get("legacy_relative_path", ""),
                "source": ref.get("source", ""),
                "collection_date": ref.get("collection_date", ""),
                "image_index_in_note": ref.get("image_index_in_note", ""),
                "image_ref": ref.get("image_ref", ""),
                "image_name": image_name,
                "image_exists_in_vault_root": ref.get("image_exists_in_vault_root", ""),
                "image_reference_normalized": ref.get("image_reference_normalized", ""),
                "image_resolution_status": resolution_status,
                "image_resolution_method": ref.get("image_resolution_method", ""),
                "image_relative_path": resolved.relative_path if resolved is not None else ref.get("image_relative_path", ""),
                "image_sha256": resolved.sha256 if resolved is not None else ref.get("image_sha256", ""),
                "image_candidate_count": ref.get("image_candidate_count", ""),
                "ocr_config_sha256": ocr.get("ocr_config_sha256", ""),
                "ocr_cache_key": ocr.get("ocr_cache_key", ""),
                "cache_reused": ocr.get("cache_reused", ""),
                "ocr_status": ocr.get("ocr_status", "not_local_or_not_processed"),
                "ocr_word_count": ocr.get("ocr_word_count", 0),
                "ocr_char_count": ocr.get("ocr_char_count", 0),
                "ocr_text": ocr.get("ocr_text", ""),
                "error": ocr.get("error", ""),
            }
        )

    write_csv(PHASE2_OUTPUT / "ocr_joined_image_references.csv", joined_rows, JOINED_FIELDS)
    note_rows = build_note_ocr_rows(corpus_rows, joined_rows)
    write_csv(PHASE2_OUTPUT / "ocr_text_by_note.csv", note_rows, NOTE_FIELDS)

    status_counts = Counter(str(row["ocr_status"]) for row in ocr_rows)
    by_source: dict[str, Counter[str]] = defaultdict(Counter)
    for row in joined_rows:
        source = str(row.get("source") or "(no_source)")
        by_source[source][str(row.get("ocr_status"))] += 1
        by_source[source]["image_refs"] += 1
        by_source[source]["ocr_words"] += int(row.get("ocr_word_count") or 0)

    source_summary_rows = []
    for source, counter in sorted(by_source.items()):
        source_summary_rows.append(
            {
                "source": source,
                "image_ref_count": counter["image_refs"],
                "ocr_ok_count": counter["ok"],
                "ocr_empty_count": counter["empty"],
                "ocr_error_count": counter["error"],
                "ocr_not_local_or_not_processed_count": counter["not_local_or_not_processed"],
                "ocr_word_count": counter["ocr_words"],
            }
        )
    write_csv(
        PHASE2_OUTPUT / "ocr_summary_by_source.csv",
        source_summary_rows,
        [
            "source", "image_ref_count", "ocr_ok_count", "ocr_empty_count",
            "ocr_error_count", "ocr_not_local_or_not_processed_count",
            "ocr_word_count",
        ],
    )

    unique_content_hashes = {resolved.sha256 for resolved in unique_images.values()}
    metadata = {
        "phase": "phase2_image_ocr",
        "pipeline_version": PIPELINE_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "vault_path": str(VAULT),
        "phase1_output_path": str(PHASE1_OUTPUT),
        "phase2_output_path": str(PHASE2_OUTPUT),
        "phase1_image_reference_count": len(image_refs),
        "phase1_image_resolution_status_counts": dict(sorted(resolution_counts.items())),
        "unique_local_image_paths_for_ocr": len(unique_images),
        "unique_local_image_hashes_for_ocr": len(unique_content_hashes),
        "ocr_image_rows": len(ocr_rows),
        "ocr_cache_reused_rows": sum(int(row.get("cache_reused") or 0) for row in ocr_rows),
        "ocr_status_counts": dict(sorted(status_counts.items())),
        "joined_image_reference_rows": len(joined_rows),
        "ocr_configuration": ocr_configuration,
        "ocr_config_sha256": ocr_config_sha256,
    }
    (PHASE2_OUTPUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    checkpoint = f"""# Phase 2 OCR Checkpoint Summary

## What Was Produced

Phase 2 verified Phase 1 image paths and hashes, then used the local Windows OCR engine. Reuse requires an exact image SHA-256 and OCR-configuration SHA-256 match.

## Key Counts

- Phase 1 image references: {len(image_refs)}
- Unique local image paths OCR attempted or reused: {len(unique_images)}
- Unique local image content hashes: {len(unique_content_hashes)}
- OCR image rows: {len(ocr_rows)}
- Cache-reused image rows: {metadata['ocr_cache_reused_rows']}
- Joined image-reference rows: {len(joined_rows)}
- OCR status counts: {dict(status_counts)}

## Main Output Files

- `ocr_text_by_image.csv`
- `ocr_joined_image_references.csv`
- `ocr_text_by_note.csv`
- `ocr_summary_by_source.csv`
- `run_metadata.json`

## Interpretation Limits

OCR output is machine-extracted text and should be treated as evidence support, not final coding. Low-quality screenshots, navigation text, avatars, repeated page furniture, and external images may require filtering before typology analysis.
"""
    (PHASE2_OUTPUT / "PHASE2_CHECKPOINT_SUMMARY.md").write_text(checkpoint, encoding="utf-8")

    zip_base = PHASE2_OUTPUT.parent / "phase2_image_ocr_outputs"
    zip_path = Path(str(zip_base) + ".zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", PHASE2_OUTPUT)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
