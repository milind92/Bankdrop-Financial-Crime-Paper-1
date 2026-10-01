"""Create a blinded OCR-quality sample and score checked human transcripts.

All image paths, review sheets, transcripts, and record-level results remain
controlled. The 50-image default is a stratified probability sample of unique
referenced image content, with a fixed seed and known inclusion probabilities.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
SHA_RE = re.compile(r"[0-9a-f]{64}\Z")
SEED = 20261001
SAMPLE_FIELDS = [
    "sample_number", "image_relative_path", "image_sha256",
    "source_stratum", "population_stratum_n", "selected_stratum_n",
    "ocr_status", "transcript_relative_path", "transcriber",
    "transcriber_blind_to_ocr", "checker", "checker_blind_to_ocr",
    "transcript_check_status", "transcript_resolution_reason",
    "image_text_legible", "ocr_extraction_adequate",
    "transcription_scope", "review_reason", "review_status",
]
IDENTITY_FIELDS = SAMPLE_FIELDS[:7]
PRE_UNBLIND_FIELDS = IDENTITY_FIELDS + [
    "transcript_relative_path", "transcriber", "transcriber_blind_to_ocr",
    "checker", "checker_blind_to_ocr", "transcript_check_status",
    "transcript_resolution_reason", "image_text_legible",
    "transcription_scope", "review_reason",
]
PER_IMAGE_FIELDS = [
    "sample_number", "image_relative_path", "image_sha256", "source_stratum",
    "design_weight", "image_text_legible", "ocr_extraction_adequate",
    "gold_characters", "gold_words", "character_edits", "word_edits",
    "character_error_rate", "word_error_rate",
]


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_csv(path: Path, fields: list[str] | None = None) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if fields is not None and reader.fieldnames != fields:
            raise ValueError(f"Unexpected columns in {path.name}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def outside_public_and_vault(path: Path, vault: Path) -> Path:
    candidate = path.resolve()
    public = ROOT.resolve()
    source = vault.resolve()
    if candidate == public or public in candidate.parents:
        raise ValueError("OCR review and outputs must remain outside the public repository")
    if candidate == source or source in candidate.parents:
        raise ValueError("OCR review and outputs must remain outside the source vault")
    return candidate


def image_path(vault: Path, relative: str) -> Path:
    canonical = unicodedata.normalize("NFC", relative).replace("\\", "/")
    if not canonical or canonical.startswith("/") or re.match(r"^[A-Za-z]:", canonical):
        raise ValueError("Image path is not vault-relative")
    parts = PurePosixPath(canonical).parts
    if ".." in parts:
        raise ValueError("Image path escapes vault")
    target = vault.joinpath(*parts).resolve()
    if vault.resolve() not in target.parents:
        raise ValueError("Image path escapes vault")
    return target


def canonical_identity(rows: list[dict[str, str]]) -> str:
    selected = [{key: row[key] for key in IDENTITY_FIELDS} for row in rows]
    encoded = json.dumps(selected, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text_sha(encoded)


def pre_unblind_identity(rows: list[dict[str, str]]) -> str:
    checked = [{key: row[key] for key in PRE_UNBLIND_FIELDS} for row in rows]
    encoded = json.dumps(checked, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text_sha(encoded)


def image_population(ocr_csv: Path, joined_csv: Path) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]], set[str]]:
    sources_by_hash: dict[str, set[str]] = defaultdict(set)
    for row in read_csv(joined_csv):
        if row.get("image_resolution_status") == "resolved":
            digest = row.get("image_sha256", "").lower()
            if not SHA_RE.fullmatch(digest):
                raise ValueError("Joined image has invalid content hash")
            sources_by_hash[digest].add(row.get("source", "").strip() or "(source missing)")

    by_hash: dict[str, dict[str, str]] = {}
    configs = set()
    for row in read_csv(ocr_csv):
        digest = row.get("image_sha256", "").lower()
        config = row.get("ocr_config_sha256", "").lower()
        if not SHA_RE.fullmatch(digest) or not SHA_RE.fullmatch(config):
            raise ValueError("OCR image or configuration hash is invalid")
        expected_key = text_sha(f"{digest}:{config}")
        if row.get("ocr_cache_key", "").lower() != expected_key:
            raise ValueError("OCR cache key does not match image and configuration")
        if row.get("ocr_status") not in {"ok", "empty", "error"}:
            raise ValueError("OCR status is missing or invalid")
        if digest not in sources_by_hash:
            raise ValueError("OCR image has no resolved Phase 2 source linkage")
        configs.add(config)
        old = by_hash.get(digest)
        if old is not None:
            if (old.get("ocr_text") != row.get("ocr_text") or old.get("ocr_status") != row.get("ocr_status")
                    or old.get("ocr_config_sha256", "").lower() != config):
                raise ValueError("Identical image content has conflicting OCR results")
            if row["image_relative_path"] < old["image_relative_path"]:
                by_hash[digest] = row
        else:
            by_hash[digest] = row
    if len(configs) != 1:
        raise ValueError("OCR-quality population has more than one OCR configuration")
    strata: dict[str, list[dict[str, str]]] = defaultdict(list)
    multi_source = set()
    for digest, row in by_hash.items():
        if len(sources_by_hash[digest]) > 1:
            multi_source.add(digest)
        stratum = sorted(sources_by_hash[digest])[0]
        strata[stratum].append(row)
    for rows in strata.values():
        rows.sort(key=lambda row: row["image_sha256"])
    return by_hash, dict(strata), multi_source


def allocation(strata: dict[str, list[dict[str, str]]], size: int,
               minimum: int) -> dict[str, int]:
    if size <= 0 or size > sum(len(rows) for rows in strata.values()):
        raise ValueError("Sample size exceeds the OCR image population")
    chosen = {source: min(minimum, len(rows)) for source, rows in sorted(strata.items())}
    if sum(chosen.values()) > size:
        raise ValueError("Sample size is smaller than the minimum stratum allocation")
    remaining = size - sum(chosen.values())
    while remaining:
        capacity = {source: len(strata[source]) - chosen[source] for source in chosen}
        total = sum(capacity.values())
        if not total:
            raise ValueError("No capacity remains for the requested sample")
        quota = {source: remaining * available / total for source, available in capacity.items()}
        floors = {source: min(capacity[source], int(value)) for source, value in quota.items()}
        used = sum(floors.values())
        for source, amount in floors.items():
            chosen[source] += amount
        remaining -= used
        if remaining:
            order = sorted(chosen, key=lambda source: (-(quota[source] - int(quota[source])), source))
            for source in order:
                if remaining and chosen[source] < len(strata[source]):
                    chosen[source] += 1
                    remaining -= 1
    return chosen


def prepare(vault: Path, ocr_csv: Path, joined_csv: Path, review_dir: Path,
            size: int = 50, minimum: int = 2, seed: int = SEED) -> dict[str, object]:
    review_dir = outside_public_and_vault(review_dir, vault)
    if review_dir.exists() and any(review_dir.iterdir()):
        raise ValueError("OCR review directory is not empty; human work will not be overwritten")
    by_hash, strata, multi_source = image_population(ocr_csv, joined_csv)
    for digest, row in by_hash.items():
        path = image_path(vault, row["image_relative_path"])
        if not path.is_file() or file_sha(path) != digest:
            raise ValueError("OCR sampling-frame image hash no longer matches the vault")
    selected_n = allocation(strata, size, minimum)
    rng = random.Random(seed)
    selected = []
    for source in sorted(strata):
        for row in rng.sample(strata[source], selected_n[source]):
            path = image_path(vault, row["image_relative_path"])
            if not path.is_file() or file_sha(path) != row["image_sha256"].lower():
                raise ValueError("Sampled image hash no longer matches the vault")
            selected.append((source, row))
    sample_rows = []
    for number, (source, row) in enumerate(sorted(selected, key=lambda item: (item[0], item[1]["image_sha256"])), 1):
        record = {field: "" for field in SAMPLE_FIELDS}
        record.update({
            "sample_number": str(number),
            "image_relative_path": row["image_relative_path"],
            "image_sha256": row["image_sha256"].lower(),
            "source_stratum": source,
            "population_stratum_n": str(len(strata[source])),
            "selected_stratum_n": str(selected_n[source]),
            "ocr_status": row["ocr_status"],
            "review_status": "pending",
        })
        sample_rows.append(record)
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "transcripts").mkdir()
    write_csv(review_dir / "ocr_quality_sample.csv", sample_rows, SAMPLE_FIELDS)
    manifest = {
        "schema_version": 1,
        "status": "blinded_review_pending",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed,
        "population_unique_image_hashes": len(by_hash),
        "population_source_strata": len(strata),
        "multi_source_content_hashes_assigned_to_first_sorted_source": len(multi_source),
        "sample_size": size,
        "minimum_per_source_if_available": minimum,
        "stratum_population_sizes": {source: len(rows) for source, rows in sorted(strata.items())},
        "stratum_sample_sizes": selected_n,
        "ocr_csv_sha256": file_sha(ocr_csv),
        "joined_csv_sha256": file_sha(joined_csv),
        "sample_identity_sha256": canonical_identity(sample_rows),
        "design": "fixed allocation by source followed by simple random sampling without replacement within source",
    }
    (review_dir / "sample_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    materialize_images(vault, review_dir)
    return manifest


def materialize_images(vault: Path, review_dir: Path) -> dict[str, object]:
    """Copy only selected screenshots into a blinded controlled review pack."""
    review_dir = outside_public_and_vault(review_dir, vault)
    manifest = json.loads((review_dir / "sample_manifest.json").read_text(encoding="utf-8"))
    rows = read_csv(review_dir / "ocr_quality_sample.csv", SAMPLE_FIELDS)
    if canonical_identity(rows) != manifest.get("sample_identity_sha256"):
        raise ValueError("OCR sample identity changed before image materialisation")
    images_dir = review_dir / "images"
    if images_dir.is_symlink() or (images_dir.exists() and review_dir not in images_dir.resolve().parents):
        raise ValueError("Blinded image directory must remain inside the controlled review directory")
    images_dir.mkdir(exist_ok=True)
    copies = []
    for row in rows:
        source = image_path(vault, row["image_relative_path"])
        digest = row["image_sha256"]
        if not source.is_file() or file_sha(source) != digest:
            raise ValueError("Sampled source image hash changed before review-pack creation")
        name = f"sample_{int(row['sample_number']):03d}.png"
        destination = images_dir / name
        if destination.is_symlink():
            raise ValueError(f"Symlinked review image is unsafe: {name}")
        if destination.exists():
            if file_sha(destination) != digest:
                raise ValueError(f"Review image copy changed: {name}")
        else:
            shutil.copyfile(source, destination)
            if file_sha(destination) != digest:
                raise ValueError(f"Review image copy failed hash check: {name}")
        copies.append({"sample_number": row["sample_number"], "review_image": f"images/{name}", "image_sha256": digest})
    result = {
        "sample_identity_sha256": manifest["sample_identity_sha256"],
        "review_image_count": len(copies),
        "copies": copies,
        "status": "blinded_screenshot_copies_ready",
    }
    (review_dir / "review_images_manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def edit_distance(reference: list[str] | str, hypothesis: list[str] | str) -> int:
    if len(reference) < len(hypothesis):
        reference, hypothesis = hypothesis, reference
    previous = list(range(len(hypothesis) + 1))
    for i, value in enumerate(reference, 1):
        current = [i]
        for j, other in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (value != other)))
        previous = current
    return previous[-1]


def normalise_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold()
    return re.sub(r"\s+", " ", value).strip()


def transcript_path(review_dir: Path, relative: str) -> Path:
    path = (review_dir / relative).resolve()
    transcript_dir = review_dir / "transcripts"
    if transcript_dir.is_symlink():
        raise ValueError("Human transcript directory must not be a symlink")
    transcript_root = transcript_dir.resolve()
    if review_dir not in transcript_root.parents:
        raise ValueError("Human transcript directory escapes controlled review storage")
    if transcript_root not in path.parents or path.suffix.casefold() != ".txt":
        raise ValueError("Human transcript must be a .txt file within the review transcripts directory")
    return path


def checked_transcripts(review_dir: Path, rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Validate human-only review fields and hash each checked full transcript."""
    transcripts = {}
    for row in rows:
        number = row["sample_number"]
        transcriber = row["transcriber"].strip()
        checker = row["checker"].strip()
        if not transcriber or not checker or transcriber.casefold() == checker.casefold():
            raise ValueError(f"Two distinct human reviewers are required for sample {number}")
        if row["transcriber_blind_to_ocr"] != "yes" or row["checker_blind_to_ocr"] != "yes":
            raise ValueError(f"Blinded transcription and checking are required for sample {number}")
        status = row["transcript_check_status"]
        if status not in {"agreed", "corrected", "not_applicable"}:
            raise ValueError(f"Transcript-check status is invalid for sample {number}")
        if status == "corrected" and not row["transcript_resolution_reason"].strip():
            raise ValueError(f"Transcript correction needs a reason for sample {number}")
        legibility = row["image_text_legible"]
        if legibility not in {"full", "partial", "none", "no_text", "unassessable"}:
            raise ValueError(f"Legibility decision is invalid for sample {number}")
        relative = row["transcript_relative_path"].strip()
        if legibility == "full":
            if status == "not_applicable" or row["transcription_scope"] != "all_visible_text" or not relative:
                raise ValueError(f"Full image needs a checked all-text transcript for sample {number}")
            path = transcript_path(review_dir, relative)
            if not normalise_text(path.read_text(encoding="utf-8-sig")):
                raise ValueError(f"Gold transcript is empty for sample {number}")
            transcripts[number] = {"relative_path": relative, "sha256": file_sha(path)}
        else:
            if status != "not_applicable" or relative or row["transcription_scope"].strip():
                raise ValueError(f"Non-full image cannot have a full-image transcript at sample {number}")
            if not row["review_reason"].strip():
                raise ValueError(f"Non-full legibility needs a reason for sample {number}")
    return transcripts


def lock_transcripts(vault: Path, ocr_csv: Path, joined_csv: Path,
                     review_dir: Path) -> dict[str, object]:
    """Record a checked transcript checkpoint before any OCR is revealed."""
    review_dir = outside_public_and_vault(review_dir, vault)
    lock_path = review_dir / "transcript_lock_manifest.json"
    if lock_path.exists():
        raise ValueError("Transcript lock already exists; it cannot be overwritten")
    manifest = json.loads((review_dir / "sample_manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or manifest.get("ocr_csv_sha256") != file_sha(ocr_csv)
            or manifest.get("joined_csv_sha256") != file_sha(joined_csv)):
        raise ValueError("OCR review does not match the frozen OCR inputs")
    rows = read_csv(review_dir / "ocr_quality_sample.csv", SAMPLE_FIELDS)
    if len(rows) != manifest.get("sample_size") or canonical_identity(rows) != manifest.get("sample_identity_sha256"):
        raise ValueError("OCR sample identity changed before transcript lock")
    review_images = json.loads((review_dir / "review_images_manifest.json").read_text(encoding="utf-8"))
    if (review_images.get("sample_identity_sha256") != manifest.get("sample_identity_sha256")
            or review_images.get("review_image_count") != len(rows)):
        raise ValueError("Blinded review images do not match the frozen sample")
    for row in rows:
        number = row["sample_number"]
        digest = row["image_sha256"]
        copied = review_dir / "images" / f"sample_{int(number):03d}.png"
        original = image_path(vault, row["image_relative_path"])
        if copied.is_symlink() or not copied.is_file() or file_sha(copied) != digest:
            raise ValueError(f"Blinded review image changed for sample {number}")
        if not original.is_file() or file_sha(original) != digest:
            raise ValueError(f"Source image changed for sample {number}")
        if row["ocr_extraction_adequate"].strip() or row["review_status"] != "pending":
            raise ValueError(f"OCR adequacy must remain blank before transcript lock at sample {number}")
    transcripts = checked_transcripts(review_dir, rows)
    locked = {
        "schema_version": 1,
        "status": "checked_human_transcripts_locked_before_ocr_review",
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_identity_sha256": manifest["sample_identity_sha256"],
        "pre_unblind_review_sha256": pre_unblind_identity(rows),
        "pre_unblind_sheet_file_sha256": file_sha(review_dir / "ocr_quality_sample.csv"),
        "transcript_file_sha256_by_sample": transcripts,
        "reviewed_images": len(rows),
        "full_transcripts": len(transcripts),
    }
    with lock_path.open("x", encoding="utf-8") as handle:
        json.dump(locked, handle, indent=2)
        handle.write("\n")
    return locked


def score(vault: Path, ocr_csv: Path, joined_csv: Path,
          review_dir: Path, output_dir: Path) -> dict[str, object]:
    review_dir = outside_public_and_vault(review_dir, vault)
    output_dir = outside_public_and_vault(output_dir, vault)
    if review_dir == output_dir or review_dir in output_dir.parents or output_dir in review_dir.parents:
        raise ValueError("OCR review and score output directories must be separate")
    manifest = json.loads((review_dir / "sample_manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or manifest.get("ocr_csv_sha256") != file_sha(ocr_csv)
            or manifest.get("joined_csv_sha256") != file_sha(joined_csv)):
        raise ValueError("OCR review does not match the frozen OCR inputs")
    rows = read_csv(review_dir / "ocr_quality_sample.csv", SAMPLE_FIELDS)
    if len(rows) != manifest.get("sample_size") or canonical_identity(rows) != manifest.get("sample_identity_sha256"):
        raise ValueError("OCR sample identity or allocation changed after preparation")
    review_images = json.loads((review_dir / "review_images_manifest.json").read_text(encoding="utf-8"))
    if (review_images.get("sample_identity_sha256") != manifest.get("sample_identity_sha256")
            or review_images.get("review_image_count") != len(rows)):
        raise ValueError("Blinded review images do not match the frozen sample")
    for row in rows:
        copied = review_dir / "images" / f"sample_{int(row['sample_number']):03d}.png"
        if copied.is_symlink() or not copied.is_file() or file_sha(copied) != row["image_sha256"]:
            raise ValueError(f"Blinded review image changed for sample {row['sample_number']}")
    lock_path = review_dir / "transcript_lock_manifest.json"
    if not lock_path.is_file():
        raise ValueError("Checked transcript lock is missing; score cannot proceed")
    locked = json.loads(lock_path.read_text(encoding="utf-8"))
    transcripts = checked_transcripts(review_dir, rows)
    if (locked.get("schema_version") != 1
            or locked.get("sample_identity_sha256") != manifest.get("sample_identity_sha256")
            or locked.get("pre_unblind_review_sha256") != pre_unblind_identity(rows)
            or locked.get("transcript_file_sha256_by_sample") != transcripts):
        raise ValueError("Pre-unblinding review or locked transcript changed")
    ocr_by_hash, _, _ = image_population(ocr_csv, joined_csv)
    per_image = []
    status_counts: Counter[str] = Counter()
    legibility_weights: dict[str, float] = defaultdict(float)
    adequacy_weights: dict[str, float] = defaultdict(float)
    total_weight = 0.0
    weighted_char_edits = weighted_gold_chars = 0.0
    weighted_word_edits = weighted_gold_words = 0.0
    full_by_stratum: Counter[str] = Counter()
    for row in rows:
        number = row["sample_number"]
        digest = row["image_sha256"]
        if digest not in ocr_by_hash or ocr_by_hash[digest]["ocr_status"] != row["ocr_status"]:
            raise ValueError(f"OCR cache row changed for sample {number}")
        path = image_path(vault, row["image_relative_path"])
        if not path.is_file() or file_sha(path) != digest:
            raise ValueError(f"Image hash changed for sample {number}")
        if row["review_status"] != "complete":
            raise ValueError(f"Human OCR review incomplete for sample {number}")
        transcriber = row["transcriber"].strip()
        checker = row["checker"].strip()
        if not transcriber or not checker or transcriber.casefold() == checker.casefold():
            raise ValueError(f"Two distinct human reviewers are required for sample {number}")
        if row["transcriber_blind_to_ocr"] != "yes" or row["checker_blind_to_ocr"] != "yes":
            raise ValueError(f"Blinded transcription and checking are required for sample {number}")
        if row["transcript_check_status"] not in {"agreed", "corrected", "not_applicable"}:
            raise ValueError(f"Transcript-check status is invalid for sample {number}")
        if row["transcript_check_status"] == "corrected" and not row["transcript_resolution_reason"].strip():
            raise ValueError(f"Transcript correction needs a reason for sample {number}")
        legibility = row["image_text_legible"]
        adequate = row["ocr_extraction_adequate"]
        if legibility not in {"full", "partial", "none", "no_text", "unassessable"} or adequate not in {"yes", "no", "uncertain"}:
            raise ValueError(f"Legibility or adequacy decision is invalid for sample {number}")
        if legibility != "full" and not row["review_reason"].strip():
            raise ValueError(f"Non-full legibility needs a reason for sample {number}")
        if legibility == "full" and row["transcript_check_status"] == "not_applicable":
            raise ValueError(f"Full-text transcript needs checking for sample {number}")
        if legibility != "full" and row["transcript_check_status"] != "not_applicable":
            raise ValueError(f"No full transcript should be marked checked for sample {number}")
        weight = int(row["population_stratum_n"]) / int(row["selected_stratum_n"])
        total_weight += weight
        adequacy_weights[adequate] += weight
        status_counts[legibility] += 1
        legibility_weights[legibility] += weight
        result: dict[str, object] = {
            "sample_number": number,
            "image_relative_path": row["image_relative_path"],
            "image_sha256": digest,
            "source_stratum": row["source_stratum"],
            "design_weight": round(weight, 9),
            "image_text_legible": legibility,
            "ocr_extraction_adequate": adequate,
            "gold_characters": "", "gold_words": "", "character_edits": "",
            "word_edits": "", "character_error_rate": "", "word_error_rate": "",
        }
        if legibility == "full":
            if row["transcription_scope"] != "all_visible_text":
                raise ValueError(f"Full transcript must cover all visible text for sample {number}")
            relative_transcript = row["transcript_relative_path"].strip()
            if not relative_transcript:
                raise ValueError(f"Gold transcript is missing for sample {number}")
            gold_path = transcript_path(review_dir, relative_transcript)
            gold = normalise_text(gold_path.read_text(encoding="utf-8-sig"))
            machine = normalise_text(ocr_by_hash[digest].get("ocr_text", ""))
            if not gold:
                raise ValueError(f"Gold transcript is empty for sample {number}")
            char_edits = edit_distance(gold, machine)
            word_edits = edit_distance(gold.split(), machine.split())
            full_by_stratum[row["source_stratum"]] += 1
            weighted_char_edits += weight * char_edits
            weighted_gold_chars += weight * len(gold)
            weighted_word_edits += weight * word_edits
            weighted_gold_words += weight * len(gold.split())
            result.update({
                "gold_characters": len(gold), "gold_words": len(gold.split()),
                "character_edits": char_edits, "word_edits": word_edits,
                "character_error_rate": round(char_edits / len(gold), 6),
                "word_error_rate": round(word_edits / len(gold.split()), 6),
            })
        elif row["transcript_relative_path"].strip() or row["transcription_scope"].strip():
            raise ValueError(f"Partial/unassessable image must not supply a full-image transcript at sample {number}")
        per_image.append(result)
    expected_population = int(manifest["population_unique_image_hashes"])
    if abs(total_weight - expected_population) > 1e-6:
        raise ValueError("Sample design weights do not sum to the OCR image population")
    report = {
        "status": "human_review_complete_descriptive_quality_diagnostic",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_size": len(rows),
        "population_unique_image_hashes": expected_population,
        "source_strata": manifest["population_source_strata"],
        "image_legibility_counts": dict(sorted(status_counts.items())),
        "image_legibility_weighted_percent": {
            answer: round(100 * legibility_weights[answer] / total_weight, 3)
            for answer in ("full", "partial", "none", "no_text", "unassessable")
        },
        "full_legibility_sources_with_scored_transcripts": len(full_by_stratum),
        "ocr_extraction_adequacy_weighted_percent": {
            answer: round(100 * adequacy_weights[answer] / total_weight, 3)
            for answer in ("yes", "no", "uncertain")
        },
        "character_error_rate_full_legible_weighted": round(weighted_char_edits / weighted_gold_chars, 6) if weighted_gold_chars else None,
        "word_error_rate_full_legible_weighted": round(weighted_word_edits / weighted_gold_words, 6) if weighted_gold_words else None,
        "normalisation": "Unicode NFC, casefold, and collapsed whitespace; punctuation retained",
        "accuracy_boundary": "CER/WER describe the fully legible reviewed subset; partial, unreadable, and text-free images are reported separately. They are not proof that study-relevant content was fully recovered.",
        "sample_identity_sha256": manifest["sample_identity_sha256"],
        "transcript_lock_manifest_sha256": file_sha(lock_path),
        "review_sheet_sha256": file_sha(review_dir / "ocr_quality_sample.csv"),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "per_image_ocr_quality_controlled.csv", per_image, PER_IMAGE_FIELDS)
    (output_dir / "ocr_quality_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    sub = top.add_subparsers(dest="command", required=True)
    for name in ("prepare", "lock", "score", "materialize"):
        command = sub.add_parser(name)
        command.add_argument("--vault", type=Path, required=True)
        command.add_argument("--review-dir", type=Path, required=True)
        if name != "materialize":
            command.add_argument("--ocr-by-image", type=Path, required=True)
            command.add_argument("--joined-references", type=Path, required=True)
        if name == "prepare":
            command.add_argument("--sample-size", type=int, default=50)
            command.add_argument("--min-per-source", type=int, default=2)
        elif name == "score":
            command.add_argument("--output-dir", type=Path, required=True)
    return top


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.vault, args.ocr_by_image, args.joined_references,
                             args.review_dir, args.sample_size, args.min_per_source)
        elif args.command == "materialize":
            result = materialize_images(args.vault, args.review_dir)
        elif args.command == "lock":
            result = lock_transcripts(args.vault, args.ocr_by_image,
                                      args.joined_references, args.review_dir)
        else:
            result = score(args.vault, args.ocr_by_image, args.joined_references,
                           args.review_dir, args.output_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
