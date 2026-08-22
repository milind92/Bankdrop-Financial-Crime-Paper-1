# Release Governance

## Public Scope

The public repository is a journal-neutral reproducibility supplement containing deterministic Phase 1-4 code, publication-safe derived aggregate results, methods documentation, a claim-to-evidence register, and aggregate human-validation evidence. It excludes manuscript and submission work, incomplete or excluded LLM phases, and all raw or record-level material.

## Release Rules

1. Run the unit tests and repository verifier before every public push or tag.
2. Build derived outputs only from controlled Phase 3 files and export controlled results only through the fail-closed allowlist.
3. Do not add raw notes, screenshots, OCR text, evidence excerpts, identifiers, coder files, or adjudication rows.
4. Review every proposed public output for fields and text that could expose controlled information.
5. Keep the all-rights-reserved position unless the copyright holders and relevant institutions approve a change.
6. Record substantive changes in `CHANGELOG.md` and update `workflow_manifest.json`.
7. Keep the primary descriptive denominator fixed at 980 screened combined note records and the 463-record exact-text population labelled as sensitivity only unless a new controlled audit and complete rerun are approved.
8. Distinguish repository readiness from article-submission administration: the supplement may be submission-ready while authorship, declarations, rights, journal policy, anonymity, or DOI information is supplied separately through the manuscript or journal portal.

## Immutable Releases

Each public tag or archive should record the commit hash, version, date, verification result, privacy review, and approver. A GitHub tag or release does not itself create a DOI or archival deposit.
