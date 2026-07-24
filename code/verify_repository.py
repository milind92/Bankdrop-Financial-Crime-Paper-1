"""Data-free integrity and privacy audit for the public analysis repository."""

from __future__ import annotations

import csv
import json
import py_compile
import re
import sys
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "CHANGELOG.md",
    "CITATION.cff",
    "LICENSE.md",
    "DATA_AVAILABILITY.md",
    "ETHICS_AND_SAFETY.md",
    "SECURITY.md",
    "REPRODUCIBILITY.md",
    "requirements-audit.txt",
    "workflow_manifest.json",
    ".github/workflows/repository-integrity.yml",
    "code/run_reproducible_pipeline.py",
    "code/export_public_release.py",
    "code/human_validation/summarize_human_validation.py",
    "docs/ANALYSIS_PLAN.md",
    "docs/DATA_COLLECTION_PROTOCOL.md",
    "docs/HUMAN_VALIDATION_PROTOCOL.md",
    "docs/CONTROLLED_AUDIT_ACCESS.md",
    "docs/AI_AUTHORING_ASSISTANCE_DISCLOSURE.md",
    "outputs/human_validation/HUMAN_ICR_COMPLETION.md",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv",
)

CSV_SCHEMAS = {
    "outputs/phase1_aggregate/entity_summary_by_source.csv": "source,entity_type,entity,hit_count",
    "outputs/phase1_aggregate/keyword_summary_by_source.csv": "source,keyword,file_count,hit_count",
    "outputs/phase1_aggregate/source_summary.csv": "source,note_count,dated_note_count,first_date,last_date,word_count,image_ref_count",
    "outputs/phase1_aggregate/top_price_amounts.csv": "amount,mention_count",
    "outputs/phase2_aggregate/ocr_summary_by_source.csv": "source,image_ref_count,ocr_ok_count,ocr_empty_count,ocr_error_count,ocr_not_local_or_not_processed_count,ocr_word_count",
    "outputs/phase3_aggregate/aml_indicator_summary_by_source.csv": "aml_indicator,label,source,note_count,hit_count",
    "outputs/phase3_aggregate/criminal_objective_summary.csv": "criminal_objective,note_count,hit_count",
    "outputs/phase3_aggregate/typology_summary.csv": "code,label,criminal_objective,note_count,hit_count,high_rule_match_intensity_notes,medium_rule_match_intensity_notes,low_rule_match_intensity_notes",
    "outputs/phase3_aggregate/typology_summary_by_source.csv": "source,code,label,note_count,hit_count",
    "outputs/phase4_aggregate/aml_red_flags_summary.csv": "rank,aml_indicator,label,source_count,note_count,hit_count,interpretation",
    "outputs/phase4_aggregate/financial_crime_findings.csv": "rank,code,label,note_count,hit_count,finding,analysis,result_type,aml_or_detection_relevance",
    "outputs/phase4_aggregate/source_profile_summary.csv": "source,dominant_typology,dominant_typology_notes,top_typologies",
    "outputs/human_validation/human_icr_aggregate_summary.csv": "protocol_id,completion_date,coder_count,coordinator_count,evidence_packet_count,assessed_target_count,decision_category_count,paired_units,exact_agreements,disagreements,agreement_percent,cohen_kappa,krippendorff_alpha_nominal,binary_subset_units,binary_subset_exact_agreements,binary_subset_agreement_percent,binary_subset_cohen_kappa,adjudicated_disagreements,consensus_cases,no_consensus_cases,final_present,final_absent,final_ambiguous,final_insufficient_evidence,final_out_of_scope",
    "outputs/human_validation/validation_code_summary.csv": "target_type,code,label,positive_population_rows,negative_population_rows,positive_unique_evidence_rows,negative_unique_evidence_rows,positive_sample_rows,negative_sample_rows,sampling_seed,sampling_rule",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv": "screened_combined_records,unique_combined_text_hashes,exact_duplicate_groups,exact_duplicate_excess,maximum_duplicate_group_size,zero_combined_word_records,markdown_only_records,markdown_and_ocr_records,ocr_only_records,neither_assessable_records,explicit_exclusion_log_available,pre_analysis_deduplication_applied,eligible_unique_analytic_records",
}

REQUIRED_NON_CSV_OUTPUTS = (
    "outputs/phase1_aggregate/PHASE1_CHECKPOINT_SUMMARY.md",
    "outputs/phase1_aggregate/phase1_summary.json",
    "outputs/phase2_aggregate/PHASE2_CHECKPOINT_SUMMARY.md",
    "outputs/phase3_aggregate/CODEBOOK_PHASE3.md",
    "outputs/phase3_aggregate/PHASE3_ANALYTIC_OVERVIEW.md",
    "outputs/phase3_aggregate/PHASE3_CHECKPOINT_SUMMARY.md",
    "outputs/phase4_aggregate/FINANCIAL_CRIME_ANALYSIS_REPORT.md",
    "outputs/phase4_aggregate/PHASE4_CHECKPOINT_SUMMARY.md",
    "outputs/phase4_aggregate/run_metadata.json",
    "outputs/human_validation/HUMAN_ICR_COMPLETION.md",
)

EXCLUDED_PATH_PARTS = {
    "phase3b_llm_validation",
    "phase4b_llm_synthesis",
    "phase5_journal_package",
    "submission_templates",
}
EXCLUDED_FILENAMES = {
    "JOURNAL_ARTICLE_DRAFT.md",
    "TABLES_FOR_ARTICLE.md",
    "COVER_LETTER_TEMPLATE.md",
    "TITLE_PAGE_TEMPLATE.md",
    "DECLARATIONS_TEMPLATE.md",
    "LLM_DISCLOSURE.md",
    "DETAILED_OUTPUTS_WITH_LLM.md",
}
RESTRICTED_FILENAMES = {
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
}
BLOCKED_EXACT_FIELDS = {"note_id", "legacy_note_id", "record_id", "source_path", "local_path", "absolute_path"}
BLOCKED_FIELD_TOKENS = {"snippet", "snippets", "raw_text", "ocr_text", "full_text"}
SAFE_AGGREGATE_FIELDS = {"unique_text_count", "positive_unique_evidence_rows", "negative_unique_evidence_rows"}
ABSOLUTE_PATH_PATTERN = re.compile(r"(?i)(?:\b[A-Z]:\\Users\\|(?<!:)/(?:home|Users)/[^/\s]+/)")


def repository_files() -> list[Path]:
    return [path for path in REPOSITORY_ROOT.rglob("*") if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts]


def blocked_public_fields(fieldnames: list[str]) -> list[str]:
    blocked: list[str] = []
    for field in fieldnames:
        normalized = field.strip().casefold()
        if normalized in SAFE_AGGREGATE_FIELDS:
            continue
        if normalized in BLOCKED_EXACT_FIELDS or any(token in normalized for token in BLOCKED_FIELD_TOKENS):
            blocked.append(field)
    return blocked


def load_manifest(errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads((REPOSITORY_ROOT / "workflow_manifest.json").read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not load workflow_manifest.json: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append("workflow_manifest.json must contain a JSON object.")
        return {}
    return value


def _read_rows(relative: str, errors: list[str]) -> list[dict[str, str]]:
    try:
        with (REPOSITORY_ROOT / relative).open("r", newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        errors.append(f"Could not read {relative}: {exc}")
        return []


def check_required_files(errors: list[str]) -> int:
    checked = 0
    for relative in (*REQUIRED_FILES, *CSV_SCHEMAS, *REQUIRED_NON_CSV_OUTPUTS):
        if not (REPOSITORY_ROOT / relative).is_file():
            errors.append(f"Required file missing: {relative}")
        else:
            checked += 1
    return checked


def check_python_and_json(errors: list[str]) -> tuple[int, int]:
    python_count = 0
    json_count = 0
    for path in repository_files():
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        if path.suffix == ".py":
            try:
                py_compile.compile(str(path), doraise=True)
                python_count += 1
            except py_compile.PyCompileError as exc:
                errors.append(f"Python syntax error in {relative}: {exc.msg}")
        elif path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
                json_count += 1
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Invalid JSON in {relative}: {exc}")
    return python_count, json_count


def check_csv_schemas(errors: list[str]) -> int:
    checked = 0
    for relative, expected in CSV_SCHEMAS.items():
        path = REPOSITORY_ROOT / relative
        if not path.is_file():
            continue
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
        actual = ",".join(header)
        if actual != expected:
            errors.append(f"Unexpected CSV schema in {relative}: {actual}")
        blocked = blocked_public_fields(header)
        if blocked:
            errors.append(f"Blocked public fields in {relative}: {', '.join(blocked)}")
        checked += 1
    return checked


def _manifest_paths(value: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            paths.extend(_manifest_paths(child))
    elif isinstance(value, list):
        for child in value:
            paths.extend(_manifest_paths(child))
    elif isinstance(value, str) and "://" not in value and value.endswith((".md", ".csv", ".json", ".py", ".yml", ".cff")):
        paths.append(value.replace("\\", "/"))
    return paths


def check_manifest(manifest: dict[str, Any], errors: list[str]) -> int:
    checked = 0
    phases = manifest.get("phases", [])
    names = [phase.get("phase") for phase in phases if isinstance(phase, dict)]
    if names != ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
        errors.append(f"Manifest must contain exactly deterministic Phases 1-4; found {names}")
    else:
        checked += 1
    if any(phase.get("llm_used") is not False for phase in phases if isinstance(phase, dict)):
        errors.append("Every included empirical phase must record llm_used=false.")
    else:
        checked += 1
    for relative in sorted(set(_manifest_paths(manifest))):
        if not (REPOSITORY_ROOT / relative).is_file():
            errors.append(f"Manifest references missing file: {relative}")
        else:
            checked += 1
    return checked


def check_excluded_material(errors: list[str]) -> int:
    checked = 0
    for file_path in repository_files():
        relative = file_path.relative_to(REPOSITORY_ROOT)
        parts = set(relative.parts)
        if parts & EXCLUDED_PATH_PARTS:
            errors.append(f"Excluded repository path is present: {relative.as_posix()}")
        elif file_path.name in EXCLUDED_FILENAMES:
            errors.append(f"Excluded repository file is present: {relative.as_posix()}")
        elif file_path.name in RESTRICTED_FILENAMES:
            errors.append(f"Restricted record-level file is present: {relative.as_posix()}")
        else:
            checked += 1
    return checked


def check_text_privacy(errors: list[str]) -> int:
    checked = 0
    text_suffixes = {".md", ".txt", ".py", ".json", ".yml", ".yaml", ".cff", ".csv"}
    for file_path in repository_files():
        if file_path.suffix.casefold() not in text_suffixes:
            continue
        relative = file_path.relative_to(REPOSITORY_ROOT).as_posix()
        try:
            text = file_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Could not inspect text file {relative}: {exc}")
            continue
        match = ABSOLUTE_PATH_PATTERN.search(text)
        if match:
            errors.append(f"Local user path exposed in {relative}: {match.group(0)}")
        checked += 1
    return checked


def check_ai_authoring_disclosure(manifest: dict[str, Any], errors: list[str]) -> int:
    record = manifest.get("ai_authoring_assistance", {})
    disclosure = record.get("disclosure") if isinstance(record, dict) else None
    if not isinstance(disclosure, str) or not disclosure.strip():
        errors.append("Manifest must contain the author-provided Codex disclosure.")
        return 0
    required_fragments = (
        "preparation and formatting of the workbook used for the intercoder reliability assessment",
        "did not generate coding responses",
        "did not perform literature discovery, citation checking, or the drafting or editing of the manuscript or submission materials",
    )
    checked = 0
    for fragment in required_fragments:
        if fragment not in disclosure:
            errors.append(f"Codex disclosure is missing required boundary: {fragment}")
        else:
            checked += 1
    try:
        disclosure_file = (REPOSITORY_ROOT / "docs/AI_AUTHORING_ASSISTANCE_DISCLOSURE.md").read_text(encoding="utf-8-sig")
    except OSError as exc:
        errors.append(f"Could not inspect AI disclosure: {exc}")
    else:
        if disclosure not in disclosure_file:
            errors.append("AI disclosure differs between the manifest and disclosure document.")
        else:
            checked += 1
    return checked


def _integer(row: dict[str, str], field: str, errors: list[str]) -> int:
    try:
        return int(row[field])
    except (KeyError, ValueError):
        errors.append(f"Human ICR field must be an integer: {field}")
        return 0


def _number(row: dict[str, str], field: str, errors: list[str]) -> float:
    try:
        return float(row[field])
    except (KeyError, ValueError):
        errors.append(f"Human ICR field must be numeric: {field}")
        return 0.0


def check_human_icr_aggregate(manifest: dict[str, Any], errors: list[str]) -> int:
    relative = "outputs/human_validation/human_icr_aggregate_summary.csv"
    rows = _read_rows(relative, errors)
    if len(rows) != 1:
        errors.append(f"Human ICR aggregate must contain exactly one row; found {len(rows)}")
        return 0
    row = rows[0]
    integers = {field: _integer(row, field, errors) for field in (
        "coder_count", "coordinator_count", "evidence_packet_count", "assessed_target_count",
        "decision_category_count", "paired_units", "exact_agreements", "disagreements",
        "binary_subset_units", "binary_subset_exact_agreements", "adjudicated_disagreements",
        "consensus_cases", "no_consensus_cases", "final_present", "final_absent",
        "final_ambiguous", "final_insufficient_evidence", "final_out_of_scope",
    )}
    numbers = {field: _number(row, field, errors) for field in (
        "agreement_percent", "cohen_kappa", "krippendorff_alpha_nominal",
        "binary_subset_agreement_percent", "binary_subset_cohen_kappa",
    )}
    if integers["exact_agreements"] + integers["disagreements"] != integers["paired_units"]:
        errors.append("Human ICR agreements plus disagreements must equal paired units.")
    if integers["adjudicated_disagreements"] != integers["disagreements"]:
        errors.append("All recorded disagreements must be adjudicated.")
    if integers["consensus_cases"] + integers["no_consensus_cases"] != integers["adjudicated_disagreements"]:
        errors.append("Consensus plus no-consensus cases must equal adjudicated disagreements.")
    final_total = sum(integers[field] for field in ("final_present", "final_absent", "final_ambiguous", "final_insufficient_evidence", "final_out_of_scope"))
    if final_total != integers["consensus_cases"]:
        errors.append("Final consensus categories must sum to consensus cases.")
    if round(100 * integers["exact_agreements"] / integers["paired_units"], 1) != numbers["agreement_percent"]:
        errors.append("Human ICR agreement percentage is inconsistent.")
    if round(100 * integers["binary_subset_exact_agreements"] / integers["binary_subset_units"], 1) != numbers["binary_subset_agreement_percent"]:
        errors.append("Binary subset agreement percentage is inconsistent.")
    validation = manifest.get("validation", {})
    manifest_checks = {
        "protocol_id": row.get("protocol_id"),
        "completion_date": row.get("completion_date"),
        "coder_count": integers["coder_count"],
        "coordinator_count": integers["coordinator_count"],
        "evidence_packet_count": integers["evidence_packet_count"],
        "assessed_target_count": integers["assessed_target_count"],
        "paired_case_target_units": integers["paired_units"],
        "exact_agreements": integers["exact_agreements"],
        "disagreements": integers["disagreements"],
    }
    for field, actual in manifest_checks.items():
        if validation.get(field) != actual:
            errors.append(f"Manifest human ICR field does not match aggregate: {field}")
    return len(integers) + len(numbers) + len(manifest_checks) + 5


def main() -> int:
    errors: list[str] = []
    manifest = load_manifest(errors)
    required_count = check_required_files(errors)
    python_count, json_count = check_python_and_json(errors)
    csv_count = check_csv_schemas(errors)
    manifest_count = check_manifest(manifest, errors)
    excluded_count = check_excluded_material(errors)
    privacy_count = check_text_privacy(errors)
    disclosure_count = check_ai_authoring_disclosure(manifest, errors)
    icr_count = check_human_icr_aggregate(manifest, errors)

    if errors:
        print("Repository integrity check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Repository integrity check passed.")
    print(f"- Required files checked: {required_count}")
    print(f"- Python files compiled: {python_count}")
    print(f"- JSON files validated: {json_count}")
    print(f"- Aggregate CSV schemas/privacy checked: {csv_count}")
    print(f"- Manifest phase and file references checked: {manifest_count}")
    print(f"- Files checked against excluded/restricted paths: {excluded_count}")
    print(f"- Publication-safe text files scanned for local paths: {privacy_count}")
    print(f"- AI authoring-disclosure checks: {disclosure_count}")
    print(f"- Human ICR aggregate checks: {icr_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
