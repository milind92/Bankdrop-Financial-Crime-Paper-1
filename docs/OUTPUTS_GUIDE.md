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

## Human Validation

`outputs/human_validation/` contains the public completion narrative, aggregate ICR and adjudication totals, and the aggregate validation sampling summary. It contains no coder-level decisions or evidence.

## Screening Audit

`outputs/analysis_audit/` contains aggregate screening and exact-text duplicate-audit totals. Text hashes are used only for sensitivity accounting and are not released.

## Excluded Outputs

The repository excludes manuscript tables, article drafts, submission files, Phase 3b, Phase 4b, Phase 5, LLM-assisted empirical outputs, raw notes, screenshots, OCR text, evidence snippets, note-level rows, coding workbooks, rationales, and adjudication records.
