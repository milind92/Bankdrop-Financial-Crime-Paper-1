# Environment And Dependencies

## Data-Free Audit

The public checkout requires CPython 3.11 and the standard library only:

```powershell
python -m unittest discover -s tests -v
python .\code\verify_repository.py
```

## Controlled Rerun

| Component | Requirement |
|---|---|
| Phase 1 | Python 3.11 standard library and authorised access to the Markdown vault. |
| Phase 2 | Windows, Python 3.11, the pinned WinRT OCR dependencies, and authorised screenshot access. |
| Phase 3 | Python 3.11 standard library and controlled Phase 1–2 outputs. |
| Phase 4 | Python 3.11 standard library and controlled Phase 3 outputs. |
| Derived-analysis builder | Python 3.11 standard library and controlled Phase 3 outputs. |
| Human-validation summariser | Python 3.11 standard library and two controlled completed coder files. |
| Public target-level ICR builder | Python 3.11 standard library, the controlled frozen aggregate ICR JSON, and an adjudication table already aggregated by target. |

The OCR dependency declaration is [requirements-windows-ocr.txt](../reproducibility/requirements-windows-ocr.txt).

## Portability And Safety

Scripts use environment variables instead of user-specific paths. Complete inputs and outputs must remain outside the public checkout. No Ollama service, model download, Phase 3b, Phase 4b, Phase 5, or LLM-assisted empirical dependency is present.
