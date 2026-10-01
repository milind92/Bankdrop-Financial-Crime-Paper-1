# Journal Reproducibility Supplement

## Status

**Methodological hold.** The [1 October 2026 post-release corpus audit](POST_RELEASE_CORPUS_AUDIT_2026-10-01.md) found collection and researcher notes inside the historical 980-note screen. This repository supports inspection of the historical deterministic workflow and aggregate results, but it is not ready to support final article claims or journal submission.

Version `1.3.15` retains the `v1.3.3` computations as historical outputs, adds aggregate audit results, and supplies [controlled evidence-screening](../code/evidence_screening/METHODS_EVIDENCE_SCREEN.md), [OCR-quality](../code/ocr_quality/METHODS_OCR_QUALITY.md), [provisional pair-boundary](../code/derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md), and [revised human sampling and scoring](../code/human_validation/METHODS_REVISED_HOLDOUT.md) procedures. Corpus eligibility, image linkage, human OCR transcription, reanalysis, and revised validation remain open. See [Author Decisions Record](AUTHOR_DECISIONS_RECORD.md) and [Supplement Submission Checklist](JOURNAL_INTEGRATION_CHECKLIST.md).

## Reviewer Audit Route

From a clean checkout with CPython 3.11:

```powershell
python -m unittest discover -s tests -v
python .\code\verify_repository.py
```

These data-free checks validate code syntax, required files, JSON and CSV schemas, manifest references, privacy exclusions, release metadata, human-validation reconciliation, claim boundaries, and derived contingency tables. GitHub Actions runs the same checks on Ubuntu and Windows.

A source-level rerun requires authorised access to the controlled vault and the pinned Windows OCR environment. The public repository cannot reconstruct excluded evidence. See [Reproducibility](../REPRODUCIBILITY.md) and [Controlled Rerun](../reproducibility/CONTROLLED_RERUN.md).

## Empirical Scope

- Design: deterministic, computer-assisted content analysis.
- Included phases: Markdown inventory, local Windows OCR, deterministic multi-label coding, and deterministic aggregate synthesis.
- Primary computational unit: one screened combined note record, consisting of one Markdown note plus validly linked and content-deduplicated OCR text where available.
- Historical screened denominator: 980 combined note records; a final evidence-only denominator is pending.
- Historical exact-text sensitivity denominator: 463 representatives, one per combined-text hash; 74 represent no-OCR research/status text.
- Historical human validation: 1,032 case-target units drawn from 313 packets across 18 targets; 191 rows came from no-OCR research/status notes.
- External inference: not permitted. Counts do not estimate market prevalence and do not establish transactions, service delivery, actors, offenders, victims, causation, or criminal liability.

The 463-record population is a duplicate-sensitivity construction, not a verified count of unique posts, listings, actors, transactions, or evidence units. Sixty-five records contained neither assessable Markdown nor joined OCR; their non-matches cannot support absence claims.

## Human Validation Boundary

Ausma Bernot and Milind Tiwari independently completed the controlled coding exercise and jointly adjudicated all disagreements. Aggregate exact agreement was 981/1,032 (95.1%); five-category Cohen's kappa was 0.839378, and binary Present/Absent kappa was 0.933155.

Reliability was strong in the historical mixed-record sample, but deterministic classification performance varied materially by target. These numbers cannot validate a revised evidence-only corpus. Authors and reviewers should use the target rows in [Human Validation Performance](../outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md) only to diagnose the historical screen. Categories with few or no human-positive cases do not support rarity or absence claims.

The sample followed a planned fixed-seed stratified design. Predicted-negative sampling excluded records with fewer than 30 combined-text words, legacy provenance labels were visible in frozen packets, the two coders jointly adjudicated disagreements, and no separate independent AML reviewer is claimed. These limitations are preserved in [Human Validation Protocol](HUMAN_VALIDATION_PROTOCOL.md).

## Claim Control

The machine-readable [Claim-to-Evidence Register](claim_to_evidence_register.csv) records historical claims and their current hold status, supporting aggregate files, validation and sensitivity boundaries, and prohibited inferences. It distinguishes:

- supported descriptive statements;
- qualified descriptive results;
- exploratory hypotheses;
- unsupported prevalence, absence, causal, transaction, or operational claims.

The `status` field applies to the broader claim scope. Where a row is `not_supported`, the `approved_wording` field supplies only a bounded descriptive replacement; it does not approve the unsupported inference named by the scope.

AML candidates are compound lexical relationships in captured records. They may motivate further research but are not confirmed red flags, suspicious-activity indicators, monitoring controls, or proof of money movement.

## Public And Controlled Boundaries

GitHub contains code, protocols, codebooks, aggregate tables, validation summaries, sensitivity analyses, and provenance metadata. It excludes raw notes, screenshots, OCR text, direct excerpts, identifiers, record-level coding, evidence packets, coder workbooks, rationales, and adjudication rows. Controlled access is discretionary and subject to ethics, law, privacy, security, and institutional approval.

## Ethics

The approved repository wording is "Griffith University Human Ethics Protocol 2025/697." The identifier does not independently establish consent status, copyright ownership, or authority to release controlled evidence.

## Citation And Versioning

Use [CITATION.cff](../CITATION.cff) for the current project-level software citation. Its generic project-author label preserves the authors' decision to finalise names and order later. Version `1.3.15` is a historical computational record plus uncompleted screening, OCR-review, revised pair-analysis, and human-holdout procedures, not a final empirical release. Each tagged release must pass the data-free audit and privacy review before publication.
