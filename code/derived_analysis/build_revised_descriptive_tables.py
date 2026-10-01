#!/usr/bin/env python3
"""Build controlled, provisional descriptive tables from reviewed source spans."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from build_revised_duplicate_sensitivity import (
    CheckedRun, QUALITY_FLAG, load_checked_run, outside_public, sha_file, write_csv,
)


FLOW_FIELDS = ["stage", "count_n", "definition"]
COVERAGE_FIELDS = [
    "scope", "source", "approved_capture_units_n", "markdown_only_units_n",
    "ocr_only_units_n", "both_modalities_units_n", "verified_unit_capture_date_n",
    "unknown_or_mixed_unit_date_n", "approved_source_spans_n",
]
PREVALENCE_FIELDS = [
    "scope", "source", "target_type", "code", "label", "approved_capture_units_n",
    "rule_positive_units_n", "rule_positive_percent", "target_validation_status",
]
MODALITY_FIELDS = [
    "target_type", "code", "label", "rule_positive_units_n",
    "markdown_only_positive_units_n", "ocr_only_positive_units_n",
    "both_modalities_positive_units_n",
]
PAIR_FIELDS = [
    "scope", "source", "removed_source", "approved_capture_units_n", "code_a",
    "code_b", "code_a_positive_units_n", "code_b_positive_units_n", "n11_both_n",
    "n10_a_only_n", "n01_b_only_n", "n00_neither_n", "jaccard", "lift",
]
CONCENTRATION_FIELDS = [
    "target_type", "code", "label", "rule_positive_units_n",
    "positive_source_groups_n", "top_source", "top_source_positive_units_n",
    "top_source_share", "top_three_source_share", "source_hhi",
]
LEAVE_OUT_FIELDS = [
    "target_type", "code", "label", "removed_source", "remaining_units_n",
    "remaining_positive_units_n", "remaining_positive_percent",
    "full_positive_units_n", "full_positive_percent",
]
OUTPUTS = {
    "revised_screen_flow_controlled.csv": FLOW_FIELDS,
    "revised_source_coverage_controlled.csv": COVERAGE_FIELDS,
    "revised_target_prevalence_controlled.csv": PREVALENCE_FIELDS,
    "revised_modality_contribution_controlled.csv": MODALITY_FIELDS,
    "revised_typology_cooccurrence_controlled.csv": PAIR_FIELDS,
    "revised_source_concentration_controlled.csv": CONCENTRATION_FIELDS,
    "revised_leave_one_source_out_controlled.csv": LEAVE_OUT_FIELDS,
}


def fraction(numerator: int, denominator: int) -> str:
    return format(numerator / denominator, ".6f") if denominator else ""


def percent(numerator: int, denominator: int) -> str:
    return format(100 * numerator / denominator, ".3f") if denominator else ""


def checked_count(value: object, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"Invalid nonnegative count in evidence manifest: {name}")
    return value


def flow_rows(run: CheckedRun) -> list[dict[str, object]]:
    manifest = run.evidence_manifest
    decisions = manifest.get("note_decisions")
    image_decisions = manifest.get("image_decisions")
    if not isinstance(decisions, dict) or not isinstance(image_decisions, dict):
        raise ValueError("Screening decision counts are missing")
    screened = checked_count(manifest.get("screened_notes"), "screened_notes")
    included = checked_count(decisions.get("include", 0), "note_decisions.include")
    excluded = checked_count(decisions.get("exclude", 0), "note_decisions.exclude")
    orphan_units = checked_count(manifest.get("approved_standalone_orphan_units"),
                                 "approved_standalone_orphan_units")
    spans = checked_count(manifest.get("approved_text_segments"), "approved_text_segments")
    if (included + excluded != screened or included + orphan_units != len(run.units)
            or spans != sum(len(unit["artifacts"]) for unit in run.units.values())):
        raise ValueError("Screening counts do not reconcile to approved evidence units")
    rows = [
        {"stage": "screened_markdown_notes", "count_n": screened,
         "definition": "Notes reviewed for source-evidence eligibility"},
        {"stage": "excluded_markdown_notes", "count_n": excluded,
         "definition": "Notes excluded after two-reviewer source screening"},
        {"stage": "included_markdown_notes", "count_n": included,
         "definition": "Included notes with at least one approved source span"},
        {"stage": "standalone_orphan_image_units", "count_n": orphan_units,
         "definition": "Separately approved units from unreferenced images"},
        {"stage": "approved_capture_units", "count_n": len(run.units),
         "definition": "Approved source-evidence units, including standalone orphan units"},
        {"stage": "approved_source_spans", "count_n": spans,
         "definition": "Approved Markdown or screenshot OCR source-text spans"},
    ]
    for decision, value in sorted(image_decisions.items()):
        if not isinstance(decision, str) or not decision:
            raise ValueError("Invalid image decision label")
        rows.append({
            "stage": f"image_review_rows:{decision}",
            "count_n": checked_count(value, f"image_decisions.{decision}"),
            "definition": "Reviewed image assignment row; not a unique image count",
        })
    return rows


def substantive_targets(run: CheckedRun) -> list[tuple[str, str]]:
    if QUALITY_FLAG not in run.targets.get("typology", set()):
        raise ValueError("Collection-quality flag is missing")
    return sorted(
        (target_type, code)
        for target_type, codes in run.targets.items()
        for code in codes if (target_type, code) != ("typology", QUALITY_FLAG)
    )


def coverage_rows(run: CheckedRun, sources: list[str]) -> list[dict[str, object]]:
    rows = []
    scopes = [("all", "", set(run.units))] + [
        ("source", source, {unit_id for unit_id, unit in run.units.items()
                            if unit["source"] == source}) for source in sources
    ]
    for scope, source, ids in scopes:
        markdown_only = ocr_only = both = known_date = spans = 0
        for unit_id in ids:
            unit = run.units[unit_id]
            kinds = {artifact["kind"] for artifact in unit["artifacts"]}
            markdown = "markdown_source_span" in kinds
            ocr = "image_ocr" in kinds
            if not markdown and not ocr:
                raise ValueError("Approved unit has no source-text modality")
            markdown_only += markdown and not ocr
            ocr_only += ocr and not markdown
            both += markdown and ocr
            known_date += bool(unit["collection_date"])
            spans += len(unit["artifacts"])
        rows.append({
            "scope": scope, "source": source, "approved_capture_units_n": len(ids),
            "markdown_only_units_n": markdown_only, "ocr_only_units_n": ocr_only,
            "both_modalities_units_n": both,
            "verified_unit_capture_date_n": known_date,
            "unknown_or_mixed_unit_date_n": len(ids) - known_date,
            "approved_source_spans_n": spans,
        })
    return rows


def target_rows(run: CheckedRun, sources: list[str],
                targets: list[tuple[str, str]]) -> tuple[list[dict[str, object]],
                                                         list[dict[str, object]],
                                                         list[dict[str, object]]]:
    prevalence = []
    concentration = []
    leave_out = []
    all_ids = set(run.units)
    ids_by_source = {
        source: {unit_id for unit_id, unit in run.units.items()
                 if unit["source"] == source} for source in sources
    }
    for target_type, code in targets:
        positive = {unit_id for unit_id in all_ids
                    if run.predictions[(unit_id, target_type, code)]}
        for scope, source, ids in [("all", "", all_ids)] + [
            ("source", source, ids_by_source[source]) for source in sources
        ]:
            count = len(positive & ids)
            prevalence.append({
                "scope": scope, "source": source, "target_type": target_type,
                "code": code, "label": run.labels[(target_type, code)],
                "approved_capture_units_n": len(ids), "rule_positive_units_n": count,
                "rule_positive_percent": percent(count, len(ids)),
                "target_validation_status": "fresh_blinded_holdout_pending",
            })
        source_counts = sorted(
            ((source, len(positive & ids_by_source[source])) for source in sources),
            key=lambda item: (-item[1], item[0]),
        )
        nonzero = [(source, count) for source, count in source_counts if count]
        top_source, top_count = nonzero[0] if nonzero else ("", 0)
        concentration.append({
            "target_type": target_type, "code": code,
            "label": run.labels[(target_type, code)],
            "rule_positive_units_n": len(positive),
            "positive_source_groups_n": len(nonzero),
            "top_source": top_source, "top_source_positive_units_n": top_count,
            "top_source_share": fraction(top_count, len(positive)),
            "top_three_source_share": fraction(sum(count for _, count in nonzero[:3]),
                                                len(positive)),
            "source_hhi": (format(sum((count / len(positive)) ** 2 for _, count in nonzero),
                                  ".6f") if positive else ""),
        })
        for source in sources:
            remaining = all_ids - ids_by_source[source]
            remaining_positive = len(positive & remaining)
            leave_out.append({
                "target_type": target_type, "code": code,
                "label": run.labels[(target_type, code)],
                "removed_source": source, "remaining_units_n": len(remaining),
                "remaining_positive_units_n": remaining_positive,
                "remaining_positive_percent": percent(remaining_positive, len(remaining)),
                "full_positive_units_n": len(positive),
                "full_positive_percent": percent(len(positive), len(all_ids)),
            })
    return prevalence, concentration, leave_out


def modality_rows(run: CheckedRun,
                  targets: list[tuple[str, str]]) -> list[dict[str, object]]:
    rows = []
    for target_type, code in targets:
        counts: Counter[str] = Counter()
        for unit_id, unit in run.units.items():
            positive_kinds = {
                artifact["kind"] for artifact in unit["artifacts"]
                if run.artifact_predictions[(unit_id, artifact["artifact_id"],
                                             target_type, code)]
            }
            machine_positive = bool(run.predictions[(unit_id, target_type, code)])
            if machine_positive != bool(positive_kinds):
                raise ValueError("Unit prediction disagrees with source-span modality")
            if positive_kinds == {"markdown_source_span"}:
                counts["markdown_only"] += 1
            elif positive_kinds == {"image_ocr"}:
                counts["ocr_only"] += 1
            elif positive_kinds == {"markdown_source_span", "image_ocr"}:
                counts["both"] += 1
            elif positive_kinds:
                raise ValueError("Unexpected positive source-span modality")
        rows.append({
            "target_type": target_type, "code": code,
            "label": run.labels[(target_type, code)],
            "rule_positive_units_n": sum(counts.values()),
            "markdown_only_positive_units_n": counts["markdown_only"],
            "ocr_only_positive_units_n": counts["ocr_only"],
            "both_modalities_positive_units_n": counts["both"],
        })
    return rows


def pair_rows(run: CheckedRun, sources: list[str]) -> list[dict[str, object]]:
    codes = sorted(run.targets["typology"] - {QUALITY_FLAG})
    all_ids = set(run.units)
    ids_by_source = {
        source: {unit_id for unit_id, unit in run.units.items()
                 if unit["source"] == source} for source in sources
    }
    scopes = [("all", "", "", all_ids)]
    scopes.extend(("source", source, "", ids_by_source[source]) for source in sources)
    scopes.extend(("leave_one_source_out", "", source, all_ids - ids_by_source[source])
                  for source in sources)
    rows = []
    for scope, source, removed_source, ids in scopes:
        present = {code: {unit_id for unit_id in ids
                          if run.predictions[(unit_id, "typology", code)]} for code in codes}
        for code_a, code_b in combinations(codes, 2):
            a, b = present[code_a], present[code_b]
            n11, n10, n01 = len(a & b), len(a - b), len(b - a)
            union = n11 + n10 + n01
            rows.append({
                "scope": scope, "source": source, "removed_source": removed_source,
                "approved_capture_units_n": len(ids), "code_a": code_a, "code_b": code_b,
                "code_a_positive_units_n": len(a), "code_b_positive_units_n": len(b),
                "n11_both_n": n11, "n10_a_only_n": n10, "n01_b_only_n": n01,
                "n00_neither_n": len(ids) - union,
                "jaccard": fraction(n11, union),
                "lift": fraction(n11 * len(ids), len(a) * len(b)),
            })
    return rows


def compute_tables(run: CheckedRun) -> dict[str, list[dict[str, object]]]:
    sources = sorted({str(unit["source"]) for unit in run.units.values()})
    targets = substantive_targets(run)
    prevalence, concentration, leave_out = target_rows(run, sources, targets)
    return {
        "revised_screen_flow_controlled.csv": flow_rows(run),
        "revised_source_coverage_controlled.csv": coverage_rows(run, sources),
        "revised_target_prevalence_controlled.csv": prevalence,
        "revised_modality_contribution_controlled.csv": modality_rows(run, targets),
        "revised_typology_cooccurrence_controlled.csv": pair_rows(run, sources),
        "revised_source_concentration_controlled.csv": concentration,
        "revised_leave_one_source_out_controlled.csv": leave_out,
    }


def build(phase3_dir: Path, evidence_corpus: Path, output_dir: Path) -> dict[str, object]:
    phase3_dir = outside_public(phase3_dir)
    evidence_corpus = outside_public(evidence_corpus)
    output_dir = outside_public(output_dir)
    if (output_dir == phase3_dir or output_dir in phase3_dir.parents
            or phase3_dir in output_dir.parents or output_dir == evidence_corpus.parent
            or output_dir in evidence_corpus.parents
            or evidence_corpus.parent in output_dir.parents):
        raise ValueError("Descriptive output must be separate from controlled inputs")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Descriptive output directory is not empty")
    run = load_checked_run(phase3_dir, evidence_corpus)
    tables = compute_tables(run)
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, fields in OUTPUTS.items():
        write_csv(output_dir / filename, fields, tables[filename])
    report = {
        "status": "provisional_reviewed_evidence_descriptive_tables",
        "approved_capture_units_n": len(run.units),
        "substantive_typology_codes_n": len(run.targets["typology"] - {QUALITY_FLAG}),
        "aml_candidates_n": len(run.targets["aml_candidate"]),
        "target_validation_complete": False,
        "ocr_quality_review_complete": False,
        "article_ready": False,
        "historical_mixed_record_denominator_used": False,
        "analysis_script_sha256": sha_file(Path(__file__)),
        "checked_loader_sha256": sha_file(Path(__file__).with_name("build_revised_duplicate_sensitivity.py")),
        "method_document_sha256": sha_file(Path(__file__).with_name("METHODS_REVISED_DESCRIPTIVES.md")),
        "input_sha256": run.input_sha256,
        "output_sha256": {filename: sha_file(output_dir / filename) for filename in OUTPUTS},
        "output_row_counts": {filename: len(tables[filename]) for filename in OUTPUTS},
    }
    (output_dir / "revised_descriptive_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-dir", type=Path, required=True)
    parser.add_argument("--evidence-corpus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build(args.phase3_dir, args.evidence_corpus, args.output_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in (
        "status", "approved_capture_units_n", "substantive_typology_codes_n",
        "aml_candidates_n", "article_ready",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
