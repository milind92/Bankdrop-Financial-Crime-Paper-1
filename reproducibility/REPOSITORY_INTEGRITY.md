# Repository Integrity

Run from the repository root:

```powershell
python -m unittest discover -s tests -v
python .\code\verify_repository.py
```

The GitHub Actions workflow runs the same checks on Ubuntu and Windows.

The verifier checks Python syntax without writing bytecode, JSON validity, required files, CSV schemas, manifest references, the deterministic four-phase boundary, absence of manuscript and excluded LLM paths, the journal-supplement role and claim register, overall and target-level human-ICR reconciliation, human-validation performance counts and public-output hashes, derived-analysis denominators and contingency tables, restricted filenames and fields, and local-path exposure.

A passing data-free audit confirms repository structure and internal consistency. It does not reproduce the controlled corpus, verify source-level evidence, turn the 980 screened combined note records into unique posts or evidence units, or replace human or institutional review.
