# Phase 3 Typology Coding: Methods Note

## Purpose

Phase 3 creates an auditable deterministic typology-coding baseline. It combines Markdown-note text with Phase 2 OCR text and applies explicit regular-expression codebook rules. No LLM or external API is used.

The default command reproduces the **historical mixed-record screen**, which
is on methodological hold. A revised, author-reviewed input is supported via
`BANK_DROP_EVIDENCE_CORPUS`; see
[`METHODS_EVIDENCE_SCREEN.md`](../evidence_screening/METHODS_EVIDENCE_SCREEN.md).
The author-reviewed provisional path also writes a controlled per-span target
matrix and supports the separate
[pair-boundary diagnostic](../derived_analysis/METHODS_REVISED_PAIR_BOUNDARIES.md).
The revised [descriptive-table builder](../derived_analysis/METHODS_REVISED_DESCRIPTIVES.md)
uses the same reviewed-evidence matrix after the screening gate is complete.
In that mode, each approved Markdown or OCR source span is coded separately,
then binary results are aggregated to the approved note/image unit. Compound
patterns cannot join terms across separate spans. The historical human
validation does not validate the revised population or target definitions.

## Inputs

- Controlled vault selected by `BANK_DROP_VAULT`.
- Controlled Phase 1 and Phase 2 outputs selected by `BANK_DROP_OUTPUTS_DIR`.

## Outputs

The phase produces typology and AML-indicator coding tables, aggregate typology summaries, criminal-objective summaries, source-level summaries, a codebook, and run metadata. Joined corpus, long-form coding, and evidence-snippet tables are controlled artifacts; only their safe aggregate derivatives are included in this repository.
The revised evidence-only path additionally writes controlled
`artifact_coding_long.csv`, with one row per approved span and target; it is
not exported or interpreted as a final article result.

## Reproduction Command

From the repository root after setting the controlled paths:

```powershell
python .\code\phase3_typology_coding\run_phase3_typology.py
python .\code\phase3_typology_coding\make_phase3_overview.py
```

## Interpretation Limits

The code is deterministic and supports audit trails, sampling, and first-pass descriptive mapping. It is not a substitute for qualitative interpretation or human validation. Do not use its counts as proof of transactions, market prevalence, or offender behaviour.
