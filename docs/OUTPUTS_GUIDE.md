# Outputs Guide

All committed outputs are aggregate and publication-safe. Raw and record-level material is excluded.

## Phase 1

`outputs/phase1_aggregate/` contains source totals, keyword totals, entity-like aggregate counts, price summaries, run totals, and a checkpoint summary.

## Phase 2

`outputs/phase2_aggregate/` contains aggregate OCR coverage by source and a checkpoint summary. It contains no screenshot or OCR text.

## Phase 3

`outputs/phase3_aggregate/` contains the deterministic codebook, typology summaries, source summaries, criminal-objective summaries, AML-candidate summaries, an analytical overview, and a checkpoint summary. It contains no note-level coding or evidence snippets.

## Phase 4

`outputs/phase4_aggregate/` contains deterministic aggregate findings, AML-candidate summaries, source profiles, run metadata, an analysis report, and a checkpoint summary.

## Deterministic Derived Analysis

`outputs/derived_analysis/` contains publication-safe duplicate-sensitivity, source-normalized typology, co-occurrence, co-occurrence source-stability, typology-to-AML-candidate overlap, exploratory functional-grouping, source-concentration, and leave-one-source-out tables. The 463-record exact-text-unique population is explicitly a sensitivity population, not a verified final eligible population. See `DERIVED_ANALYSIS_NOTES.md` for formulas and evidence boundaries.

## Human Validation

`outputs/human_validation/` contains the public completion narrative, overall aggregate ICR and adjudication totals, the aggregate validation sampling summary, and target-level agreement intervals, kappa, binary Gwet AC1, and adjudication totals. The folder also contains file-level SHA-256 provenance metadata for the target report. It contains no coder-level decisions, rationales, identifiers, signatures, or evidence.

## Screening Audit

`outputs/analysis_audit/` contains aggregate screening and exact-text duplicate-audit totals. Text hashes are used only for sensitivity accounting and are not released.

## Excluded Outputs

The repository excludes article-ready manuscript tables, article drafts, submission files, Phase 3b, Phase 4b, Phase 5, LLM-assisted empirical outputs, raw notes, screenshots, OCR text, evidence snippets, note-level rows, coding workbooks, rationales, and adjudication records. Publication-safe analytical CSVs are included only as aggregate reproducibility outputs.
