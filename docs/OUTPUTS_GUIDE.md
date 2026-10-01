# Outputs Guide

All committed outputs are aggregate and publication-safe. Raw and record-level material is excluded.

**Status:** Historical Phase 1-4, derived and July validation outputs document the mixed-record pathway. The current [screenshot Methods and Results](IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md) uses `outputs/image_archive_20261002/` for archive calculations and `outputs/image_validation_20261002/` for completed agreement, five weighted PPVs, raw review classifications and provenance. Its final article interpretation remains with the authors.

## Fixed screenshot archive (2 October 2026)

`outputs/image_archive_20261002/` contains the 1,037-image flow, 19-rule summary, pattern and within-image overlap diagnostics, exact OCR-text and OCR-length sensitivity, historical modality comparison, anonymised leave-one-group-out ranges, legacy ICR applicability aggregate, and file-level provenance. It contains no screenshot, raw OCR, image/coder row, source-group label, or record-level hash. These percentages describe a fixed archive, not an external market.

The journal-facing interpretation boundary is maintained in `docs/claim_to_evidence_register.csv`; it is a documentation control rather than a new empirical output.

## Phase 1

`outputs/phase1_aggregate/` contains source totals, keyword totals, entity-like aggregate counts, price summaries, run totals, and a checkpoint summary.

## Phase 2

`outputs/phase2_aggregate/` contains aggregate OCR coverage by source and a checkpoint summary. It contains no screenshot or OCR text.

## Phase 3

`outputs/phase3_aggregate/` contains the deterministic codebook, typology summaries, source summaries, criminal-objective summaries, AML-candidate summaries, an analytical overview, and a checkpoint summary. It contains no note-level coding or evidence snippets.

## Phase 4

`outputs/phase4_aggregate/` contains deterministic aggregate findings, AML-candidate summaries, source profiles, bounded recommendations, run metadata, an analysis report, and a checkpoint summary.

## Deterministic Derived Analysis

`outputs/derived_analysis/` contains publication-safe duplicate-sensitivity, source-normalized typology, co-occurrence, co-occurrence source-stability, typology-to-AML-candidate overlap, exploratory functional-grouping, source-concentration, and leave-one-source-out tables. The 463-record exact-text population is explicitly sensitivity only, not a verified unique-post or eligible-evidence-unit population. See `DERIVED_ANALYSIS_NOTES.md` for formulas and evidence boundaries.

## Human Validation

`outputs/human_validation/` contains the public completion narrative, overall aggregate ICR and adjudication totals, target-level agreement intervals, kappa, binary Gwet AC1, and machine-versus-final-human classification performance. The performance table reports unweighted sample estimates and sampling-weighted point estimates with their documented limits. The folder also contains file-level SHA-256 provenance metadata. It contains no coder-level decisions, rationales, identifiers, signatures, or evidence.

## Screening Audit

`outputs/analysis_audit/` contains aggregate historical screening totals and the 1 October 2026 image-coverage and record-type sensitivity diagnostics. Text hashes are used only in controlled sensitivity accounting and are not released.

## Excluded Outputs

The repository excludes article-ready manuscript tables, article drafts, submission files, Phase 3b, Phase 4b, Phase 5, LLM-assisted empirical outputs, raw notes, screenshots, OCR text, evidence snippets, note-level rows, coding workbooks, rationales, and adjudication records. Publication-safe analytical CSVs are included only as aggregate reproducibility outputs.
