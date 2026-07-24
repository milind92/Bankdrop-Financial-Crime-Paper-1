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

## Public Aggregate Export

```powershell
python .\code\export_public_release.py --source $env:BANK_DROP_OUTPUTS_DIR --repository . --dry-run
python .\code\export_public_release.py --source $env:BANK_DROP_OUTPUTS_DIR --repository .
```

Review the dry-run inventory before copying. The exporter never walks the controlled tree and copies only named aggregate files.

## Excluded Pathways

No Phase 3b, Phase 4b, Phase 5, manuscript builder, submission packager, Ollama dependency, model download, or LLM-assisted empirical pathway is included.
