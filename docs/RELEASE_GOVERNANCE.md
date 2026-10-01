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
7. Treat the 980 screened combined note records and 463 exact-text representatives as historical populations. The revised substantive denominator requires a controlled eligibility audit, author review, complete rerun, and validation.
8. Keep the supplement on methodological hold until the revised evidence boundary and dependent analyses are verified; authorship, declarations, rights, journal policy, anonymity, and DOI information are separate submission tasks.

## Immutable Releases

Each public tag or archive should record the commit hash, version, date, verification result, privacy review, and approver. A GitHub tag or release does not itself create a DOI or archival deposit.
