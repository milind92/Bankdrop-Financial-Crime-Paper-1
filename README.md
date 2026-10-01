# Bankdrop Financial Crime Paper 1

[![Repository integrity](https://github.com/milind92/Bankdrop-Financial-Crime-Paper-1/actions/workflows/repository-integrity.yml/badge.svg)](https://github.com/milind92/Bankdrop-Financial-Crime-Paper-1/actions/workflows/repository-integrity.yml)

A public, privacy-clean, journal-neutral reproducibility supplement containing the deterministic analysis and human-validation record for Bankdrop Financial Crime Paper 1.

## Reproducibility Supplement Status

**2 October 2026 status:** The [fixed screenshot analysis](docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md) is computationally complete. It verifies and codes 1,037 content-unique, locally referenced archived screenshots and releases [19 OCR-rule aggregate counts and sensitivity checks](outputs/image_archive_20261002/). A [portable controlled reproducer](code/image_archive/reproduce_controlled.py) generated all 12 original result files byte for byte identically in an authorised rerun. The five possible source-claim constructs have a small, blank Milind–Ausma coding packet in controlled storage: 249 decisions per author across 205 screenshots. Independent image-level agreement, adjudication, and Milind's final claim decision have **not occurred**; the repository is therefore not yet a claim-validated journal submission.

The earlier [post-release controlled-corpus audit](docs/POST_RELEASE_CORPUS_AUDIT_2026-10-01.md) found that the historical 980-note screen includes research/status records and cannot serve as the substantive article denominator. Its computations and July mixed-record validation remain historical audit material. The new article scope is a bounded retrospective archive analysis: collector identity for each image, capture dates, source completeness, and OCR gold accuracy are unknown. Filename dates are not used as capture dates. No rule-positive count is presented as a completed sale, transaction, victim count, or external market prevalence. See the [image protocol](docs/IMAGE_ARCHIVE_PROTOCOL_2026-10-02.md) for the exact frame, five-construct validation design, and limits.

It deliberately contains no manuscript, title page, declarations, or journal-portal forms because those are article-submission materials rather than reproducibility components. Final author metadata, declarations, rights, and any archival DOI are supplied with the manuscript or through the selected journal's submission process; they do not represent missing empirical work in this repository. A submitter must still follow an eventual journal's file-format and review-anonymity rules.

Reviewers should begin with the [fixed screenshot analysis](docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md), [image protocol](docs/IMAGE_ARCHIVE_PROTOCOL_2026-10-02.md), [public aggregates](outputs/image_archive_20261002/), and [post-release corpus audit](docs/POST_RELEASE_CORPUS_AUDIT_2026-10-01.md). The [Journal Reproducibility Supplement](docs/JOURNAL_REPRODUCIBILITY_SUPPLEMENT.md) and [Claim-to-Evidence Register](docs/claim_to_evidence_register.csv) document the historical mixed-record workflow and its hold.

## Scope

The empirical workflow contains four deterministic phases:

1. Phase 1: Markdown baseline extraction.
2. Phase 2: local screenshot OCR.
3. Phase 3: deterministic typology coding.
4. Phase 4: deterministic financial-crime analysis.

Blinded human inter-coder reliability and subsequent adjudication were completed by Ausma Bernot and Milind Tiwari on 26 July 2026 under Griffith University Human Ethics Protocol 2025/697. Publication-safe historical results are available in [Human ICR Completion](outputs/human_validation/HUMAN_ICR_COMPLETION.md), [Human ICR Results by Target](outputs/human_validation/HUMAN_ICR_BY_TARGET.md), and [Human Validation Performance](outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md). These metrics apply to the historical mixed-record sample, not a revised evidence-only corpus. Coder workbooks, evidence packets, rationales, and record-level adjudication material remain controlled and are not published.

The repository also includes publication-safe deterministic derived analyses for exact-text duplicate sensitivity, source-normalized typology reporting, typology co-occurrence with source-stratified and leave-one-source-out stability, AML-candidate overlap, exploratory functional grouping, source concentration, and leave-one-source-out sensitivity. These are descriptive post-processing outputs, not a Phase 5 or LLM-assisted empirical analysis.

The new image-level analysis is a separate retrospective reanalysis of the archived screenshots. Its five source-claim targets were chosen after reviewing earlier error diagnostics, and the other 13 substantive OCR rules remain exploratory lexical results. The previous 1,032 paired July decisions are not reused as current image-level reliability: only 83 judgments map to a single image with equivalent OCR and no extra Markdown, and 79 of those are absent.

## Repository Contents

- `code/`: deterministic Phase 1–4 scripts, derived-analysis and human-validation summarisation utilities, guarded orchestrator, public-output exporter, and repository verifier.
- `outputs/`: privacy-safe Phase 1–4 aggregates, deterministic derived analyses, corpus-screening audit totals, and aggregate human-validation results.
- `docs/`: analysis plan, data-collection protocol, code index, validation protocol, controlled-access guidance, environment record, and release governance.
- `reproducibility/`: controlled-rerun and integrity instructions.
- `tests/`: data-free automated tests for provenance, privacy, orchestration, validation calculations, and repository integrity.

## Start Here

- [Analysis plan](docs/ANALYSIS_PLAN.md)
- [Fixed screenshot Methods and Results](docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md)
- [Fixed screenshot protocol and validation](docs/IMAGE_ARCHIVE_PROTOCOL_2026-10-02.md)
- [Fixed screenshot aggregate outputs](outputs/image_archive_20261002/rule_summary.csv)
- [Post-release corpus audit](docs/POST_RELEASE_CORPUS_AUDIT_2026-10-01.md)
- [Data-collection protocol](docs/DATA_COLLECTION_PROTOCOL.md)
- [Phase 3 codebook](outputs/phase3_aggregate/CODEBOOK_PHASE3.md)
- [Human-validation protocol](docs/HUMAN_VALIDATION_PROTOCOL.md)
- [Completed aggregate human ICR results](outputs/human_validation/HUMAN_ICR_COMPLETION.md)
- [Human ICR results by target](outputs/human_validation/HUMAN_ICR_BY_TARGET.md)
- [Human validation classification performance](outputs/human_validation/HUMAN_VALIDATION_PERFORMANCE.md)
- [Deterministic derived analysis notes](outputs/derived_analysis/DERIVED_ANALYSIS_NOTES.md)
- [Outputs guide](docs/OUTPUTS_GUIDE.md)
- [Workflow manifest](workflow_manifest.json)
- [Reproducibility instructions](REPRODUCIBILITY.md)
- [Data availability](DATA_AVAILABILITY.md)
- [Controlled audit access](docs/CONTROLLED_AUDIT_ACCESS.md)
- [Ethics and safety](ETHICS_AND_SAFETY.md)
- [Journal reproducibility supplement](docs/JOURNAL_REPRODUCIBILITY_SUPPLEMENT.md)
- [Author decisions record](docs/AUTHOR_DECISIONS_RECORD.md)
- [Supplement submission checklist](docs/JOURNAL_INTEGRATION_CHECKLIST.md)
- [Claim-to-evidence register](docs/claim_to_evidence_register.csv)

## Data Boundary

This is not a public release of the underlying research corpus. The repository excludes raw notes, screenshots, OCR text, direct excerpts, record-level coding, evidence packets, coder workbooks, adjudication rows, handles, URLs, payment identifiers, local paths, and archives.

The aggregate outputs describe a controlled research corpus. They do not establish transaction truth, market prevalence, offender or victim counts, completed services, or causal relationships.

## Verify The Repository

The data-free audit requires Python 3.11 and the standard library:

```powershell
python -m unittest discover -s tests -v
python .\code\verify_repository.py
```

A controlled rerun requires authorised access to the restricted source vault and the documented local OCR environment. See [CONTROLLED_RERUN.md](reproducibility/CONTROLLED_RERUN.md).

## Citation And Rights

Citation metadata is provided in [CITATION.cff](CITATION.cff). No reuse licence is granted. The repository remains all rights reserved as described in [LICENSE.md](LICENSE.md).
