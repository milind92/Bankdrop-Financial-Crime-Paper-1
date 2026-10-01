# Revised source-evidence descriptive tables

This provisional controlled builder is the descriptive route for a future
two-reviewer approved evidence corpus and its span-bounded Phase 3 run. It
does not use the historical 980-note denominator, the 463 combined-note text
hashes, or the historical Phase 4 narratives. No revised study table has yet
been produced because the real review sheets remain blank.

The script shares the hash and matrix checks used by the revised
[exact-span duplicate sensitivity](METHODS_REVISED_DUPLICATE_SENSITIVITY.md):
the screened evidence corpus and Phase 3 codebook must match their manifests;
each approved unit, span, target prediction, and span-level hit count must
reconcile. It also checks that screening flow counts reconcile to approved
units and source spans. Outputs are restricted to a separate controlled
directory outside the public repository.

Run from the repository root with controlled paths:

```powershell
python .\code\derived_analysis\build_revised_descriptive_tables.py `
  --phase3-dir $env:BANK_DROP_REVISED_PHASE3_DIR `
  --evidence-corpus $env:BANK_DROP_EVIDENCE_CORPUS `
  --output-dir $env:BANK_DROP_REVISED_DESCRIPTIVES_DIR
```

The output contains seven controlled CSVs and a hash manifest:

1. `revised_screen_flow_controlled.csv` reconciles screened and included
   Markdown notes, standalone approved orphan-image units, source spans, and
   image decision rows. Image decision rows are not unique image counts.
2. `revised_source_coverage_controlled.csv` reports approved capture units by
   source, text modality, and verified unit capture-date availability. A unit
   with unknown or mixed span dates has no verified unit date.
3. `revised_target_prevalence_controlled.csv` reports rule-positive counts and
   denominators overall and by source for the 12 substantive typologies and
   six exploratory AML candidates. The collection-quality flag is excluded.
4. `revised_modality_contribution_controlled.csv` partitions positive units
   into Markdown-only, OCR-only, and both-modality contributions. These refer
   to where a rule matched, not human-confirmed evidence of a service.
5. `revised_typology_cooccurrence_controlled.csv` reports all typology pairs
   overall, within each source, and after removing each source. It includes
   all four binary cells, Jaccard, and lift. Jaccard is blank when the union
   is empty; lift is blank when either marginal count or the denominator is
   zero. Co-occurrence within one capture unit can cross source artefacts;
   use the separate [pair-boundary diagnostic](METHODS_REVISED_PAIR_BOUNDARIES.md)
   before interpreting a highlighted pair.
6. `revised_source_concentration_controlled.csv` reports the share of
   rule-positive units contributed by the largest one and three sources,
   source HHI, and the number of positive source groups.
7. `revised_leave_one_source_out_controlled.csv` reports target counts and
   denominators after removing each source.

These are **rule-output diagnostics**, not validated article estimates. The
screened corpus is purposive; percentages describe approved captured units
and cannot estimate an external market. One approved unit can combine
multiple underlying posts, and source-text repetition does not prove item
identity. No p-values, confidence intervals for market prevalence, causal
claims, transaction claims, operational alerts, or automatic Phase 4 prose
are produced. Before an article uses any table, authors must lock target
definitions, complete fresh blinded target-level validation and OCR review,
inspect source and duplicate sensitivity, and approve the interpretation.
