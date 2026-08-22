# Journal Integration Checklist

## Repository-Technical Gate

- [x] Repository role fixed as a journal-neutral reproducibility supplement.
- [x] Deterministic empirical scope limited to Phases 1-4.
- [x] Primary unit and denominator fixed as 980 screened combined note records.
- [x] Exact-text sensitivity population separately labelled as 463 representatives.
- [x] Human validation and all 51 adjudications completed and reported in aggregate.
- [x] Target-level classification performance and uncertainty published.
- [x] Claim-to-evidence register included.
- [x] Raw and record-level controlled material excluded.
- [x] Data-free tests and privacy/integrity verifier available on Windows and Ubuntu.
- [x] Ethics identifier and repository-only AI-assistance boundary recorded.

## Target-Journal Gate

- [ ] Select the journal and article type.
- [ ] Check repository, data, code, ethics, AI-assistance, supplementary-file, and archival requirements against the current author instructions.
- [ ] Confirm the review model. For double-anonymous review, do not cite this identity-bearing public repository unless the editor permits it; prepare a separate anonymised snapshot or defer the repository citation until acceptance.
- [ ] Check file, table, figure, word-count, reporting-guideline, and reference-style limits.

## Author And Declaration Gate

- [ ] Replace provisional author metadata with full names, order, affiliations, ORCIDs, and corresponding-author details.
- [ ] Approve the CRediT contribution statement.
- [ ] Confirm funding, acknowledgements, and competing interests.
- [ ] Confirm copyright holders, institutional ownership interests, and the licence decision.
- [ ] Confirm whether a DOI or archival deposit is required.

## Manuscript Integration Gate

- [ ] Map every result claim to `claim_to_evidence_register.csv`.
- [ ] Use 980 screened combined note records as the descriptive denominator and 463 exact-text representatives as sensitivity only.
- [ ] Disclose 65 unassessable zero-word records and the limitations of non-matches.
- [ ] Report target-level validation limitations; do not rely on aggregate agreement alone.
- [ ] Keep AML candidates exploratory unless a separately documented independent review supports narrower wording.
- [ ] Do not make external prevalence, rarity, absence, transaction, causal, offender, victim, or operational-detection claims.
- [ ] Reconcile every number and version with the tagged repository release.

## Final Journal-Linked Release Gate

- [ ] Complete journal-specific metadata and declarations.
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python .\code\verify_repository.py`.
- [ ] Review the full Git diff and reachable history for controlled material.
- [ ] Record final author/institutional approval, tag the journal-linked version, push it, and confirm both GitHub Actions jobs pass.

The repository-technical gate may be complete while target-journal and author-declaration items remain pending. Do not describe the full article submission as ready until every applicable unchecked item is resolved.
