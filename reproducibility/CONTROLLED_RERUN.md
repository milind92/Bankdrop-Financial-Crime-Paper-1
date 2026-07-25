# Controlled Deterministic Rerun

## Requirements

- Authorised access to the restricted Bank Drop vault.
- Python 3.11.
- Windows OCR dependencies for Phase 2.
- A controlled output directory outside the public repository.

## Guarded Orchestrator

```powershell
$env:BANK_DROP_VAULT = "D:\approved\bank-drop-vault"
$env:BANK_DROP_OUTPUTS_DIR = "D:\approved\bank-drop-controlled-outputs"
python .\code\run_reproducible_pipeline.py
```

The orchestrator executes:

1. Phase 1 Markdown baseline extraction.
2. Phase 2 local OCR.
3. Phase 3 deterministic typology coding.
4. Phase 4 deterministic financial-crime analysis.

It refuses a missing vault, an output directory inside the vault, or complete controlled outputs inside the public checkout.

## Deterministic Derived Aggregates

After the controlled Phase 3 output is available:

```powershell
python .\code\derived_analysis\build_derived_analysis.py `
  --source-dir (Join-Path $env:BANK_DROP_OUTPUTS_DIR "phase3_typology_coding") `
  --output-dir (Join-Path $env:BANK_DROP_OUTPUTS_DIR "derived_analysis")
```

This step writes only grouped descriptive outputs. The exact-text-unique population remains a sensitivity population until the final eligibility and evidence-unit audit is locked.

## Public Aggregate Export

```powershell
python .\code\export_public_release.py `
  --source-output-root $env:BANK_DROP_OUTPUTS_DIR `
  --repository-root . `
  --dry-run
python .\code\export_public_release.py `
  --source-output-root $env:BANK_DROP_OUTPUTS_DIR `
  --repository-root .
```

Review the dry-run inventory before copying. The exporter never walks the controlled tree and copies only named aggregate files.

## Excluded Pathways

No Phase 3b, Phase 4b, Phase 5, manuscript builder, submission packager, Ollama dependency, model download, or LLM-assisted empirical pathway is included.

### Portable OCR cache replay

Phase 2 generation uses Windows Media OCR. On another operating system, a controlled complete cache produced with the recorded OCR configuration may be replayed by setting `BANK_DROP_OCR_CACHE_ONLY=1`. Replay fails if any eligible image lacks a matching image SHA-256 and OCR-configuration SHA-256; it never silently substitutes a different OCR engine. The raw cache remains controlled and is not published.
