# Controlled OCR-quality assessment

The Phase 2 cache records whether OCR ran, not whether it transcribed the
screenshots accurately. This procedure prepares a **blinded, controlled**
human review and scores it only when the review is complete. Neither the
screenshots, OCR text, transcripts, sample sheet, nor per-image scores belong
in the public repository.

## Sampling frame and design

The current preparation uses the 1,037 distinct content hashes among local
PNG images referenced by historical Phase 1 notes and represented in the
hash-checked Phase 2 image OCR cache. Repeated paths with identical content
appear once. Each image is assigned to its first source in lexical order if
linked to multiple sources; the manifest reports how many such cases occur.
The frozen 1 October 2026 inputs had none.
These are source-*folder* labels inherited from the researcher vault; the
sampling procedure does not verify a screenshot's actual site of origin.

The default fixed-seed sample contains 50 images. It takes at least two
images from each of the 15 source strata where available, assigns the
remaining places in proportion to remaining stratum capacity, and draws
uniformly without replacement within each stratum. The review manifest
records each stratum's population and sample size, so an image's inclusion
probability is `selected_stratum_n / population_stratum_n`. This replaces an
earlier **blank** purposeful sample that deliberately selected OCR-length
extremes and therefore could not support a corpus-wide average.

The preparer verifies the OCR cache keys, input file hashes, all sampling-frame
image hashes, and every selected image copy. It creates a CSV with **no OCR
text**, 50 numbered screenshot copies in `images/`, and an empty
`transcripts/` directory. Keep this directory under controlled access.

```powershell
python .\code\ocr_quality\assess_ocr_quality.py prepare `
  --vault $env:BANK_DROP_VAULT `
  --ocr-by-image $env:BANK_DROP_OCR_BY_IMAGE `
  --joined-references $env:BANK_DROP_PHASE2_JOINED `
  --review-dir $env:BANK_DROP_OCR_REVIEW_DIR
```

`prepare` refuses to overwrite a nonempty directory. If only the numbered
image copies need restoring for an intact sample, use the `materialize`
subcommand with `--vault` and `--review-dir`; it checks hashes and refuses
to replace changed copies.

## Blinded human work

For every `sample_001.png` through `sample_050.png`:

1. A human transcriber views the numbered screenshot **without seeing its
   OCR text**. If all visible text is legible, transcribe all of it in UTF-8
   to `transcripts/001.txt`, preserving word order. Include page furniture;
   study relevance is a separate judgment. Do not silently correct spelling.
2. A different human checks the screenshot against the transcript, still
   without seeing OCR. Save the agreed or corrected final transcript in the
   same file. Record both names, blinding confirmations, check status, and a
   correction rationale when relevant.
3. Record legibility as `full`, `partial`, `none`, `no_text`, or
   `unassessable`. For non-full images, record a reason and leave the
   full-image transcript field blank. Keep `ocr_extraction_adequate` blank
   and `review_status=pending` at this stage.
4. Before revealing OCR, the project coordinator runs `lock` below. It
   verifies the checked human fields and images, then creates a one-time
   `transcript_lock_manifest.json` with the human-review and transcript file
   hashes. It refuses an already existing lock. Retain this manifest in
   controlled storage; a hash checkpoint documents the recorded sequence,
   while the team remains responsible for actual blinding and independence.
5. The checker can then compare OCR with the image and record whether
   extraction would be adequate for source-content coding (`yes`, `no`, or
   `uncertain`). Mark `review_status=complete` only after that judgment.

For fully legible images, `transcript_relative_path` must point inside the
review folder's `transcripts/` directory, `transcription_scope` must be
`all_visible_text`, and `transcript_check_status` must be `agreed` or
`corrected`. For all other images, use `not_applicable` as the check status.
The script verifies names and fields; the researchers must verify that the
reviews were in fact independent and blinded.

```powershell
python .\code\ocr_quality\assess_ocr_quality.py lock `
  --vault $env:BANK_DROP_VAULT `
  --ocr-by-image $env:BANK_DROP_OCR_BY_IMAGE `
  --joined-references $env:BANK_DROP_PHASE2_JOINED `
  --review-dir $env:BANK_DROP_OCR_REVIEW_DIR
```

## Scoring and reporting

```powershell
python .\code\ocr_quality\assess_ocr_quality.py score `
  --vault $env:BANK_DROP_VAULT `
  --ocr-by-image $env:BANK_DROP_OCR_BY_IMAGE `
  --joined-references $env:BANK_DROP_PHASE2_JOINED `
  --review-dir $env:BANK_DROP_OCR_REVIEW_DIR `
  --output-dir $env:BANK_DROP_OCR_SCORE_DIR
```

The scorer fails before writing output if the pre-reveal lock is absent or if
any locked human field, transcript, image, cache, selection identity, review
copy, or final review decision is missing or altered. It compares
the checked human transcript to the original OCR text after Unicode NFC,
case-folding, and whitespace collapse; punctuation remains. Character error
rate is Levenshtein character edits divided by gold characters, and word
error rate is token edits divided by gold words. Pooled scores use the known
source-stratum design weights. They are **conditional on fully legible images**;
partial, unreadable, and text-free images are counted separately. The report
gives both unweighted sample counts and design-weighted population
percentages for legibility; human adequacy judgments use the same design
weights. These 50-image figures are descriptive estimates with sampling
uncertainty, not exact frame parameters. CER/WER can
exceed 1 when OCR inserts enough extra text.

The current sample describes the historical referenced-image OCR frame. It
does **not** yet measure OCR accuracy specifically in the final
author-approved evidence corpus or any novel orphan images. After eligibility
and image linkage are locked, assess coverage of the final OCR image frame
and add or redraw a gold sample where necessary. The score is a measurement
diagnostic, not validation of the financial-crime regex targets.
