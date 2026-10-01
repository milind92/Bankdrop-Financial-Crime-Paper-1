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

Of the 980 screened notes, 948 have filename-derived dates from 17 February
to 24 June 2026 and 32 are undated. Filename dates do not establish source-post
dates or the actual visit schedule. The old July article draft's earlier start
date came from project material outside the screened source-note date range.

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

## Validation and joined-text limitation

The historical human exercise remains documented: 1,032 paired case-target
rows from 313 packets, 981 exact agreements, and 51 jointly adjudicated
disagreements. Its sample contains 191 rows from 15 no-OCR research/status
notes. The historical pooled agreement and per-target classifier performance
apply to that mixed sample, not to a future evidence-only corpus. The revised
sampling frame and any changed code definitions require a new validation
assessment; prior human decisions may be reusable only after their eligibility
and sampling weights are checked.

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
