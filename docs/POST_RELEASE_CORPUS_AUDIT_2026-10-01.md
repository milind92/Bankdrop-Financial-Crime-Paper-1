# Post-release corpus audit — 1 October 2026

## Status

This post hoc audit places the Paper 1 supplement **on methodological hold**.
Release `v1.3.3` remains a reproducible historical screen of 980 combined note
records. Its substantive percentages, duplicate sensitivity, source
comparisons, co-occurrences, AML interpretations, and human-validation
performance must not be treated as final article results while the revised
evidence boundary is established. The audit has not produced a new final
eligible denominator or replaced the historical aggregate tables.

The audit inspected the frozen controlled source archive, its Phase 1–3
intermediates, and a fresh Phase 1–4 replay of the current repository code.
No raw notes, screenshots, OCR, excerpts, record identifiers, or local source
paths are released here. The record-level audit and review queues remain in
controlled storage.

## Confirmed inventory and reproducibility

| Item | Count | Boundary |
|---|---:|---|
| Markdown files in the frozen archive | 999 | 19 internal files were structurally excluded from the historical screen. |
| Historical screened combined notes | 980 | Includes collection and researcher notes; not a final evidence-only denominator. |
| Image-reference occurrences | 1,140 | 1,048 resolved, 7 missing, 85 external. |
| Referenced local PNG paths OCR-processed or cache-replayed | 1,043 | 1,037 distinct image-content hashes; OCR completion is not accuracy. |
| PNG paths in the frozen archive | 1,101 | Inventory includes images never referenced in Markdown. |
| Unreferenced PNG paths | 58 | 22 duplicate referenced content; 36 files contain 35 novel-content hashes. |

The fresh controlled replay reproduced all historical note-level binary Phase
3 classifications and the public per-code note counts. The old computation is
repeatable. The methodological concern is which records and text segments
represent captured source evidence.

Of the 980 screened notes, 948 have date-like filename tokens and 32 are
undated. Only 947 tokens are valid calendar dates (17 February to 24 June
2026); one token is the impossible date `2026-02-31`. A controlled exception
sheet now isolates that note for author review. Filename tokens do not
establish source-post dates or the actual visit schedule. The old July article
draft's earlier start date came from project material outside the screened
source-note date range.

The 947 valid note-filename tokens occupy 97 distinct calendar days within
the inclusive 128-day token span. Thirty-one days have no note filename
token. These are filename-coverage counts, not evidence of visits on the
other days or missed collection on the days without a note.

Controlled project notes describe an **intended** 15-source daily-tracing
procedure, while the historical screen represents 16 source groups. Groups
numbered 1-15 have screened notes; folder 16 is empty in the checked extract;
and group 17 supplies six screened Markdown files, including three zero-byte
placeholders (one dated and two undated). A 7 May 2026 meeting note discusses
the sites corresponding to groups 16 and 17 as potentially useful, but does
not document when either was selected or captured. Four group-17 note
filenames carry June 2026 date tokens. This
narrows the source-frame discrepancy without proving that groups 1-15 were
the original November selection or that group 17 was a planned addition.
A task table's collection-start entry carries a year earlier than later
source-selection and equipment-setup entries; whether they concern the same
collection phase is unresolved. The original preparers must explain the
chronology and source-frame changes. These records do not verify the actual
start date or daily visit schedule.

A separate controlled filename check found 1,032 resolved note/image
assignments with parseable note-date and pasted-image filename timestamps.
Their calendar days match in 704 cases and differ in 328: nine image-name
dates are earlier than the note token and 319 are later. Fifteen resolved
image filenames were not parseable by the expected timestamp pattern; one
linked note has a blank date token. A 41-row priority queue isolates earlier
images, gaps over 30 days, and unparseable or blank dates. An image filename
may reflect pasting or saving rather than capture. Neither the matches nor
the mismatches certify a source-post date or collection visit.

The current schema-v3 controlled review gate treats capture dates and
source-displayed publication dates separately. Included images require their
own source and capture-date-basis decisions; a verified capture date needs a
contemporaneous record locator. Revised unit dates remain blank if the
approved spans have unknown or different capture dates. The gate has only
blank worksheets and synthetic tests so far; it has not verified the actual
collection schedule.

## Record provenance and denominator

Among the 980 screened notes, 589 had no usable joined OCR. A preliminary
manual review of their 47 distinct normalized Markdown bodies classified 511
as collection-status/access notes, 64 as collector instructions or
assessments, 11 as researcher-written source profiles, and three as search
keyword tables. These classifications are post hoc auditor decisions awaiting
independent author review. The other 391 notes have linked OCR and are
**candidate** evidence records pending note, image, and text-provenance review;
391 is not an approved replacement denominator.

Ten no-OCR researcher records generated at least one substantive typology
positive. The accompanying [aggregate diagnostic table](../outputs/analysis_audit/record_type_sensitivity_20261001.csv)
shows, for each historically positive code, how many positives came from no-OCR notes
and how many occurred in OCR-linked candidates. Within OCR-linked notes,
Markdown sometimes contains copied source material and sometimes contains
researcher text. An OCR-only analysis would discard some copied source text;
a combined-text analysis without segment provenance can code research notes
as source observations. Both channels require provenance review.

A provisional 391-note modality sensitivity confirms that switching to OCR
alone would lose candidate signals: `fullz_identity_package` falls from 120
combined-note positives to 106 OCR-only positives. In the historical
OCR-linked validation subset, the OCR-only rule retained 12 of 19 true
positives for that target, with zero false positives under either modality.
These are post hoc diagnostics on unadjudicated candidates, not final article
estimates. The revised method should retain Markdown passages only when their
source provenance is confirmed and screen separate images within justified
artefact boundaries.

The historical exact-text sensitivity set has 463 representatives. Only 389
are from OCR-linked candidate records; 74 are distinct no-OCR research/status
texts. Accordingly, the reported 517 duplicate excess records are not a
measure of repeated marketplace posts.

A [controlled revised duplicate-sensitivity procedure](../code/derived_analysis/METHODS_REVISED_DUPLICATE_SENSITIVITY.md)
is available for a future author-approved evidence corpus. It preserves
approved span boundaries and counts identical span-content signatures, not
verified identical posts. No revised duplicate count has been produced.

## Validation and joined-text limitation

The historical human exercise remains documented: 1,032 paired case-target
rows from 313 packets, 981 exact agreements, and 51 jointly adjudicated
disagreements. Its sample contains 191 rows from 15 no-OCR research/status
notes. The historical pooled agreement and per-target classifier performance
apply to that mixed sample, not to a future evidence-only corpus. The revised
sampling frame and any changed code definitions require a fresh blinded
validation holdout. The prior decisions can inform an error-diagnosis pilot;
they cannot replace validation of the new frame or changed constructs.

A post hoc subset calculation using the frozen independent coder decisions
found 792/841 exact agreements (94.2%; five-category Cohen's kappa 0.834)
among OCR-linked candidate case-target rows. The no-OCR subset had 189/191
agreements (99.0%; kappa 0.828). The all-row calculation reproduces 981/1,032
and kappa 0.839. Thus the concern is corpus and sampling validity, not a claim
that the coders failed to agree on the remaining cases. These subset figures
are diagnostic and are not revised-corpus validation results.

The historical classifier's low target precision persists within that
OCR-linked subset: among sampled predicted-positive cases, the cash-out
service rule had 2 true positives and 18 false positives, while the
crypto-to-bank AML candidate had one true positive and 19 false positives.
These unweighted diagnostics do not estimate performance on a revised corpus.
Pattern-level checks show that the generic cash-out-term rule and broad
crypto-to-bank word-proximity rule account for these sampled false positives.
The associated labels imply a service or conversion relationship that the
lexical rules alone do not establish. The targets need refinement or narrower
interpretation followed by independent validation.

Four compound-rule positives appeared only after text from distinct note or
image artefacts was concatenated: three `crypto_to_bank_cashout` and one
`telegram_sales_or_proof`. This is a boundary sensitivity, not proof that the
four observations are false. Claims relying on them need artefact-level review.

The Phase 2 cache reports successful processing for all 1,043 referenced
local PNG paths. No human transcription gold set or OCR character/word error
rate has yet been verified. The 58 unreferenced images also lack an approved
source/date/eligibility decision. Neither gap can be closed by rewording the
Methods section alone.

Version `1.3.7` adds a pre-reveal transcript lock to the [blinded OCR-quality procedure](../code/ocr_quality/METHODS_OCR_QUALITY.md).
Its controlled, fixed-seed probability sample selects 50 distinct image
hashes from the 1,037-hash historical referenced-image frame across 15 source
strata, with recorded selection probabilities and hash-checked screenshot
copies. All transcript and review fields are blank; no error rate is reported.
The earlier unreviewed sample deliberately included OCR-length extremes and
would not justify an unweighted population-wide accuracy estimate. The new
sample still requires a coverage check against the future approved corpus and
any novel orphan images it includes.

Version `1.3.8` adds controlled per-span Phase 3 coding and a
[pair-boundary diagnostic](../code/derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md).
The diagnostic can separate codes found in one approved text span from codes
found only in different spans of a capture unit. No revised pair counts exist
for the unreviewed real corpus, and this does not resolve duplicate, source,
OCR, or target-validation concerns.

Version `1.3.9` adds a [guarded revised holdout procedure](../code/human_validation/METHODS_REVISED_HOLDOUT.md).
It includes short approved source units in the predicted-negative frame and
requires a hash-bound, author-approved allocation and precision plan before
a probability draw. Only synthetic gate tests have run; the real review sheets,
source-evidence frame, coder work, and revised performance estimates remain
pending.

Version `1.3.10` adds a controlled closeout scorer. It verifies two locked
independent coder sheets and privacy-checked evidence packets, locks
adjudicated human decisions before reading deterministic predictions, and
computes per-target estimates with finite-population uncertainty for a future
approved holdout. Synthetic tests alone exercise this path. It has not
produced a revised study result.

A separate controlled, blank collection-provenance packet reconciles the
historical 980 notes, 948 date-like filename tokens, 391 OCR-linked candidate
notes, and 1,140 image-reference occurrences across 16 source groups. Its
questions and per-source fields seek confirmation from the original preparers;
no collection-process answer or source-specific eligibility decision is yet
verified.

## Release gate for a revised analysis

Version `1.3.5` adds a [controlled evidence-screening gate](../code/evidence_screening/METHODS_EVIDENCE_SCREEN.md).
It has generated blank, hash-bound review sheets for all 980 notes, 1,048
linked note/image assignments, 92 unresolved references, and 58 unlinked PNG
paths. No author decisions or approved source-text spans have been entered;
the gate currently refuses to build a revised corpus. A future approved run
will code each source span within its own artefact boundary. The current
Phase 4 interpretations and historical human validation cannot automatically
carry over to that run.

1. Confirm the collection and note-creation procedure from contemporaneous
   records and responsible authors, including source/date attribution and
   whether Markdown passages are copied content, paraphrase, or collector
   commentary.
2. Independently review the 391 OCR-linked candidate notes and the 58
   unreferenced PNG paths, documenting exclusions, missingness, image links,
   and any separate image-level evidence units. Keep collection-status notes
   for coverage analysis outside the substantive negative denominator.
3. Freeze the revised record and text-segment inclusion decisions, then rerun
   the deterministic coding, aggregate analyses, and claims register. Bound
   compound matches to justified source artefacts.
4. Measure OCR quality on a fixed, human-transcribed image sample. Reassess
   low-precision code definitions and validate the revised corpus/design with
   independent human judgments where required.
5. Reconcile the manuscript, all tables, workflow manifest, and controlled
   reproducibility record before lifting this hold.

Until then, all numeric output files in this checkout are historical
computational outputs. They are retained for transparency and regression
checking, not approved article estimates.
