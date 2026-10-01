# Revised source-evidence human-validation holdout

## Status and purpose

This is a guarded **future** holdout procedure. The real source-evidence review
and target definitions are unfinished. No revised sample, coder decisions,
classification performance, or article-ready result exists. The July 2026
1,032 case-target judgments validate only their historical mixed-record
sample. Do not move them into this new frame or call them a validation of the
revised corpus.

The estimand is performance of each frozen deterministic target rule on the
finite set of **approved, assessable source-evidence capture units**, after
documented pilot exclusions. Capture units are not assumed to be unique posts,
transactions, actors, or a probability sample of an outside market.

## Before preparing the frame

1. Complete the independent source, Markdown-span, image-link, and orphan-image
   review in `code/evidence_screening/METHODS_EVIDENCE_SCREEN.md`; build its
   controlled `approved_evidence_units.jsonl`.
2. Freeze target definitions with inclusion and exclusion rules, distinction
   between broad mention and narrower service/transaction constructs, and
   treatment of quoted, negated, interface, and OCR-uncertain text. Make a
   controlled human decision codebook. Rerun revised Phase 3 with the matching
   deterministic codebook. The Phase 3 metadata records the generated rule
   codebook SHA-256; the holdout pins both that file and the human codebook.
3. Use a development pilot to resolve coder instructions. Record its approved
   unit IDs in a controlled CSV with header `unit_id`. An empty file with that
   header is valid only if the authors affirm that no pilot units need
   exclusion. The tool removes listed pilot units **and any units with exactly
   the same approved combined-text hash**, preventing an identical capture
   from entering both pilot and holdout. Near duplicates require human review
   and may require additional exclusions before the frame is locked.
4. Write a target-specific precision and feasibility rationale. State the
   intended positive predictive value and sensitivity precision, expected
   non-assessable fraction, any rare-code census, and the coding budget. The
   tool enforces valid quotas and author sign-off; it cannot judge whether a
   chosen quota is scientifically precise enough. The [US Census Bureau's
   Statistical Quality Standard A3](https://www.census.gov/about/policies/quality/standards/standarda3.html)
   likewise calls for a defined target population, key estimates, precision,
   frame, selection probabilities, and documented weighting.

## Frame and selection

The sampling unit is one approved capture unit **for one target code**. All
approved source units with nonempty approved text enter every applicable
target frame, including units shorter than 30 words. `market_access_limitation`
is a collection-quality flag and is not a substantive validation target.

For each target, the tool crosses deterministic predicted status (positive or
negative) with approved-text length (`short`: fewer than 30 words; `long`: 30
or more). The 30-word boundary ensures the short predicted-negative records
excluded from the historical holdout are assessed; it is a sampling stratum,
**not** an eligibility cutoff. A simple random sample without replacement is
drawn independently within every nonempty stratum. An author-approved quota
must cover each stratum; where its population exceeds one, at least two draws
are required. A one-unit stratum is censused. The conditional inclusion
probability for a unit-target judgment is exactly `n_h / N_h`, and its
inverse-probability weight is `N_h / n_h`.

The controlled frame and machine key retain source, Markdown/OCR modality,
approved-text length, exact duplicate cluster hash and size, target, machine
status, stratum population/sample size, probability, and weight. Source and
duplicate composition must be inspected **before** making source-specific or
unique-content claims. This design does not guarantee a useful sample in
every source group or for every trigger family. Any purposive diagnostic cases
added later must be labelled separately and excluded from weighted estimates.
If source-specific performance is a primary estimand, revise and approve the
sampling design before drawing.

## Controlled commands

All paths below are controlled and outside the public repository. The
`--human-codebook` file must contain the actual human inclusion/exclusion
definitions, not only regex patterns.

```powershell
python .\code\human_validation\prepare_revised_holdout.py prepare `
  --phase3-dir $env:BANK_DROP_REVISED_PHASE3_DIR `
  --evidence-corpus $env:BANK_DROP_EVIDENCE_CORPUS `
  --pilot-units $env:BANK_DROP_PILOT_UNITS `
  --human-codebook $env:BANK_DROP_HUMAN_CODEBOOK `
  --output-dir $env:BANK_DROP_REVISED_FRAME_DIR
```

This writes `validation_frame.csv`, `frame_manifest.json`, and
`allocation_plan_template.json`. The template is **draft** and has blank
quotas and approvals. Fill every quota, the overall and per-target precision
rationales, a precommitted integer seed, two distinct author names, ISO
approval date, and the two frozen/exclusions-final flags. Save a separate
approved plan; do not overwrite the draft without preserving its history.

```powershell
python .\code\human_validation\prepare_revised_holdout.py draw `
  --phase3-dir $env:BANK_DROP_REVISED_PHASE3_DIR `
  --evidence-corpus $env:BANK_DROP_EVIDENCE_CORPUS `
  --pilot-units $env:BANK_DROP_PILOT_UNITS `
  --human-codebook $env:BANK_DROP_HUMAN_CODEBOOK `
  --frame-dir $env:BANK_DROP_REVISED_FRAME_DIR `
  --plan $env:BANK_DROP_APPROVED_SAMPLE_PLAN `
  --output-dir $env:BANK_DROP_REVISED_SAMPLE_DIR
```

The draw recomputes the frame, checks all pinned SHA-256 values, verifies the
complete target matrix and per-span hit reconciliation, and refuses a
nonempty output directory. It writes a separate coordinator machine key and
two blank, randomized coder sheets. The coder sheets contain opaque case IDs
and target codes, **no machine predictions, weights, sources, unit IDs, or
text**. The coordinator must create privacy-screened evidence packets keyed
to the case IDs and check that each packet supplies enough context without
exposing the machine output. The script does not create these packets.

## After independent coding

Freeze and hash each coder sheet before comparison. Calculate pre-adjudication
agreement by target; adjudicate only after both sheets are locked, while
keeping deterministic predictions hidden. Preserve ambiguous, insufficient,
and out-of-scope judgments as separate outcomes. Do not silently recode them
as absent or drop them without counts and sensitivity analysis.

Once human reference decisions lock, compare them to the coordinator key.
For each target, report raw confusion cells and design-weighted ratios for
positive predictive value and sensitivity, with finite-population,
stratification-aware uncertainty. Dependence from repeated capture units
across targets and exact duplicate content must be considered in pooled or
cross-target summaries. Do not reuse the historical tool's approximate Kish
intervals as if they were full design-based confidence intervals. If a quota
or assessability rate leaves a metric too imprecise, report that limit instead
of declaring the code validated. A changed target definition or evidence
frame after the draw requires a fresh holdout for affected claims.

The public exporter and repository verifier block the frame, plan, machine
key, coder sheets, and selection manifest. Only reviewed, disclosure-safe
aggregates may later enter a new release after the methodological hold is
lifted.
