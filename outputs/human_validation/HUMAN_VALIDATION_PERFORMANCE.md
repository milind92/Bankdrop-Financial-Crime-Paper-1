# Human validation aggregate results

## Interpretation boundary

Independent human coders: Ausma Bernot and Milind Tiwari.
The final decision counts below cover every sampled case-target unit. They are distinct from the disagreement-only adjudication outcomes reported in the ICR completion record.
The overall row pools heterogeneous case-target units across 18 targets; use the target rows for claim-specific performance.

Unweighted classification metrics describe this validation sample and cannot estimate corpus prevalence. Predictive values depend on the sampled class composition. When positive analysis_weight values are supplied, weighted point estimates require those weights to be valid for the sampling design; their approximate intervals use Kish effective sample sizes and do not account for clustering, finite-population corrections, or weight estimation.

Final classifications use the supplied adjudication decisions.
Raw agreement includes all five completed decision categories. Cohen's kappa and Gwet's AC1 use only pairs for which both coders selected present or absent. Confusion metrics use only final present/absent decisions. Blank metrics mean the denominator was zero or the statistic was mathematically undefined.

## Overall

- Sampled case-target units: 1032
- Complete coder pairs: 1032
- Exact agreement: 981/1032 (0.951)
- Cohen's kappa (binary pairs): 0.933; paired-record bootstrap 95% interval 0.905 to 0.961
- Gwet's AC1 (binary pairs): 0.973; paired-record bootstrap 95% interval 0.960 to 0.986
- Final decision counts: present=184; absent=846; ambiguous=2; insufficient_evidence=0; out_of_scope_record=0
- Final binary classifications: 1030
- Excluded from the confusion matrix: 2 (including unresolved=0)
- Analysis weights supplied for 1032 records.
- Weighted accuracy: 0.874; approximate 95% interval 0.851 to 0.893.

## Per-target aggregates

| Target type | Code | n | Agreement | Kappa | AC1 | Excluded | TP | FP | TN | FN | Precision | NPV | Sensitivity | Specificity | Accuracy | Weighted accuracy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| aml_candidate | bank_log_plus_email_access | 55 | 52/55 (0.945) | 0.911 | 0.936 | 0 | 15 | 0 | 38 | 2 | 1.000 | 0.950 | 0.882 | 1.000 | 0.964 | 0.952 |
| aml_candidate | crypto_to_bank_cashout | 60 | 50/60 (0.833) | 0.000 | 0.920 | 0 | 1 | 19 | 37 | 3 | 0.050 | 0.925 | 0.250 | 0.661 | 0.633 | 0.852 |
| aml_candidate | domestic_account_preference | 60 | 50/60 (0.833) | 0.914 | 0.928 | 1 | 9 | 11 | 28 | 11 | 0.450 | 0.718 | 0.450 | 0.718 | 0.627 | 0.639 |
| aml_candidate | escrow_or_exit_scam_risk | 60 | 58/60 (0.967) | NA | 1.000 | 1 | 0 | 19 | 40 | 0 | 0.000 | 1.000 | NA | 0.678 | 0.678 | 0.760 |
| aml_candidate | mule_or_account_holder_recruitment | 48 | 45/48 (0.938) | 0.000 | 0.956 | 0 | 2 | 6 | 40 | 0 | 0.250 | 1.000 | 1.000 | 0.870 | 0.875 | 0.985 |
| aml_candidate | telegram_sales_or_proof | 60 | 58/60 (0.967) | 0.659 | 0.982 | 0 | 2 | 18 | 40 | 0 | 0.100 | 1.000 | 1.000 | 0.690 | 0.700 | 0.953 |
| typology | bank_drop_sale | 60 | 57/60 (0.950) | 0.962 | 0.968 | 0 | 20 | 0 | 39 | 1 | 1.000 | 0.975 | 0.952 | 1.000 | 0.983 | 0.982 |
| typology | bank_log_sale | 60 | 57/60 (0.950) | 0.926 | 0.937 | 0 | 20 | 0 | 37 | 3 | 1.000 | 0.925 | 0.870 | 1.000 | 0.950 | 0.958 |
| typology | cashout_laundering_service | 60 | 55/60 (0.917) | 0.000 | 0.964 | 0 | 2 | 18 | 40 | 0 | 0.100 | 1.000 | 1.000 | 0.690 | 0.700 | 0.738 |
| typology | crypto_payment_or_conversion | 60 | 59/60 (0.983) | 0.946 | 0.976 | 0 | 12 | 8 | 40 | 0 | 0.600 | 1.000 | 1.000 | 0.833 | 0.867 | 0.876 |
| typology | email_access_takeover | 60 | 60/60 (1.000) | 1.000 | 1.000 | 0 | 16 | 4 | 40 | 0 | 0.800 | 1.000 | 1.000 | 0.909 | 0.933 | 0.969 |
| typology | escrow_trust_reputation | 60 | 57/60 (0.950) | 0.000 | 0.982 | 0 | 2 | 18 | 40 | 0 | 0.100 | 1.000 | 1.000 | 0.690 | 0.700 | 0.731 |
| typology | fullz_identity_package | 60 | 58/60 (0.967) | 0.965 | 0.967 | 0 | 20 | 0 | 36 | 4 | 1.000 | 0.900 | 0.833 | 1.000 | 0.933 | 0.931 |
| typology | jurisdiction_localisation | 60 | 58/60 (0.967) | 1.000 | 1.000 | 0 | 10 | 10 | 32 | 8 | 0.500 | 0.800 | 0.556 | 0.762 | 0.700 | 0.713 |
| typology | mule_recruitment | 49 | 47/49 (0.959) | NA | 1.000 | 0 | 0 | 9 | 40 | 0 | 0.000 | 1.000 | NA | 0.816 | 0.816 | 0.978 |
| typology | telegram_off_platform | 60 | 60/60 (1.000) | 1.000 | 1.000 | 0 | 5 | 15 | 40 | 0 | 0.250 | 1.000 | 1.000 | 0.727 | 0.750 | 0.848 |
| typology | tutorial_training_recruitment | 60 | 60/60 (1.000) | 1.000 | 1.000 | 0 | 13 | 7 | 37 | 3 | 0.650 | 0.925 | 0.812 | 0.841 | 0.833 | 0.854 |
| typology | vulnerable_group_exploitation | 40 | 40/40 (1.000) | NA | 1.000 | 0 | 0 | 0 | 40 | 0 | NA | 1.000 | NA | 1.000 | 1.000 | 1.000 |

## Interval methods and limits

The CSV reports Wilson 95% intervals for exact agreement and unweighted confusion-derived proportions. Kappa and AC1 intervals are deterministic paired-record percentile bootstrap intervals with 1000 resamples; they are blank when too few defined resamples exist. Weighted proportion intervals are labelled approximate and use Kish effective sample sizes. None of these intervals adjusts for source or duplicate clustering, a finite population, or estimated weights.
