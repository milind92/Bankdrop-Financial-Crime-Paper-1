# Revised typology pair-boundary diagnostic

The historical derived-analysis tables use the mixed 980-note screen and are
not estimates for the author-reviewed evidence corpus. After approved source
spans and Phase 3 coding are available, this separate controlled diagnostic
distinguishes two codes observed within one approved text span from codes
observed only in different spans of the same capture unit.

In revised mode, Phase 3 writes `artifact_coding_long.csv` outside this public
repository. It has one row per approved text span and target code, including
zeroes, with the unit ID, span ID, source, content hash, binary presence, hit
count, and pattern count. The existing unit-level tables remain available.
The pair builder checks that every approved unit and span has a complete code
matrix and that the span hit totals reproduce the unit-level hit totals.

Run only on a controlled revised Phase 3 directory:

```powershell
python .\code\derived_analysis\build_revised_pair_boundaries.py `
  --phase3-dir $env:BANK_DROP_REVISED_PHASE3_DIR `
  --evidence-corpus $env:BANK_DROP_EVIDENCE_CORPUS `
  --output-dir $env:BANK_DROP_REVISED_PAIR_DIR
```

The output directory must be separate from Phase 3 and outside the public
repository. The script refuses historical Phase 3 metadata and nonempty
output directories. It checks the screened evidence-corpus hash and every
span identity against the Phase 3 table. It writes a controlled aggregate
`revised_typology_pair_boundaries.csv` and a hash-bearing manifest; both are
blocked from public export while the methodological hold remains open.

For each pair of the 12 substantive typology codes, overall and by approved
source, the table reports:

- `units_with_both_codes_n`: capture units containing both codes anywhere;
- `units_with_both_in_same_artifact_n`: those units with at least one approved
  span containing both codes;
- `cross_artifact_only_units_n`: units containing both codes but never in the
  same approved span; and
- `artifacts_with_both_codes_n`: approved spans containing both codes.

Here an *artifact* is one approved Markdown or OCR text span. Different spans
may still come from the same screenshot or source post. A capture unit can
contain multiple posts or images. The counts do not identify unique posts,
actors, transactions, coordination, or market prevalence. No lift or
significance test is produced from this purposive collection. Duplicate
captures, source concentration, construct validity, OCR accuracy, and the
revised human holdout remain to be assessed before any pair claim enters an
article. The manifest always labels the result provisional and not article
ready.
