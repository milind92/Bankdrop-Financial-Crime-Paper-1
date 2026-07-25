"""
Phase 1 Markdown baseline extraction for the Bank Drop Project.

Reads an extracted Obsidian-style vault and writes deterministic CSV/JSON
outputs for corpus indexing, keyword/entity counts, price mentions, and image
references. The script uses only Python standard library modules.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import unquote, urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
DEFAULT_VAULT = Path(os.environ.get("BANK_DROP_VAULT", WORKSPACE / "work" / "bank_drop_project" / "DW Project"))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
DEFAULT_OUTPUT = OUTPUTS / "phase1_markdown_baseline"
CONFIG_PATH = Path(__file__).with_name("config.json")


@dataclass(frozen=True)
class NoteRecord:
    note_id: str
    legacy_note_id: str
    path: Path
    relative_path: str
    legacy_relative_path: str
    source: str
    collection_date: str
    text: str
    word_count: int
    char_count: int
    image_refs: list[str]


@dataclass(frozen=True)
class ImageResolution:
    normalized_ref: str
    status: str
    method: str
    relative_path: str
    sha256: str
    candidate_count: int


def read_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_relative_path(path: Path, root: Path) -> str:
    """Return a stable, Unicode-normalised POSIX path below ``root``."""
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return unicodedata.normalize("NFC", relative)


def note_id_from_relative_path(relative_path: str) -> str:
    normalized = unicodedata.normalize("NFC", relative_path.replace("\\", "/"))
    canonical = PurePosixPath(normalized).as_posix()
    return sha256_text(canonical)[:16]


def build_png_index(vault: Path) -> dict[str, list[Path]]:
    """Index PNG files by case-folded basename without losing path identity."""
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
        paths.sort(key=lambda path: canonical_relative_path(path, vault))
    return dict(indexed)


def normalise_image_reference(image_ref: str) -> tuple[str, str]:
    """Normalise a local image reference and flag external or unsafe forms."""
    decoded = unicodedata.normalize("NFC", unquote(image_ref.strip().strip("<>")))
    decoded = decoded.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", decoded) or decoded.startswith(("/", "//")):
        return decoded, "unsafe"
    parsed = urlsplit(decoded)
    if parsed.scheme or parsed.netloc:
        return decoded, "external"
    return parsed.path.strip(), ""


def _safe_resolved_candidate(candidate: Path, vault: Path) -> Path | None:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(vault.resolve())
    except ValueError:
        return None
    return resolved


def resolve_image_reference(
    image_ref: str,
    note_path: Path,
    vault: Path,
    png_index: dict[str, list[Path]] | None = None,
) -> ImageResolution:
    """Resolve a PNG reference safely and report ambiguity instead of guessing."""
    normalized, preliminary_status = normalise_image_reference(image_ref)
    if preliminary_status:
        return ImageResolution(normalized, preliminary_status, "", "", "", 0)
    if not normalized:
        return ImageResolution(normalized, "missing", "", "", "", 0)

    posix_ref = PurePosixPath(normalized)
    image_name = posix_ref.name
    if not image_name or Path(image_name).suffix.casefold() != ".png":
        return ImageResolution(normalized, "missing", "", "", "", 0)

    index = png_index if png_index is not None else build_png_index(vault)
    if len(posix_ref.parts) == 1:
        candidates = index.get(image_name.casefold(), [])
        if len(candidates) > 1:
            return ImageResolution(normalized, "ambiguous", "unique_basename", "", "", len(candidates))
        if not candidates:
            return ImageResolution(normalized, "missing", "unique_basename", "", "", 0)
        resolved = candidates[0]
        return ImageResolution(
            normalized,
            "resolved",
            "unique_basename",
            canonical_relative_path(resolved, vault),
            file_sha256(resolved),
            1,
        )

    native_parts = list(posix_ref.parts)
    candidate_specs = [
        ("note_relative", note_path.parent.joinpath(*native_parts)),
        ("vault_relative", vault.joinpath(*native_parts)),
    ]
    matches: dict[Path, set[str]] = defaultdict(set)
    safe_candidate_seen = False
    for method, candidate in candidate_specs:
        safe = _safe_resolved_candidate(candidate, vault)
        if safe is None:
            continue
        safe_candidate_seen = True
        if safe.is_file() and safe.suffix.casefold() == ".png":
            matches[safe].add(method)
    if len(matches) > 1:
        return ImageResolution(normalized, "ambiguous", "explicit_path", "", "", len(matches))
    if not matches:
        status = "missing" if safe_candidate_seen else "unsafe"
        return ImageResolution(normalized, status, "explicit_path", "", "", 0)

    resolved, methods = next(iter(matches.items()))
    return ImageResolution(
        normalized,
        "resolved",
        "+".join(sorted(methods)),
        canonical_relative_path(resolved, vault),
        file_sha256(resolved),
        1,
    )


def extract_date(name: str, config: dict) -> str:
    for pattern in config["date_patterns"]:
        match = re.search(pattern, name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
    return ""


def infer_source(relative_path: str, config: dict) -> str:
    parts = list(Path(relative_path).parts)
    root_parts = config["source_root_parts"]
    for index in range(0, max(0, len(parts) - len(root_parts)) + 1):
        if parts[index : index + len(root_parts)] == root_parts:
            source_index = index + len(root_parts)
            if source_index < len(parts) - 1:
                return re.sub(r"\s+", " ", parts[source_index]).strip()
    return ""


def extract_image_refs(text: str) -> list[str]:
    pattern = re.compile(
        r"!\[\[(.*?\.png)(?:\|.*?)?\]\]|!\[[^\]]*\]\(([^)]*\.png)\)",
        flags=re.IGNORECASE,
    )
    refs: list[str] = []
    for wiki_ref, md_ref in pattern.findall(text):
        ref = (wiki_ref or md_ref).strip()
        if ref:
            refs.append(ref)
    return refs


@lru_cache(maxsize=None)
def compile_term_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", flags=re.IGNORECASE)


def term_count(text: str, term: str) -> int:
    return len(compile_term_pattern(term).findall(text))


def compile_patterns(patterns: dict[str, str]) -> dict[str, re.Pattern[str]]:
    return {
        name: re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
        for name, pattern in patterns.items()
    }


def extract_price_mentions(record: NoteRecord) -> list[dict[str, str]]:
    """Extract currency-labelled fiat-symbol and cryptocurrency amounts."""
    rows: list[dict[str, str]] = []
    patterns = (
        (re.compile(r"(?<!\w)(?:(USD|AUD|CAD|NZD)\s*)?(\$)\s*([0-9][0-9,]*(?:\.\d{1,2})?)(?:\s*(USD|AUD|CAD|NZD))?(?!\w)", re.IGNORECASE), "dollar"),
        (re.compile(r"(?<![\w.])([0-9]+(?:\.[0-9]+)?)\s*(BTC|XMR|USDT|bitcoin|monero)\b", re.IGNORECASE), "crypto"),
    )
    for pattern, kind in patterns:
        for match in pattern.finditer(record.text):
            if kind == "dollar":
                amount_text = match.group(3)
                currency = (match.group(1) or match.group(4) or "UNSPECIFIED_DOLLAR").upper()
            else:
                amount_text = match.group(1)
                raw_currency = match.group(2).upper()
                currency = {"BITCOIN": "BTC", "MONERO": "XMR"}.get(raw_currency, raw_currency)
            amount = float(amount_text.replace(",", ""))
            if amount <= 0 or amount > 10_000_000:
                continue
            start = max(0, match.start() - 100)
            end = min(len(record.text), match.end() + 100)
            rows.append({
                "note_id": record.note_id,
                "legacy_note_id": record.legacy_note_id,
                "relative_path": record.relative_path,
                "legacy_relative_path": record.legacy_relative_path,
                "source": record.source,
                "collection_date": record.collection_date,
                "currency": currency,
                "amount": f"{amount:.8f}".rstrip("0").rstrip("."),
                "raw_mention": match.group(0),
                "context": " ".join(record.text[start:end].split()),
            })
    return rows


def iter_notes(vault: Path, config: dict) -> Iterable[NoteRecord]:
    paths = sorted(vault.rglob("*.md"), key=lambda item: canonical_relative_path(item, vault))
    for path in paths:
        relative_path = canonical_relative_path(path, vault)
        source = infer_source(relative_path, config)
        if not source:
            continue
        text = normalise_newlines(path.read_text(encoding="utf-8", errors="replace"))
        legacy_relative_path = str(path.relative_to(vault))
        yield NoteRecord(
            note_id=note_id_from_relative_path(relative_path),
            legacy_note_id=sha256_text(legacy_relative_path)[:16],
            path=path,
            relative_path=relative_path,
            legacy_relative_path=legacy_relative_path,
            source=source,
            collection_date=extract_date(path.name, config),
            text=text,
            word_count=len(re.findall(r"\b\w+\b", text)),
            char_count=len(text),
            image_refs=extract_image_refs(text),
        )


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    config = read_config()
    vault = DEFAULT_VAULT
    output = DEFAULT_OUTPUT
    output.mkdir(parents=True, exist_ok=True)

    if not vault.exists():
        raise FileNotFoundError(f"Vault path not found: {vault}")

    patterns = compile_patterns(config["keyword_patterns"])
    records = list(iter_notes(vault, config))

    corpus_rows: list[dict[str, object]] = []
    keyword_rows: list[dict[str, object]] = []
    image_rows: list[dict[str, object]] = []
    entity_rows: list[dict[str, object]] = []
    png_index = build_png_index(vault)

    price_rows: list[dict[str, str]] = []

    entity_groups = {
        "bank": config["bank_terms"],
        "country_region": config["country_region_terms"],
        "payment_rail": config["payment_rail_terms"],
    }

    for record in records:
        corpus_rows.append(
            {
                "note_id": record.note_id,
                "legacy_note_id": record.legacy_note_id,
                "relative_path": record.relative_path,
                "legacy_relative_path": record.legacy_relative_path,
                "source": record.source,
                "collection_date": record.collection_date,
                "word_count": record.word_count,
                "char_count": record.char_count,
                "image_ref_count": len(record.image_refs),
                "sha256_text": sha256_text(record.text),
            }
        )

        for keyword, pattern in patterns.items():
            count = len(pattern.findall(record.text))
            keyword_rows.append(
                {
                    "note_id": record.note_id,
                    "legacy_note_id": record.legacy_note_id,
                    "relative_path": record.relative_path,
                    "legacy_relative_path": record.legacy_relative_path,
                    "source": record.source,
                    "collection_date": record.collection_date,
                    "keyword": keyword,
                    "count": count,
                    "present": 1 if count else 0,
                }
            )

        for index, image_ref in enumerate(record.image_refs, start=1):
            resolution = resolve_image_reference(image_ref, record.path, vault, png_index)
            image_name = PurePosixPath(resolution.normalized_ref).name
            image_rows.append(
                {
                    "note_id": record.note_id,
                    "legacy_note_id": record.legacy_note_id,
                    "relative_path": record.relative_path,
                    "legacy_relative_path": record.legacy_relative_path,
                    "source": record.source,
                    "collection_date": record.collection_date,
                    "image_index_in_note": index,
                    "image_ref": image_ref,
                    "image_name": image_name,
                    "image_exists_in_vault_root": 1 if resolution.status == "resolved" else 0,
                    "image_reference_normalized": resolution.normalized_ref,
                    "image_resolution_status": resolution.status,
                    "image_resolution_method": resolution.method,
                    "image_relative_path": resolution.relative_path,
                    "image_sha256": resolution.sha256,
                    "image_candidate_count": resolution.candidate_count,
                }
            )

        for entity_type, terms in entity_groups.items():
            for term in terms:
                count = term_count(record.text, term)
                if count:
                    entity_rows.append(
                        {
                            "note_id": record.note_id,
                            "legacy_note_id": record.legacy_note_id,
                            "relative_path": record.relative_path,
                            "legacy_relative_path": record.legacy_relative_path,
                            "source": record.source,
                            "collection_date": record.collection_date,
                            "entity_type": entity_type,
                            "entity": term,
                            "count": count,
                        }
                    )

        price_rows.extend(extract_price_mentions(record))

    write_csv(
        output / "corpus_index.csv",
        corpus_rows,
        [
            "note_id",
            "legacy_note_id",
            "relative_path",
            "legacy_relative_path",
            "source",
            "collection_date",
            "word_count",
            "char_count",
            "image_ref_count",
            "sha256_text",
        ],
    )
    write_csv(
        output / "keyword_counts_long.csv",
        keyword_rows,
        [
            "note_id",
            "legacy_note_id",
            "relative_path",
            "legacy_relative_path",
            "source",
            "collection_date",
            "keyword",
            "count",
            "present",
        ],
    )
    write_csv(
        output / "image_references.csv",
        image_rows,
        [
            "note_id",
            "legacy_note_id",
            "relative_path",
            "legacy_relative_path",
            "source",
            "collection_date",
            "image_index_in_note",
            "image_ref",
            "image_name",
            "image_reference_normalized",
            "image_resolution_status",
            "image_resolution_method",
            "image_relative_path",
            "image_sha256",
            "image_candidate_count",
            "image_exists_in_vault_root",
        ],
    )
    write_csv(
        output / "entity_mentions_long.csv",
        entity_rows,
        [
            "note_id",
            "legacy_note_id",
            "relative_path",
            "legacy_relative_path",
            "source",
            "collection_date",
            "entity_type",
            "entity",
            "count",
        ],
    )
    write_csv(
        output / "price_mentions.csv",
        price_rows,
        [
            "note_id",
            "legacy_note_id",
            "relative_path",
            "legacy_relative_path",
            "source",
            "collection_date",
            "currency",
            "amount",
            "raw_mention",
            "context",
        ],
    )

    source_stats: dict[str, Counter] = defaultdict(Counter)
    for record in records:
        key = record.source or "(no_source)"
        source_stats[key]["notes"] += 1
        source_stats[key]["words"] += record.word_count
        source_stats[key]["image_refs"] += len(record.image_refs)
        if record.collection_date:
            source_stats[key]["dated_notes"] += 1

    source_rows = []
    for source, counter in sorted(source_stats.items()):
        dates = sorted(
            {
                record.collection_date
                for record in records
                if (record.source or "(no_source)") == source and record.collection_date
            }
        )
        source_rows.append(
            {
                "source": source,
                "note_count": counter["notes"],
                "dated_note_count": counter["dated_notes"],
                "first_date": dates[0] if dates else "",
                "last_date": dates[-1] if dates else "",
                "word_count": counter["words"],
                "image_ref_count": counter["image_refs"],
            }
        )
    write_csv(
        output / "source_summary.csv",
        source_rows,
        [
            "source",
            "note_count",
            "dated_note_count",
            "first_date",
            "last_date",
            "word_count",
            "image_ref_count",
        ],
    )

    image_status_counts = Counter(
        str(row["image_resolution_status"]) for row in image_rows
    )
    unique_resolved_images = {
        str(row["image_relative_path"])
        for row in image_rows
        if row["image_resolution_status"] == "resolved"
    }

    run_metadata = {
        "phase": "phase1_markdown_baseline",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "vault_path": str(vault),
        "output_path": str(output),
        "note_count": len(records),
        "image_reference_count": len(image_rows),
        "price_mention_count": len(price_rows),
        "entity_mention_rows": len(entity_rows),
        "image_resolution_status_counts": dict(sorted(image_status_counts.items())),
        "unique_resolved_image_count": len(unique_resolved_images),
        "keyword_count_rows": len(keyword_rows),
        "config_path": str(CONFIG_PATH),
    }
    (output / "run_metadata.json").write_text(
        json.dumps(run_metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(run_metadata, indent=2))


if __name__ == "__main__":
    main()
