# Reproducibility

## Data-Free Audit

A checkout can be audited without the controlled corpus and without third-party packages:

```powershell
python -m unittest discover -s tests -v
python .\code\verify_repository.py
```

The audit compiles Python files, validates JSON, checks required files and CSV schemas, verifies manifest references, reconciles overall and target-level human-ICR totals, checks derived-analysis denominators and contingency tables, scans for restricted filenames and fields, and checks for local-path exposure.

## Controlled Deterministic Rerun

A complete rerun requires authorised access to the restricted source vault and a Windows OCR environment:

```powershell
$env:BANK_DROP_VAULT = "D:\approved\bank-drop-vault"
$env:BANK_DROP_OUTPUTS_DIR = "D:\approved\bank-drop-controlled-outputs"
python .\code\run_reproducible_pipeline.py
```

The orchestrator executes deterministic Phases 1–4 only. Complete outputs must remain outside the public repository. After Phase 3 completes, authorised researchers can regenerate the publication-safe deterministic derived tables in the controlled output tree:

```powershell
python .\code\derived_analysis\build_derived_analysis.py `
  --source-dir (Join-Path $env:BANK_DROP_OUTPUTS_DIR "phase3_typology_coding") `
  --output-dir (Join-Path $env:BANK_DROP_OUTPUTS_DIR "derived_analysis")
```

Use the fail-closed exporter to validate and copy only allowlisted aggregate files:

```powershell
python .\code\export_public_release.py `
  --source-output-root $env:BANK_DROP_OUTPUTS_DIR `
  --repository-root . `
  --dry-run
python .\code\export_public_release.py `
  --source-output-root $env:BANK_DROP_OUTPUTS_DIR `
  --repository-root .
```

## Boundaries

The public checkout cannot reconstruct the controlled corpus or independently reproduce source-level counts. Aggregate human-validation and deterministic derived results can be checked for internal consistency, but the public repository does not include coder-level or note-level data. The 479-record exact-text-unique sensitivity population is not a verified final eligible population.

No Phase 3b, Phase 4b, Phase 5, or LLM-assisted empirical pathway is included.
