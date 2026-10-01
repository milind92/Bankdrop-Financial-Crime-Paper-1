> **Post-release status (1 October 2026):** The [corpus audit](POST_RELEASE_CORPUS_AUDIT_2026-10-01.md) found 191 of the 1,032 historical case-target rows came from 15 no-OCR research/status notes. The completed 26 July validation remains authentic for its historical mixed-record design, but it does not validate a revised evidence-only corpus.

> **Revised holdout requirement:** After author-reviewed source units, target
> definitions, and the versioned codebook are frozen, draw a new blinded
> probability-documented holdout from the entire assessable revised unit frame,
> including short approved source spans. Do not reuse the old 30-word
> predicted-negative eligibility rule or treat old pooled coder agreement as
> performance for the new frame. Preserve source, modality, duplicate, and
> target-specific sampling information, then calculate design-aware
> uncertainty before article claims. The guarded frame and draw procedure is
> [documented here](../code/human_validation/METHODS_REVISED_HOLDOUT.md); no
> real revised sample or validation result exists yet.

> **Historical status (26 July 2026):** The corrected-corpus validation was completed after the earlier 23 July release was withdrawn because 14 ineligible internal project documents contributed 59 paired case-target units. Ausma Bernot and Milind Tiwari independently coded the fresh sample drawn from the 980-note source-folder screen and jointly adjudicated every disagreement. See `outputs/human_validation/HUMAN_VALIDATION_STATUS.md`.

# Human Validation Protocol

## Status And Purpose

This document preserves the prospective protocol and records the completed human inter-coder reliability implementation. A validation plan, sample, or empty worksheet is not a result; the completed, frozen coder records and separate adjudication archive are the evidentiary basis for the completion status below.

The empirical validation pathway is no-LLM. No LLM output may be shown to coders, used as a reference decision, included in adjudication, or reported as reliability evidence for the current study.

## Completed Implementation And Deviation Record

The blinded human ICR and post-ICR adjudication stages were completed on 26 July 2026.

- Coders: Ausma Bernot and Milind Tiwari.
- Coordinator: none.
- Independent coding: 1,032 paired case-target units across 313 evidence packets and 18 assessed targets.
- Permitted decisions: Present, Absent, Ambiguous, Insufficient evidence, and Out of scope record.
- Independence: each researcher confirmed that the submitted answers were their own independent human judgements.
- Locking: both completed workbooks were frozen before comparison and discussion.
- Pre-adjudication result: 981 exact agreements, 51 disagreements, 95.1% exact agreement, Cohen's kappa 0.839, and nominal Krippendorff's alpha 0.839.
- Binary sensitivity subset: 998 Present/Absent pairs, 98.1% agreement, and kappa 0.933; other categories were excluded, not recoded.
- Adjudication: Ausma and Milind jointly reviewed all 51 disagreements after ICR was frozen and reached consensus in every case.
- Final disagreement outcomes: 22 Present and 29 Absent; zero Ambiguous, Insufficient evidence, Out of scope record, pending, deferred, or no-consensus cases.
- Expertise: both coders were author-confirmed subject-matter experts; Milind Tiwari also has AML expertise.
- Sampling-plan confirmation: the authors confirmed that a sample-size plan was used before coding.

The preferred generic role separation below was not fully used: there was no coordinator or independent third adjudicator. The same two researchers jointly adjudicated after their independent workbooks and pre-adjudication metrics were frozen. Because all 51 disagreements reached consensus, a third coder was not invoked. This role overlap must be disclosed as a design limitation; it does not alter the frozen ICR calculation.

A controlled post-closeout audit on 22 August 2026 found that the frozen evidence-packet text retained 840 legacy `[OCR: relative-path]` provenance labels across the 313 packets. The labels did not reveal deterministic predictions. Label-only text produced no Phase 3 typology or AML-rule hits, and removing every label changed zero packet-target deterministic classifications. Each coder had 114 positive rationales that referenced screenshot evidence; every one retained substantive non-path rationale after the provenance tokens were removed. The frozen human decisions and reliability statistics were therefore not recomputed. This aggregate audit cannot prove that visible provenance had zero cognitive influence, so the legacy label exposure should be disclosed if the target journal requires strict evidence-provenance masking.

The publication-safe completion record is `outputs/human_validation/HUMAN_ICR_COMPLETION.md`. Target-level agreement intervals, reliability coefficients, and aggregate adjudication outcomes are reported in `outputs/human_validation/HUMAN_ICR_BY_TARGET.md` and `human_icr_by_target.csv`. Machine-versus-final-human classification performance is reported separately in `HUMAN_VALIDATION_PERFORMANCE.md` and `human_validation_performance.csv`. Coder-level decisions, evidence packets, rationales, adjudication rows, signatures, and record identifiers remain outside GitHub under controlled governance.

ICR quantifies consistency between coders within the validation design. It does not, by itself, establish corpus prevalence or construct validity. The separate classification-performance output reports sample-specific and sampling-weighted sensitivity, specificity, predictive values, accuracy, and their stated uncertainty limits; it does not establish external-market prevalence or transaction truth.

## Validation Objectives

The completed human-validation exercise assessed:

1. whether each deterministic typology assignment represents the construct defined in the locked codebook;
2. whether sampled deterministic-negative records meeting the implemented eligibility rule contain missed instances;
3. whether OCR, repeated interface text, broad patterns, source context, or duplication causes systematic error;
4. whether the codebook can be applied consistently by independent humans;
5. whether each corpus-derived AML candidate is supported as a cautious research hypothesis rather than an operational rule;
6. which claims must be retained, qualified, revised, or withdrawn.

Validation does not verify transactions, offenders, victims, delivery of advertised services, or external prevalence.

## Materials To Lock Before Coding

The validation coordinator must freeze and hash:

- the data-collection protocol and analytic inventory;
- the codebook version, including definitions, inclusion rules, exclusion rules, and safe examples;
- the deterministic coding output to be evaluated;
- the validation sampling frame and selection probabilities;
- the random seed and sample-generation code;
- the blinded evidence packets;
- the coder instructions and decision form;
- the claim-specific acceptance and stop rules;
- the analysis script or spreadsheet specification for agreement and confusion metrics.

The lock record must include date, version, SHA-256 values, and author approval. Changes after the locked holdout begins invalidate the holdout for any materially changed code unless a fresh independent holdout is drawn.

## Validation Targets

The completed validation covered 18 targets:

- all 12 substantive typology codes retained in the journal codebook; and
- all six AML indicator candidates retained in the journal analysis.

The `market_access_limitation` collection-quality flag, modality provenance, duplicate status, and exploratory higher-order functional groupings were not separate validation targets. Collection barriers remain data-quality states, not criminal objectives. Compound AML candidates received content assessment but are retained only as hypotheses because no independent external domain-review record is claimed.

## Roles And Independence

| Role | Requirement |
|---|---|
| Validation coordinator | Creates identifiers, sampling strata, and blinded packets. Does not code records if avoidable. Holds the deterministic predictions until human decisions are locked. |
| Coder 1 | Independently applies the locked codebook to blinded records. |
| Coder 2 | Independently applies the same locked codebook to the same blinded records. |
| Adjudicator | Reviews disagreements after independent decisions are locked. Remains blind to deterministic predictions until the human reference decision is final. A third independent coder is preferred where the two coders cannot resolve a case. |
| Statistical analyst | Runs the aggregate validation tool and interprets its limits. Produces a separate design-based analysis when clustering, finite-population corrections, or estimated weights matter. |
| AML domain reviewer | Separately evaluates the interpretation and practical boundaries of AML candidates; does not convert observed text into transaction-monitoring claims without external evidence. |

Coder identities are confirmed as Ausma Bernot and Milind Tiwari. Both were author-confirmed subject-matter experts, and Milind Tiwari also has AML expertise. No additional qualification, title, conflict-of-interest, or statistical-analyst detail is inferred. Milind's AML expertise is not described as an independent external review because he also coded and adjudicated the validation material.

## Blinding

Coders must receive the code definition and the minimum controlled evidence needed to decide the code. They must not receive:

- deterministic `present` or `sample_type` status;
- hit counts, matched-pattern counts, or mechanical rule-match intensity labels;
- the exact pattern that triggered selection, unless the codebook makes that pattern part of the human definition;
- automated classifications, model-generated decisions, or machine summaries;
- the other coder's decisions;
- expected prevalence, rank, or manuscript claim language.

Each packet should use a random validation identifier and randomized order. Source and modality may be shown only where needed for interpretation; otherwise they remain masked and are restored after decisions lock. Evidence packets must not expose handles, URLs, payment identifiers, account-like identifiers, operational instructions, or unnecessary personal information.

## Development Pilot

The pilot is for improving the codebook and coder instructions, not estimating final performance.

1. Draw a purposive development set spanning every code, deterministic positives and negatives, source groups, modalities, record lengths, duplicates, and known difficult cases.
2. Both coders apply the draft codebook independently.
3. Discuss disagreements, ambiguous concepts, missing exclusions, and unsafe evidence presentation.
4. Revise definitions, split conflated constructs, add inclusion/exclusion rules, and document every change.
5. Repeat a small pilot if material ambiguity remains.
6. Lock the final codebook before drawing or opening the holdout.

Pilot records must not be reused to estimate final reliability or classifier performance.

## Locked Holdout Sampling Design

The completed holdout sampled combined-note-record/target judgements. A single evidence packet could be selected for more than one target, so the 1,032 case-target units are not 1,032 independent records. Reliability and performance are reported at the paired case-target level, with target-specific rows retained.

The sampling coordinator may use deterministic status for stratification, but that status remains hidden from coders and adjudicators. The design must record the inclusion probability for every sampled record.

Required strata are:

- source group, including a source-unknown stratum;
- text modality: Markdown only, OCR only, and Markdown plus OCR;
- record-length band, defined from the eligible corpus distribution without excluding short records;
- exact-duplicate status and duplicate-cluster size;
- deterministic positive and deterministic negative status for each target;
- trigger-pattern or rule family, to prevent one common term from dominating validation;
- mechanical match-intensity band, used only by the sampling coordinator;
- data-quality status, including OCR-heavy and access/interface-heavy records;
- low-frequency and substantively sensitive codes.

The implemented fixed-seed plan separated deterministic predicted-positive and predicted-negative frames for each target, selected up to 20 positives and 40 negatives per target, and used source, modality, and length strata. Fewer than 20 positive records resulted in complete positive-frame selection. Selection probabilities and analysis weights were retained in the controlled machine key.

Predicted-negative records required at least 30 combined-text words. This deviated from the preferred rule that short records remain eligible. Consequently, the published negative-side performance does not establish false-negative behaviour among shorter or unassessable records, and no rarity or absence claim may rely on it.

### Sample Size

The authors confirmed on 22 August 2026 that a sample-size plan was used before coding. The implemented plan and fixed selection design are described above. A stronger claim-specific precision plan would additionally state:

- the parameter to be estimated, such as positive predictive value, sensitivity, or agreement;
- the anticipated value or conservative assumption;
- the desired 95% confidence-interval width;
- design effects from source or duplicate clustering;
- expected ambiguous or non-assessable fraction;
- feasible numbers for rare codes.

A sample of 15 predicted positives and 5 predicted negatives per code is not, by itself, sufficient justification. For illustration, even 15 correct decisions out of 15 yield a lower 95% Wilson bound of approximately 0.80, and 5 out of 5 yield a lower bound of approximately 0.57.

The public repository does not contain a contemporaneous claim-specific numerical acceptance threshold. It therefore reports the resulting estimates and uncertainty descriptively and does not state that any target passed a prespecified performance threshold.

## Evidence Packet

Each blinded record should contain:

- random validation identifier;
- privacy-clean Markdown text or a controlled viewer reference;
- privacy-clean screenshot or OCR text where required;
- enough surrounding context to distinguish content from interface text, quotation, warning, or negation;
- a modality indicator only where necessary;
- the locked code definitions and coder decision form.

The coordinator should preserve a separate crosswalk linking validation identifiers to controlled records, source strata, deterministic predictions, hashes, and selection probabilities.

## Permitted Human Decisions

For each record-code pair, coders select exactly one substantive decision:

| Decision | Meaning |
|---|---|
| `present` | The record satisfies the locked inclusion definition with adequate context. |
| `absent` | The record does not satisfy the definition or meets an explicit exclusion rule. |
| `ambiguous` | Available evidence supports competing interpretations that the locked rules do not resolve. |
| `insufficient_evidence` | The evidence packet is missing, illegible, context-poor, or otherwise not assessable. |
| `out_of_scope_record` | The record should not have entered the substantive analytic denominator under the collection protocol. |

Coders also record independent, non-decisional flags where applicable:

- OCR error influenced the assessment;
- repeated interface or navigation text;
- exact or suspected near duplicate;
- quoted or negated content;
- multiple underlying evidence units in one record;
- codebook clarification needed;
- ethics or safety escalation required.

Coders must provide a short non-operational rationale for `ambiguous`, `insufficient_evidence`, and `out_of_scope_record`. They must not assign `true_positive`, `false_positive`, `true_negative`, or `false_negative`; those labels are derived only after human decisions are locked and predictions are unblinded.

## Adjudication

1. Lock and hash both coders' independent decisions.
2. Calculate and retain pre-adjudication agreement before discussion.
3. Give the adjudicator the evidence, codebook, both rationales, and disagreement type, but not the deterministic prediction.
4. Resolve to `present`, `absent`, `ambiguous`, `insufficient_evidence`, or `out_of_scope_record`.
5. Use a third coder or retain `ambiguous` when evidence or rules do not support resolution.
6. Record the adjudication rationale and whether the issue is record-specific or codebook-wide.
7. Unblind deterministic predictions only after the human reference decisions are final.

Adjudicated decisions are the reference for evaluating the deterministic rules. Adjudication must not overwrite or erase the original coder decisions.

## Reliability Reporting

Report, overall and by code where sample size permits:

- the number independently coded;
- the number and percentage of exact agreements;
- coder 1 `present`/coder 2 `absent` and coder 1 `absent`/coder 2 `present` counts, plus a count of other multicategory disagreements;
- `ambiguous`, `insufficient_evidence`, and `out_of_scope_record` counts;
- Cohen's kappa across the five nominal decision categories, with a deterministic paired-unit percentile-bootstrap 95% interval by target;
- a separately labelled Present/Absent sensitivity subset with binary kappa and Gwet's AC1, with a deterministic paired-unit percentile-bootstrap interval for AC1;
- source-, modality-, length-, and duplicate-stratum agreement;
- pre-adjudication results separately from adjudicated results.

Reliability coefficients must be interpreted with prevalence and sample design in mind. A coefficient must not be described as proof of validity.

## Deterministic-Code Performance

After unblinding, derive the following against adjudicated `present` and `absent` decisions:

| Human decision / deterministic decision | Deterministic present | Deterministic absent |
|---|---:|---:|
| Human present | True positive | False negative |
| Human absent | False positive | True negative |

Report per code:

- TP, FP, TN, and FN counts;
- positive predictive value;
- negative predictive value;
- sensitivity/recall;
- specificity;
- F1 score or balanced accuracy only as supplementary summaries;
- Wilson 95% intervals for unweighted confusion-derived proportions;
- unweighted sample results, and weighted point estimates when a valid positive `analysis_weight` is supplied for every machine-key row;
- the number excluded from binary metrics and why.

The repository tool reports weighted confusion cells and weighted proportions, with explicitly approximate Wilson intervals based on Kish effective sample sizes. Those intervals do not account for source or duplicate clustering, finite-population corrections, or estimated/calibrated weights. If any of those features matter to a planned claim, the statistical analyst must produce a separate design-based variance analysis and identify it as separate from the repository tool. `ambiguous`, `insufficient_evidence`, `out_of_scope_record`, and unresolved records remain outside every binary confusion metric; they are counted rather than recoded as present or absent.

For low-volume or absence-oriented claims, sensitivity and false-negative uncertainty are more important than positive predictive value alone. No claim that a phenomenon is rare or absent should rely on a validation design with inadequate negative-side coverage.

## AML-Candidate Review

The completed exercise provides content assessment for each retained AML candidate. Stronger interpretive validation would require two separate judgements:

1. **Content validity:** independent coders confirm that the record actually contains the compound textual relationship defined by the code.
2. **Interpretive validity:** an AML domain reviewer assesses whether the aggregate observation can cautiously motivate further research.

An independent reviewer would classify each candidate as:

- suitable as a corpus-derived research hypothesis;
- requires narrower wording or additional evidence;
- not supportable from this corpus.

No candidate may be described as a confirmed suspicious-activity indicator, detection rule, causal mechanism, or validated transaction-monitoring control without independent transaction-level and operational evaluation.

Milind Tiwari has AML expertise and supplied an internal expert boundary, but he also participated as coder and adjudicator. No separate independent external AML review is claimed. The public claim register therefore keeps all six candidates at `exploratory_only`.

## Stop, Revision, And Publication Rules

The following rules apply regardless of numerical performance:

1. No human validation results means no final substantive typology or AML claim.
2. A materially revised code cannot inherit performance estimates from the old code; it requires a fresh independent holdout.
3. Pilot results cannot be reported as locked-holdout performance.
4. A code dominated by interface text, OCR error, duplicates, or one source must be revised, downgraded, or withdrawn.
5. A code with too few human-positive or human-negative cases for its claim must be reported as unvalidated or exploratory.
6. Unresolved systematic coder disagreement requires codebook revision and new validation.
7. A low-volume or absence claim must be withdrawn when the design cannot bound false negatives adequately.
8. An AML interpretation rejected by domain review must not appear as an AML implication.
9. Any post hoc threshold, code change, exclusion, or regrouping must be disclosed and may not be presented as prespecified.

The authors confirmed that a sample-size plan existed, but the public record does not establish a contemporaneous numerical pass/fail threshold for every claim. Results therefore remain descriptive, retain their full uncertainty, and are not labelled as having passed a prespecified validation threshold.

## Executable Aggregate Analysis

Use `code/human_validation/summarize_human_validation.py` after both coder
files are locked and, when applicable, adjudication is complete. The tool uses
only the Python standard library and writes aggregate CSV and Markdown files.

Required machine-key columns are:

- `record_id`
- `target_type`
- `code`
- `model_present`

The optional `analysis_weight` column must be present for every row or
absent entirely. If present, every value must be numeric, finite, and greater
than zero. The machine key may contain additional controlled columns; they are
not copied to either output.

Each coder file requires `record_id` and `decision`. The optional
adjudication file requires `record_id`, `coder_1_decision`,
`coder_2_decision`, and `adjudicated_decision`. Extra rationale or
flag columns are permitted and ignored by the aggregate tool. All files must
contain the same unique `record_id` set. The five valid decisions are
exactly:

- `present`
- `absent`
- `ambiguous`
- `insufficient_evidence`
- `out_of_scope_record`

Example command:

```powershell
python code/human_validation/summarize_human_validation.py `
  --machine-key controlled/validation_machine_key.csv `
  --coder-1 controlled/coder_1.csv `
  --coder-2 controlled/coder_2.csv `
  --adjudication controlled/adjudication.csv `
  --output-csv reviewer_safe/human_validation_aggregates.csv `
  --output-markdown reviewer_safe/human_validation_aggregates.md `
  --output-metadata reviewer_safe/human_validation_performance_metadata.json `
  --coder-1-label "Ausma Bernot" `
  --coder-2-label "Milind Tiwari"
```

Without `--adjudication`, a final decision is created only when both
coders made the same nonblank decision. `--allow-incomplete` permits blank
decisions and reports them as unresolved; otherwise blanks are rejected.

The CSV reports overall and per-`target_type`/`code` aggregates. It
includes coder-specific and final counts for every decision category, exact
agreement, binary directional disagreements, Cohen's kappa, Gwet's AC1,
unweighted confusion counts and proportions, and optional weighted confusion
estimates. Kappa and AC1 use 1,000 deterministic paired-record bootstrap
resamples. Weighted intervals are explicitly labelled `approx` and use
Kish effective sample sizes. To report agreement by source, modality, length,
or duplicate stratum, run the tool on separately frozen stratum-specific
machine-key and coder-file subsets and retain the subset definitions and hashes.
The tool does not compute cluster-robust or survey-design variance.

### Publication-safe target-level close-out

After the frozen controlled ICR calculation and completed adjudication have been reduced to aggregate inputs, authorised researchers can reproduce the public target-level table with:

```powershell
python .\code\human_validation\build_public_icr_by_target.py `
  --frozen-results <controlled-frozen-results-json> `
  --adjudication-by-target <controlled-aggregate-adjudication-csv> `
  --output-csv .\outputs\human_validation\human_icr_by_target.csv `
  --output-markdown .\outputs\human_validation\HUMAN_ICR_BY_TARGET.md `
  --output-metadata .\outputs\human_validation\human_icr_target_metadata.json `
  --adjudication-workbook-sha256 <completed-workbook-sha256>
```

The adjudication input to this public builder is already grouped by target. It must not contain Case IDs, Packet IDs, coder-level decisions, rationales, evidence, or signatures.

## Required Validation Outputs

The controlled archive should retain:

- locked sample manifest and selection probabilities;
- blinded packets and crosswalk;
- original coder decisions;
- adjudication log;
- codebook versions and change log;
- analysis code and machine-readable metrics;
- code-level confusion tables and intervals;
- source/modality/length/duplicate sensitivity tables;
- AML expertise and reviewer-independence record;
- validation deviations and author sign-off.

The public or reviewer-safe repository should contain only aggregate validation results, methods, codebook changes, file-level provenance hashes, and privacy-clean reporting approved under the controlled-access policy. This repository includes the completed target-level reliability and machine-versus-human performance aggregates, records Milind Tiwari's AML expertise, and explicitly states that no independent external AML review or public numerical claim-threshold record is claimed.
