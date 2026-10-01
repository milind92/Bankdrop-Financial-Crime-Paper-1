# Changelog

## 1.3.7 - 2026-10-01

- Added a one-time, pre-reveal lock for checked OCR gold transcripts and human legibility decisions. The scorer now rejects missing locks and changed locked fields or transcript files; the controlled lock manifest is blocked from public export.
- Added design-weighted legibility percentages alongside raw sample counts. The 50-image human review remains blank, so no OCR accuracy or adequacy estimate is claimed.

## 1.3.6 - 2026-10-01

- Added a fixed-seed, source-stratified probability sample and blinded two-human OCR transcription workflow for the historical referenced-image frame, with known per-stratum inclusion probabilities and hash-checked screenshot copies.
- Added a fail-closed scorer for checked gold transcripts, per-image and weighted character/word error diagnostics, and weighted source-coding adequacy judgments. No OCR accuracy result is claimed because the human review is blank.
- Distinguished the earlier unreviewed, OCR-length-extreme sample as a purposeful diagnostic. The new 50-image sample covers the historical referenced-image frame; final-corpus and novel-orphan OCR coverage still require review.

## 1.3.5 - 2026-10-01

- Added a controlled, hash-checked evidence-screening gate that requires two recorded reviewer decisions and adjudication for every screened note and image, plus approved source-text spans before an evidence-only corpus can be built.
- Added an optional Phase 3 path that codes approved Markdown/OCR spans within artefact boundaries. The default historical replay and all previously published aggregate result files remain unchanged.
- Blocked the old Phase 4 narrative from treating a revised evidence corpus as covered by the historical human validation. The revised denominator, OCR accuracy, target validity, and article tables remain pending.
- Prevented the public exporter from replacing historical aggregate files with provisional revised-evidence outputs.
- Blocked the historical derived-analysis definitions for revised evidence units and corrected the Phase 3 overview's revised-mode validation wording.
- Added a provisional OCR-only sensitivity explanation to the public audit. All new record-level review sheets and source text remain controlled.

## 1.3.4 - 2026-10-01

- Placed the supplement on methodological hold after a controlled audit distinguished captured source evidence from collection-status and researcher-written Markdown records.
- Disclosed aggregate image coverage, preliminary record-type counts, historical code-count impact, human-validation sample impact, and cross-artefact compound-match sensitivity without releasing controlled evidence.
- Preserved the `v1.3.3` calculations as historical, reproducible outputs and withdrew the prior submission-ready claim pending author-reviewed eligibility, image linkage, OCR quality, and revised validation.

## 1.3.3 - 2026-08-22

- Simplified environment and reviewer documentation at author direction.
- Removed the superseded cloud-runtime compatibility guide and its related manifest and verifier requirements.
- Preserved the deterministic no-LLM empirical scope, controlled-rerun instructions, and all analysis and human-validation outputs.

## 1.3.2 - 2026-08-22

- Updated repository governance documentation and integrity checks at author direction.
- Preserved the deterministic no-LLM empirical scope and all analysis and human-validation outputs.
- Aligned the reviewer landing page, submission checklist, citation metadata, and workflow manifest with the `v1.3.2` release.

## 1.3.1 - 2026-08-22

- Marked the repository explicitly submission-ready as a journal-neutral reproducibility supplement.
- Separated completed supplement requirements from manuscript, authorship, declaration, journal-portal, rights, and DOI tasks that sit outside the repository artifact.
- Added a visible repository-integrity badge and strengthened the verifier so the readiness status cannot regress to “technically ready.”
- Updated the reviewer landing page, submission checklist, and citation metadata for the audited `v1.3.1` release.

## 1.3.0 - 2026-08-22

- Fixed the repository role as a journal-neutral reproducibility supplement; manuscript and journal submission files remain outside GitHub.
- Recorded the author-approved primary computational unit and 980-record descriptive denominator, with 463 exact-text representatives retained only as duplicate sensitivity and 65 zero-word records disclosed.
- Added a reviewer landing page, author-decisions record, journal-integration checklist, and machine-readable claim-to-evidence register.
- Added public audit commands and controlled-data/OCR portability boundaries.
- Recorded both coders as subject-matter experts, Milind Tiwari's AML expertise, and the author confirmation that a sample-size plan was used.
- Preserved transparent validation limitations: short predicted-negative eligibility, legacy provenance labels, joint two-coder adjudication, and no claim of an independent external AML review.
- Corrected the legacy screening-audit row so it no longer claims a record-level exclusion log or 980 eligible unique analytic records.
- Extended the repository verifier and tests to enforce the journal-supplement role, denominators, pending integration items, and claim boundaries.

## 1.2.1 - 2026-08-22

- Recorded the completed corrected-corpus validation by Ausma Bernot and Milind Tiwari: 1,032 paired units, 981 agreements, 51 jointly adjudicated disagreements, and no unresolved cases.
- Regenerated target-level agreement intervals, kappa, binary Gwet AC1, adjudication totals, and file-level provenance metadata from the frozen controlled closeout.
- Added publication-safe machine-versus-final-human classification performance, including unweighted and sampling-weighted estimates with explicit interpretation limits.
- Repaired the repository verifier so aggregate and target-level validation checks execute in CI and reject stale schemas or unreconciled totals.
- Kept OCR filenames and paths out of analytic text, retained zero-count typology categories explicitly, and regenerated Phase 1-4 and derived aggregates. A controlled audit of the 313 frozen evidence packets found that removing 840 legacy provenance labels changed no packet-target classifications and that label-only text triggered no deterministic rule. The rerun changed no validation-sample classifications, no typology-positive counts, and no duplicate-sensitivity denominator.
- Corrected controlled-rerun commands, stale validation figures, Phase 4 claim boundaries, and the Phase 4 public-export allowlist.

## 1.2.0 - 2026-07-25

- Corrected the eligibility boundary and reran the deterministic analysis on 980 source-folder notes after excluding 19 internal project documents.
- Made Phase 3 consume the frozen Phase 1 eligible corpus instead of rescanning every Markdown file.
- Normalized the `17.  XmrBazaar` display label and documented the empty source index 16.
- Tightened generic lexical and bank-entity patterns and added currency-labelled price extraction, including supported cryptocurrency amount forms.
- Added provenance-matched OCR cache-only replay for non-Windows environments.
- Regenerated Phase 1-4 and derived aggregate outputs: 980 screened records and 463 exact-text sensitivity representatives.
- Withdrew the 23 July human-validation statistics because 14 ineligible internal records contributed 59 paired case-target units; the replacement validation was subsequently completed and released in 1.2.1.

## 1.1.0 - 2026-07-25

- Added deterministic publication-safe tables for exact-text duplicate sensitivity, source-normalized typology reporting, typology co-occurrence with source-stratified and leave-one-source-out stability, typology-to-AML-candidate overlap, exploratory functional unions, source concentration, and leave-one-source-out sensitivity.
- Added target-level human ICR reporting for all 18 assessed targets, including agreement intervals, Cohen’s kappa intervals, binary Gwet AC1 intervals, and aggregate adjudication outcomes.
- Added data-free tests and repository-verifier reconciliation for all new aggregate outputs.
- Extended the allowlisted public exporter and workflow manifest without expanding the public data boundary.
- Clarified that the then-reported 479-record exact-text-unique population was a sensitivity denominator, not the final eligible analytic population; the corrected 1.2.0 rerun superseded that historical count with 463.

## 1.0.0 - 2026-07-25

- Created a new history-free public repository for Bankdrop Financial Crime Paper 1.
- Included only deterministic Phase 1–4 code and aggregate results.
- Included the Phase 3 codebook, analysis plan, data-collection protocol, and reproducibility documentation.
- Included the human-validation protocol and publication-safe aggregate ICR and adjudication results.
- Included privacy, ethics, security, controlled-access, and rights disclosures.
- Excluded manuscript drafts, submission materials, literature-review materials, incomplete Phase 3b and Phase 4b work, Phase 5 materials, raw data, screenshots, record-level evidence, coder workbooks, and adjudication records.
