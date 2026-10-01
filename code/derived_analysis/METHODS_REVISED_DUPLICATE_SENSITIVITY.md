# Revised exact-span duplicate sensitivity

This **provisional** controlled diagnostic applies only after two-reviewer
source-evidence screening and a revised Phase 3 run. It does not use the old
980-note mixed-record denominator or reinterpret the old 463 combined-text
hashes as unique posts. No real revised corpus or result is available yet.

Each approved capture unit has one or more source-text spans. The script
builds a signature from the sorted **multiset** of each span's modality and
SHA-256 text hash. Repeated spans remain repeated inside a signature. This
preserves artefact boundaries: two units with the same concatenated words
but different Markdown/OCR segmentation need not be grouped together. The
script requires identical deterministic predictions for units sharing one
signature. It stops if those predictions differ.

For each of the 12 substantive typologies and six AML candidates, the output
compares the proportion of approved units coded positive with the proportion
of distinct exact-span signatures coded positive. It reports the count of
positive units removed by this deterministic collapse. A separate controlled
summary counts within-source repeated signatures, cross-source repetition,
and reused span content. The collection-quality flag remains outside the
substantive target table.

Run from the repository root with controlled paths:

```powershell
python .\code\derived_analysis\build_revised_duplicate_sensitivity.py `
  --phase3-dir $env:BANK_DROP_REVISED_PHASE3_DIR `
  --evidence-corpus $env:BANK_DROP_EVIDENCE_CORPUS `
  --output-dir $env:BANK_DROP_REVISED_DUPLICATE_DIR
```

The script checks the evidence JSONL and manifest hashes, the revised Phase 3
mode and generated codebook hash, every approved unit and span, the complete
target and span matrices, and the reconciliation of span hits to unit hits.
It refuses historical Phase 3 files and output inside the public repository.
It writes a controlled CSV for each table and a manifest pinning every input
and output hash. Its `article_ready` value remains false.

The signature is an **exact-text sensitivity convention**, not a verified
identity of posts, listings, actors, or transactions. Repeated text may be a
template used independently, and different text may represent the same
underlying item. Counts from a purposive captured corpus do not estimate
external-market prevalence. Authors must review near duplicates, composite
notes, source dependence, and target validity before selecting any
article-facing denominator or interpreting a difference between tables.
