# Phase 2 Image OCR: Methods Note

## Purpose

Phase 2 extracts text from PNG screenshots referenced in Phase 1 and joins OCR text back to the Markdown note, source, and date metadata.

## OCR Engine

This phase uses the local Windows OCR engine through Python WinRT packages. Screenshots are processed locally; no external OCR API is used.

## Inputs

- Phase 1 image reference table and corpus table in the controlled `BANK_DROP_OUTPUTS_DIR`.
- Controlled extracted vault identified by `BANK_DROP_VAULT`.

## Outputs

The phase creates image-level and note-level OCR tables, coverage summaries, run metadata, and a checkpoint summary. Raw OCR tables are controlled artifacts and must not be added to GitHub; only aggregate OCR coverage is included here.

Image filenames and relative paths remain in controlled provenance columns and are not inserted into the OCR evidence text passed to Phase 3. This prevents provenance labels from triggering content rules or altering analytic duplicate hashes.

## Reproduction Command

From the repository root after setting the controlled paths:

```powershell
python .\code\phase2_image_ocr\run_phase2_ocr.py
```

The script can reuse existing successful OCR rows in the controlled output location.

## Interpretation Limits

OCR may capture navigation text, repeated interface text, usernames, and noisy fragments. It is evidence support, not final qualitative coding. OCR output can vary with Windows language packs, screenshot rendering, and the installed OCR environment.

The cache's `ok` status records pipeline completion only. The separate
[controlled OCR-quality procedure](../ocr_quality/METHODS_OCR_QUALITY.md)
prepares blinded human transcripts and fails until error rates can be measured.
