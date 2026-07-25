# Code Index

## Repository Utilities

| File | Purpose |
|---|---|
| `code/run_reproducible_pipeline.py` | Runs deterministic Phases 1–4 against controlled data and refuses unsafe output locations. |
| `code/export_public_release.py` | Copies only explicitly allowlisted aggregate outputs and rejects note-level fields and local paths. |
| `code/verify_repository.py` | Performs the data-free integrity, privacy, manifest, schema, and human-ICR audit. |
| `code/human_validation/summarize_human_validation.py` | Summarises two completed human coding workbooks in controlled storage; only aggregate results may be exported. |
| `code/human_validation/build_public_icr_by_target.py` | Produces the publication-safe per-target ICR table and report from controlled aggregate reliability and adjudication inputs. |

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
