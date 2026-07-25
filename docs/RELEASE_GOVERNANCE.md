# Release Governance

## Public Scope

The public repository contains deterministic Phase 1–4 code, publication-safe derived aggregate results, methods documentation, and aggregate human-validation evidence. It excludes manuscript and submission work, incomplete or excluded LLM phases, and all raw or record-level material.

## Release Rules

1. Run the unit tests and repository verifier before every public push or tag.
2. Build derived outputs only from controlled Phase 3 files and export controlled results only through the fail-closed allowlist.
3. Do not add raw notes, screenshots, OCR text, evidence excerpts, identifiers, coder files, or adjudication rows.
4. Review every proposed public output for fields and text that could expose controlled information.
5. Keep the all-rights-reserved position unless the copyright holders and relevant institutions approve a change.
6. Record substantive changes in `CHANGELOG.md` and update `workflow_manifest.json`.

## Immutable Releases

A future tag or archive should record the commit hash, version, date, verification result, privacy review, and approver. Creating this repository does not itself create a DOI or archival deposit.
