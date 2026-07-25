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
    "code/derived_analysis/build_derived_analysis.py",
    "code/human_validation/build_public_icr_by_target.py",
    "code/human_validation/summarize_human_validation.py",
    "docs/ANALYSIS_PLAN.md",
    "docs/DATA_COLLECTION_PROTOCOL.md",
    "docs/HUMAN_VALIDATION_PROTOCOL.md",
    "docs/CONTROLLED_AUDIT_ACCESS.md",
    "docs/AI_AUTHORING_ASSISTANCE_DISCLOSURE.md",
    "outputs/human_validation/HUMAN_VALIDATION_STATUS.md",
    "outputs/derived_analysis/DERIVED_ANALYSIS_NOTES.md",
    "outputs/derived_analysis/derived_analysis_metadata.json",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv",
)

CSV_SCHEMAS = {
    "outputs/phase1_aggregate/entity_summary_by_source.csv": "source,entity_type,entity,hit_count",
    "outputs/phase1_aggregate/keyword_summary_by_source.csv": "source,keyword,file_count,hit_count",
    "outputs/phase1_aggregate/source_summary.csv": "source,note_count,dated_note_count,first_date,last_date,word_count,image_ref_count",
    "outputs/phase1_aggregate/top_price_amounts.csv": "currency,amount,mention_count",
    "outputs/phase2_aggregate/ocr_summary_by_source.csv": "source,image_ref_count,ocr_ok_count,ocr_empty_count,ocr_error_count,ocr_not_local_or_not_processed_count,ocr_word_count",
    "outputs/phase3_aggregate/aml_indicator_summary_by_source.csv": "aml_indicator,label,source,note_count,hit_count",
    "outputs/phase3_aggregate/criminal_objective_summary.csv": "criminal_objective,note_count,hit_count",
    "outputs/phase3_aggregate/typology_summary.csv": "code,label,criminal_objective,note_count,hit_count,high_rule_match_intensity_notes,medium_rule_match_intensity_notes,low_rule_match_intensity_notes",
    "outputs/phase3_aggregate/typology_summary_by_source.csv": "source,code,label,note_count,hit_count",
    "outputs/phase4_aggregate/aml_red_flags_summary.csv": "rank,aml_indicator,label,source_count,note_count,hit_count,interpretation",
    "outputs/phase4_aggregate/financial_crime_findings.csv": "rank,code,label,note_count,hit_count,finding,analysis,result_type,aml_or_detection_relevance",
    "outputs/phase4_aggregate/source_profile_summary.csv": "source,dominant_typology,dominant_typology_notes,top_typologies",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv": "screened_combined_records,unique_combined_text_hashes,exact_duplicate_groups,exact_duplicate_excess,maximum_duplicate_group_size,zero_combined_word_records,markdown_only_records,markdown_and_ocr_records,ocr_only_records,neither_assessable_records,explicit_exclusion_log_available,pre_analysis_deduplication_applied,eligible_unique_analytic_records",
    "outputs/derived_analysis/duplicate_sensitivity.csv": "code,label,full_screened_denominator_n,full_screened_present_n,full_screened_percent,full_screened_rank,exact_text_unique_denominator_n,exact_text_unique_present_n,exact_text_unique_percent,exact_duplicate_excess_positive_records_n,positive_count_reduction_percent,percentage_point_difference,exact_text_unique_rank,rank_change",
    "outputs/derived_analysis/service_chain_grouping.csv": "population,population_definition,mapping_status,stage,label,definition,included_codes,denominator_n,unique_records_present_n,records_present_percent",
    "outputs/derived_analysis/source_concentration.csv": "population,population_definition,denominator_n,code,label,positive_records_n,source_groups_with_positive_records_n,top_source,top_source_positive_records_n,top_source_share,top_three_source_share,source_hhi,full_rank_by_record_count",
    "outputs/derived_analysis/source_leave_one_out.csv": "population,population_definition,removed_source,code,label,remaining_denominator_n,remaining_positive_records_n,remaining_positive_percent,full_rank_by_record_count,remaining_rank_by_record_count,rank_change",
    "outputs/derived_analysis/typology_aml_crosswalk.csv": "population,population_definition,denominator_n,typology_code,typology_label,aml_candidate,aml_candidate_label,typology_present_n,aml_candidate_present_n,n11_both_present,n10_typology_only,n01_aml_only,n00_neither,jaccard,typology_share_with_candidate,candidate_share_with_typology,lift",
    "outputs/derived_analysis/typology_cooccurrence.csv": "population,population_definition,denominator_n,code_a,label_a,code_b,label_b,code_a_present_n,code_b_present_n,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift",
    "outputs/derived_analysis/typology_cooccurrence_by_source.csv": "population,population_definition,source,source_denominator_n,code_a,label_a,code_b,label_b,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift",
    "outputs/derived_analysis/typology_cooccurrence_leave_one_source_out.csv": "population,population_definition,removed_source,remaining_denominator_n,code_a,label_a,code_b,label_b,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift,full_population_n11,n11_difference,full_population_jaccard,jaccard_difference,full_population_lift,lift_difference",
    "outputs/derived_analysis/typology_source_normalized.csv": "population,population_definition,source,source_denominator_n,markdown_present_n,ocr_present_n,markdown_and_ocr_present_n,neither_modality_present_n,code,label,source_positive_records_n,within_source_percent,all_sources_positive_records_n,source_share_of_positive_records",
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
    "outputs/derived_analysis/DERIVED_ANALYSIS_NOTES.md",
    "outputs/derived_analysis/derived_analysis_metadata.json",
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


def check_release_metadata(manifest: dict[str, Any], errors: list[str]) -> int:
    project = manifest.get("project", {})
    if not isinstance(project, dict):
        errors.append("Manifest project metadata must be an object.")
        return 0
    try:
        citation = (REPOSITORY_ROOT / "CITATION.cff").read_text(encoding="utf-8-sig")
        changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    except OSError as exc:
        errors.append(f"Could not inspect release metadata: {exc}")
        return 0
    checks = {
        "title": re.search(r"(?m)^title: \"([^\"]+)\"$", citation),
        "version": re.search(r"(?m)^version: \"([^\"]+)\"$", citation),
        "repository": re.search(r"(?m)^repository-code: \"([^\"]+)\"$", citation),
        "license": re.search(r"(?m)^license: \"([^\"]+)\"$", citation),
    }
    expected = {
        "title": project.get("title"),
        "version": project.get("version"),
        "repository": project.get("repository"),
        "license": "LicenseRef-All-Rights-Reserved",
    }
    checked = 0
    for field, match in checks.items():
        actual = match.group(1) if match else None
        if actual != expected[field]:
            errors.append(f"CITATION.cff {field} does not match release metadata.")
        else:
            checked += 1
    version = str(project.get("version", ""))
    if not re.search(rf"(?m)^## {re.escape(version)} - \d{{4}}-\d{{2}}-\d{{2}}$", changelog):
        errors.append("CHANGELOG.md has no dated heading for the manifest version.")
    else:
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


def check_human_icr_by_target(manifest: dict[str, Any], errors: list[str]) -> int:
    rows = _read_rows(
    )
    if len(rows) != 18:
        errors.append(f"Human ICR target table must contain 18 rows; found {len(rows)}")
        return 0
    codes = [row.get("code", "") for row in rows]
    if any(not code for code in codes) or len(codes) != len(set(codes)):
        errors.append("Human ICR target codes must be nonblank and unique.")
    totals = {
        field: sum(_integer(row, field, errors) for row in rows)
        for field in (
            "paired_units", "exact_agreements", "disagreements",
            "binary_subset_units", "binary_subset_exact_agreements",
            "adjudicated_disagreements", "final_present", "final_absent",
            "final_ambiguous", "final_insufficient_evidence",
            "final_out_of_scope_record",
        )
    }
    for row in rows:
        code = row.get("code", "(blank)")
        paired = _integer(row, "paired_units", errors)
        agreements = _integer(row, "exact_agreements", errors)
        disagreements = _integer(row, "disagreements", errors)
        adjudicated = _integer(row, "adjudicated_disagreements", errors)
        if agreements + disagreements != paired:
            errors.append(f"Target ICR counts do not reconcile for {code}.")
        if adjudicated != disagreements:
            errors.append(f"Target adjudication count does not reconcile for {code}.")
        final_total = sum(
            _integer(row, field, errors)
            for field in (
                "final_present", "final_absent", "final_ambiguous",
                "final_insufficient_evidence", "final_out_of_scope_record",
            )
        )
        if final_total != adjudicated:
            errors.append(f"Target final decisions do not reconcile for {code}.")
        agreement = _number(row, "agreement_percent", errors)
        low = _number(row, "agreement_ci95_low_percent", errors)
        high = _number(row, "agreement_ci95_high_percent", errors)
        if not (0 <= low <= agreement <= high <= 100):
            errors.append(f"Target agreement interval is invalid for {code}.")
        for field in (
            "cohen_kappa", "cohen_kappa_bootstrap_ci95_low",
            "cohen_kappa_bootstrap_ci95_high", "krippendorff_alpha_nominal",
            "binary_subset_cohen_kappa", "binary_subset_gwet_ac1",
            "binary_subset_gwet_ac1_bootstrap_ci95_low",
            "binary_subset_gwet_ac1_bootstrap_ci95_high",
        ):
            value = _number(row, field, errors)
            if not -1 <= value <= 1:
                errors.append(f"Target reliability metric outside [-1, 1] for {code}: {field}")
    aggregate_rows = _read_rows(
    )
    if len(aggregate_rows) == 1:
        aggregate = aggregate_rows[0]
        expected = {
            "paired_units": _integer(aggregate, "paired_units", errors),
            "exact_agreements": _integer(aggregate, "exact_agreements", errors),
            "disagreements": _integer(aggregate, "disagreements", errors),
            "binary_subset_units": _integer(aggregate, "binary_subset_units", errors),
            "binary_subset_exact_agreements": _integer(aggregate, "binary_subset_exact_agreements", errors),
            "adjudicated_disagreements": _integer(aggregate, "adjudicated_disagreements", errors),
            "final_present": _integer(aggregate, "final_present", errors),
            "final_absent": _integer(aggregate, "final_absent", errors),
            "final_ambiguous": _integer(aggregate, "final_ambiguous", errors),
            "final_insufficient_evidence": _integer(aggregate, "final_insufficient_evidence", errors),
            "final_out_of_scope_record": _integer(aggregate, "final_out_of_scope", errors),
        }
        for field, value in expected.items():
            if totals[field] != value:
                errors.append(f"Target ICR totals do not match overall aggregate: {field}")
    metadata_path = REPOSITORY_ROOT / "outputs/human_validation/human_icr_target_metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not read target-level ICR metadata: {exc}")
        metadata = {}
    if metadata.get("target_count") != len(rows):
        errors.append("Target-level ICR metadata target count does not reconcile.")
    for field in ("paired_units", "disagreements", "adjudicated_disagreements"):
        if metadata.get(field) != totals[field]:
            errors.append(f"Target-level ICR metadata does not reconcile: {field}")
    input_hashes = metadata.get("controlled_input_sha256", {})
    coder_hashes = metadata.get("frozen_coder_workbook_sha256", [])
    if not isinstance(input_hashes, dict) or len(input_hashes) != 3 or any(
        not re.fullmatch(r"[0-9a-f]{64}", str(value))
        for value in input_hashes.values()
    ):
        errors.append("Target-level ICR controlled input hashes are incomplete or invalid.")
    if not isinstance(coder_hashes, list) or len(coder_hashes) != 2 or any(
        not isinstance(item, dict)
        or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")))
        for item in coder_hashes
    ):
        errors.append("Target-level ICR frozen coder workbook hashes are incomplete or invalid.")
    validation = manifest.get("validation", {})
    if isinstance(validation, dict):
        if validation.get("public_target_results") != "outputs/human_validation/human_icr_by_target.csv":
            errors.append("Manifest does not reference the public target-level ICR table.")
        if validation.get("public_target_metadata") != "outputs/human_validation/human_icr_target_metadata.json":
            errors.append("Manifest does not reference the target-level ICR metadata.")
    return len(rows) * 12 + len(totals) + 8


def check_derived_analysis(manifest: dict[str, Any], errors: list[str]) -> int:
    metadata_path = REPOSITORY_ROOT / "outputs/derived_analysis/derived_analysis_metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not read derived-analysis metadata: {exc}")
        return 0
    populations = metadata.get("population_counts", {})
    expected_populations = {
        "full_screened": 980,
        "exact_text_unique_sensitivity": 463,
    }
    if populations != expected_populations:
        errors.append(f"Unexpected derived-analysis populations: {populations}")
    corpus_counts = manifest.get("corpus_counts", {})
    if isinstance(corpus_counts, dict):
        if populations.get("full_screened") != corpus_counts.get("screened_combined_records"):
            errors.append("Derived full-screened denominator differs from manifest.")
        if populations.get("exact_text_unique_sensitivity") != corpus_counts.get("unique_combined_text_hashes"):
            errors.append("Derived exact-text denominator differs from manifest.")
    row_counts = metadata.get("output_row_counts", {})
    if not isinstance(row_counts, dict):
        errors.append("Derived-analysis metadata has no output row counts.")
        row_counts = {}
    checked = 3
    for filename, expected in row_counts.items():
        rows = _read_rows(f"outputs/derived_analysis/{filename}", errors)
        if len(rows) != expected:
            errors.append(
                f"Derived row count mismatch for {filename}: expected {expected}, found {len(rows)}"
            )
        checked += 1
    for relative, denominator_field, fields in (
        ("outputs/derived_analysis/typology_cooccurrence.csv", "denominator_n", ("n11_both_present", "n10_a_only", "n01_b_only", "n00_neither")),
        ("outputs/derived_analysis/typology_cooccurrence_by_source.csv", "source_denominator_n", ("n11_both_present", "n10_a_only", "n01_b_only", "n00_neither")),
        ("outputs/derived_analysis/typology_cooccurrence_leave_one_source_out.csv", "remaining_denominator_n", ("n11_both_present", "n10_a_only", "n01_b_only", "n00_neither")),
        ("outputs/derived_analysis/typology_aml_crosswalk.csv", "denominator_n", ("n11_both_present", "n10_typology_only", "n01_aml_only", "n00_neither")),
    ):
        for row in _read_rows(relative, errors):
            denominator = _integer(row, denominator_field, errors)
            cells = sum(_integer(row, field, errors) for field in fields)
            if cells != denominator:
                errors.append(f"Contingency cells do not sum to denominator in {relative}.")
            checked += 1
    for row in _read_rows("outputs/derived_analysis/typology_source_normalized.csv", errors):
        denominator = _integer(row, "source_denominator_n", errors)
        positive = _integer(row, "source_positive_records_n", errors)
        within_source = _number(row, "within_source_percent", errors)
        if positive > denominator or not 0 <= within_source <= 100:
            errors.append("Source-normalized typology row has invalid count or percentage.")
        checked += 1
    for row in _read_rows("outputs/derived_analysis/service_chain_grouping.csv", errors):
        if row.get("mapping_status") != "exploratory_descriptive_grouping":
            errors.append("Service-chain grouping must remain explicitly exploratory.")
        checked += 1
    hashes = metadata.get("controlled_input_sha256", {})
    if not isinstance(hashes, dict) or len(hashes) != 3:
        errors.append("Derived-analysis metadata must contain three controlled input hashes.")
    elif any(not re.fullmatch(r"[0-9a-f]{64}", str(value)) for value in hashes.values()):
        errors.append("Derived-analysis controlled input hash is invalid.")
    derived_manifest = manifest.get("derived_analysis", {})
    if not isinstance(derived_manifest, dict) or derived_manifest.get("metadata") != "outputs/derived_analysis/derived_analysis_metadata.json":
        errors.append("Manifest does not reference the derived-analysis metadata.")
    return checked + 2


def main() -> int:
    errors: list[str] = []
    manifest = load_manifest(errors)
    required_count = check_required_files(errors)
    python_count, json_count = check_python_and_json(errors)
    csv_count = check_csv_schemas(errors)
    manifest_count = check_manifest(manifest, errors)
    excluded_count = check_excluded_material(errors)
    privacy_count = check_text_privacy(errors)
    release_count = check_release_metadata(manifest, errors)
    disclosure_count = check_ai_authoring_disclosure(manifest, errors)
    icr_count = 0
    icr_target_count = 0
    derived_count = check_derived_analysis(manifest, errors)

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
    print(f"- Release metadata checks: {release_count}")
    print(f"- AI authoring-disclosure checks: {disclosure_count}")
    print("- Human validation: withdrawn pending corrected-corpus revalidation")
    print(f"- Derived-analysis checks: {derived_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
