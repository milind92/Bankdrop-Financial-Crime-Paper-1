# Data Collection Protocol

## Status And Purpose

This protocol records the historical repository-level corpus boundary and the additional provenance, sampling, and ethics information required before journal use. It distinguishes earlier author decisions about the computation from collection facts that remain unverified.

**Post-release audit notice (1 October 2026):** The source-folder boundary screened 980 notes but did not distinguish source evidence from collection-status or researcher-written records. The 980 is a historical computational count, not an approved substantive denominator. See [Post-release corpus audit](POST_RELEASE_CORPUS_AUDIT_2026-10-01.md) before using the historical flow table or human-validation figures below.

Items marked **AUTHOR CONFIRMATION REQUIRED** must be completed from contemporaneous collection records or direct author knowledge. They must not be inferred from filenames, aggregate tables, repository history, or automated output.

The study concerns observed online material. It does not provide transaction data and cannot establish that an advertised product or service existed, was purchased, was delivered, or caused financial harm.

## Study Design

The study is a deterministic, computer-assisted content analysis of a controlled research vault containing researcher-maintained Markdown notes and referenced screenshots. The design is descriptive and exploratory. It maps signals visible in the captured corpus; it is not a prevalence study of an external criminal market.

The repository records a staged workflow in which Markdown content is inventoried, referenced screenshots are processed with local OCR, and the combined text is screened using a fixed, version-controlled rule-based codebook. Human validation is governed separately by `docs/HUMAN_VALIDATION_PROTOCOL.md`.

## Research Scope

The collection protocol must support the following bounded questions:

1. Which defined financial-crime service, access, identity, coordination, trust, and monetisation signals are visible in author-approved source-evidence capture units?
2. How are validated signals distributed across the included source groups and text modalities?
3. Which signals co-occur within approved source artefacts, without treating co-occurrence as proof of a transaction pathway?
4. Which observations may be framed as hypotheses for later AML research or expert assessment, rather than operational monitoring rules?

## Unit Definitions

| Unit | Definition | Permitted use |
|---|---|---|
| Source group | A named folder or documented collection stratum representing an online forum, market, search surface, or other source context. | Coverage and source-stratified description. It is not an independent population. |
| Markdown note | One Markdown file in the controlled vault. A note may contain researcher text, embedded links, metadata, or references to screenshots. | Inventory unit and basis of the screened combined note record; it is not assumed to be one unique online post. |
| Screenshot | One unique local image, identified by cryptographic file hash rather than filename alone. | Image-level provenance and OCR quality assessment. |
| Image reference | One link from a Markdown note to an image. Multiple references may point to the same screenshot. | Linkage and missingness reporting; not a count of unique images. |
| Combined note record | The normalized Markdown text for one note plus deduplicated OCR text from screenshots validly linked to that note. | Historical screening record. It must not duplicate OCR merely because an image is referenced more than once. |
| Evidence unit | The underlying captured post, listing, page, thread segment, or other online artefact represented by a note or screenshot. | Preferred substantive unit where the collection log permits reconstruction. |
| Historical analytic record | One screened combined note record: one Markdown note plus validly linked and content-deduplicated OCR text where available. | Historical computational denominator, n = 980. It is not the approved substantive article denominator and may be composite. |
| Note-code row | One analytic record evaluated against one typology or AML-candidate definition. | Coding-table structure only. It is not an independent observation when multiple rows come from the same record. |
| Duplicate cluster | Two or more notes or screenshots with identical content hashes, or a separately documented near-duplicate relationship. | Sensitivity analysis and prevention of double counting. |

The earlier author decision retained the Markdown-note-based combined record because underlying evidence-unit reconstruction was not completed. The post-release audit found researcher and collection records inside that screen, so a revised substantive unit and denominator require author review. Any discussion of the historical screen must state that notes may be composite and cannot be equated with posts, listings, actors, or transactions.

## Source Selection And Sampling Frame

The final manuscript must describe the corpus as a purposive or otherwise specified captured sample unless a complete sampling frame can be demonstrated.

For every source group, retain a controlled provenance record with:

- canonical source label and privacy-safe public label;
- source type, such as forum, market, search surface, or other category;
- rationale for inclusion;
- discovery route and search terms or navigation strategy, recorded at a level that supports audit without publishing operational criminal instructions;
- access conditions, including whether registration, invitation, or authentication was required;
- intended jurisdictional and language scope;
- collection start and end dates;
- collection frequency or visit schedule;
- collector identifier or role;
- known outages, login walls, access failures, and other coverage interruptions;
- the stopping rule, saturation rule, time boundary, or resource boundary used;
- any source aliases, migrations, or suspected mirrors;
- whether the collector interacted with users or only observed content.

**AUTHOR CONFIRMATION REQUIRED:** Provide the original source-selection rationale, collection/search procedure, collection personnel, language scope, geographical scope, collection schedule, stopping rule, and any deviations. The current source-folder inventory alone does not establish these facts.

## Current Inclusion Boundary

The corrected release included the 980 Markdown notes located within the named source-folder structure after excluding 19 internal or administrative files outside that structure. The following criteria describe a future evidence-unit refinement and must not be represented as having been applied record by record in the current release:

1. It falls within the documented collection period and source scope.
2. Its provenance can be linked to a controlled source record; uncertain provenance is recorded as pending rather than silently treated as confirmed source evidence.
3. It contains assessable source material, such as attributable copied source text or a valid screenshot. Researcher-only notes remain available for coverage reporting, not substantive coding.
4. It relates to the prespecified study scope rather than solely to a collection-system test, navigation page, access failure, or unrelated material.
5. It can be assigned a stable privacy-safe record identifier and integrity hash.
6. Inclusion does not violate the approved ethics, legal, institutional, or anti-misuse boundary.

Image-only records may be eligible when the screenshot linkage is valid and the image is assessable. Short records must not be excluded solely because of word count; length is a validation and sensitivity stratum.

## Future Exclusion And Flagging Refinement

A future evidence-unit analysis should exclude or separately classify a record, while retaining a controlled exclusion log, when it is:

- an exact duplicate of another retained analytic record under the prespecified duplicate rule;
- a collection-system test, empty placeholder, or corrupted file;
- only an access error, login wall, loading screen, or unrelated navigation artefact;
- outside the documented source, date, language, or topic scope;
- missing enough provenance or content to support assessment;
- prohibited from analysis under the approved ethics or legal conditions.

Do not silently discard near duplicates, reposts, mirrors, inaccessible images, OCR failures, short records, or ambiguous material. Flag them and report their counts. Near duplicates should be retained or clustered according to the locked analysis plan, with a sensitivity analysis showing the consequence of the choice.

The historical design retained these conditions within the 980-record screen where they occurred and used exact-text and source sensitivity without resolving them. A revised treatment requires a controlled audit, documented decision, and complete downstream rerun.

## Provenance And Integrity Fields

The controlled master inventory should contain, at minimum:

| Field | Requirement |
|---|---|
| `record_id` | Stable privacy-safe identifier that does not expose a local path. |
| `source_id` | Controlled source identifier and publication-safe source group. |
| `record_type` | Post, listing, page, thread segment, researcher summary, collection log, error/access record, or other prespecified type. |
| `collection_datetime` | Time of capture with timezone where known; distinguish from source publication time. |
| `source_publication_datetime` | Source-displayed time where available, with uncertainty recorded. |
| `collector_role` | Coded collector identifier or role. |
| `markdown_sha256` | Hash of normalized Markdown content. |
| `image_sha256` | Hash for each linked local screenshot. |
| `image_link_status` | Resolved, unresolved, external, missing, or ambiguous. |
| `text_modality` | Markdown only, OCR only, both, or neither assessable. |
| `language` | Observed or assessed language and method of determination. |
| `inclusion_status` | Included, excluded, or pending. |
| `exclusion_reason` | One prespecified reason, with secondary flags allowed. |
| `duplicate_cluster_id` | Exact or reviewed near-duplicate cluster identifier. |
| `ethics_restriction` | Any record-specific restriction on access, quotation, or retention. |
| `protocol_version` | Version under which the record was processed. |

Absolute paths, handles, URLs, payment identifiers, account-like identifiers, and operational excerpts remain controlled and must not be placed in GitHub.

## Corpus Assembly Procedure

1. Freeze a read-only copy of the authorised vault and record a corpus-level integrity fingerprint.
2. Build the master note and image inventory without changing source files.
3. Resolve image links using normalized full reference paths; verify local files by hash rather than basename alone.
4. Record unresolved and external references without treating them as OCR failures.
5. Identify exact duplicate Markdown and image hashes before substantive counting.
6. Assign record types and apply inclusion/exclusion criteria independently of the study findings.
7. Join each eligible note to unique linked OCR text once per screenshot hash.
8. Record Markdown-only, OCR-only, and combined text fields separately.
9. Freeze the analytic inventory and exclusion log before final coding and validation.
10. Record every post-freeze change in a protocol-deviation log and regenerate downstream outputs.

## Historical Aggregate Screening Audit

The figures below were derived from the controlled Phase 1-3 aggregate inventory on 25 July 2026. They document what the historical pipeline did; they do not reconstruct source content, substitute for the missing locked inclusion/exclusion audit, or define the revised article population.

| Flow item | Historical aggregate count | Interpretation/status |
|---|---:|---|
| Markdown notes inventoried | 980 | Historical source-root screen; not an approved evidence-unit denominator. |
| Notes with date-like filename tokens | 948 | Of these, 947 parse as calendar dates and one is invalid (`2026-02-31`); 32 notes have no filename date. None is a verified capture date. |
| Historical source folders represented | 16 | The old structural screen used notes within named `Core Trace/<source folder>/` directories. Folder index 16 contains no Markdown notes; the next represented label is normalized to `17. XmrBazaar`. Folder membership alone does not establish source-evidence eligibility. |
| Image references | 1,140 | Reference occurrences, not unique screenshots. |
| Locally resolved image references | 1,048 | Current aggregate count; path-resolution audit required. |
| Unresolved, missing, or external image references | 92 | Must be classified and reported. |
| Unique local PNG files processed by OCR | 1,043 | Local image-path count; distinct from content-hash count. |
| Unique local image-content hashes | 1,037 | Six path-level image rows share content hashes with other images. |
| Combined records screened | 980 | Every current combined note record was passed to deterministic screening. |
| Unique combined-text hashes | 463 | Hash-level text uniqueness only; not proof of 463 unique posts, listings, actors, or evidence units. |
| Exact combined-text duplicate groups | 34 | Groups containing at least two identical combined-text hashes. |
| Exact combined-text duplicate excess | 517 | Difference between 980 screened records and 463 unique combined-text hashes. |
| Largest exact combined-text group | 99 | Requires controlled interpretation; repeated, empty, or boilerplate records may contribute. |
| Zero combined-word records | 65 | Must not be treated as substantive negatives without the eligibility audit. |
| Markdown-only records | 524 | Assessable modality count from the current combined inventory. |
| Markdown-and-OCR records | 391 | Assessable modality count from the current combined inventory. |
| OCR-only records | 0 | Current combined inventory. |
| Neither Markdown nor OCR assessable | 65 | Same count as zero combined-word records in the current inventory. |
| Internal project documents excluded before analysis | 19 | Excluded by the source-root eligibility rule before Phase 1 extraction. |
| Exact duplicate records removed before analysis | 0 | The 980-record screen was not deduplicated before Phase 3 coding. |
| Historical combined-note records | 980 | Earlier author-approved computational denominator; not the revised source-evidence population. |
| Historical human validation | Complete for the historical mixed-record sample | Ausma Bernot and Milind Tiwari independently coded 1,032 case-target units across 313 evidence packets; all 51 disagreements were jointly adjudicated on 26 July 2026. This exercise does not validate a revised source-evidence corpus. The earlier 1,036-unit result remains withdrawn. |

The 999-file archive, 19 structural exclusions, 980 historical screened records, 463 exact-text representatives, and 313 historical validation packets belong in an audit trail if discussed in the manuscript. A separate revised flow diagram must report independently reviewed source evidence, exclusions, image coverage, and validation cases. Historical Phase 3 and 4 counts are diagnostics for the mixed-record screen, not final substantive article estimates. The 463 unique hashes must not be called unique posts or a final eligible evidence-unit denominator.

## Collection Bias And Missingness

The collection report must distinguish:

- absence of a signal from failure to access or capture it;
- source size from substantive concentration;
- source-displayed dates from unverified filename-derived dates;
- source text from researcher-authored summaries;
- unique screenshots from repeated image references;
- genuine empty content from OCR failure;
- market closure or outage from a negative substantive observation.

Coverage should be reported by source, date, record type, text modality, and exclusion reason. No missing or inaccessible record may be recoded as evidence that a typology was absent.

## Ethics, Legal, And Researcher-Safety Requirements

Before submission, the authors must document:

- institutional ethics approval, waiver, exemption, or written determination, including institution and reference number;
- the rationale for observation without individual consent, where applicable;
- whether spaces were publicly accessible, registered-access, invitation-only, or private;
- whether researchers created accounts, interacted with users, joined private groups, made purchases, or used deception;
- applicable institutional cyber-safety, data-governance, legal, and platform-terms assessment;
- procedures for incidental personal information, suspected victim data, illegal content, and material outside the approved scope;
- researcher exposure minimisation, wellbeing support, and incident escalation;
- encryption, access control, logging, backup, retention, and destruction arrangements;
- quotation and paraphrase rules designed to prevent re-identification, source tracing, or operational misuse;
- whether source names may be published or must be generalised;
- the conditions under which editors or reviewers may receive time-limited controlled audit access.

The approved public ethics wording is “Griffith University Human Ethics Protocol 2025/697.” Consent or waiver rationale, access conditions, interaction status, retention, controlled-access authority, and the remaining items above still require confirmation from contemporaneous records or responsible institutional decision-makers. Repository redaction and aggregate-only publication are safeguards, not substitutes for ethics or legal review.

## Deviations And Change Control

The authors should assign this protocol a version and approval date before final corpus screening. Any later change to source scope, unit definitions, eligibility, duplicate handling, or ethics restrictions must be recorded with:

- date and approver;
- reason for the change;
- affected records and outputs;
- whether coding, validation, analysis, or tables were rerun;
- whether the change was made before or after viewing substantive results.

Changes made after results are known must be disclosed as post hoc. The final manuscript should cite the locked protocol version and describe material deviations.

## Author Sign-Off

Before the article submission is described as journal-ready, all authors must confirm:

- the collection account is complete and accurate;
- source and unit definitions match how the material was actually created;
- flow counts reconcile;
- exclusions and duplicate rules were applied consistently;
- ethics, legal, data-retention, and controlled-access statements are accurate;
- no corpus count is described as offender, victim, transaction, or external market prevalence.
