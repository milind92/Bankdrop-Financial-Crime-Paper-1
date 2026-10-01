# Author Decisions Record

## Status

This record captures author instructions supplied on 22 August 2026 for the public Bankdrop Financial Crime Paper 1 repository. It applies to the repository as a journal-neutral reproducibility supplement. It is not a substitute for the final manuscript title page, declarations, journal forms, or institutional approvals.

**Current status:** The 1 October 2026 [post-release corpus audit](POST_RELEASE_CORPUS_AUDIT_2026-10-01.md) supersedes the earlier submission-readiness decision. The 980-note denominator and 463-hash sensitivity below are preserved as historical computational choices. Authors have not yet confirmed the revised source-evidence boundary or image-coverage decisions.

## Earlier Decisions For The Historical Screen

These decisions document the released calculation. The source-evidence audit
supersedes the computational unit, denominator, and duplicate-sensitivity
choices for substantive article analysis; it does not erase their value as a
record of what the historical pipeline computed.

| Topic | Earlier decision | Historical repository effect |
|---|---|---|
| Target outlet | A quality journal will be selected later. | The repository uses journal-neutral reporting and does not claim compliance with an unnamed journal's instructions. |
| Repository role | Reproducibility supplement only. | No manuscript, cover letter, title page, or submission form is included. |
| Primary computational unit | One screened combined note record: one Markdown note plus validly linked, content-deduplicated OCR text where available. | Results are reported at the combined-note-record level, not as unique posts, listings, actors, transactions, offenders, or victims. |
| Primary descriptive denominator | All 980 screened combined note records. | Historical mixed-record denominator only; not an approved substantive article population. |
| Duplicate sensitivity | One representative per exact combined-text hash, n = 463. | This is a sensitivity population only and is not called the number of eligible unique posts or evidence units. |
| Zero-word records | Retain and disclose 65 records with neither assessable Markdown nor joined OCR. | Non-matches cannot be interpreted as substantive absence, and denominators are stated explicitly. |
| Ethics wording | Use “Griffith University Human Ethics Protocol 2025/697.” | The identifier is reported without inferring consent, waiver, copyright, access, or release permissions that it does not itself establish. |
| Coder expertise | Ausma Bernot and Milind Tiwari are subject-matter experts; Milind Tiwari also has AML expertise. | Expertise is reported at this bounded level. No unprovided qualifications, titles, or institutional roles are inferred. |
| Validation sampling | A sample-size plan was used. | The implemented fixed-seed, stratified design is documented. No claim is described as passing an undisclosed numerical acceptance threshold. |

## Validation Qualifications

- The validation used a documented, fixed-seed stratified sample and retained selection probabilities and analysis weights in controlled files.
- Predicted-negative eligibility required at least 30 combined-text words. Performance estimates therefore do not establish false-negative behaviour among shorter or unassessable records.
- Frozen packets contained legacy screenshot-provenance labels. A controlled audit found that label-only text triggered no deterministic rule and that removing the labels changed no sampled classification. Their possible cognitive influence on human coders cannot be disproved and remains a disclosed limitation.
- Ausma Bernot and Milind Tiwari coded independently before comparison and then jointly adjudicated all 51 disagreements. No third adjudicator participated.
- Milind Tiwari has AML expertise, but he was also a coder and adjudicator. The repository therefore does not claim an independent external AML-domain review. The six AML candidates remain corpus-derived research hypotheses rather than operational red flags or controls.

## Journal-Specific Tasks Outside Supplement Scope

The following items will be completed after the target journal and final paper team are confirmed. They belong to the manuscript, journal portal, or archival handoff rather than the reproducibility supplement itself:

- exact journal and article type;
- author names, order, affiliations, ORCIDs, and corresponding-author details;
- funding, acknowledgements, competing interests, and CRediT contributions;
- copyright-holder and institutional ownership confirmation;
- licence choice and any archival DOI;
- journal-specific repository, data, ethics, and anonymity wording.

At current version `1.3.14`, the repository remains on methodological hold. The historical `v1.3.3` submission-ready statement has been withdrawn pending the author-reviewed reanalysis and validation described in the post-release audit. The revised holdout sampler and closeout scorer are available, but no real sample or score can exist before the evidence frame, target definitions, author allocation plan, and independent human judgments are locked.
