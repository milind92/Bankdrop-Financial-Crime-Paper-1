# Data Collection Protocol

## Status And Purpose

This protocol defines the minimum provenance, sampling, inclusion, exclusion, and ethics information required to describe the Bank Drop corpus in a journal article. It is a prospective reporting and audit protocol. It does not assert that unresolved steps have already occurred.

Items marked **AUTHOR CONFIRMATION REQUIRED** must be completed from contemporaneous collection records or direct author knowledge. They must not be inferred from filenames, aggregate tables, repository history, or automated output.

The study concerns observed online material. It does not provide transaction data and cannot establish that an advertised product or service existed, was purchased, was delivered, or caused financial harm.

## Study Design

The planned study is a deterministic, computer-assisted content analysis of a controlled research vault containing researcher-maintained Markdown notes and referenced screenshots. The design is descriptive and exploratory. It maps signals visible in the captured corpus; it is not a prevalence study of an external criminal market.

The repository currently records a staged workflow in which Markdown content is inventoried, referenced screenshots are processed with local OCR, and the combined text is screened using a prespecified rule-based codebook. Human validation is governed separately by `docs/HUMAN_VALIDATION_PROTOCOL.md`.

## Research Scope

The collection protocol must support the following bounded questions:

1. Which prespecified financial-crime service, access, identity, coordination, trust, and monetisation signals are visible in eligible captured records?
2. How are validated signals distributed across the included source groups and text modalities?
3. Which signals co-occur within unique eligible records, without treating co-occurrence as proof of a transaction pathway?
4. Which observations may be framed as hypotheses for later AML research or expert assessment, rather than operational monitoring rules?

## Unit Definitions

| Unit | Definition | Permitted use |
|---|---|---|
| Source group | A named folder or documented collection stratum representing an online forum, market, search surface, or other source context. | Coverage and source-stratified description. It is not an independent population. |
| Markdown note | One Markdown file in the controlled vault. A note may contain researcher text, embedded links, metadata, or references to screenshots. | Inventory unit only until its creation method and relationship to underlying captures are confirmed. |
| Screenshot | One unique local image, identified by cryptographic file hash rather than filename alone. | Image-level provenance and OCR quality assessment. |
| Image reference | One link from a Markdown note to an image. Multiple references may point to the same screenshot. | Linkage and missingness reporting; not a count of unique images. |
| Combined note record | The normalized Markdown text for one note plus deduplicated OCR text from screenshots validly linked to that note. | Current screening record. It must not duplicate OCR merely because an image is referenced more than once. |
| Evidence unit | The underlying captured post, listing, page, thread segment, or other online artefact represented by a note or screenshot. | Preferred substantive unit where the collection log permits reconstruction. |
| Analytic record | One eligible, unique evidence unit or, where evidence-unit reconstruction is impossible, one eligible deduplicated combined note record. | Primary denominator for descriptive analysis. |
| Note-code row | One analytic record evaluated against one typology or AML-candidate definition. | Coding-table structure only. It is not an independent observation when multiple rows come from the same record. |
| Duplicate cluster | Two or more notes or screenshots with identical content hashes, or a separately documented near-duplicate relationship. | Sensitivity analysis and prevention of double counting. |

**AUTHOR CONFIRMATION REQUIRED:** State whether a Markdown note normally represents one post/listing, several captures, a daily collection log, a researcher summary, or a mixture. If the relationship varies, define record types and report counts for each type.

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

## Inclusion Criteria

A record is eligible for substantive analysis only when all applicable criteria are met:

1. It falls within the documented collection period and source scope.
2. Its provenance can be linked to a controlled source record or explicitly classified as `source_unknown`.
3. It contains interpretable researcher text, interpretable source text, or a valid screenshot from which text or visible context can be assessed.
4. It relates to the prespecified study scope rather than solely to a collection-system test, navigation page, access failure, or unrelated material.
5. It can be assigned a stable privacy-safe record identifier and integrity hash.
6. Inclusion does not violate the approved ethics, legal, institutional, or anti-misuse boundary.

Image-only records may be eligible when the screenshot linkage is valid and the image is assessable. Short records must not be excluded solely because of word count; length is a validation and sensitivity stratum.

## Exclusion And Flagging Criteria

Exclude a record from the primary substantive denominator, while retaining a controlled exclusion log, when it is:

- an exact duplicate of another retained analytic record under the prespecified duplicate rule;
- a collection-system test, empty placeholder, or corrupted file;
- only an access error, login wall, loading screen, or unrelated navigation artefact;
- outside the documented source, date, language, or topic scope;
- missing enough provenance or content to support assessment;
- prohibited from analysis under the approved ethics or legal conditions.

Do not silently discard near duplicates, reposts, mirrors, inaccessible images, OCR failures, short records, or ambiguous material. Flag them and report their counts. Near duplicates should be retained or clustered according to the locked analysis plan, with a sensitivity analysis showing the consequence of the choice.

**AUTHOR CONFIRMATION REQUIRED:** Approve the treatment of reposts, mirrors, translated copies, daily collection logs, source-unknown notes, access/error pages, and records containing multiple underlying posts.

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

## Current Aggregate Screening Audit

The figures below were derived from the controlled Phase 1-3 aggregate inventory on 25 July 2026. They safely document what the existing pipeline did; they do not reconstruct source content or substitute for the missing locked inclusion/exclusion audit.

| Flow item | Current aggregate count | Interpretation/status |
|---|---:|---|
| Markdown notes inventoried | 980 | File inventory; eligibility and unique evidence-unit count remain to be confirmed. |
| Eligible source groups represented | 16 | Only notes within named `Core Trace/<source folder>/` directories are eligible. Folder index 16 exists but contains no Markdown notes; the next represented label is normalized to `17. XmrBazaar`. |
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
| Eligible unique analytic records | **AUTHOR CONFIRMATION REQUIRED** | This becomes the primary descriptive denominator. |
| Human validation | Withdrawn | The prior sample contained 14 ineligible internal documents (59 paired case-target units); fresh corrected-corpus validation is required. |

The final manuscript should include a flow diagram or table showing identified, screened, excluded, deduplicated, eligible, validated, and analysed records. Counts must reconcile across the controlled inventory, manuscript, tables, and machine-readable manifest. Until the authors complete the collection and eligibility audit, the existing Phase 3 and 4 counts must be described as descriptive signals among 980 screened combined note records, with exact-text sensitivity reported separately. The 463 unique hashes must not be called the final eligible denominator.

## Collection Bias And Missingness

The collection report must distinguish:

- absence of a signal from failure to access or capture it;
- source size from substantive concentration;
- source-displayed dates from filename-derived collection dates;
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

**AUTHOR CONFIRMATION REQUIRED:** Complete every item above. Repository redaction and aggregate-only publication are safeguards, but they are not substitutes for institutional ethics or legal review.

## Deviations And Change Control

The authors should assign this protocol a version and approval date before final corpus screening. Any later change to source scope, unit definitions, eligibility, duplicate handling, or ethics restrictions must be recorded with:

- date and approver;
- reason for the change;
- affected records and outputs;
- whether coding, validation, analysis, or tables were rerun;
- whether the change was made before or after viewing substantive results.

Changes made after results are known must be disclosed as post hoc. The final manuscript should cite the locked protocol version and describe material deviations.

## Author Sign-Off

Before the corpus is described as journal-ready, all authors must confirm:

- the collection account is complete and accurate;
- source and unit definitions match how the material was actually created;
- flow counts reconcile;
- exclusions and duplicate rules were applied consistently;
- ethics, legal, data-retention, and controlled-access statements are accurate;
- no corpus count is described as offender, victim, transaction, or external market prevalence.
