# End-to-end audit of the completed Paper 1 analysis

**Scope:** the current fixed-screenshot analysis and supplied two-author assessment. Historical mixed-note and alternative reviewed-evidence workflows remain audit records; their incomplete alternative-design gates are not outstanding tasks for this completed screenshot design. Final interpretation and article wording remain with Milind.

## Findings corrected

| Finding | Correction | Effect on current results |
|---|---|---|
| Public status pages still said author coding was pending | Integrated the supplied completed assessment into Methods/Results, protocol, current claims, aggregate outputs and version metadata | Current drafting status is accurate |
| Scorer checked final IDs/categories but insufficient adjudication provenance, and wrote outputs before all checks | Validate image/target identities, copied author decisions/reasons and nonblank final reasons before any output; reject input/output aliases | Current supplied decisions passed; no label changed |
| A pending rerun could retain an old validity CSV | Clear that derived file when adjudication is absent; protect original author inputs | Prevents stale results appearing current |
| Draft builder did not freeze every reported scoring value | Require scoring-output hashes to match both scoring manifest and independent audit; record scorer/audit hashes | Current numbers reproduce unchanged |
| Archive replay hashed only part of its loaded inputs | Added both old coding matrices, orphan audit and both legacy coder workbooks to the input inventory | Twelve original result files remain byte-identical |
| Prior CI run warned about Node.js 20 action runtimes | Updated checkout and Python setup to their Node.js 24 versions, verified against [checkout](https://github.com/actions/checkout) and [setup-python](https://github.com/actions/setup-python) upstream documentation | CI verification uses maintained runtimes |

## Verification evidence

- A fresh controlled run of `reproduce_controlled.py` verified all included PNG bytes against the extracted source, original ZIP entries and OCR-cache image hashes, and recalculated all 19 rules separately within each image. All **12** original aggregate/controlled output files match byte for byte.
- The completed author files cover all 249 assignments with unique item identities and unchanged target/question/image metadata. The private key, frozen blank sheets, original images and viewer data agree. The offline JavaScript passes Node syntax checks; browser interaction was not separately exercised during this audit, and completed author CSVs are the authoritative coding record.
- Exact-fraction agreement and weighted confusion cells were independently reconstructed from the source rows. The scorer replay matched every saved validation field. A separate read-only reviewer regenerated all assignments from the frame and seed, confirmed strata and weights, and reviewed the corrections.
- Results remain **243/249 exact agreements (97.6%)**, pooled five-category **kappa 0.955**, and five weighted PPVs of **80.0%, 80.9%, 71.6%, 54.6% and 84.2%** in the order reported by the current Methods/Results. The last target is a positive census of 16 present claims among 19 rule positives.
- The data-free suite, public integrity/privacy verifier and controlled package verification passed. Regression checks cover invalid adjudication before writes, preserved author inputs, stale pending-run results, category pairing, weighting, nonbinary handling, public-output guards and altered released kappa. The exact final test count and GitHub CI result are recorded in the controlled release completion record.
- Public release fields are explicitly selected aggregates and whole-file fingerprints. Raw images/OCR, individual answers/reasons, image hashes, source groups and sample keys are excluded. Current claim entries map to their public evidence files.

## Interpretation retained in the article

The five constructs were selected post hoc and some screenshots had prior packet exposure. Independence is author-reported; the supplied CSVs establish identities and arithmetic but cannot prove coding conduct. Small positive samples have wide descriptive uncertainty ranges. The 84.2% census applies to the assessed package-or-explicit-link relationship, including tutorials, requests and recommendations. It does not validate a narrower product-offer-only definition. Sampled negatives do not establish perfect recall.

Other substantive rules remain exploratory lexical results. Collection history, actual capture dates, source completeness and OCR transcription accuracy are unknown limits. The analysis supports visible claims in a defined archive, without establishing truthful advertisements, completed services, actor/victim counts, market prevalence or financial flows. No further empirical task is required to draft the analysis within this scope; final author interpretation and ordinary manuscript preparation remain.
