# Phase 1 Checkpoint Summary

## What Was Produced

Phase 1 created a reproducible Markdown-only baseline for the Bank Drop Project vault. No OCR or LLM interpretation was used in this phase.

## Key Coverage Counts

- Markdown notes indexed: 999
- Source folders identified: 16
- Image references in notes: 1,140
- Image references resolving to files in the vault root: 1,048
- Price mentions extracted: 518
- Entity mention rows: 425
- Keyword count rows: 15,984

## Highest-Coverage Sources By Note Count

1. Secure ccSeller: 94 notes
2. Tor Shop: 93 notes
3. Meta Banklogs: 92 notes
4. CardPro: 91 notes
5. Pitch: 90 notes
6. The X Wave Market: 90 notes
7. Legit Market: 88 notes
8. Caders Heven: 77 notes

## Initial Descriptive Signals

The Markdown corpus contains strong signals for bank drops, bank logs, fullz/identity packages, cashout/payment rails, Telegram/private-channel references, escrow/trust mechanisms, crypto references, and source-specific marketplace activity. These are descriptive indicators only; interpretive typology coding is reserved for Phase 3.

## Reproducibility

Code is stored under:

`code/phase1_markdown_baseline/run_phase1.py`

Run with:

```powershell
python .\code\phase1_markdown_baseline\run_phase1.py
```

Main output folder:

`<BANK_DROP_OUTPUTS_DIR>/phase1_markdown_baseline/`

## Next Phase

Phase 2 should add OCR for the PNG screenshots and join OCR text back to the note/source/date structure already created here.
