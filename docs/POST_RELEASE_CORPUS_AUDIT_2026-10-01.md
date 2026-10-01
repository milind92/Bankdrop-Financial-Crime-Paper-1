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

Four compound-rule positives appeared only after text from distinct note or
image artefacts was concatenated: three `crypto_to_bank_cashout` and one
`telegram_sales_or_proof`. This is a boundary sensitivity, not proof that the
four observations are false. Claims relying on them need artefact-level review.

The Phase 2 cache reports successful processing for all 1,043 referenced
local PNG paths. No human transcription gold set or OCR character/word error
rate has yet been verified. The 58 unreferenced images also lack an approved
source/date/eligibility decision. Neither gap can be closed by rewording the
Methods section alone.

## Release gate for a revised analysis

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
