# Phase 2 OCR Checkpoint Summary

## What Was Produced

Phase 2 verified Phase 1 image paths and hashes, then used the local Windows OCR engine. Reuse requires an exact image SHA-256 and OCR-configuration SHA-256 match.

## Key Counts

- Phase 1 image references: 1140
- Unique local image paths OCR attempted or reused: 1043
- Unique local image content hashes: 1037
- OCR image rows: 1043
- Cache-reused image rows: 6
- Joined image-reference rows: 1140
- OCR status counts: {'ok': 1043}

## Main Output Files

- `ocr_text_by_image.csv`
- `ocr_joined_image_references.csv`
- `ocr_text_by_note.csv`
- `ocr_summary_by_source.csv`
- `run_metadata.json`

## Interpretation Limits

OCR output is machine-extracted text and should be treated as evidence support, not final coding. Low-quality screenshots, navigation text, avatars, repeated page furniture, and external images may require filtering before typology analysis.
