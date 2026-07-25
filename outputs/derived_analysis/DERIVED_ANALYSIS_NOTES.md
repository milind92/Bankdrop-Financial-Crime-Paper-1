# Deterministic Derived Analysis Notes

## Status

These tables extend the aggregate, deterministic Phase 1–4 analysis. They are descriptive post-processing outputs and are not a Phase 5 or LLM-assisted empirical analysis.

The controlled deterministic screen evaluated 999 combined records. A final eligibility and evidence-unit audit has not been locked. The tables therefore report two clearly separated populations:

| Population value | Denominator | Meaning |
|---|---:|---|
| `full_screened` | 999 | Every combined record evaluated by the completed deterministic screen. |
| `exact_text_unique_sensitivity` | 479 | One deterministic representative per combined-text SHA-256 value. This is an exact-text duplicate sensitivity population, not a verified set of unique posts, listings, actors, transactions, or eligible evidence units. |

The 479-record sensitivity population must not be described as the prospective primary deduplicated population in the analysis plan. A later locked eligibility or evidence-unit audit may require a complete deterministic rerun.

## Files

### `duplicate_sensitivity.csv`

Reports each substantive typology’s full-screened and exact-text-unique counts, descriptive percentages, duplicate-associated count difference, and rank comparison. `percentage_point_difference` is the exact-text-unique percentage minus the full-screened percentage.

### `typology_cooccurrence.csv`

Reports every pair among the 12 substantive typologies in each analysis population, including pairs with zero overlap:

- `n11_both_present`: both codes present;
- `n10_a_only`: code A present and code B absent;
- `n01_b_only`: code B present and code A absent;
- `n00_neither`: neither code present;
- `jaccard`: `n11 / (n11 + n10 + n01)`; and
- `lift`: `(n11 / N) / ((nA / N) × (nB / N))`.

No minimum-support threshold has been imposed because that remains an author decision. Small-support pairs must be treated as unstable. Co-occurrence does not establish direction, chronology, common actors, transactions, coordination, a completed service chain, or causation.

### `typology_cooccurrence_by_source.csv`

Repeats the complete typology-pair contingency table within each source group and population. Source-specific denominators are shown explicitly. Small source strata and zero-overlap pairs are retained for transparency and must not be treated as stable estimates.

### `typology_cooccurrence_leave_one_source_out.csv`

Removes each source group in turn and recalculates every typology pair. The table reports the remaining contingency cells, Jaccard and lift, plus their differences from the corresponding full-population values. This is the source-stability analysis for co-occurrence; it remains descriptive.

### `typology_aml_crosswalk.csv`

Reports descriptive overlap between substantive typologies and AML candidates for both populations. AML candidates remain corpus-derived research hypotheses; they are not confirmed red flags, suspicious-activity indicators, or monitoring controls.

Seven pairs are excluded because their rule definitions reuse the same lexical construct or define the AML candidate as a strict subset or conjunction of the typology:

- `bank_log_sale` with `bank_log_plus_email_access`;
- `email_access_takeover` with `bank_log_plus_email_access`;
- `jurisdiction_localisation` with `domestic_account_preference`;
- `escrow_trust_reputation` with `escrow_or_exit_scam_risk`;
- `telegram_off_platform` with `telegram_sales_or_proof`;
- `crypto_payment_or_conversion` with `crypto_to_bank_cashout`; and
- `mule_recruitment` with `mule_or_account_holder_recruitment`.

Excluding these structural overlaps avoids presenting associations that arise by construction as empirical discoveries.

### `service_chain_grouping.csv`

Reports unique-record unions for four exploratory descriptive groupings:

| Group | Included substantive codes |
|---|---|
| Account access and takeover | `bank_log_sale`; `email_access_takeover` |
| Identity and receiving-account infrastructure | `bank_drop_sale`; `fullz_identity_package`; `mule_recruitment` |
| Coordination, learning, and market trust | `escrow_trust_reputation`; `telegram_off_platform`; `tutorial_training_recruitment` |
| Monetisation and settlement | `cashout_laundering_service`; `crypto_payment_or_conversion` |

Counts are unions of records and do not double-count a record within a group. The mapping is labelled `exploratory_descriptive_grouping`. It does not validate a theory, establish sequence, or show that any service chain was completed. Final theoretical use still requires explicit author and domain review.

### `typology_source_normalized.csv`

Reports each typology’s positive-record count and percentage within each source and population, the source’s share of all positive records for that typology, and source-level Markdown/OCR availability counts. Modality counts describe whether those inputs were present; they are not OCR accuracy measures.

### `source_concentration.csv`

Reports, for each typology and population:

- positive-record count;
- number of contributing source groups;
- largest contributing source and share;
- cumulative share of the three largest contributing sources; and
- Herfindahl–Hirschman concentration index calculated from source shares among positive records.

The concentration measures describe the captured corpus only. They do not estimate source activity outside the controlled dataset.

### `source_leave_one_out.csv`

Removes one source group at a time and recalculates each typology’s count, descriptive percentage, and count-based rank. A positive `rank_change` means the typology moved down after that source was removed; a negative value means it moved up. Rank changes are descriptive and should be interpreted together with the remaining numerator and denominator.

### `derived_analysis_metadata.json`

Records the population counts, duplicate-audit totals, output row counts, script version, interpretation boundaries, and SHA-256 values of the three controlled aggregate-generation inputs. It contains no local path or record-level data.

## Reproduction

Authorised researchers can regenerate the tables from the controlled Phase 3 output directory:

```powershell
python .\code\derived_analysis\build_derived_analysis.py `
  --source-dir <controlled-phase3-output-directory> `
  --output-dir .\outputs\derived_analysis
```

The public repository does not contain the record-level inputs required by that command. Access is governed by the data-availability and controlled-audit documents.
