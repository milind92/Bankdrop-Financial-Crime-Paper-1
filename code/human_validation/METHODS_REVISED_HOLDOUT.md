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
two blank, randomized coder sheets, plus a blank packet-manifest template. The coder sheets contain opaque case IDs
and target codes, **no machine predictions, weights, sources, unit IDs, or
text**. The coordinator must create privacy-screened evidence packets keyed
to the case IDs and check that each packet supplies enough context without
exposing the machine output. The script does not create these packets.

## Lock, adjudicate, and score

The companion `close_revised_holdout.py` enforces this sequence. Complete the
two coder sheets independently using only the case IDs, target definitions,
and privacy-screened packets. Allowed judgments are `present`, `absent`,
`ambiguous`, `insufficient_evidence`, and `out_of_scope_record`; each
nonbinary judgment needs a rationale. Fill a copy of
`packet_manifest_template.csv` with the controlled relative packet file,
its SHA-256, two distinct reviewers for privacy and context, and
`packet_checked=yes`. Preserve the prefilled `source_unit_sha256`, which
binds each case to the selected approved text. The packet manifest is a
coordinator record and must not be shown to coders. The tool verifies packet
bytes, source-unit hashes, and case IDs. Reviewers must still check that each
privacy-screened packet faithfully conveys the approved text and enough
context; a hash cannot establish the accuracy of that human preparation.

First run `lock-coders` with the completed sheets, packet manifest/root, two
distinct coder names, and a fresh controlled lock directory. This stage
hashes the machine key to check selection integrity but does not parse or
show its predictions. It records pre-adjudication agreement and disagreement
counts. Changes to coder sheets or packet bytes invalidate the lock.

Next run `prepare-reference` using the same inputs and coder-lock directory.
It creates a controlled reference template containing both frozen human
judgments, with consensus judgments prefilled and disagreements blank. Fill
each disagreement with a final judgment, named adjudicator, and rationale;
record a rationale for any override of an agreement. Run `lock-reference`
with this completed sheet and a fresh reference-lock directory. It verifies
the coder lock and freezes the human reference **before** prediction
unblinding.

Finally run `score` with the approved frame and plan, sample directory,
both locks, completed coder sheets, checked packet files, and completed
reference sheet. The scorer reconstructs the seeded probability draw and
rejects altered case IDs, target/status assignments, frame metadata,
selection probabilities, or weights. Only this final command reads the
machine predictions.

Each command accepts `--sample-dir`, `--coder-1`, `--coder-2`,
`--packet-manifest`, `--packet-root`, and a fresh `--output-dir`. Later
commands also take `--coder-lock-dir`; `lock-reference` and `score` take
`--reference`; `score` additionally takes `--reference-lock-dir`,
`--frame-dir`, and `--plan`. The lock command takes `--coder-1-name` and
`--coder-2-name`. For exact command help:

```powershell
python .\code\human_validation\close_revised_holdout.py lock-coders --help
python .\code\human_validation\close_revised_holdout.py prepare-reference --help
python .\code\human_validation\close_revised_holdout.py lock-reference --help
python .\code\human_validation\close_revised_holdout.py score --help
```

The scorer retains all five final-decision categories. A final adjudicated
`out_of_scope_record` judgment stops performance scoring because it calls the
approved frame into question. If any target has `ambiguous` or
`insufficient_evidence` judgments, the tool leaves its primary performance
point estimates blank and reports conservative bounds instead. It never
silently treats those judgments as negatives. A changed target definition or
evidence frame after selection requires a fresh holdout for affected claims.

## Design-based estimates and limits

For a target with complete binary reference decisions, each stratum's
estimated human-present count is `N_h × observed_present_h / n_h`. Summing
these counts across machine-positive and machine-negative strata yields
estimated TP and FN; the known machine-status population counts determine FP
and TN. PPV, sensitivity, NPV, and specificity follow from those cells. The
reported weighted Cohen kappa is a **point estimate** for coder agreement in
the finite target frame; the unweighted agreement count is also retained.

For uncertainty, the tool inverts equal-tail hypergeometric tests separately
in each nonempty stratum. It divides the 5% error allowance by the number of
strata within that target and combines the stratum count bounds using the
Bonferroni inequality. The resulting intervals are conservative, with at
least 95% random-selection coverage **for each target** under this sampling
design. They account for sampling without replacement and census strata.
They are not simultaneous intervals across all target codes. This follows
the finite-population hypergeometric model described by
[Bartroff, Lorden and Wang](https://arxiv.org/abs/2109.05624); the tool uses
simple equal-tail inversion rather than that paper's optimized intervals.
Where a final decision is nonbinary, the bound allows it to be either present
or absent. The scorer suppresses a sensitivity interval if the approved
population might contain no human-positive units, making sensitivity
undefined.

These intervals address only the random draw from the approved, finite
capture-unit frame. They do not absorb source-selection bias, missing images,
OCR errors, uncertain constructs, coder error, or duplication. Repeated units
across targets and exact duplicate content matter for pooled and comparative
claims; the tool makes **per-target** estimates and does not supply a pooled
independence assumption. A wide bound or a target with unresolved human
decisions must be reported as such. The historical tool's Kish intervals
are not a substitute for this design analysis.

The public exporter and repository verifier block the frame, plan, machine
key, coder sheets, packet manifest, locks, adjudication, and performance
files. Only reviewed, disclosure-safe
aggregates may later enter a new release after the methodological hold is
lifted.
