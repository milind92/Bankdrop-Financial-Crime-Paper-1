#!/usr/bin/env python3
"""Build publication-safe aggregate sensitivity and co-occurrence tables.

The script reads controlled Phase 3 record-level outputs but writes only
grouped counts and descriptive statistics. It deliberately distinguishes the
980-record full deterministic screen from an exact-combined-text-hash
sensitivity population. The latter is not asserted to be a final eligible
analytic population.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SCRIPT_VERSION = "1.0.0"
DATA_QUALITY_CODES = frozenset({"market_access_limitation"})
POPULATION_LABELS = {
    "full_screened": "All combined records evaluated by the deterministic screen",
    "exact_text_unique_sensitivity": (
        "One deterministic representative per combined-text SHA-256 value; "
        "sensitivity population only"
    ),
}
STRUCTURAL_TYPOLOGY_AML_PAIRS = frozenset(
    {
        ("bank_log_sale", "bank_log_plus_email_access"),
        ("email_access_takeover", "bank_log_plus_email_access"),
        ("jurisdiction_localisation", "domestic_account_preference"),
        ("escrow_trust_reputation", "escrow_or_exit_scam_risk"),
        ("telegram_off_platform", "telegram_sales_or_proof"),
        ("crypto_payment_or_conversion", "crypto_to_bank_cashout"),
        ("mule_recruitment", "mule_or_account_holder_recruitment"),
    }
)
SERVICE_CHAIN_STAGES = {
    "account_access": {
        "label": "Account access and takeover",
        "definition": (
            "Observed references to compromised bank access and "
            "recovery-channel control."
        ),
        "codes": ("bank_log_sale", "email_access_takeover"),
    },
    "identity_and_receiving": {
        "label": "Identity and receiving-account infrastructure",
        "definition": (
            "Observed references to identity packages, bank drops, or "
            "solicited account holders."
        ),
        "codes": ("bank_drop_sale", "fullz_identity_package", "mule_recruitment"),
    },
    "coordination_and_trust": {
        "label": "Coordination, learning, and market trust",
        "definition": (
            "Observed references to private-channel coordination, tutorials, "
            "escrow, reputation, or scam-risk discourse."
        ),
        "codes": (
            "escrow_trust_reputation",
            "telegram_off_platform",
            "tutorial_training_recruitment",
        ),
    },
    "monetisation_and_settlement": {
        "label": "Monetisation and settlement",
        "definition": (
            "Observed references to cash-out services or cryptocurrency "
            "payment and conversion."
        ),
        "codes": ("cashout_laundering_service", "crypto_payment_or_conversion"),
    },
}


class DerivedAnalysisError(ValueError):
    """Raised when controlled inputs are incomplete or inconsistent."""


def read_csv(path: Path, required: Sequence[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise DerivedAnalysisError(f"Required controlled input is missing: {path.name}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        missing = [field for field in required if field not in headers]
        if missing:
            raise DerivedAnalysisError(
                f"{path.name} is missing required column(s): {', '.join(missing)}"
            )
        return [
            {str(key): (value or "").strip() for key, value in row.items()}
            for row in reader
        ]


def write_csv(path: Path, rows: Sequence[Mapping[str, object]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ratio(numerator: int, denominator: int, digits: int = 6) -> float:
    return round(numerator / denominator, digits) if denominator else 0.0


def percent(numerator: int, denominator: int) -> float:
    return round(100 * numerator / denominator, 3) if denominator else 0.0


def normalize_source(value: str) -> str:
    return value.strip() or "(no_source)"


def validate_unique_note_ids(corpus: Sequence[Mapping[str, str]]) -> None:
    note_ids = [row["note_id"] for row in corpus]
    if not note_ids or any(not value for value in note_ids):
        raise DerivedAnalysisError("Corpus contains no records or a blank note_id")
    duplicates = [note_id for note_id, count in Counter(note_ids).items() if count > 1]
    if duplicates:
        raise DerivedAnalysisError(
            f"Corpus note_id is not unique ({len(duplicates)} duplicate value(s))"
        )


def build_populations(
    corpus: Sequence[Mapping[str, str]],
) -> tuple[dict[str, set[str]], dict[str, str], dict[str, str], dict[str, object]]:
    validate_unique_note_ids(corpus)
    source_by_note = {
        row["note_id"]: normalize_source(row["source"])
        for row in corpus
    }
    hash_by_note: dict[str, str] = {}
    note_ids_by_hash: dict[str, list[str]] = defaultdict(list)
    for row in corpus:
        note_id = row["note_id"]
        text_hash = row["combined_text_sha256"] or f"missing:{note_id}"
        hash_by_note[note_id] = text_hash
        note_ids_by_hash[text_hash].append(note_id)

    representatives = {
        sorted(note_ids, key=lambda value: (source_by_note[value], value))[0]
        for note_ids in note_ids_by_hash.values()
    }
    populations = {
        "full_screened": set(source_by_note),
        "exact_text_unique_sensitivity": representatives,
    }
    hash_counts = Counter(hash_by_note.values())
    metadata = {
        "screened_records_n": len(corpus),
        "unique_combined_text_hashes_n": len(hash_counts),
        "exact_duplicate_groups_n": sum(count > 1 for count in hash_counts.values()),
        "records_in_exact_duplicate_groups_n": sum(
            count for count in hash_counts.values() if count > 1
        ),
        "exact_duplicate_excess_records_n": sum(
            count - 1 for count in hash_counts.values() if count > 1
        ),
        "maximum_exact_duplicate_group_size_n": max(hash_counts.values(), default=0),
        "zero_combined_word_records_n": sum(
            int(row["combined_word_count"] or "0") == 0 for row in corpus
        ),
    }
    return populations, source_by_note, hash_by_note, metadata


def build_presence(
    rows: Sequence[Mapping[str, str]],
    *,
    code_field: str,
    label_field: str = "label",
    excluded_codes: Iterable[str] = (),
) -> tuple[dict[str, set[str]], dict[str, str]]:
    excluded = set(excluded_codes)
    present: dict[str, set[str]] = defaultdict(set)
    labels: dict[str, str] = {}
    for row in rows:
        code = row[code_field]
        if code in excluded:
            continue
        labels[code] = row[label_field]
        if row["present"] == "1":
            present[code].add(row["note_id"])
    return dict(present), labels


def population_presence(
    presence: Mapping[str, set[str]], population: set[str]
) -> dict[str, set[str]]:
    return {code: note_ids & population for code, note_ids in presence.items()}


def validate_duplicate_code_consistency(
    presence: Mapping[str, set[str]],
    population: set[str],
    hash_by_note: Mapping[str, str],
    label: str,
) -> None:
    """Ensure canonical duplicate representatives do not change code status."""

    for code, positive_note_ids in presence.items():
        statuses_by_hash: dict[str, set[bool]] = defaultdict(set)
        for note_id in population:
            statuses_by_hash[hash_by_note[note_id]].add(note_id in positive_note_ids)
        conflicting = sum(len(statuses) > 1 for statuses in statuses_by_hash.values())
        if conflicting:
            raise DerivedAnalysisError(
                f"{label} {code} has inconsistent deterministic status within "
                f"{conflicting} exact-text duplicate group(s)"
            )


def ranked_codes(presence: Mapping[str, set[str]]) -> dict[str, int]:
    ordered = sorted(presence, key=lambda code: (-len(presence[code]), code))
    return {code: rank for rank, code in enumerate(ordered, 1)}


def build_duplicate_sensitivity(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
) -> list[dict[str, object]]:
    full = population_presence(typology_presence, populations["full_screened"])
    unique = population_presence(
        typology_presence, populations["exact_text_unique_sensitivity"]
    )
    full_ranks = ranked_codes(full)
    unique_ranks = ranked_codes(unique)
    rows: list[dict[str, object]] = []
    for code in sorted(typology_presence):
        full_n = len(full[code])
        unique_n = len(unique[code])
        full_percent = percent(full_n, len(populations["full_screened"]))
        unique_percent = percent(
            unique_n, len(populations["exact_text_unique_sensitivity"])
        )
        rows.append(
            {
                "code": code,
                "label": typology_labels[code],
                "full_screened_denominator_n": len(populations["full_screened"]),
                "full_screened_present_n": full_n,
                "full_screened_percent": full_percent,
                "full_screened_rank": full_ranks[code],
                "exact_text_unique_denominator_n": len(
                    populations["exact_text_unique_sensitivity"]
                ),
                "exact_text_unique_present_n": unique_n,
                "exact_text_unique_percent": unique_percent,
                "exact_duplicate_excess_positive_records_n": full_n - unique_n,
                "positive_count_reduction_percent": percent(full_n - unique_n, full_n),
                "percentage_point_difference": round(
                    unique_percent - full_percent, 3
                ),
                "exact_text_unique_rank": unique_ranks[code],
                "rank_change": unique_ranks[code] - full_ranks[code],
            }
        )
    return sorted(rows, key=lambda row: (int(row["full_screened_rank"]), str(row["code"])))


def build_cooccurrence(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        selected = population_presence(typology_presence, population)
        denominator = len(population)
        for code_a, code_b in combinations(sorted(selected), 2):
            notes_a = selected[code_a]
            notes_b = selected[code_b]
            n11 = len(notes_a & notes_b)
            n10 = len(notes_a - notes_b)
            n01 = len(notes_b - notes_a)
            n00 = denominator - n11 - n10 - n01
            expected = len(notes_a) * len(notes_b) / denominator if denominator else 0
            rows.append(
                {
                    "population": population_name,
                    "population_definition": POPULATION_LABELS[population_name],
                    "denominator_n": denominator,
                    "code_a": code_a,
                    "label_a": typology_labels[code_a],
                    "code_b": code_b,
                    "label_b": typology_labels[code_b],
                    "code_a_present_n": len(notes_a),
                    "code_b_present_n": len(notes_b),
                    "n11_both_present": n11,
                    "n10_a_only": n10,
                    "n01_b_only": n01,
                    "n00_neither": n00,
                    "jaccard": ratio(n11, n11 + n10 + n01),
                    "lift": round(n11 / expected, 6) if expected else 0.0,
                }
            )
    return rows


def build_cooccurrence_source_stability(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
    source_by_note: Mapping[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Build source-stratified and leave-one-source-out pair tables."""

    by_source_rows: list[dict[str, object]] = []
    leave_one_out_rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        full_selected = population_presence(typology_presence, population)
        sources = sorted({source_by_note[note_id] for note_id in population})
        full_pairs = {
            (row["code_a"], row["code_b"]): row
            for row in build_cooccurrence(
                typology_presence,
                typology_labels,
                {population_name: population},
            )
        }
        for source in sources:
            source_population = {
                note_id
                for note_id in population
                if source_by_note[note_id] == source
            }
            selected = {
                code: note_ids & source_population
                for code, note_ids in full_selected.items()
            }
            denominator = len(source_population)
            for code_a, code_b in combinations(sorted(selected), 2):
                notes_a = selected[code_a]
                notes_b = selected[code_b]
                n11 = len(notes_a & notes_b)
                n10 = len(notes_a - notes_b)
                n01 = len(notes_b - notes_a)
                n00 = denominator - n11 - n10 - n01
                expected = (
                    len(notes_a) * len(notes_b) / denominator
                    if denominator
                    else 0
                )
                by_source_rows.append(
                    {
                        "population": population_name,
                        "population_definition": POPULATION_LABELS[population_name],
                        "source": source,
                        "source_denominator_n": denominator,
                        "code_a": code_a,
                        "label_a": typology_labels[code_a],
                        "code_b": code_b,
                        "label_b": typology_labels[code_b],
                        "n11_both_present": n11,
                        "n10_a_only": n10,
                        "n01_b_only": n01,
                        "n00_neither": n00,
                        "jaccard": ratio(n11, n11 + n10 + n01),
                        "lift": round(n11 / expected, 6) if expected else 0.0,
                    }
                )

            remaining_population = population - source_population
            remaining = {
                code: note_ids & remaining_population
                for code, note_ids in full_selected.items()
            }
            denominator = len(remaining_population)
            for code_a, code_b in combinations(sorted(remaining), 2):
                notes_a = remaining[code_a]
                notes_b = remaining[code_b]
                n11 = len(notes_a & notes_b)
                n10 = len(notes_a - notes_b)
                n01 = len(notes_b - notes_a)
                n00 = denominator - n11 - n10 - n01
                expected = (
                    len(notes_a) * len(notes_b) / denominator
                    if denominator
                    else 0
                )
                jaccard = ratio(n11, n11 + n10 + n01)
                lift = round(n11 / expected, 6) if expected else 0.0
                full = full_pairs[(code_a, code_b)]
                leave_one_out_rows.append(
                    {
                        "population": population_name,
                        "population_definition": POPULATION_LABELS[population_name],
                        "removed_source": source,
                        "remaining_denominator_n": denominator,
                        "code_a": code_a,
                        "label_a": typology_labels[code_a],
                        "code_b": code_b,
                        "label_b": typology_labels[code_b],
                        "n11_both_present": n11,
                        "n10_a_only": n10,
                        "n01_b_only": n01,
                        "n00_neither": n00,
                        "jaccard": jaccard,
                        "lift": lift,
                        "full_population_n11": full["n11_both_present"],
                        "n11_difference": n11 - int(full["n11_both_present"]),
                        "full_population_jaccard": full["jaccard"],
                        "jaccard_difference": round(
                            jaccard - float(full["jaccard"]), 6
                        ),
                        "full_population_lift": full["lift"],
                        "lift_difference": round(
                            lift - float(full["lift"]), 6
                        ),
                    }
                )
    return by_source_rows, leave_one_out_rows


def build_source_normalized(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
    source_by_note: Mapping[str, str],
    corpus: Sequence[Mapping[str, str]],
) -> list[dict[str, object]]:
    """Report within-source typology rates with source modality coverage."""

    corpus_by_note = {row["note_id"]: row for row in corpus}
    rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        selected = population_presence(typology_presence, population)
        sources = sorted({source_by_note[note_id] for note_id in population})
        for source in sources:
            source_population = {
                note_id
                for note_id in population
                if source_by_note[note_id] == source
            }
            denominator = len(source_population)
            markdown_n = sum(
                corpus_by_note[note_id].get("markdown_present") == "1"
                for note_id in source_population
            )
            ocr_n = sum(
                corpus_by_note[note_id].get("ocr_present") == "1"
                for note_id in source_population
            )
            markdown_and_ocr_n = sum(
                corpus_by_note[note_id].get("markdown_present") == "1"
                and corpus_by_note[note_id].get("ocr_present") == "1"
                for note_id in source_population
            )
            neither_n = sum(
                corpus_by_note[note_id].get("markdown_present") != "1"
                and corpus_by_note[note_id].get("ocr_present") != "1"
                for note_id in source_population
            )
            for code in sorted(selected):
                source_positive_n = len(selected[code] & source_population)
                total_positive_n = len(selected[code])
                rows.append(
                    {
                        "population": population_name,
                        "population_definition": POPULATION_LABELS[population_name],
                        "source": source,
                        "source_denominator_n": denominator,
                        "markdown_present_n": markdown_n,
                        "ocr_present_n": ocr_n,
                        "markdown_and_ocr_present_n": markdown_and_ocr_n,
                        "neither_modality_present_n": neither_n,
                        "code": code,
                        "label": typology_labels[code],
                        "source_positive_records_n": source_positive_n,
                        "within_source_percent": percent(
                            source_positive_n, denominator
                        ),
                        "all_sources_positive_records_n": total_positive_n,
                        "source_share_of_positive_records": ratio(
                            source_positive_n, total_positive_n
                        ),
                    }
                )
    return rows


def build_aml_crosswalk(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    aml_presence: Mapping[str, set[str]],
    aml_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        typologies = population_presence(typology_presence, population)
        indicators = population_presence(aml_presence, population)
        denominator = len(population)
        for typology_code in sorted(typologies):
            for aml_code in sorted(indicators):
                if (typology_code, aml_code) in STRUCTURAL_TYPOLOGY_AML_PAIRS:
                    continue
                typology_notes = typologies[typology_code]
                aml_notes = indicators[aml_code]
                n11 = len(typology_notes & aml_notes)
                n10 = len(typology_notes - aml_notes)
                n01 = len(aml_notes - typology_notes)
                n00 = denominator - n11 - n10 - n01
                expected = (
                    len(typology_notes) * len(aml_notes) / denominator
                    if denominator
                    else 0
                )
                rows.append(
                    {
                        "population": population_name,
                        "population_definition": POPULATION_LABELS[population_name],
                        "denominator_n": denominator,
                        "typology_code": typology_code,
                        "typology_label": typology_labels[typology_code],
                        "aml_candidate": aml_code,
                        "aml_candidate_label": aml_labels[aml_code],
                        "typology_present_n": len(typology_notes),
                        "aml_candidate_present_n": len(aml_notes),
                        "n11_both_present": n11,
                        "n10_typology_only": n10,
                        "n01_aml_only": n01,
                        "n00_neither": n00,
                        "jaccard": ratio(n11, n11 + n10 + n01),
                        "typology_share_with_candidate": ratio(
                            n11, len(typology_notes)
                        ),
                        "candidate_share_with_typology": ratio(
                            n11, len(aml_notes)
                        ),
                        "lift": round(n11 / expected, 6) if expected else 0.0,
                    }
                )
    return rows


def build_service_chain(
    typology_presence: Mapping[str, set[str]],
    populations: Mapping[str, set[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        selected = population_presence(typology_presence, population)
        for stage, definition in SERVICE_CHAIN_STAGES.items():
            note_ids: set[str] = set()
            for code in definition["codes"]:
                note_ids.update(selected.get(code, set()))
            rows.append(
                {
                    "population": population_name,
                    "population_definition": POPULATION_LABELS[population_name],
                    "mapping_status": "exploratory_descriptive_grouping",
                    "stage": stage,
                    "label": definition["label"],
                    "definition": definition["definition"],
                    "included_codes": "; ".join(definition["codes"]),
                    "denominator_n": len(population),
                    "unique_records_present_n": len(note_ids),
                    "records_present_percent": percent(len(note_ids), len(population)),
                }
            )
    return rows


def source_counts(
    note_ids: Iterable[str], source_by_note: Mapping[str, str]
) -> Counter[str]:
    return Counter(source_by_note[note_id] for note_id in note_ids)


def build_source_concentration(
    typology_presence: Mapping[str, set[str]],
    typology_labels: Mapping[str, str],
    populations: Mapping[str, set[str]],
    source_by_note: Mapping[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    concentration_rows: list[dict[str, object]] = []
    leave_one_out_rows: list[dict[str, object]] = []
    for population_name, population in populations.items():
        selected = population_presence(typology_presence, population)
        denominator = len(population)
        sources = sorted({source_by_note[note_id] for note_id in population})
        full_ranks = ranked_codes(selected)
        for code in sorted(selected):
            counts = source_counts(selected[code], source_by_note)
            total = sum(counts.values())
            top = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            top_source, top_count = top[0] if top else ("", 0)
            top_three = sum(count for _, count in top[:3])
            hhi = sum((count / total) ** 2 for count in counts.values()) if total else 0.0
            concentration_rows.append(
                {
                    "population": population_name,
                    "population_definition": POPULATION_LABELS[population_name],
                    "denominator_n": denominator,
                    "code": code,
                    "label": typology_labels[code],
                    "positive_records_n": total,
                    "source_groups_with_positive_records_n": len(counts),
                    "top_source": top_source,
                    "top_source_positive_records_n": top_count,
                    "top_source_share": ratio(top_count, total),
                    "top_three_source_share": ratio(top_three, total),
                    "source_hhi": round(hhi, 6),
                    "full_rank_by_record_count": full_ranks[code],
                }
            )

        for removed_source in sources:
            remaining_population = {
                note_id
                for note_id in population
                if source_by_note[note_id] != removed_source
            }
            remaining = {
                code: note_ids & remaining_population
                for code, note_ids in selected.items()
            }
            remaining_ranks = ranked_codes(remaining)
            for code in sorted(remaining):
                leave_one_out_rows.append(
                    {
                        "population": population_name,
                        "population_definition": POPULATION_LABELS[population_name],
                        "removed_source": removed_source,
                        "code": code,
                        "label": typology_labels[code],
                        "remaining_denominator_n": len(remaining_population),
                        "remaining_positive_records_n": len(remaining[code]),
                        "remaining_positive_percent": percent(
                            len(remaining[code]), len(remaining_population)
                        ),
                        "full_rank_by_record_count": full_ranks[code],
                        "remaining_rank_by_record_count": remaining_ranks[code],
                        "rank_change": remaining_ranks[code] - full_ranks[code],
                    }
                )
    return concentration_rows, leave_one_out_rows


def build_analysis(source_dir: Path, output_dir: Path) -> dict[str, object]:
    source_files = {
        "combined_corpus_with_ocr.csv": source_dir / "combined_corpus_with_ocr.csv",
        "typology_coding_long.csv": source_dir / "typology_coding_long.csv",
        "aml_indicator_coding_long.csv": source_dir / "aml_indicator_coding_long.csv",
    }
    corpus = read_csv(
        source_files["combined_corpus_with_ocr.csv"],
        (
            "note_id",
            "source",
            "combined_word_count",
            "combined_text_sha256",
            "markdown_present",
            "ocr_present",
        ),
    )
    typology_rows = read_csv(
        source_files["typology_coding_long.csv"],
        ("note_id", "code", "label", "present"),
    )
    aml_rows = read_csv(
        source_files["aml_indicator_coding_long.csv"],
        ("note_id", "aml_indicator", "label", "present"),
    )
    populations, source_by_note, hash_by_note, duplicate_metadata = build_populations(
        corpus
    )
    typology_presence, typology_labels = build_presence(
        typology_rows,
        code_field="code",
        excluded_codes=DATA_QUALITY_CODES,
    )
    aml_presence, aml_labels = build_presence(
        aml_rows,
        code_field="aml_indicator",
    )
    validate_duplicate_code_consistency(
        typology_presence,
        populations["full_screened"],
        hash_by_note,
        "Typology",
    )
    validate_duplicate_code_consistency(
        aml_presence,
        populations["full_screened"],
        hash_by_note,
        "AML candidate",
    )
    unknown_typology_notes = sorted(
        set().union(*typology_presence.values()) - populations["full_screened"]
    )
    unknown_aml_notes = sorted(
        set().union(*aml_presence.values()) - populations["full_screened"]
    )
    if unknown_typology_notes or unknown_aml_notes:
        raise DerivedAnalysisError("Coding rows refer to note_id values absent from corpus")

    duplicate_rows = build_duplicate_sensitivity(
        typology_presence, typology_labels, populations
    )
    cooccurrence_rows = build_cooccurrence(
        typology_presence, typology_labels, populations
    )
    cooccurrence_by_source_rows, cooccurrence_leave_one_out_rows = (
        build_cooccurrence_source_stability(
            typology_presence,
            typology_labels,
            populations,
            source_by_note,
        )
    )
    source_normalized_rows = build_source_normalized(
        typology_presence,
        typology_labels,
        populations,
        source_by_note,
        corpus,
    )
    crosswalk_rows = build_aml_crosswalk(
        typology_presence,
        typology_labels,
        aml_presence,
        aml_labels,
        populations,
    )
    service_rows = build_service_chain(typology_presence, populations)
    concentration_rows, leave_one_out_rows = build_source_concentration(
        typology_presence,
        typology_labels,
        populations,
        source_by_note,
    )

    write_csv(
        output_dir / "duplicate_sensitivity.csv",
        duplicate_rows,
        tuple(duplicate_rows[0]),
    )
    write_csv(
        output_dir / "typology_cooccurrence.csv",
        cooccurrence_rows,
        tuple(cooccurrence_rows[0]),
    )
    write_csv(
        output_dir / "typology_cooccurrence_by_source.csv",
        cooccurrence_by_source_rows,
        tuple(cooccurrence_by_source_rows[0]),
    )
    write_csv(
        output_dir / "typology_cooccurrence_leave_one_source_out.csv",
        cooccurrence_leave_one_out_rows,
        tuple(cooccurrence_leave_one_out_rows[0]),
    )
    write_csv(
        output_dir / "typology_source_normalized.csv",
        source_normalized_rows,
        tuple(source_normalized_rows[0]),
    )
    write_csv(
        output_dir / "typology_aml_crosswalk.csv",
        crosswalk_rows,
        tuple(crosswalk_rows[0]),
    )
    write_csv(
        output_dir / "service_chain_grouping.csv",
        service_rows,
        tuple(service_rows[0]),
    )
    write_csv(
        output_dir / "source_concentration.csv",
        concentration_rows,
        tuple(concentration_rows[0]),
    )
    write_csv(
        output_dir / "source_leave_one_out.csv",
        leave_one_out_rows,
        tuple(leave_one_out_rows[0]),
    )

    metadata = {
        "script_version": SCRIPT_VERSION,
        "analysis_scope": "deterministic_descriptive_derived_analysis",
        "population_counts": {
            name: len(note_ids) for name, note_ids in populations.items()
        },
        "population_definitions": POPULATION_LABELS,
        "duplicate_audit": duplicate_metadata,
        "substantive_typology_codes_n": len(typology_presence),
        "aml_candidate_codes_n": len(aml_presence),
        "structural_typology_aml_pairs_excluded_n": len(
            STRUCTURAL_TYPOLOGY_AML_PAIRS
        ),
        "output_row_counts": {
            "duplicate_sensitivity.csv": len(duplicate_rows),
            "typology_cooccurrence.csv": len(cooccurrence_rows),
            "typology_cooccurrence_by_source.csv": len(
                cooccurrence_by_source_rows
            ),
            "typology_cooccurrence_leave_one_source_out.csv": len(
                cooccurrence_leave_one_out_rows
            ),
            "typology_source_normalized.csv": len(source_normalized_rows),
            "typology_aml_crosswalk.csv": len(crosswalk_rows),
            "service_chain_grouping.csv": len(service_rows),
            "source_concentration.csv": len(concentration_rows),
            "source_leave_one_out.csv": len(leave_one_out_rows),
        },
        "controlled_input_sha256": {
            name: sha256_file(path) for name, path in source_files.items()
        },
        "interpretation_boundaries": [
            "The exact-text-unique population is a duplicate sensitivity population, not a final eligible population.",
            "Co-occurrence and lift are descriptive of captured records and do not establish direction, sequence, common actors, transactions, or causation.",
            "AML candidates are corpus-derived research hypotheses, not confirmed red flags or monitoring controls.",
            "Service-chain stages are an exploratory descriptive grouping and do not establish a completed service chain.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "derived_analysis_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        required=True,
        type=Path,
        help="Controlled phase3_typology_coding output directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "outputs" / "derived_analysis",
        help="Publication-safe aggregate output directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        metadata = build_analysis(args.source_dir.resolve(), args.output_dir.resolve())
    except DerivedAnalysisError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(json.dumps(metadata, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
