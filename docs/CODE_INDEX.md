# Code Index

## Repository Utilities

| File | Purpose |
|---|---|
| `code/run_reproducible_pipeline.py` | Runs deterministic Phases 1–4 against controlled data and refuses unsafe output locations. |
| `code/export_public_release.py` | Copies only explicitly allowlisted aggregate outputs and rejects note-level fields and local paths. |
| `code/verify_repository.py` | Performs the data-free integrity, privacy, manifest, schema, human-ICR, and classification-performance audit. |
| `code/evidence_screening/build_evidence_corpus.py` | Creates blank controlled review sheets and refuses a revised corpus until every note, image, and included text span has adjudicated provenance decisions. |
| `code/evidence_screening/METHODS_EVIDENCE_SCREEN.md` | Documents the revised screening gate, privacy boundary, and provisional Phase 3 path. |
| `code/derived_analysis/build_revised_pair_boundaries.py` | Checks revised span and unit coding consistency, then counts typology pairs within approved spans and across spans of one capture unit. Outputs remain controlled and provisional. |
| `code/derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md` | Defines the provisional pair counts and their unit, source, and interpretation limits. |
| `code/ocr_quality/assess_ocr_quality.py` | Prepares a blinded probability sample, locks checked human transcripts before OCR is revealed, and scores complete reviews only when the locked material is unchanged. |
| `code/ocr_quality/METHODS_OCR_QUALITY.md` | Documents OCR sampling, human transcription, scoring, and limits for the historical referenced-image frame. |
| `code/human_validation/summarize_human_validation.py` | Summarises normalized controlled machine, coder, and adjudication tables; only aggregate performance results and file-level provenance hashes may be exported. |
| `code/human_validation/prepare_revised_holdout.py` | Prepares a controlled revised-evidence frame and draws a blinded probability holdout only after a hash-bound, author-approved allocation plan. |
| `code/human_validation/METHODS_REVISED_HOLDOUT.md` | Specifies the revised sampling unit, strata, weights, blinding, pilot exclusions, and interpretation limits. |
| `code/human_validation/build_public_icr_by_target.py` | Produces the publication-safe per-target ICR table and report from controlled aggregate reliability and adjudication inputs. |

The journal-neutral reviewer route and claim boundaries are documented in `docs/JOURNAL_REPRODUCIBILITY_SUPPLEMENT.md` and `docs/claim_to_evidence_register.csv`; they add no empirical processing stage.

## Phase 1: Markdown Baseline

| File | Purpose |
|---|---|
| `code/phase1_markdown_baseline/run_phase1.py` | Main Phase 1 entrypoint. |
| `code/phase1_markdown_baseline/extract_phase1.py` | Extracts canonical note, image-reference, keyword, entity-like, and price information. |
| `code/phase1_markdown_baseline/summarise_phase1.py` | Produces aggregate Phase 1 summaries. |
| `code/phase1_markdown_baseline/config.json` | Records deterministic configuration. |
| `code/phase1_markdown_baseline/METHODS_PHASE1.md` | Documents the phase method and limitations. |

## Phase 2: Local OCR

| File | Purpose |
|---|---|
| `code/phase2_image_ocr/run_phase2_ocr.py` | Resolves controlled screenshot references, runs local OCR, and creates aggregate OCR summaries. |
| `code/phase2_image_ocr/METHODS_PHASE2.md` | Documents OCR provenance, caching, and limitations. |

## Phase 3: Deterministic Typology Coding

| File | Purpose |
|---|---|
| `code/phase3_typology_coding/run_phase3_typology.py` | Applies the deterministic typology and AML-candidate rules. |
| `code/phase3_typology_coding/make_phase3_overview.py` | Builds a privacy-safe aggregate overview. |
| `code/phase3_typology_coding/METHODS_PHASE3.md` | Documents the deterministic coding method. |

## Phase 4: Deterministic Financial-Crime Analysis

| File | Purpose |
|---|---|
| `code/phase4_financial_crime_analysis/run_phase4_analysis.py` | Produces aggregate financial-crime findings and source profiles. |
| `code/phase4_financial_crime_analysis/METHODS_PHASE4.md` | Documents the Phase 4 synthesis boundary. |

## Deterministic Derived Analysis

| File | Purpose |
|---|---|
| `code/derived_analysis/build_derived_analysis.py` | Builds publication-safe duplicate sensitivity, source-normalized typology, co-occurrence source-stability, AML-candidate overlap, exploratory functional grouping, source concentration, and leave-one-source-out tables from controlled Phase 3 outputs. |

## Excluded Work

This repository contains no Phase 3b, Phase 4b, Phase 5, manuscript generator, submission package, or LLM-assisted empirical analysis.
