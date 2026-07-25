# Bankdrop Financial Crime Paper 1

A public, privacy-clean repository containing the deterministic analysis and human-validation record for Bankdrop Financial Crime Paper 1.

## Scope

The empirical workflow contains four deterministic phases:

1. Phase 1: Markdown baseline extraction.
2. Phase 2: local screenshot OCR.
3. Phase 3: deterministic typology coding.
4. Phase 4: deterministic financial-crime analysis.

No Phase 3b, Phase 4b, Phase 5, LLM-assisted empirical analysis, manuscript draft, literature review, cover letter, title page, or submission package is included. Phase 2 uses OCR, which is not an LLM stage.

Blinded human inter-coder reliability and subsequent adjudication were completed by Ausma and Milind on 23 July 2026. Publication-safe overall results are available in [Human ICR Completion](outputs/human_validation/HUMAN_ICR_COMPLETION.md), with agreement intervals, kappa, binary Gwet AC1, and adjudication totals by target in [Human ICR Results by Target](outputs/human_validation/HUMAN_ICR_BY_TARGET.md). Coder workbooks, evidence packets, rationales, and record-level adjudication material remain controlled and are not published.

The repository also includes publication-safe deterministic derived analyses for exact-text duplicate sensitivity, source-normalized typology reporting, typology co-occurrence with source-stratified and leave-one-source-out stability, AML-candidate overlap, exploratory functional grouping, source concentration, and leave-one-source-out sensitivity. These are descriptive post-processing outputs, not a Phase 5 or LLM-assisted empirical analysis.

## Repository Contents

- `code/`: deterministic Phase 1–4 scripts, derived-analysis and human-validation summarisation utilities, guarded orchestrator, public-output exporter, and repository verifier.
- `outputs/`: privacy-safe Phase 1–4 aggregates, deterministic derived analyses, corpus-screening audit totals, and aggregate human-validation results.
- `docs/`: analysis plan, data-collection protocol, code index, validation protocol, controlled-access guidance, environment record, release governance, and AI-assistance disclosure.
- `reproducibility/`: controlled-rerun and integrity instructions.
- `tests/`: data-free automated tests for provenance, privacy, orchestration, validation calculations, and repository integrity.

## Start Here

- [Analysis plan](docs/ANALYSIS_PLAN.md)
- [Data-collection protocol](docs/DATA_COLLECTION_PROTOCOL.md)
- [Phase 3 codebook](outputs/phase3_aggregate/CODEBOOK_PHASE3.md)
- [Human-validation protocol](docs/HUMAN_VALIDATION_PROTOCOL.md)
- [Completed aggregate human ICR results](outputs/human_validation/HUMAN_ICR_COMPLETION.md)
- [Human ICR results by target](outputs/human_validation/HUMAN_ICR_BY_TARGET.md)
- [Deterministic derived analysis notes](outputs/derived_analysis/DERIVED_ANALYSIS_NOTES.md)
- [Outputs guide](docs/OUTPUTS_GUIDE.md)
- [Workflow manifest](workflow_manifest.json)
- [Reproducibility instructions](REPRODUCIBILITY.md)
- [Data availability](DATA_AVAILABILITY.md)
- [Controlled audit access](docs/CONTROLLED_AUDIT_ACCESS.md)
- [Ethics and safety](ETHICS_AND_SAFETY.md)
- [AI authoring-assistance disclosure](docs/AI_AUTHORING_ASSISTANCE_DISCLOSURE.md)

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
