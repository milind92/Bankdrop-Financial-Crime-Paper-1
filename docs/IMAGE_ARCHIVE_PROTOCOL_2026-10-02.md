# Fixed screenshot archive: reproduction and completed author assessment

The current Paper 1 analysis comprises a bounded archive calculation and a completed five-construct author assessment. Read the [Methods and Results](IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md), [archive aggregates](../outputs/image_archive_20261002/) and [assessment aggregates](../outputs/image_validation_20261002/). Historical mixed-note outputs remain an audit record. Final interpretation and article wording remain with Milind.

## Defined frame

The fixed archive has 999 Markdown paths and 1,101 PNG paths. The historical screen selected 980 notes; 391 have resolved local image links. Of 1,140 reference occurrences, 1,048 resolve, seven are missing and 85 external. Resolved links identify 1,043 PNG paths and 1,037 SHA-256-unique image contents. Thirty-five novel unreferenced image contents are outside this linked-image frame. The unit is screenshot content, not a verified unique post, account, person or transaction. Folder labels and filename dates are archive metadata; source identities and capture dates are unverified.

The [portable archive reproducer](../code/image_archive/reproduce_controlled.py) verifies each included PNG against its extracted copy, original frozen ZIP member and OCR-cache SHA-256. It applies all 19 released rules separately to each image's OCR: 12 typology families, six AML candidates and one quality flag. A positive means at least one pattern matched in that image. Text from other images and researcher Markdown is not joined. All six images with fewer than 30 recorded OCR words stay in the denominator. OCR completion does not establish transcription accuracy.

The computation reports counts, within-image co-occurrence, rule overlap, pattern diagnostics, exact OCR-text and OCR-length sensitivity, a unit-matched historical comparison and leave-one-folder-group-out ranges. A fresh end-to-end replay after the audit reproduced all 12 original result files byte for byte. All loaded matrices, the orphan audit, source ZIP, rule source and both legacy workbooks now have input file hashes. Public provenance contains whole-file fingerprints, with no image-level hashes or source text.

## Completed five-construct assessment

The five constructs are bank-drop offers/requests; bank-log/account-access offers/requests; bundled identity/credential offers/requests; an explicit email/recovery/session relationship with account access; and bank-log/account access packaged or explicitly linked with email, cookie, recovery or session access. The focus followed earlier mixed-record error diagnostics and rule wording, so selection is post hoc. The other 13 substantive rule families remain exploratory lexical results.

The packet assigned 249 paired judgments over 205 original images. Four targets each have 20 sampled rule positives and 30 sampled negatives. The package-or-link target has all 19 rule positives and 30 sampled negatives. Seed 20261002 fixes selection, stratified by OCR word count (<30 versus >=30) and conservative mapping to prior July packet exposure. The private key retains N_h, n_h and predictions; author-facing materials omit predictions, weights and prior answers. Of 249 assignments, 143 map to prior exposure and 106 do not. The sample is not wholly unseen.

The authors reported independent coding of original images using present, absent, ambiguous, unreadable and out_of_scope. Packet masking is verified; CSV contents alone do not establish actual coding conduct. Present means a visible claim meets the question, without establishing its truth. Pre-adjudication exact agreement is 243/249 (97.6%); pooled five-category unweighted Cohen's kappa is 0.955. Six disagreements and 12 matching nonbinary pairs have recorded final decisions and reasons. Final labels are 94 present, 142 absent, 12 out of scope and one unreadable.

PPV uses N_h/n_h expansion weights and adjudicated present/absent labels. Nonbinary outcomes are retained separately; all reviewed rule positives have binary final labels. The four sampled-positive targets have 1,000 seeded within-stratum bootstrap descriptive ranges using the 2.5th/97.5th percentiles. These small-sample ranges do not cover human-label error or external-market variation. The package-or-link target's 16/19 PPV is an observed census of its finite positive set; its zero-width resampling range is not presented as a precise population confidence interval. Sampled rule negatives do not justify a perfect-recall claim.

Weighted PPVs are 80.0% (bank drops), 80.9% (bank logs), 71.6% (bundled identity/credentials), 54.6% (email/access relationship) and 84.2% (bank-log plus email/access relationship). The last criterion includes tutorials, requests and recommendations as well as listings. These estimates measure correspondence with visible claims within the defined archive, with target-specific uncertainty.

The old July sample has 1,032 paired mixed Markdown/OCR judgments. Only 83 map to a single preserved screenshot with equivalent OCR and no extra Markdown; 79 were absent and four present. Older definitions and presentation differ. Those decisions and reliability figures are not substituted for the new assessment.

## Controlled reproduction

Run archive reproduction with authorised inputs using the five arguments shown by `python code/image_archive/reproduce_controlled.py --help`. The output must remain outside the public checkout. The archival OCR cache is an input; the command does not perform or validate a new transcription.

Reproduce author assessment with [score_author_validation.py](../code/image_archive/score_author_validation.py):

```text
python code/image_archive/score_author_validation.py --packet-dir CONTROLLED/simple_icr --output-dir CONTROLLED/new_scoring --milind CONTROLLED/completed_author_sheets/Milind_sheet.csv --ausma CONTROLLED/completed_author_sheets/Ausma_sheet.csv --adjudicated CONTROLLED/simple_icr/scoring_results/adjudication_completed.csv
```

The controlled root retains the blank packet, private key, frame and original images. Node.js checks the viewer scripts; scoring mathematics use Python's standard library. The scorer validates immutable assignment metadata, viewer/blank-sheet equality, image hashes and complete final adjudication provenance before writing. It protects input files from output aliases and clears a stale derived validity CSV if a rerun has no adjudication. Original author files are never modified.

[export_validation.py](../code/image_archive/export_validation.py) accepts `--controlled-root CONTROLLED` and exports only explicitly selected aggregate fields after checking the independently audited hashes. The coordinator's independent arithmetic audit and manuscript builder remain controlled; their file hashes and the public scorer/exporter hashes are recorded in the public metadata. The data-free repository verifier reconciles all released assessment totals, PPVs and hashes.

## Reporting boundary

Unknown collectors, capture times, source completeness and OCR gold accuracy are disclosed limits. No additional collection history is presumed to exist. Archive percentages describe screenshot detections; visible claims do not establish completed sales, money movement, actor/victim counts or external prevalence. Screenshots, OCR text, individual decisions/reasons, sample keys and image-level rows remain controlled. Final article interpretation and publication decisions remain with the authors.
