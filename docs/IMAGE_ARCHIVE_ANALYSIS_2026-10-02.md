# Paper 1: fixed screenshot Methods and Results

**Decision status (2 October 2026):** The computational analysis and bounded article text are complete for the frozen screenshot/OCR frame. Milind and Ausma's final independent image coding, agreement calculation, adjudication, and Milind's publication decision are the sole remaining human steps. All percentages below describe OCR rule positives rather than verified criminal activity. This is an observational archive analysis with unverified collection history; that absence is an explicit method limit, not a missing field to be guessed.

## Methods

### Design and archival frame

We conducted a retrospective, descriptive content analysis of a fixed archive of Bank Drop research materials. The archive contains 999 Markdown paths and 1,101 PNG paths. An earlier folder-based screen selected 980 Markdown notes. We used those notes only to identify locally referenced screenshots: 391 selected notes contained at least one resolved local image reference. This produced 1,048 resolved reference occurrences to 1,043 PNG paths, alongside seven missing and 85 external references. We collapsed byte-identical screenshots by SHA-256, yielding 1,037 unique image contents in 15 archive folder groups. The unit of analysis is an archived screenshot, not a unique post, listing, actor, transaction, or platform. Thirty-five novel image contents not referenced by the selected notes were outside the defined linked-image frame. Folder labels and filename date tokens were treated as archive metadata, not verified source identities or collection/post dates.

### Integrity, OCR, and coding

For each included screenshot, we verified that its extracted PNG bytes matched both the frozen ZIP entry and the SHA-256 value in the OCR table. The fixed OCR cache reported completed extraction for all 1,043 referenced PNG paths. We retained all 1,037 distinct image contents, including the 6 with fewer than 30 words according to the OCR table. OCR completion is a software status and does not establish transcription accuracy. We then applied the released, fixed case-insensitive regular-expression codebook to each image's OCR separately. The codebook comprises 12 substantive typology signal families, six candidate AML signal families, and one data-quality flag. A code was positive if at least one of its patterns matched within that single image; multiple hits in one image did not add to its binary count. No text from separate images or researcher Markdown was joined to create a positive result. All code and file hashes are in the controlled analysis manifest.

### Analysis and final independent assessment protocol

We report the number and percentage of included screenshots with each rule-positive OCR signal. These descriptive percentages refer only to the fixed image archive; the material was not sampled probabilistically from an external marketplace. We also examined within-image signal co-occurrence, exact OCR-text deduplication, OCR-length restriction, leave-one-archive-group-out percentages, and differences from the earlier joined-note calculation. Five source-claim constructs were selected for final author assessment: bank-log offers/requests, bank-drop offers/requests, bundled identity products, email-access relations, and the bank-log-plus-email-access relation. Selection was informed by theory and the earlier mixed-record error audit, so it is a post hoc focus rather than a preregistered hypothesis set. The other 13 substantive rule families remain completed exploratory lexical results, without a source-claim validity assertion. A fixed-seed, stratified packet contains 249 target judgments over 205 original screenshots: up to 20 rule positives and 30 rule negatives for each of the five constructs, with census selection when a positive stratum has fewer than 20 images. Stratification uses OCR word count (<30 versus >=30) and conservative appearance in July coder packets. Stratum population and sample sizes are retained in a separate coordinator key. Milind and Ausma will independently judge each original screenshot as present, absent, ambiguous, unreadable, or out of scope before seeing machine predictions or each other's responses. Five-category exact agreement and Cohen's kappa, reported overall and by target, will describe coder consistency. Disagreements and nonbinary judgments require a recorded final decision. The scorer then uses N_h/n_h weights to estimate the rule's true-positive, false-positive, true-negative, and false-negative image counts within the fixed archive; it reports nonbinary totals separately and descriptive within-stratum bootstrap intervals for derived ratios. These are archive-level validity diagnostics, not estimates of external market prevalence. No final image-level ICR or adjudicated accuracy estimate is asserted before the authors return their sheets.

The July 2026 workbooks contain 1,032 paired judgments on 313 mixed Markdown/OCR packets. We audited them against the new screenshot frame. Only 83 judgments map to one preserved screenshot with no non-embed Markdown words and OCR text exactly matching the present cache; the authors agreed on all 83, but 79 were absent and four present, distributed thinly across 18 targets. The July code definitions and packet context also differ from the present source-claim task. We therefore retain the earlier agreement as a historical sensitivity and do not transfer its kappa or apparent accuracy to the five current constructs. The prepared new sheets contain no copied July answers.

### Research governance and reporting boundary

The project documentation identifies Griffith University Human Ethics Protocol 2025/697. This identifier does not itself establish the approved access, consent, quotation, or screenshot-release conditions. We kept screenshot-level material, OCR text, and reviewer files in a controlled workspace; this draft uses aggregate counts and no verbatim source extracts. The authors' final publication decision must remain within the protocol and applicable institutional conditions.

## Results before independent claim-level assessment

The 1,037 distinct screenshot contents had a median of 111 recorded OCR words (range 14-512). The rule-positive counts are shown below. The five rows selected for final source-claim review are `bank_log_sale`, `bank_drop_sale`, `fullz_identity_package`, `email_access_takeover`, and `bank_log_plus_email_access`. Every table entry remains a lexical signal and must not be interpreted as a verified offer, service, recruitment, financial flow, or victimisation before the relevant human result exists.

| Type | OCR rule | Rule-positive images | Percentage of 1,037 |
|---|---|---:|---:|
| typology | `bank_log_sale` | 343 | 33.08% |
| typology | `bank_drop_sale` | 213 | 20.54% |
| typology | `fullz_identity_package` | 184 | 17.74% |
| typology | `email_access_takeover` | 84 | 8.10% |
| typology | `mule_recruitment` | 10 | 0.96% |
| typology | `cashout_laundering_service` | 178 | 17.16% |
| typology | `crypto_payment_or_conversion` | 183 | 17.65% |
| typology | `telegram_off_platform` | 121 | 11.67% |
| typology | `escrow_trust_reputation` | 229 | 22.08% |
| typology | `tutorial_training_recruitment` | 156 | 15.04% |
| typology | `jurisdiction_localisation` | 199 | 19.19% |
| typology | `vulnerable_group_exploitation` | 0 | 0.00% |
| aml_candidate | `bank_log_plus_email_access` | 19 | 1.83% |
| aml_candidate | `domestic_account_preference` | 199 | 19.19% |
| aml_candidate | `telegram_sales_or_proof` | 26 | 2.51% |
| aml_candidate | `crypto_to_bank_cashout` | 38 | 3.66% |
| aml_candidate | `escrow_or_exit_scam_risk` | 205 | 19.77% |
| aml_candidate | `mule_or_account_holder_recruitment` | 9 | 0.87% |

The separate collection-quality flag matched 2 images. The 12 typology and six AML candidate counts overlap and should not be added together.

Exact OCR strings formed 1,035 groups among the 1,037 distinct images. Retaining one representative per identical OCR string changed the cash-out rule count from 178 to 177 and did not change the other substantive rule counts. Restricting to images with at least 30 recorded OCR words removes 6 images; target-specific counts are in the controlled sensitivity table. The bank-log rule-positive percentage ranged from 29.54% to 37.00% in leave-one-folder-group-out analyses, compared with 33.08% overall, indicating sensitivity to archive composition.

Within a single screenshot, bank-log and bank-drop rules co-occurred in 91 images. The jurisdiction-localisation and domestic-account-preference rules produced exactly the same 199 positive images in this corpus; these labels therefore do not supply independent evidence. The broad cash-out regex matched 173 of 178 cash-out-rule-positive images, and the broad crypto-to-bank proximity regex matched all 38 crypto-to-bank candidate-positive images. Earlier human validation of the historical mixed-record analysis also identified low precision for those service/flow targets. We consequently report their counts only as rule detections pending the new claim-level assessment.

A unit-matched check on the 391 notes with local images showed 118 cash-out positives in the historical Markdown-plus-OCR analysis, 106 using note-joined OCR alone, and 106 when positive status was taken from separately coded images. For the crypto-to-bank candidate, the corresponding counts were 34, 28, and 25, including three joined-OCR positives that did not occur within any one screenshot. The old 980-note and current 1,037-image percentages cannot be interpreted as a temporal change because their units and text provenance differ.

## Interpretation limits for the final article

The supplied archive alone does not verify who captured the screenshots, the actual capture dates, source completeness, or the truth of text visible in a screenshot. We do not use filename dates as capture dates. OCR accuracy has not been measured against a gold transcript; the new authors' image judgments assess the *combined* OCR-and-rule decisions and do not establish transcription error rates. Generic regex patterns can match navigation or discussion. The original coauthor packets mentioned 832 of the 1,037 image contents by basename, so the final author assessment includes both previously mentioned and apparently unseen images. No claim about market prevalence, transaction frequency, actor identity, or victim harm follows from these results. The final article should use source-claim language only for targets that survive the independent image-based assessment and Milind's final construct decision. The five focused constructs should not be treated as validated merely because this computation is complete.
