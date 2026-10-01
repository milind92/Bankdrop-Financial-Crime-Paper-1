# Reviewed source-evidence gate (provisional)

The historical Phase 3 screen coded the whole Markdown note plus OCR from its
linked screenshots. The post-release audit found researcher and collection
text inside that population. This gate creates a separate, controlled input
for a revised Phase 3 run. It does **not** retroactively validate the old
human sample, the OCR, or the regex targets.

## Inputs and privacy boundary

Use the frozen vault, its hash-matched Phase 1 `corpus_index.csv`, and Phase 2
`ocr_joined_image_references.csv`. The review sheets and resulting JSONL
contain controlled paths, judgments, and source text. Store them outside this
public repository and the vault. Do not commit or export them.

`prepare` rechecks every note and resolved PNG against the frozen hashes,
inventories all PNGs, and creates three **blank** worksheets:

- `note_decisions.csv`: one row for every Phase 1 screened note;
- `image_decisions.csv`: content-deduplicated linked images per note, each
  unresolved reference, and every unreferenced PNG path;
- `source_segments.csv`: approved source-text spans from Markdown or OCR.

The current frozen inputs generate 980 note rows, 1,048 linked-image rows, 92
unresolved-reference rows, and 58 unreferenced-image rows. The linked-image
rows are note/image-content assignments, not distinct image files.

Run from the repository root with controlled paths supplied locally:

```powershell
python .\code\evidence_screening\build_evidence_corpus.py prepare `
  --vault $env:BANK_DROP_VAULT `
  --phase1-index $env:BANK_DROP_PHASE1_INDEX `
  --phase2-joined $env:BANK_DROP_PHASE2_JOINED `
  --review-dir $env:BANK_DROP_REVIEW_DIR
```

`prepare` refuses to overwrite a nonempty review directory. Its manifest pins
the exact Phase 1 and Phase 2 input hashes. The frozen identity columns in
the sheets must not be edited.

## Human decisions

Two distinct reviewers record independent `include`/`exclude` decisions for
each note. Set the final decision, adjudicator, record type, and exclusion
reason. A note can enter substantive coding only as `source_capture` or
`mixed_source_and_researcher`. Collection-status, researcher-only,
out-of-scope, and unassessable notes remain in the inventory but outside the
substantive denominator. A reviewer must confirm the included note's source.
For each included note, set `markdown_decision` to `source_spans`,
`no_source_text`, or `unassessable`. The first requires at least one approved
Markdown span; the other two require a reason and prohibit an approved
Markdown span. This records the OCR-only choice rather than silently dropping
copied source text from Markdown.

For every linked, unresolved, and orphan image, reviewers independently
choose `include`, `exclude`, or `unavailable`. Unresolved references cannot
be included. A linked image belongs only to an included note. An orphan with
novel content may be assigned to a reviewed note or become its own unit after
source/linkage review; a duplicate of already referenced content cannot be
included a second time. Every non-inclusion needs a reason. An included
orphan needs a source/linkage rationale and provenance-matched OCR supplied
in the documented supplemental CSV schema.

The `capture_date_basis` is `source_metadata`, `collector_record`,
`filename_only`, or `unknown`. Enter an ISO `capture_date` only for the first
two bases. Filename-derived dates remain inventory metadata and do not become
verified capture dates in the revised analytical output.

In `source_segments.csv`, each row gives a `reference_key`, zero-based
`start_char`, exclusive `end_char`, and SHA-256 of the **exact substring**.
For a Markdown span, use `markdown:<note_id>` and offsets in the original
note after newline normalisation. For OCR, use the linked or orphan image's
`reference_key` and offsets in its exact Phase 2 or supplemental OCR text.
Approve only passages attributable to captured source material. Separate
posts, listings, and images must have separate rows; the coder never joins
them to satisfy a compound rule. Overlapping spans, edited text, and
included images without an approved span are rejected. Where a screenshot
has no assessable text, record an exclusion or unavailable decision with a
reason instead of entering it as a substantive negative.

The code checks that two reviewers, their decisions, a final decision, and
an adjudicator are recorded for every row. Disagreements and adjudicator
overrides need a rationale. This enforces complete recording, though it
cannot by itself prove that review was independent or that a span is genuine
source text. The author/collector must attest to those facts.

## Build and provisional analysis

After completing all sheets, run `build` with the same frozen inputs and an
output directory outside the public repository:

```powershell
python .\code\evidence_screening\build_evidence_corpus.py build `
  --vault $env:BANK_DROP_VAULT `
  --phase1-index $env:BANK_DROP_PHASE1_INDEX `
  --phase2-joined $env:BANK_DROP_PHASE2_JOINED `
  --review-dir $env:BANK_DROP_REVIEW_DIR `
  --output-dir $env:BANK_DROP_EVIDENCE_DIR
```

If an approved novel orphan requires OCR, add `--orphan-ocr` with a controlled
CSV having the exact columns `image_relative_path,image_sha256,
ocr_config_sha256,ocr_cache_key,ocr_status,ocr_text`. The SHA and cache key
must match the image and the single Phase 2 OCR configuration; status must be
`ok`. A different OCR engine or configuration requires a documented method
revision and comparability check. Document the engine and quality review
separately. The build produces
`approved_evidence_units.jsonl` and `evidence_build_manifest.json`, both
controlled. The manifest includes decision-sheet hashes, flow counts, and
the JSONL hash. Its `article_ready` field remains false.

For a **provisional** artefact-bounded coding run, set
`BANK_DROP_EVIDENCE_CORPUS` to the approved JSONL path and
`BANK_DROP_OUTPUTS_DIR` to a separate controlled output root, then run the
Phase 3 script. Phase 3 verifies the build manifest and codes each approved
span separately while retaining note-level binary aggregates. The historical
`run_reproducible_pipeline.py` entrypoint remains the historical replay path.
In revised-mode CSVs, the inherited `note_count` column counts **approved
evidence units**, including any separately approved orphan-image units. It
does not count unique posts, listings, actors, or transactions. Composite
notes and repeated source captures need separate sensitivity analysis.
The old Phase 4 narrative script refuses the revised mode because its
interpretation and human-validation wording belong to the old sample.
The historical derived-analysis script also refuses it until its population
and duplicate-sensitivity definitions are revised for approved evidence
units. The Phase 3 overview labels revised results as provisional.

No revised counts are approved for publication until OCR transcription
quality, low-precision target definitions, sampling and two-coder validation,
source dependence, duplicates, all downstream tables, and manuscript claims
are reconciled to this new corpus.
