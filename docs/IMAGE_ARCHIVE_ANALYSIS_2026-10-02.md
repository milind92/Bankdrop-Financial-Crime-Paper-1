# Paper 1: Methods and Results incorporating completed author assessment

**Completed article-support report, 2 October 2026.** The fixed screenshot computation, returned two-author judgments, and final adjudication are complete and their arithmetic is verified. This draft integrates all five assessed targets and their uncertainty. Milind retains the final interpretation and publication decision. The full archive percentages remain OCR rule-positive counts; the human assessment supplies separate estimates of correspondence with visible source claims.

Public [agreement and validity tables](../outputs/image_validation_20261002/) and file-level provenance support the human-assessment results. The report is Methods/Results support text; final article interpretation remains with the authors.

## Methods

### Design and archival frame

We conducted a retrospective, descriptive content analysis of a fixed archive of Bank Drop research materials. The archive contains 999 Markdown paths and 1,101 PNG paths. An earlier folder-based screen selected 980 Markdown notes. We used those notes only to identify locally referenced screenshots: 391 selected notes contained at least one resolved local image reference. This produced 1,048 resolved reference occurrences to 1,043 PNG paths, alongside seven missing and 85 external references. We collapsed byte-identical screenshots by SHA-256, yielding 1,037 unique image contents in 15 archive folder groups. The unit of analysis is an archived screenshot, not a unique post, listing, actor, transaction, or platform. Thirty-five novel image contents not referenced by the selected notes were outside the defined linked-image frame. Folder labels and filename date tokens were treated as archive metadata, not verified source identities or collection/post dates.

### Integrity, OCR, and coding

For each included screenshot, we verified that its extracted PNG bytes matched both the frozen ZIP entry and the SHA-256 value in the OCR table. The fixed OCR cache reported completed extraction for all 1,043 referenced PNG paths. We retained all 1,037 distinct image contents, including the 6 with fewer than 30 words according to the OCR table. OCR completion is a software status and does not establish transcription accuracy. We then applied the released, fixed case-insensitive regular-expression codebook to each image's OCR separately. The codebook comprises 12 substantive typology signal families, six candidate AML signal families, and one data-quality flag. A code was positive if at least one of its patterns matched within that single image; multiple hits in one image did not add to its binary count. No text from separate images or researcher Markdown was joined to create a positive result. All code and file hashes are in the controlled analysis manifest.

### Descriptive analysis and independent author assessment

We reported the number and percentage of included screenshots with each OCR rule match, within-image co-occurrence, exact OCR-text deduplication, restriction to at least 30 recorded OCR words, leave-one-archive-group-out percentages, and a unit-matched comparison with the earlier joined-note calculation. The percentages describe the fixed archive; the screenshots were not sampled probabilistically from an external marketplace.

Five constructs were selected for assessment against original images: bank-drop offers/requests; bank-log/account-access offers/requests; bundled identity/credential offers/requests; an explicit email/recovery/session relationship with account access; and bank-log/account access packaged or explicitly linked with email, cookie, recovery, or session access. Selection followed examination of earlier mixed-record error diagnostics and the rule wording, so the focus was post hoc. The other 13 substantive rule families remain exploratory lexical results without a corresponding human validity assessment.

A fixed-seed packet (seed 20261002) contained 249 image-and-target assignments over 205 distinct screenshots. Each of four targets had 20 sampled rule positives and 30 sampled rule negatives. For the bank-log-plus-email/access relationship, all 19 rule positives were assessed, together with 30 sampled rule negatives. Sampling was stratified by recorded OCR length (<30 versus >=30 words) and conservative mapping to prior July coder-packet exposure. The private coordinator key retained stratum populations, sample sizes and machine predictions. The author-facing materials omitted machine predictions, sample weights and previous answers. Each author assessed the original screenshot separately as present, absent, ambiguous, unreadable or out of scope, with reasons recorded. The authors reported independent coding; packet masking was verified, while coding conduct is not established by agreement or CSV contents alone. Present meant that visible source text satisfied the specified claim criterion; it did not establish that the claim was truthful or that an advertised event occurred.

Five-category exact agreement and unweighted Cohen's kappa were calculated overall and for each target from the returned independent answers, before adjudication. These describe consistency in the deliberately stratified review packet. Since some screenshots were assessed for multiple targets, 249 is the number of paired judgments, while 205 is the number of distinct images. All disagreements and all matching nonbinary answers were sent for a recorded final decision. Nonbinary final outcomes were reported separately and were not converted to absent. The integrity audit checked complete assignment coverage, unchanged image/target/question identities, all adjudication identities and reasons, and the input and output file hashes.

For classification performance, an image judged present was counted as a true positive when the rule was positive and as a false negative when the rule was negative. A judged-absent image was counted as a false positive or true negative correspondingly. Each sampled judgment received its stratum expansion weight N_h/n_h, where N_h is the archive population and n_h the reviewed sample in stratum h. Positive predictive value (PPV) was the weighted true-positive total divided by the sum of weighted true-positive and false-positive totals. It therefore measures the correspondence of a rule match with the adjudicated claim criterion within this fixed archive. All reviewed rule positives had final binary labels; nonbinary outcomes occurred only among reviewed rule negatives. A 1,000-resample bootstrap, seeded by 20261002 and conducted separately within each stratum, supplied descriptive ranges using the 2.5th and 97.5th percentiles for PPV. Census strata were kept fixed. The ranges reflect variability supported by this small sample and are not intervals for external market prevalence or human-label error.

The July 2026 workbooks contained 1,032 paired judgments on mixed Markdown/OCR packets. Only 83 older judgments mapped to one preserved screenshot with no extra Markdown and exactly matching OCR; 79 of those were absent and four present, across 18 targets. The earlier definitions and packet context differed, so old answers and reliability statistics were not substituted for the present task. Of the 249 new assignments, 143 were conservatively mapped to earlier packet exposure and 106 were not. Thus the current masking design concealed predictions, while the sample was not wholly unfamiliar to the authors.

### Research governance and reporting boundary

The project documentation identifies Griffith University Human Ethics Protocol 2025/697. This identifier does not itself establish the approved access, consent, quotation, or screenshot-release conditions. We kept screenshot-level material, OCR text, and reviewer files in a controlled workspace; this draft uses aggregate counts and no verbatim source extracts. The authors' final publication decision must remain within the protocol and applicable institutional conditions.

## Results

### Archive rule detections and sensitivity

The 1,037 distinct screenshot contents had a median of 111 recorded OCR words (range 14–512). Table 1 presents the unchanged automatic rule counts. These are detections in OCR; the separate human assessment below evaluates five specific claim interpretations. A rule-positive image is not automatically a human-confirmed claim or a separate incident.

**Table 1. OCR rule matches in the 1,037-image archive.**

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

Within a single screenshot, bank-log and bank-drop rules co-occurred in 91 images. The jurisdiction-localisation and domestic-account-preference rules produced exactly the same 199 positive images in this corpus; these labels therefore do not supply independent evidence. The broad cash-out regex matched 173 of 178 cash-out-rule-positive images, and the broad crypto-to-bank proximity regex matched all 38 crypto-to-bank candidate-positive images. Earlier human validation of the historical mixed-record analysis also identified low precision for those service/flow targets. We consequently report these cash-out and crypto-to-bank counts as exploratory lexical detections; these service/flow constructs were outside the five-target human assessment.

A unit-matched check on the 391 notes with local images showed 118 cash-out positives in the historical Markdown-plus-OCR analysis, 106 using note-joined OCR alone, and 106 when positive status was taken from separately coded images. For the crypto-to-bank candidate, the corresponding counts were 34, 28, and 25, including three joined-OCR positives that did not occur within any one screenshot. The old 980-note and current 1,037-image percentages cannot be interpreted as a temporal change because their units and text provenance differ.

### Agreement and adjudication

The two authors agreed on 243 of 249 assigned judgments (97.6% exact agreement; pooled five-category Cohen's kappa = 0.955). All six disagreements occurred in the bank-drop or bank-log offer/request targets. Table 2 reports target-specific agreement. The 18-row final review included the six disagreements and 12 matching nonbinary pairs. Final labels comprised 94 present, 142 absent, 12 out of scope and one unreadable judgment. Reliability was calculated before this reconciliation and was not recomputed from consensus labels.

**Table 2. Agreement on original images before adjudication.**

| Target | Exact agreements / assigned judgments | Agreement | Five-category Cohen's kappa |
|---|---:|---:|---:|
| Bank-drop offer/request | 47/50 | 94.0% | 0.897 |
| Bank-log/account-access offer/request | 47/50 | 94.0% | 0.892 |
| Bundled identity/credential offer/request | 50/50 | 100.0% | 1.000 |
| Email/recovery/session relation with account access | 50/50 | 100.0% | 1.000 |
| Bank-log/account access linked to email/cookie/recovery/session access | 49/49 | 100.0% | 1.000 |

### Correspondence between rule matches and visible source claims

Table 3 gives the weighted PPVs for all five assessed constructs. Bank-drop PPV was 80.0%, based on 16 adjudicated positives among 20 sampled rule-positive images; its descriptive bootstrap range was wide (56.8%–98.3%). The bank-log-plus-email/access rule had 16 adjudicated positives and three false positives among all 19 rule-positive images, producing an observed PPV of 84.2% for this finite positive set. This relationship criterion included visible packaging or an explicit linkage in listings, requests, recommendations or tutorials. The percentage therefore applies to that broader criterion rather than to product offers alone.

**Table 3. PPV against the adjudicated visible-claim criteria.**

| Target | Reviewed rule positives / archive rule positives | Human-present among reviewed positives | Weighted PPV | Descriptive PPV bootstrap range or census basis |
|---|---:|---:|---:|---|
| Bank-drop offer/request | 20/213 | 16/20 | 80.0% | 56.8%–98.3% |
| Bank-log/account-access offer/request | 20/343 | 17/20 | 80.9% | 55.9%–100.0% |
| Bundled identity/credential offer/request | 20/184 | 15/20 | 71.6% | 46.3%–95.3% |
| Email/recovery/session relation with account access | 20/84 | 13/20 | 54.6% | 27.7%–81.5% |
| Bank-log/account access linked to email/cookie/recovery/session access | 19/19 | 16/19 | 84.2% | Positive census; 16/19 |

The review sample was deliberately stratified. Consequently, raw sample proportions are not always the same as estimates expanded to the archive: bank-log PPV was 85.0% in the reviewed positive sample and 80.9% after weighting; the corresponding values were 65.0% and 54.6% for the email/access relationship, and 75.0% and 71.6% for bundled identity products. The variation in these results shows why high agreement between authors cannot be used as evidence of uniform accuracy across the five automated rules. For the relationship target with a positive census, the degenerate bootstrap range at 84.2% represents complete coverage of the rule-positive set, without accounting for human judgment error or performance in other archives.

Table 4 reports the unweighted adjudicated sample classifications, including outcomes among sampled rule negatives. These are review-sample counts, not incident counts or extrapolated archive totals. The rule-negative sample contained missed visible claims for four targets. No missed claim was observed among the 28 evaluable rule negatives for the bank-log-plus-email/access target, but two additional negatives were out of scope and the 30 reviewed negatives were only a sample of 1,018 rule-negative images. These observations do not establish perfect recall or negative predictive value in the archive. Nonbinary negative judgments remain explicit; estimates of missed-claim behaviour that omit them are conditional on an evaluable reference label.

**Table 4. Adjudicated classifications in the stratified review sample.**

| Target | True positive | False positive | False negative | True negative | Out of scope or unreadable |
|---|---:|---:|---:|---:|---:|
| Bank-drop offer/request | 16 | 4 | 3 | 22 | 5 |
| Bank-log/account-access offer/request | 17 | 3 | 4 | 24 | 2 |
| Bundled identity/credential offer/request | 15 | 5 | 3 | 25 | 2 |
| Email/recovery/session relation with account access | 13 | 7 | 7 | 21 | 2 |
| Bank-log/account access linked to email/cookie/recovery/session access | 16 | 3 | 0 | 28 | 2 |

## Interpretation and reporting limits

The current evidence supports a completed, reproducible analysis of OCR rule detections in a defined archive and a separate assessment of five visible source-claim criteria. Source claims must be distinguished from the truth of an advertisement or an event. Automatic detections and weighted performance estimates cannot establish completed services, money movement, market prevalence, actor identity, victim counts or harm. Images are not verified unique posts or transactions. The 13 other substantive rule families remain exploratory lexical results.

The supplied archive does not verify who captured each image, actual capture dates or source completeness. Filename dates are not used as capture dates, and no time trend is inferred. The linked-image frame excludes 35 novel unreferenced contents, seven missing references and 85 external references by definition. The included frame also contains nonbinary items identified during review; it has not been retrospectively redefined as an evidence-only denominator from the validation sample.

OCR accuracy has not been benchmarked against a gold transcript. The original-image assessment evaluates the combined OCR-and-rule classification against visible claim criteria, without estimating transcription error separately. Generic patterns may match navigation or discussion. The four targets with only 20 reviewed positives have wide PPV ranges, and 143 assigned judgments were mapped to prior exposure. The post hoc focus and these limits should be carried into the Discussion. Additional collection history is not presumed to exist.

The results can now be used to draft the article's analysis section. The authors' final decision is how strongly each assessed construct should be interpreted and whether weaker targets should retain lexical wording or be omitted from substantive claims. The Methods and Results present every assessed target rather than treating the two highest cited PPVs as evidence that the entire codebook is valid.

## Method citation

Cohen, J. (1960). A coefficient of agreement for nominal scales. *Educational and Psychological Measurement, 20*(1), 37–46. https://doi.org/10.1177/001316446002000104
