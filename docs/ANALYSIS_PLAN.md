# Analysis Plan

## Status And Scope

This plan defines the analyses required for the deterministic, no-LLM journal study. It is prospective for the final validated analysis. Existing aggregate outputs are screening results and must not be treated as final merely because they are reproducible.

The study analyses observed online content in a captured corpus. It does not estimate offender, victim, transaction, financial-loss, or external market prevalence. It does not establish that advertised goods or services existed, were delivered, or were used.

## Analysis Questions

1. Which validated, prespecified typology signals are present in eligible unique records?
2. How are those signals distributed across source groups and Markdown/OCR modalities?
3. Which signals co-occur within records, and how stable are those relationships across sources and duplicate handling?
4. Which aggregate observations can be framed cautiously as research hypotheses for AML expert assessment?

The analysis is descriptive and exploratory. Co-occurrence is not evidence of temporal sequence, coordination between actors, causal linkage, or a completed service chain.

## Data And Version Lock

Before final analysis, lock and hash:

- the approved data-collection protocol;
- the master analytic inventory and exclusion log;
- exact-duplicate and reviewed near-duplicate assignments;
- the final codebook;
- the human-validation results and adjudication log;
- the deterministic coding output produced with the validated rules;
- the analysis code, software environment, and random seeds;
- a claim register mapping every manuscript result to its source table and validation status.

If human validation changes a definition or pattern, rerun the entire deterministic corpus before producing final tables. Do not manually alter aggregate counts.

## Primary Analytic Denominator

The primary denominator is the number of eligible unique analytic records after applying the locked inclusion, exclusion, and exact-duplicate rules in `docs/DATA_COLLECTION_PROTOCOL.md`.

The denominator is not:

- the number of note-code rows;
- the number of regex hits;
- the number of image references;
- the number of screenshots where one image is referenced repeatedly;
- the total number of files before eligibility screening;
- an estimate of the size of any external market.

Where one Markdown note contains multiple underlying posts or listings, the authors must either reconstruct evidence units or explicitly retain the note as a composite record and describe the resulting unit limitation.

**AUTHOR CONFIRMATION REQUIRED:** Approve the final primary unit and denominator after the corpus audit. Report the full-data and deduplicated denominators side by side.

### Current Implementation Audit

The completed deterministic screen evaluated all 999 combined note records. The controlled aggregate audit found 479 unique combined-text hashes, 34 exact duplicate groups, 520 exact duplicate excess records, and 68 zero-word combined records. No locked inclusion/exclusion log or pre-analysis deduplication was applied before Phase 3 coding. Consequently:

- existing Phase 3 and 4 counts are full-screened-record descriptive results, not results from a final eligible deduplicated population;
- 479 unique hashes are a duplicate-sensitivity denominator, not a verified count of unique posts, listings, actors, transactions, or evidence units;
- zero-word and otherwise unassessable records must not be treated as substantive negatives in a prevalence or classifier-performance claim;
- the final manuscript must disclose this implementation boundary and may not claim that the prospective primary-denominator procedure was completed;
- any later eligibility or evidence-unit audit that changes the denominator requires a complete deterministic rerun and a documented deviation.

Publication-safe deterministic post-processing now reports the full 999-record screen beside a 479-record exact-combined-text-hash sensitivity population. The added tables cover source-normalized typology reporting, typology co-occurrence, source-stratified and leave-one-source-out co-occurrence stability, AML-candidate overlap, duplicate sensitivity, exploratory functional unions, source concentration, and leave-one-source-out counts. This implementation does not resolve the prospective primary-denominator decision, near-duplicate treatment, image-hash deduplication, modality sensitivity, or a final eligibility/exclusion log.

## Analysis Populations

| Population | Definition | Purpose |
|---|---|---|
| Primary deduplicated population | Eligible records with one retained representative per exact duplicate cluster. | Main descriptive results. |
| Full eligible population | All eligible records before exact-duplicate removal. | Duplicate sensitivity analysis. |
| Human-validation holdout | Locked, probability-documented validation sample. | Reliability and deterministic-code performance only. |
| Markdown-assessable population | Eligible records containing assessable Markdown text. | Markdown-only sensitivity. |
| OCR-assessable population | Eligible records containing assessable, validly linked OCR text. | OCR contribution and error sensitivity. |
| Combined-text population | Eligible records with normalized Markdown plus deduplicated OCR text. | Main rule application where both modalities are permitted. |

Records may belong to more than one modality population. Missing or unavailable OCR must not be treated as a substantive negative.

## Descriptive Corpus Reporting

Report the following before typology results:

- identified, screened, excluded, duplicate-clustered, eligible, validated, and analysed counts;
- exclusions by prespecified reason;
- named source groups plus the source-unknown group;
- notes and eligible analytic records per source;
- dated and undated records, distinguishing collection date from source-displayed date;
- Markdown words, image references, resolved references, unique screenshot hashes, missing references, OCR successes, OCR empty results, and OCR errors;
- record type, language, text modality, and length distribution;
- exact duplicate clusters by source and cross-source status;
- source access failures and collection interruptions.

Use totals and denominators in every table. A label such as `OCR OK` must state whether it counts unique screenshots, successful reference occurrences, or notes with at least one successful OCR result.

## Typology Prevalence Within The Corpus

For each validated typology, calculate:

- number of unique eligible records coded present;
- proportion of the primary analytic denominator;
- number and proportion by source group;
- number and proportion by modality;
- number of deterministic hits as a supplementary rule-diagnostics measure only;
- validation status and code-level performance interval;
- contribution from records appearing only in the full, non-deduplicated population.

The unit-level binary presence measure is primary. Repeated terms within a record are not independent events and must not be described as incidents.

### Multi-Label Warning

Typologies are non-mutually exclusive unless the final codebook explicitly states otherwise. A single record may contribute to several typologies. Therefore:

- typology percentages need not sum to 100%;
- summed typology counts are not a count of unique criminal events or service chains;
- a “criminal objective” grouping must use the union of unique records within each higher-order category, not the sum of component-code counts;
- uncertainty and clustering must be handled at the unique-record level.

Every typology table must include this warning in a note.

## Source-Normalized Analysis

Raw source counts are strongly influenced by source size. For each typology and source, report:

- records present divided by eligible records in that source;
- numerator and denominator, not percentage alone;
- source share of all records positive for that typology;
- text-modality coverage and missingness for that source;
- validation performance where sample size permits.

Do not label a typology “dominant” in a source solely because it has the largest raw count. Use within-source proportions and uncertainty, and disclose small denominators.

### Source Concentration

For each typology, calculate:

1. the percentage of positive records contributed by the largest source;
2. the cumulative percentage contributed by the three largest sources;
3. a descriptive concentration index, such as the Herfindahl-Hirschman index, using source shares among positive records;
4. leave-one-source-out counts, proportions, and rank order.

If a finding disappears, changes rank materially, or reverses after removing one source, describe it as source-concentrated rather than corpus-wide.

## Co-Occurrence Analysis

Construct one binary record-by-code matrix from the primary deduplicated population. For every prespecified code pair, report:

- `n11`: records with both codes;
- `n10`: records with the first code only;
- `n01`: records with the second code only;
- `n00`: records with neither code;
- marginal counts and the eligible denominator;
- Jaccard similarity;
- lift;
- source-stratified and leave-one-source-out stability where counts permit.

Use:

`Jaccard(A,B) = n11 / (n11 + n10 + n01)`

and:

`Lift(A,B) = (n11 / N) / ((nA / N) * (nB / N))`

Interpretation rules:

- Jaccard describes overlap among records containing either code.
- Lift above 1 describes greater co-occurrence than expected from the two observed marginal frequencies within this corpus.
- Neither measure establishes direction, chronology, shared actors, transactions, or causation.
- Pairs with very small support must be suppressed, pooled cautiously, or labelled unstable.
- Code pairs and higher-order service-chain groupings should be prespecified from theory and the locked codebook. Exploratory pairs must be labelled post hoc.

The manuscript may describe a connected service infrastructure only when the claim is supported by validated co-occurrence patterns, source-stability checks, and evidence-bound qualitative interpretation. Marginal rankings alone are insufficient.

## Higher-Order Functional Grouping

If the article uses access, identity, coordination/trust, monetisation, recruitment, or other higher-order functions:

1. map each validated code to a function before final analysis;
2. allow documented multi-membership where conceptually justified;
3. calculate unique-record union counts for each function;
4. report within-function overlap rather than copying code counts;
5. validate the mapping with authors and relevant domain expertise;
6. distinguish substantive functions from data-quality flags.

**AUTHOR DECISION REQUIRED:** Approve the theoretical framework and code-to-function mapping before the final analysis is opened.

## AML-Candidate Analysis

AML candidates are analysed as corpus-derived hypotheses only. For each candidate, report:

- the locked compound definition;
- unique-record count and corpus proportion;
- source and modality distribution;
- human content-validation metrics;
- AML domain-review outcome;
- explicit evidence boundary and alternative interpretations.

Country names, payment terms, communication-platform names, escrow terms, or other isolated keywords are not sufficient on their own to establish preference, conversion, recruitment, risk, or laundering behaviour. No table may label a candidate as a confirmed red flag, suspicious-activity indicator, detection rule, or monitoring control.

## Exact-Duplicate Sensitivity

Exact duplicates must be identified using normalized Markdown hashes and image file hashes. Run the main typology, source, functional-group, and co-occurrence analyses on:

1. the primary deduplicated population; and
2. the full eligible population before exact-duplicate removal.

For each result, report:

- absolute count difference;
- percentage-point difference;
- change in typology rank;
- change in source concentration;
- change in Jaccard and lift for highlighted code pairs.

Where the same screenshot hash is linked repeatedly, OCR text should contribute once to the relevant evidence unit. Cross-source duplicate clusters should be separately flagged because they may represent copied listings or shared page material rather than independent observations.

Near-duplicate analysis may be exploratory, but its method and threshold must be documented and its results kept separate from exact-hash deduplication.

## Modality And OCR Sensitivity

Repeat key descriptive results using:

- Markdown text only;
- OCR text only;
- combined text with each unique screenshot represented once;
- a subset passing the prespecified OCR-quality review.

Report which codes depend heavily on OCR, how often OCR creates or removes a classification after human review, and whether OCR error is concentrated by source. A nonempty OCR response is not an accuracy measure.

## Source And Record-Length Sensitivity

Assess whether findings are driven by unequal text volume or source structure:

- report within-source record prevalence;
- optionally report hits per 1,000 words as rule diagnostics, never as incident rates;
- repeat key results across prespecified record-length bands;
- retain short records in sensitivity analyses;
- repeat results after excluding access/error records and interface-heavy records;
- report source-unknown records separately and with them excluded.

## Human-Validation Integration

The final analysis must use the locked post-validation codebook and a complete rerun. Report:

- coder agreement before adjudication;
- adjudicated confusion matrices and 95% intervals;
- code changes prompted by the pilot;
- fresh-holdout results for any revised code;
- ambiguous and insufficient-evidence counts;
- weighted estimates where the holdout used unequal sampling probabilities.

Do not mechanically “correct” full-corpus counts using a small unweighted validation rate. If design-based adjustment is attempted, specify the estimator, stratum weights, clustering, assumptions, and uncertainty, and retain the observed validated-rule counts as the primary transparent result.

### Completed Human-ICR Reporting

The repository now includes publication-safe target-level human ICR results for all 18 assessed targets. Each row reports the paired-unit denominator, exact agreement with a Wilson 95% interval, Cohen’s kappa with a deterministic paired-unit bootstrap interval, nominal Krippendorff’s alpha, binary-subset kappa and Gwet AC1, and aggregate adjudication outcomes. These intervals describe the controlled validation sample only. Original independent decisions remain frozen, and the 59 consensus decisions were not substituted into the reliability calculation.

## Statistical Inference Boundary

The corpus is not currently documented as a probability sample of an external population. Therefore:

- corpus proportions are descriptive of eligible captured records only;
- confidence intervals for validation performance quantify uncertainty in the validation sample, not market prevalence;
- no p-value or interval may be used to imply population representativeness;
- source comparisons are descriptive unless a defensible sampling model is established;
- low observed counts do not establish that a phenomenon is rare outside the corpus;
- missing records, private-channel migration, and source outages limit absence claims;
- co-occurrence does not establish a pathway, sequence, organisation, or causal mechanism.

Any later inferential model requires a separate prespecified sampling and modelling justification.

## Deterministic Empirical Boundary

The repository’s empirical workflow is limited to deterministic Phases 1–4. Phase 2 uses local OCR, which is not an LLM stage. No Phase 3b, Phase 4b, Phase 5, or LLM-assisted empirical analysis is included.

OpenAI Codex assistance outside the empirical workflow is disclosed separately. Codex did not generate coding responses, classify or interpret evidence, calculate or assess agreement, resolve disagreements, adjudicate cases, or make methodological or substantive decisions.

## Planned Tables And Figures

The main article should contain, subject to the target journal's limits:

1. corpus-flow and coverage table with complete denominators and missingness;
2. validated typology table with unique-record counts, proportions, source concentration, and validation status;
3. human-validation table with agreement, confusion metrics, and 95% intervals;
4. source-normalized typology table or figure;
5. prespecified co-occurrence matrix or network with support, Jaccard, and lift;
6. AML-hypothesis table with human and expert-review boundaries;
7. duplicate, OCR, and leave-one-source-out sensitivity summary.

Reproducibility inventories, software details, full source profiles, and extended sensitivity tables belong in the supplement rather than the substantive results section.

## Claim-To-Evidence Register

Before manuscript submission, maintain a register with:

- claim identifier and exact manuscript wording;
- research question;
- analytic population and denominator;
- source table and code version;
- validation result and uncertainty;
- duplicate/source/OCR sensitivity result;
- ethics or disclosure restriction;
- status: supported, qualified, exploratory, withdrawn, or author confirmation required.

A claim must be withdrawn or softened when its validation, sensitivity, or evidence boundary does not support the proposed wording.

## Deviations And Reproducibility

Record all deviations from this plan with date, rationale, approver, whether results had been viewed, and affected outputs. Label analyses conceived after inspecting results as exploratory.

The final release should include deterministic analysis code, aggregate inputs sufficient to recreate publication tables where safe, a synthetic test fixture, codebook and protocol versions, environment metadata, and integrity hashes. Raw or sensitive evidence remains controlled under the data-availability and audit-access policy.

## Author Decisions Required Before Lock

- target journal, article type, and reporting constraints;
- final primary unit and corpus denominator;
- theoretical functional grouping;
- exact and near-duplicate treatment;
- minimum support for reported co-occurrences;
- claim-specific validation-performance thresholds;
- publication-safe source labels;
- AML domain-review personnel and decision rules;
- treatment of source-unknown, multilingual, composite, access/error, and interface-heavy records;
- final ethics and controlled-access wording.
