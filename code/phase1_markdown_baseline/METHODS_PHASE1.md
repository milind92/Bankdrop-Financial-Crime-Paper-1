# Phase 1 Markdown Baseline: Methods Note

## Purpose

Phase 1 creates a reproducible, deterministic baseline from the extracted `DW Project` Obsidian-style vault. It does not use OCR or LLM interpretation. It establishes file coverage, source/date coverage, keyword counts, entity mentions, price mentions, and image-reference mapping for later analysis.

## Controlled Inputs And Outputs

Set `BANK_DROP_VAULT` to the controlled vault location. If it is not set, the script expects `work\bank_drop_project\DW Project` below `BANK_DROP_WORKSPACE`.

Set `BANK_DROP_OUTPUTS_DIR` to the controlled output location. If it is not set, outputs are written below `outputs` in `BANK_DROP_WORKSPACE`.

## Code Files

- `config.json`: keyword, bank, country/region, payment-rail, and date-pattern dictionaries.
- `extract_phase1.py`: creates the primary corpus and long-form extraction tables.
- `summarise_phase1.py`: creates compact summary tables from primary outputs.
- `run_phase1.py`: convenience runner for the two scripts.

## Outputs

Primary outputs include note-level corpus metadata, keyword and entity tables, image references, and price mentions. Derived outputs include `source_summary.csv`, `keyword_summary_by_source.csv`, `entity_summary_by_source.csv`, `top_price_amounts.csv`, `phase1_summary.json`, and run metadata.

Long-form input-derived tables are controlled artifacts and must not be added to GitHub. The checked-in repository contains publication-safe aggregate outputs only.

## Reproduction Command

From the repository root after setting the controlled paths:

```powershell
python .\code\phase1_markdown_baseline\run_phase1.py
```

## Interpretation Limits

Phase 1 is descriptive and dictionary-based. Counts indicate where relevant material appears; they are not final typology findings or evidence of completed criminal activity. OCR is deferred to Phase 2.