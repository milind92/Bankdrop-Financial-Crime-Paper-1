# Reproducibility

**Current status:** The [fixed-screenshot analysis and focused author assessment](docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md) are complete for the defined 1,037-image frame. A fresh [portable controlled replay](code/image_archive/reproduce_controlled.py) reproduced all 12 original files; the [author scorer](code/image_archive/score_author_validation.py) reproduces the completed results with strengthened provenance checks. Follow the [current image protocol](docs/IMAGE_ARCHIVE_PROTOCOL_2026-10-02.md) for those two workflows. Commands below document the historical mixed-note computation; its article-use hold remains specific to that older pathway.

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
$vault = "D:\approved\bank-drop-vault"
$outputs = "D:\approved\bank-drop-controlled-outputs"
python .\code\run_reproducible_pipeline.py `
  --vault $vault `
  --output-root $outputs
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

The public checkout cannot reconstruct the controlled corpus or independently reproduce source-level counts. Aggregate human-validation and deterministic derived results can be checked for internal consistency, but the public repository does not include coder-level or note-level data. The historical screen used 980 combined notes; 463 exact-text representatives were a historical sensitivity population. Neither is the approved denominator for a revised evidence-only analysis.

No Phase 3b, Phase 4b, Phase 5, or LLM-assisted empirical pathway is included.

### Portable OCR cache replay

Phase 2 generation uses Windows Media OCR. On another operating system, a controlled complete cache produced with the recorded OCR configuration may be replayed by setting `BANK_DROP_OCR_CACHE_ONLY=1`. Replay fails if any eligible image lacks a matching image SHA-256 and OCR-configuration SHA-256; it never silently substitutes a different OCR engine. The raw cache remains controlled and is not published.
