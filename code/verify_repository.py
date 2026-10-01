"""Data-free integrity and privacy audit for the public analysis repository."""

from __future__ import annotations

import csv
import hashlib
import json
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
    "code/evidence_screening/build_evidence_corpus.py",
    "code/evidence_screening/METHODS_EVIDENCE_SCREEN.md",
    "code/ocr_quality/assess_ocr_quality.py",
    "code/ocr_quality/METHODS_OCR_QUALITY.md",
    "code/derived_analysis/build_derived_analysis.py",
    "code/derived_analysis/build_revised_pair_boundaries.py",
    "code/derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md",
    "code/derived_analysis/build_revised_duplicate_sensitivity.py",
    "code/derived_analysis/METHODS_REVISED_DUPLICATE_SENSITIVITY.md",
    "code/derived_analysis/build_revised_descriptive_tables.py",
    "code/derived_analysis/METHODS_REVISED_DESCRIPTIVES.md",
    "code/human_validation/build_public_icr_by_target.py",
    "code/human_validation/summarize_human_validation.py",
    "code/human_validation/prepare_revised_holdout.py",
    "code/human_validation/close_revised_holdout.py",
    "code/human_validation/METHODS_REVISED_HOLDOUT.md",
    "docs/ANALYSIS_PLAN.md",
    "docs/DATA_COLLECTION_PROTOCOL.md",
    "docs/HUMAN_VALIDATION_PROTOCOL.md",
    "docs/CONTROLLED_AUDIT_ACCESS.md",
    "docs/AUTHOR_DECISIONS_RECORD.md",
    "docs/JOURNAL_REPRODUCIBILITY_SUPPLEMENT.md",
    "docs/JOURNAL_INTEGRATION_CHECKLIST.md",
    "docs/POST_RELEASE_CORPUS_AUDIT_2026-10-01.md",
    "outputs/human_validation/HUMAN_VALIDATION_STATUS.md",
    "outputs/human_validation/HUMAN_ICR_COMPLETION.md",
    "outputs/human_validation/HUMAN_ICR_BY_TARGET.md",
    "outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md",
    "outputs/human_validation/human_icr_aggregate_summary.csv",
    "outputs/human_validation/human_icr_by_target.csv",
    "outputs/human_validation/human_icr_target_metadata.json",
    "outputs/human_validation/human_validation_performance.csv",
    "outputs/human_validation/human_validation_performance_metadata.json",
    "outputs/derived_analysis/DERIVED_ANALYSIS_NOTES.md",
    "outputs/derived_analysis/derived_analysis_metadata.json",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv",
    "outputs/analysis_audit/image_coverage_20261001.csv",
    "outputs/analysis_audit/record_type_sensitivity_20261001.csv",
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
    "outputs/phase4_aggregate/phase4_recommendations.csv": "priority,recommendation,reason",
    "outputs/human_validation/human_icr_aggregate_summary.csv": "completion_date,coder_count,coordinator_count,evidence_packet_count,assessed_target_count,decision_category_count,paired_units,exact_agreements,disagreements,agreement_percent,cohen_kappa,krippendorff_alpha_nominal,binary_subset_units,binary_subset_exact_agreements,binary_subset_agreement_percent,binary_subset_cohen_kappa,adjudicated_disagreements,consensus_cases,no_consensus_cases,final_present,final_absent,final_ambiguous,final_insufficient_evidence,final_out_of_scope",
    "outputs/human_validation/human_icr_by_target.csv": "code,target_group,paired_units,exact_agreements,disagreements,agreement_percent,agreement_ci95_low_percent,agreement_ci95_high_percent,cohen_kappa,cohen_kappa_bootstrap_ci95_low,cohen_kappa_bootstrap_ci95_high,krippendorff_alpha_nominal,binary_subset_units,binary_subset_exact_agreements,binary_subset_agreement_percent,binary_subset_cohen_kappa,binary_subset_gwet_ac1,binary_subset_gwet_ac1_bootstrap_ci95_low,binary_subset_gwet_ac1_bootstrap_ci95_high,adjudicated_disagreements,final_present,final_absent,final_ambiguous,final_insufficient_evidence,final_out_of_scope_record",
    "outputs/analysis_audit/corpus_screening_audit_summary.csv": "screened_combined_records,unique_combined_text_hashes,exact_duplicate_groups,exact_duplicate_excess,maximum_duplicate_group_size,zero_combined_word_records,markdown_only_records,markdown_and_ocr_records,ocr_only_records,neither_assessable_records,explicit_exclusion_log_available,pre_analysis_deduplication_applied,eligible_unique_analytic_records",
    "outputs/analysis_audit/image_coverage_20261001.csv": "historical_screened_notes,image_reference_occurrences,resolved_reference_occurrences,missing_reference_occurrences,external_reference_occurrences,referenced_local_png_paths,referenced_local_png_hashes,all_png_paths,unreferenced_png_paths,unreferenced_paths_duplicate_referenced_content,unreferenced_novel_content_files,unreferenced_novel_content_hashes",
    "outputs/analysis_audit/record_type_sensitivity_20261001.csv": "target_group,target_code,full_screened_positive_n,no_ocr_record_positive_n,ocr_linked_candidate_positive_n,joined_ocr_positive_n,markdown_exclusive_candidate_positive_n,cross_modality_only_candidate_positive_n",
    "outputs/derived_analysis/duplicate_sensitivity.csv": "code,label,full_screened_denominator_n,full_screened_present_n,full_screened_percent,full_screened_rank,exact_text_unique_denominator_n,exact_text_unique_present_n,exact_text_unique_percent,exact_duplicate_excess_positive_records_n,positive_count_reduction_percent,percentage_point_difference,exact_text_unique_rank,rank_change",
    "outputs/derived_analysis/service_chain_grouping.csv": "population,population_definition,mapping_status,stage,label,definition,included_codes,denominator_n,unique_records_present_n,records_present_percent",
    "outputs/derived_analysis/source_concentration.csv": "population,population_definition,denominator_n,code,label,positive_records_n,source_groups_with_positive_records_n,top_source,top_source_positive_records_n,top_source_share,top_three_source_share,source_hhi,full_rank_by_record_count",
    "outputs/derived_analysis/source_leave_one_out.csv": "population,population_definition,removed_source,code,label,remaining_denominator_n,remaining_positive_records_n,remaining_positive_percent,full_rank_by_record_count,remaining_rank_by_record_count,rank_change",
    "outputs/derived_analysis/typology_aml_crosswalk.csv": "population,population_definition,denominator_n,typology_code,typology_label,aml_candidate,aml_candidate_label,typology_present_n,aml_candidate_present_n,n11_both_present,n10_typology_only,n01_aml_only,n00_neither,jaccard,typology_share_with_candidate,candidate_share_with_typology,lift",
    "outputs/derived_analysis/typology_cooccurrence.csv": "population,population_definition,denominator_n,code_a,label_a,code_b,label_b,code_a_present_n,code_b_present_n,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift",
    "outputs/derived_analysis/typology_cooccurrence_by_source.csv": "population,population_definition,source,source_denominator_n,code_a,label_a,code_b,label_b,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift",
    "outputs/derived_analysis/typology_cooccurrence_leave_one_source_out.csv": "population,population_definition,removed_source,remaining_denominator_n,code_a,label_a,code_b,label_b,n11_both_present,n10_a_only,n01_b_only,n00_neither,jaccard,lift,full_population_n11,n11_difference,full_population_jaccard,jaccard_difference,full_population_lift,lift_difference",
    "outputs/derived_analysis/typology_source_normalized.csv": "population,population_definition,source,source_denominator_n,markdown_present_n,ocr_present_n,markdown_and_ocr_present_n,neither_modality_present_n,code,label,source_positive_records_n,within_source_percent,all_sources_positive_records_n,source_share_of_positive_records",
    "docs/claim_to_evidence_register.csv": "claim_id,claim_scope,approved_wording,status,primary_denominator_n,evidence_files,human_validation_boundary,sensitivity_boundary,prohibited_inference",
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
    "note_decisions.csv",
    "image_decisions.csv",
    "source_segments.csv",
    "approved_evidence_units.jsonl",
    "evidence_build_manifest.json",
    "artifact_coding_long.csv",
    "revised_typology_pair_boundaries.csv",
    "revised_typology_pair_manifest.json",
    "review_inventory.json",
    "ocr_quality_sample.csv",
    "sample_manifest.json",
    "review_images_manifest.json",
    "transcript_lock_manifest.json",
    "per_image_ocr_quality_controlled.csv",
    "ocr_quality_report.json",
    "pilot_units.csv",
    "validation_frame.csv",
    "frame_manifest.json",
    "allocation_plan_template.json",
    "approved_allocation_plan.json",
    "coordinator_machine_key.csv",
    "coder_1_blank.csv",
    "coder_2_blank.csv",
    "selection_manifest.json",
    "packet_manifest_template.csv",
    "packet_manifest.csv",
    "coder_1.csv",
    "coder_2.csv",
    "coder_lock_manifest.json",
    "reference_decisions_template.csv",
    "reference_template_manifest.json",
    "reference_decisions.csv",
    "reference_lock_manifest.json",
    "revised_holdout_performance_controlled.csv",
    "revised_holdout_score_manifest.json",
    "revised_duplicate_sensitivity_controlled.csv",
    "revised_source_signature_summary_controlled.csv",
    "revised_duplicate_manifest.json",
    "revised_screen_flow_controlled.csv",
    "revised_source_coverage_controlled.csv",
    "revised_target_prevalence_controlled.csv",
    "revised_modality_contribution_controlled.csv",
    "revised_typology_cooccurrence_controlled.csv",
    "revised_source_concentration_controlled.csv",
    "revised_leave_one_source_out_controlled.csv",
    "revised_descriptive_manifest.json",
}
PUBLIC_TEXT_SUFFIXES = {".md", ".txt", ".py", ".json", ".yml", ".yaml", ".cff", ".csv"}
PUBLIC_EXTENSIONLESS_FILES = {".gitignore", ".gitattributes"}
BLOCKED_EXACT_FIELDS = {"note_id", "legacy_note_id", "record_id", "unit_id", "case_id", "duplicate_cluster_hash", "source_unit_sha256", "packet_file", "packet_sha256", "source_path", "local_path", "absolute_path", "capture_date_record_locator"}
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
                source = path.read_text(encoding="utf-8-sig")
                compile(source, str(path), "exec")
                python_count += 1
            except (OSError, UnicodeError, SyntaxError) as exc:
                errors.append(f"Python syntax error in {relative}: {exc}")
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
        elif file_path.suffix.casefold() not in PUBLIC_TEXT_SUFFIXES and file_path.name not in PUBLIC_EXTENSIONLESS_FILES:
            errors.append(f"Unapproved public file type is present: {relative.as_posix()}")
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


def check_journal_reproducibility_supplement(
    manifest: dict[str, Any], errors: list[str]
) -> int:
    section = manifest.get("journal_reproducibility_supplement", {})
    if not isinstance(section, dict):
        errors.append("Manifest journal reproducibility supplement must be an object.")
        return 0

    checked = 0
    expected_values = {
        "repository_role": "journal-neutral reproducibility supplement",
        "repository_status": "methodological hold pending evidence-only reanalysis",
        "supplement_submission_ready": False,
        "readiness_scope": (
            "Historical computations are retained for audit; substantive article use "
            "requires author-reviewed corpus eligibility, image linkage, OCR quality, "
            "revised analyses, and validation."
        ),
        "manuscript_included": False,
        "primary_descriptive_denominator_n": 980,
        "exact_text_sensitivity_denominator_n": 463,
        "external_prevalence_claims_permitted": False,
        "author_confirmation_date": "2026-08-22",
    }
    for field, expected in expected_values.items():
        if section.get(field) != expected:
            errors.append(
                f"Journal supplement field {field} must be {expected!r}."
            )
        else:
            checked += 1

    audit = manifest.get("post_release_corpus_audit", {})
    expected_audit = {
        "status": "methodological_hold_pending_evidence_only_reanalysis",
        "historical_screened_notes": 980,
        "filename_date_like_notes": 948,
        "valid_filename_calendar_dates": 947,
        "invalid_filename_calendar_dates": 1,
        "filename_date_undated_notes": 32,
        "filename_dates_capture_verified": False,
        "controlled_collection_provenance_packet_prepared": True,
        "collection_provenance_author_confirmed": False,
        "planned_source_groups_in_internal_protocol": 15,
        "historical_source_groups_represented": 16,
        "actual_collection_start_verified": False,
        "actual_daily_visit_schedule_verified": False,
        "comparable_note_image_filename_date_pairs": 1032,
        "same_day_note_image_filename_pairs": 704,
        "different_day_note_image_filename_pairs": 328,
        "image_filename_earlier_pairs": 9,
        "image_filename_later_pairs": 319,
        "image_filename_later_over_30_days_pairs": 16,
        "unparseable_linked_image_filename_times": 15,
        "blank_linked_note_filename_date_assignments": 1,
        "timestamp_priority_review_rows": 41,
        "filename_timestamp_meaning_author_confirmed": False,
        "png_paths_embedded_metadata_checked": 1101,
        "png_software_text_chunks": 1096,
        "png_exif_chunks": 0,
        "png_time_chunks": 0,
        "png_embedded_numeric_date_candidates": 0,
        "png_metadata_capture_dates_verified": False,
        "no_ocr_research_or_collection_notes_preliminary": 589,
        "ocr_linked_candidate_notes_pending_review": 391,
        "unreferenced_png_paths": 58,
        "unreferenced_novel_content_hashes": 35,
        "historical_validation_case_target_rows_from_no_ocr_notes": 191,
        "final_evidence_only_denominator": None,
        "author_eligibility_adjudication_complete": False,
        "ocr_accuracy_gold_set_complete": False,
        "revised_human_validation_complete": False,
    }
    if not isinstance(audit, dict):
        errors.append("Post-release corpus audit must be an object.")
        audit = {}
    for field, expected in expected_audit.items():
        if audit.get(field) != expected:
            errors.append(f"Post-release audit field {field} must be {expected!r}.")
        else:
            checked += 1
    evidence_gate = manifest.get("revised_evidence_screening_gate", {})
    for field, expected in {
        "status": "review_template_prepared_author_decisions_pending",
        "review_schema_version": 3,
        "script": "code/evidence_screening/build_evidence_corpus.py",
        "method": "code/evidence_screening/METHODS_EVIDENCE_SCREEN.md",
        "review_templates_controlled_only": True,
        "historical_outputs_modified": False,
        "revised_evidence_units_approved": None,
        "article_ready": False,
    }.items():
        if not isinstance(evidence_gate, dict) or evidence_gate.get(field) != expected:
            errors.append(f"Revised evidence-screening gate {field} is missing or incorrect.")
        else:
            checked += 1
    revised_pairs = manifest.get("revised_pair_boundary_diagnostic", {})
    for field, expected in {
        "status": "code_available_author_reviewed_evidence_pending",
        "script": "code/derived_analysis/build_revised_pair_boundaries.py",
        "method": "code/derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md",
        "span_coding_output_controlled_only": True,
        "historical_outputs_modified": False,
        "revised_pair_counts_complete": False,
        "article_ready": False,
    }.items():
        if not isinstance(revised_pairs, dict) or revised_pairs.get(field) != expected:
            errors.append(f"Revised pair-boundary diagnostic {field} is missing or incorrect.")
        else:
            checked += 1
    revised_duplicates = manifest.get("revised_duplicate_sensitivity", {})
    for field, expected in {
        "status": "code_available_author_reviewed_evidence_pending",
        "script": "code/derived_analysis/build_revised_duplicate_sensitivity.py",
        "method": "code/derived_analysis/METHODS_REVISED_DUPLICATE_SENSITIVITY.md",
        "outputs_controlled_only": True,
        "historical_outputs_modified": False,
        "revised_duplicate_counts_complete": False,
        "article_ready": False,
    }.items():
        if not isinstance(revised_duplicates, dict) or revised_duplicates.get(field) != expected:
            errors.append(f"Revised duplicate-sensitivity {field} is missing or incorrect.")
        else:
            checked += 1
    revised_descriptives = manifest.get("revised_descriptive_tables", {})
    for field, expected in {
        "status": "code_available_author_reviewed_evidence_and_target_validation_pending",
        "script": "code/derived_analysis/build_revised_descriptive_tables.py",
        "method": "code/derived_analysis/METHODS_REVISED_DESCRIPTIVES.md",
        "outputs_controlled_only": True,
        "historical_outputs_modified": False,
        "revised_study_tables_complete": False,
        "article_ready": False,
    }.items():
        if not isinstance(revised_descriptives, dict) or revised_descriptives.get(field) != expected:
            errors.append(f"Revised descriptive tables {field} is missing or incorrect.")
        else:
            checked += 1
    revised_holdout = manifest.get("revised_human_holdout", {})
    for field, expected in {
        "status": "sampler_and_scorer_available_author_reviewed_evidence_and_target_definitions_pending",
        "script": "code/human_validation/prepare_revised_holdout.py",
        "scorer": "code/human_validation/close_revised_holdout.py",
        "method": "code/human_validation/METHODS_REVISED_HOLDOUT.md",
        "short_predicted_negative_records_eligible": True,
        "hash_bound_author_approved_plan_required": True,
        "controlled_frame_and_coder_sheets_in_repository": False,
        "revised_holdout_drawn": False,
        "human_decision_and_reference_locks_complete": False,
        "revised_human_decisions_complete": False,
        "revised_performance_estimates_complete": False,
        "article_ready": False,
    }.items():
        if not isinstance(revised_holdout, dict) or revised_holdout.get(field) != expected:
            errors.append(f"Revised human holdout {field} is missing or incorrect.")
        else:
            checked += 1
    ocr_quality = manifest.get("ocr_quality_assessment", {})
    for field, expected in {
        "status": "blinded_probability_sample_prepared_human_transcripts_pending",
        "script": "code/ocr_quality/assess_ocr_quality.py",
        "method": "code/ocr_quality/METHODS_OCR_QUALITY.md",
        "historical_referenced_image_hashes": 1037,
        "source_strata": 15,
        "probability_sample_images": 50,
        "transcript_lock_required": True,
        "human_transcripts_locked": False,
        "human_transcripts_complete": False,
        "character_word_error_estimates_complete": False,
        "final_approved_corpus_coverage_confirmed": False,
        "controlled_review_images_in_repository": False,
    }.items():
        if not isinstance(ocr_quality, dict) or ocr_quality.get(field) != expected:
            errors.append(f"OCR-quality assessment {field} is missing or incorrect.")
        else:
            checked += 1
    if (
        audit.get("no_ocr_research_or_collection_notes_preliminary", 0)
        + audit.get("ocr_linked_candidate_notes_pending_review", 0)
        != audit.get("historical_screened_notes")
    ):
        errors.append("Post-release audit note counts do not reconcile.")
    else:
        checked += 1
    if (
        audit.get("same_day_note_image_filename_pairs", 0)
        + audit.get("different_day_note_image_filename_pairs", 0)
        != audit.get("comparable_note_image_filename_date_pairs")
        or audit.get("image_filename_earlier_pairs", 0)
        + audit.get("image_filename_later_pairs", 0)
        != audit.get("different_day_note_image_filename_pairs")
        or audit.get("comparable_note_image_filename_date_pairs", 0)
        + audit.get("unparseable_linked_image_filename_times", 0)
        + audit.get("blank_linked_note_filename_date_assignments", 0)
        != 1048
        or audit.get("image_filename_earlier_pairs", 0)
        + audit.get("image_filename_later_over_30_days_pairs", 0)
        + audit.get("unparseable_linked_image_filename_times", 0)
        + audit.get("blank_linked_note_filename_date_assignments", 0)
        != audit.get("timestamp_priority_review_rows")
    ):
        errors.append("Post-release audit filename-concordance counts do not reconcile.")
    else:
        checked += 1
    if (
        audit.get("valid_filename_calendar_dates", 0)
        + audit.get("invalid_filename_calendar_dates", 0)
        != audit.get("filename_date_like_notes")
        or audit.get("filename_date_like_notes", 0)
        + audit.get("filename_date_undated_notes", 0)
        != audit.get("historical_screened_notes")
    ):
        errors.append("Post-release audit filename-date counts do not reconcile.")
    else:
        checked += 1
    for field, expected in {
        "public_report": "docs/POST_RELEASE_CORPUS_AUDIT_2026-10-01.md",
        "image_coverage_aggregate": "outputs/analysis_audit/image_coverage_20261001.csv",
        "record_type_sensitivity_aggregate": "outputs/analysis_audit/record_type_sensitivity_20261001.csv",
    }.items():
        if audit.get(field) != expected:
            errors.append(f"Post-release audit file {field} is missing or incorrect.")
        else:
            checked += 1
    image_rows = _read_rows("outputs/analysis_audit/image_coverage_20261001.csv", errors)
    if len(image_rows) != 1:
        errors.append("Post-release image coverage audit must have one row.")
    else:
        image_row = image_rows[0]
        for field, expected in {
            "historical_screened_notes": "980",
            "image_reference_occurrences": "1140",
            "resolved_reference_occurrences": "1048",
            "missing_reference_occurrences": "7",
            "external_reference_occurrences": "85",
            "referenced_local_png_paths": "1043",
            "referenced_local_png_hashes": "1037",
            "all_png_paths": "1101",
            "unreferenced_png_paths": "58",
            "unreferenced_paths_duplicate_referenced_content": "22",
            "unreferenced_novel_content_files": "36",
            "unreferenced_novel_content_hashes": "35",
        }.items():
            if image_row.get(field) != expected:
                errors.append(f"Post-release image audit {field} must be {expected}.")
            else:
                checked += 1
    impact_rows = _read_rows("outputs/analysis_audit/record_type_sensitivity_20261001.csv", errors)
    if len(impact_rows) != 18:
        errors.append("Post-release record-type sensitivity must include 18 historically positive targets.")
    else:
        for row in impact_rows:
            try:
                full_n = int(row["full_screened_positive_n"])
                no_ocr_n = int(row["no_ocr_record_positive_n"])
                candidate_n = int(row["ocr_linked_candidate_positive_n"])
                joined_n = int(row["joined_ocr_positive_n"])
                markdown_only_n = int(row["markdown_exclusive_candidate_positive_n"])
                cross_n = int(row["cross_modality_only_candidate_positive_n"])
            except (KeyError, TypeError, ValueError):
                errors.append("Post-release record-type sensitivity has non-integer counts.")
                break
            if full_n != no_ocr_n + candidate_n or candidate_n != joined_n + markdown_only_n + cross_n:
                errors.append("Post-release record-type sensitivity counts do not reconcile.")
                break
        else:
            checked += 1

    primary_unit = str(section.get("primary_analysis_unit", ""))
    normalized_primary_unit = primary_unit.casefold()
    forbidden_primary_units = (
        "unique post",
        "unique listing",
        "unique actor",
        "unique transaction",
        "unique offender",
        "unique victim",
        "eligible evidence unit",
    )
    if (
        "screened combined note record" not in normalized_primary_unit
        or any(term in normalized_primary_unit for term in forbidden_primary_units)
    ):
        errors.append(
            "Journal supplement primary unit must be a screened combined note record, "
            "not a unique post, listing, actor, or transaction."
        )
    else:
        checked += 1

    corpus_counts_value = manifest.get("corpus_counts", {})
    corpus_counts = corpus_counts_value if isinstance(corpus_counts_value, dict) else {}
    if not isinstance(corpus_counts_value, dict) or (
        section.get("primary_descriptive_denominator_n")
        != corpus_counts.get("screened_combined_records")
    ):
        errors.append("Journal supplement primary denominator differs from the corpus manifest.")
    else:
        checked += 1
    if not isinstance(corpus_counts_value, dict) or (
        section.get("exact_text_sensitivity_denominator_n")
        != corpus_counts.get("unique_combined_text_hashes")
    ):
        errors.append("Journal supplement sensitivity denominator differs from the corpus manifest.")
    else:
        checked += 1
    try:
        source_archive_n = int(corpus_counts.get("source_archive_markdown_files"))
        structurally_excluded_n = int(
            corpus_counts.get("structurally_excluded_internal_admin_files")
        )
        screened_n = int(corpus_counts.get("screened_combined_records"))
    except (TypeError, ValueError):
        errors.append("Journal supplement corpus-flow counts must be integers.")
    else:
        if source_archive_n - structurally_excluded_n != screened_n:
            errors.append("Journal supplement corpus-flow counts do not reconcile.")
        else:
            checked += 1

    screening_audit = manifest.get("screening_audit", {})
    expected_screening_audit = {
        "primary_descriptive_denominator_n": 980,
        "explicit_exclusion_log_available": False,
        "pre_analysis_deduplication_applied": False,
        "eligible_unique_analytic_records": None,
    }
    if not isinstance(screening_audit, dict):
        errors.append("Manifest screening audit must be an object.")
    else:
        for field, expected in expected_screening_audit.items():
            if screening_audit.get(field) != expected:
                errors.append(
                    f"Screening audit field {field} must be {expected!r}."
                )
            else:
                checked += 1

    audit_rows = _read_rows(
        "outputs/analysis_audit/corpus_screening_audit_summary.csv", errors
    )
    if len(audit_rows) != 1:
        errors.append("Corpus screening audit must contain exactly one summary row.")
    else:
        audit_row = audit_rows[0]
        expected_audit_row = {
            "screened_combined_records": str(
                corpus_counts.get("screened_combined_records")
            ),
            "unique_combined_text_hashes": str(
                corpus_counts.get("unique_combined_text_hashes")
            ),
            "exact_duplicate_groups": str(
                corpus_counts.get("exact_duplicate_groups")
            ),
            "exact_duplicate_excess": str(
                corpus_counts.get("exact_duplicate_excess")
            ),
            "zero_combined_word_records": str(
                corpus_counts.get("zero_combined_word_records")
            ),
            "neither_assessable_records": str(
                corpus_counts.get("zero_combined_word_records")
            ),
            "explicit_exclusion_log_available": "no",
            "pre_analysis_deduplication_applied": "no",
            "eligible_unique_analytic_records": "",
        }
        for field, expected in expected_audit_row.items():
            if audit_row.get(field) != expected:
                errors.append(
                    f"Corpus screening audit field {field} must be {expected!r}."
                )
            else:
                checked += 1
        try:
            modality_total = sum(
                int(audit_row[field])
                for field in (
                    "markdown_only_records",
                    "markdown_and_ocr_records",
                    "ocr_only_records",
                    "neither_assessable_records",
                )
            )
        except (KeyError, TypeError, ValueError):
            errors.append("Corpus screening audit modality counts must be integers.")
        else:
            if modality_total != corpus_counts.get("screened_combined_records"):
                errors.append("Corpus screening audit modality counts do not reconcile.")
            else:
                checked += 1

    validation = manifest.get("validation", {})
    expected_validation = {
        "ethics_approval": "Griffith University Human Ethics Protocol 2025/697",
        "coder_expertise": (
            "Both coders were author-confirmed subject-matter experts; "
            "Milind Tiwari also has AML expertise."
        ),
        "sample_size_plan_author_confirmed": True,
        "independent_external_aml_review_claimed": False,
    }
    if not isinstance(validation, dict):
        errors.append("Manifest validation record must be an object.")
    else:
        for field, expected in expected_validation.items():
            if validation.get(field) != expected:
                if field == "independent_external_aml_review_claimed":
                    errors.append(
                        "The repository must not claim an independent external AML review."
                    )
                else:
                    errors.append(
                        f"Journal supplement validation field {field} must be {expected!r}."
                    )
            else:
                checked += 1

    expected_outside_scope = {
        "target journal policy and review model",
        "final citation and authorship metadata",
        "manuscript declarations",
        "rights licence and archival DOI",
    }
    outside_scope = section.get(
        "journal_specific_items_outside_supplement_scope", []
    )
    if (
        not isinstance(outside_scope, list)
        or set(outside_scope) != expected_outside_scope
    ):
        errors.append("Journal supplement outside-scope handoff items are incomplete.")
    else:
        checked += 1

    expected_files = {
        "reviewer_landing_page": "docs/JOURNAL_REPRODUCIBILITY_SUPPLEMENT.md",
        "author_decisions": "docs/AUTHOR_DECISIONS_RECORD.md",
        "integration_checklist": "docs/JOURNAL_INTEGRATION_CHECKLIST.md",
        "claim_register": "docs/claim_to_evidence_register.csv",
    }
    files = section.get("files", {})
    if not isinstance(files, dict) or files != expected_files:
        errors.append("Journal supplement file map is incomplete or incorrect.")
    else:
        checked += 1

    rows = _read_rows(expected_files["claim_register"], errors)
    allowed_statuses = {
        "supported_descriptive",
        "qualified_descriptive",
        "exploratory_only",
        "not_supported",
    }
    identifiers = [row.get("claim_id", "") for row in rows]
    if len(rows) < 8 or len(identifiers) != len(set(identifiers)) or any(
        not identifier for identifier in identifiers
    ):
        errors.append("Claim-to-evidence register must contain at least eight unique claims.")
    else:
        checked += 1
    for row in rows:
        row_id = row.get("claim_id", "")
        row_valid = True
        if row.get("status") not in allowed_statuses:
            errors.append(
                f"Claim-to-evidence register has invalid status for {row_id}."
            )
            row_valid = False
        required_boundary_fields = (
            "claim_scope",
            "approved_wording",
            "human_validation_boundary",
            "sensitivity_boundary",
            "prohibited_inference",
        )
        if any(not row.get(field, "").strip() for field in required_boundary_fields):
            errors.append(
                f"Claim-to-evidence register has an incomplete boundary for {row_id}."
            )
            row_valid = False
        try:
            denominator_n = int(row.get("primary_denominator_n", ""))
        except (TypeError, ValueError):
            denominator_n = 0
        if denominator_n <= 0:
            errors.append(
                f"Claim-to-evidence register has an invalid denominator for {row_id}."
            )
            row_valid = False
        evidence_files = [
            value.strip()
            for value in row.get("evidence_files", "").split(";")
            if value.strip()
        ]
        if not evidence_files:
            errors.append(
                f"Claim-to-evidence register has no evidence files for {row_id}."
            )
            row_valid = False
        for evidence_file in evidence_files:
            evidence_path = Path(evidence_file)
            if (
                evidence_path.is_absolute()
                or ".." in evidence_path.parts
                or not (REPOSITORY_ROOT / evidence_path).is_file()
            ):
                errors.append(
                    f"Claim-to-evidence register references an invalid file for {row_id}: "
                    f"{evidence_file}"
                )
                row_valid = False
        if row_valid:
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


def _optional_number(
    row: dict[str, str], field: str, errors: list[str]
) -> float | None:
    raw = row.get(field, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        errors.append(f"Human ICR field must be numeric or blank: {field}")
        return None


def _sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (REPOSITORY_ROOT / relative).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_normalized_text_bytes(data: bytes) -> str:
    """Hash text content after canonicalising CRLF and CR line endings to LF."""
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _sha256_text(relative: str) -> str:
    return _sha256_normalized_text_bytes((REPOSITORY_ROOT / relative).read_bytes())


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
        "outputs/human_validation/human_icr_by_target.csv", errors
    )
    if len(rows) != 18:
        errors.append(f"Human ICR target table must contain 18 rows; found {len(rows)}")
        return 0
    codes = [row.get("code", "") for row in rows]
    if any(not code for code in codes) or len(codes) != len(set(codes)):
        errors.append("Human ICR target codes must be nonblank and unique.")
    if any(row.get("target_group") not in {"typology", "aml_candidate"} for row in rows):
        errors.append("Human ICR target groups must be typology or aml_candidate.")
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
        metrics = {
            field: _optional_number(row, field, errors)
            for field in (
            "cohen_kappa", "cohen_kappa_bootstrap_ci95_low",
            "cohen_kappa_bootstrap_ci95_high", "krippendorff_alpha_nominal",
            "binary_subset_cohen_kappa", "binary_subset_gwet_ac1",
            "binary_subset_gwet_ac1_bootstrap_ci95_low",
            "binary_subset_gwet_ac1_bootstrap_ci95_high",
            )
        }
        for field, value in metrics.items():
            if value is None:
                continue
            if not -1 <= value <= 1:
                errors.append(f"Target reliability metric outside [-1, 1] for {code}: {field}")
        for low_field, high_field in (
            ("cohen_kappa_bootstrap_ci95_low", "cohen_kappa_bootstrap_ci95_high"),
            (
                "binary_subset_gwet_ac1_bootstrap_ci95_low",
                "binary_subset_gwet_ac1_bootstrap_ci95_high",
            ),
        ):
            low_metric = metrics[low_field]
            high_metric = metrics[high_field]
            if (low_metric is None) != (high_metric is None):
                errors.append(f"Target reliability interval is incomplete for {code}.")
            elif low_metric is not None and high_metric is not None and low_metric > high_metric:
                errors.append(f"Target reliability interval is reversed for {code}.")
    aggregate_rows = _read_rows(
        "outputs/human_validation/human_icr_aggregate_summary.csv", errors
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


def check_human_validation_performance(
    manifest: dict[str, Any], errors: list[str]
) -> int:
    relative = "outputs/human_validation/human_validation_performance.csv"
    rows = _read_rows(relative, errors)
    if len(rows) != 19:
        errors.append(
            f"Human-validation performance table must contain 19 rows; found {len(rows)}"
        )
        return 0
    required_fields = {
        "scope", "target_type", "code", "sample_case_target_units_n",
        "coder_pair_complete_n", "agreement_n", "agreement_rate",
        "agreement_ci95_low", "agreement_ci95_high", "kappa_evaluable_n",
        "cohen_kappa", "gwet_ac1", "unresolved_n", "final_present_n",
        "final_absent_n", "final_ambiguous_n",
        "final_insufficient_evidence_n", "final_out_of_scope_record_n",
        "excluded_from_confusion_n", "confusion_evaluable_n", "tp", "fp",
        "tn", "fn", "accuracy", "analysis_weight_supplied_n",
        "weighted_confusion_weight_sum", "weighted_tp", "weighted_fp",
        "weighted_tn", "weighted_fn", "weighted_accuracy",
    }
    header = set(rows[0])
    missing = sorted(required_fields - header)
    if missing:
        errors.append(
            "Human-validation performance table is missing fields: "
            + ", ".join(missing)
        )
    blocked = blocked_public_fields(list(rows[0]))
    if blocked:
        errors.append(
            "Blocked public fields in human-validation performance table: "
            + ", ".join(blocked)
        )

    overall_rows = [row for row in rows if row.get("scope") == "overall"]
    target_rows = [row for row in rows if row.get("scope") == "target"]
    if len(overall_rows) != 1 or len(target_rows) != 18:
        errors.append("Human-validation performance table must have one overall and 18 target rows.")
        return len(rows)
    target_keys = [
        (row.get("target_type", ""), row.get("code", "")) for row in target_rows
    ]
    if any(
        target_type not in {"typology", "aml_candidate"} or not code
        for target_type, code in target_keys
    ) or len(target_keys) != len(set(target_keys)):
        errors.append("Human-validation performance target keys must be valid and unique.")

    overall = overall_rows[0]
    integer_fields = (
        "sample_case_target_units_n", "coder_pair_complete_n", "agreement_n",
        "kappa_evaluable_n", "unresolved_n", "final_present_n",
        "final_absent_n", "final_ambiguous_n",
        "final_insufficient_evidence_n", "final_out_of_scope_record_n",
        "excluded_from_confusion_n", "confusion_evaluable_n", "tp", "fp",
        "tn", "fn", "analysis_weight_supplied_n",
    )
    integers = {field: _integer(overall, field, errors) for field in integer_fields}
    expected_integers = {
        "sample_case_target_units_n": 1032,
        "coder_pair_complete_n": 1032,
        "agreement_n": 981,
        "kappa_evaluable_n": 998,
        "unresolved_n": 0,
        "confusion_evaluable_n": 1030,
        "analysis_weight_supplied_n": 1032,
    }
    for field, expected in expected_integers.items():
        if integers[field] != expected:
            errors.append(
                f"Unexpected overall human-validation performance count for {field}: "
                f"{integers[field]}"
            )
    final_total = sum(
        integers[field]
        for field in (
            "final_present_n", "final_absent_n", "final_ambiguous_n",
            "final_insufficient_evidence_n", "final_out_of_scope_record_n",
        )
    )
    if final_total + integers["unresolved_n"] != integers["sample_case_target_units_n"]:
        errors.append("Final human-validation outcomes do not sum to the sampled units.")
    confusion_total = sum(integers[field] for field in ("tp", "fp", "tn", "fn"))
    if confusion_total != integers["confusion_evaluable_n"]:
        errors.append("Human-validation confusion cells do not sum to evaluable units.")
    if (
        integers["confusion_evaluable_n"]
        + integers["excluded_from_confusion_n"]
        != integers["sample_case_target_units_n"]
    ):
        errors.append("Evaluable and excluded human-validation units do not reconcile.")

    agreement = _number(overall, "agreement_rate", errors)
    agreement_low = _number(overall, "agreement_ci95_low", errors)
    agreement_high = _number(overall, "agreement_ci95_high", errors)
    accuracy = _number(overall, "accuracy", errors)
    if not 0 <= agreement_low <= agreement <= agreement_high <= 1:
        errors.append("Overall human-validation agreement interval is invalid.")
    if abs(
        agreement
        - integers["agreement_n"] / integers["sample_case_target_units_n"]
    ) > 1e-6:
        errors.append("Overall human-validation agreement rate is inconsistent.")
    expected_accuracy = (
        (integers["tp"] + integers["tn"]) / integers["confusion_evaluable_n"]
    )
    if abs(accuracy - expected_accuracy) > 1e-6:
        errors.append("Overall human-validation accuracy is inconsistent.")

    weighted_fields = (
        "weighted_confusion_weight_sum", "weighted_tp", "weighted_fp",
        "weighted_tn", "weighted_fn", "weighted_accuracy",
    )
    weighted = {field: _number(overall, field, errors) for field in weighted_fields}
    weighted_cells = sum(
        weighted[field] for field in ("weighted_tp", "weighted_fp", "weighted_tn", "weighted_fn")
    )
    if abs(weighted_cells - weighted["weighted_confusion_weight_sum"]) > 1e-6:
        errors.append("Weighted human-validation confusion cells do not reconcile.")
    expected_weighted_accuracy = (
        (weighted["weighted_tp"] + weighted["weighted_tn"]) / weighted_cells
        if weighted_cells
        else 0.0
    )
    if abs(weighted["weighted_accuracy"] - expected_weighted_accuracy) > 1e-6:
        errors.append("Weighted human-validation accuracy is inconsistent.")

    metadata_relative = (
        "outputs/human_validation/human_validation_performance_metadata.json"
    )
    try:
        metadata = json.loads(
            (REPOSITORY_ROOT / metadata_relative).read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Could not read human-validation performance metadata: {exc}")
        metadata = {}
    validation = manifest.get("validation", {})
    expected_coders = ["Ausma Bernot", "Milind Tiwari"]
    if metadata.get("coders") != expected_coders:
        errors.append("Human-validation performance metadata has unexpected coder names.")
    if not isinstance(validation, dict) or validation.get("coders") != expected_coders:
        errors.append("Manifest must identify Ausma Bernot and Milind Tiwari as coders.")
    if metadata.get("adjudication_supplied") is not True:
        errors.append("Human-validation performance metadata must record adjudication.")
    if metadata.get("aggregate_rows") != len(rows):
        errors.append("Human-validation performance metadata row count does not reconcile.")
    if (
        metadata.get("sample_case_target_units")
        != integers["sample_case_target_units_n"]
    ):
        errors.append("Human-validation performance metadata sample count does not reconcile.")
    input_hashes = metadata.get("controlled_input_sha256", {})
    if not isinstance(input_hashes, dict) or len(input_hashes) != 4 or any(
        not re.fullmatch(r"[0-9a-f]{64}", str(value))
        for value in input_hashes.values()
    ):
        errors.append("Human-validation performance controlled input hashes are invalid.")
    public_hashes = metadata.get("public_output_sha256", {})
    if metadata.get("public_output_hash_method") != (
        "SHA-256 after CRLF and CR line endings are normalized to LF"
    ):
        errors.append("Human-validation performance public output hash method is invalid.")
    expected_hash_paths = {
        "human_validation_performance.csv": relative,
        "HUMAN_VALIDATION_PERFORMANCE.md": (
            "outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md"
        ),
    }
    if not isinstance(public_hashes, dict) or set(public_hashes) != set(expected_hash_paths):
        errors.append("Human-validation performance public output hashes are incomplete.")
    else:
        for filename, output_relative in expected_hash_paths.items():
            try:
                actual_hash = _sha256_text(output_relative)
            except OSError as exc:
                errors.append(f"Could not hash {output_relative}: {exc}")
                continue
            if public_hashes.get(filename) != actual_hash:
                errors.append(f"Human-validation performance output hash is stale: {filename}")
    expected_manifest_paths = {
        "public_performance_results": relative,
        "public_performance_report": "outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md",
        "public_performance_metadata": metadata_relative,
    }
    if isinstance(validation, dict):
        for field, expected in expected_manifest_paths.items():
            if validation.get(field) != expected:
                errors.append(f"Manifest human-validation performance path is incorrect: {field}")
    return len(rows) * 4 + len(integers) + len(weighted) + 18


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
    journal_count = check_journal_reproducibility_supplement(manifest, errors)
    icr_count = check_human_icr_aggregate(manifest, errors)
    icr_target_count = check_human_icr_by_target(manifest, errors)
    performance_count = check_human_validation_performance(manifest, errors)
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
    print(f"- Journal reproducibility-supplement checks: {journal_count}")
    print(f"- Aggregate human-validation checks: {icr_count}")
    print(f"- Target-level human-validation checks: {icr_target_count}")
    print(f"- Human-validation performance checks: {performance_count}")
    print(f"- Derived-analysis checks: {derived_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
