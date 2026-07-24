# Phase 3 Typology Coding: Methods Note

## Purpose

Phase 3 creates an auditable deterministic typology-coding baseline. It combines Markdown-note text with Phase 2 OCR text and applies explicit regular-expression codebook rules. No LLM or external API is used.

## Inputs

- Controlled vault selected by `BANK_DROP_VAULT`.
- Controlled Phase 1 and Phase 2 outputs selected by `BANK_DROP_OUTPUTS_DIR`.

## Outputs

The phase produces typology and AML-indicator coding tables, aggregate typology summaries, criminal-objective summaries, source-level summaries, a codebook, and run metadata. Joined corpus, long-form coding, and evidence-snippet tables are controlled artifacts; only their safe aggregate derivatives are included in this repository.

## Reproduction Command

From the repository root after setting the controlled paths:

```powershell
python .\code\phase3_typology_coding\run_phase3_typology.py
python .\code\phase3_typology_coding\make_phase3_overview.py
```

## Interpretation Limits

The code is deterministic and supports audit trails, sampling, and first-pass descriptive mapping. It is not a substitute for qualitative interpretation or human validation. Do not use its counts as proof of transactions, market prevalence, or offender behaviour.