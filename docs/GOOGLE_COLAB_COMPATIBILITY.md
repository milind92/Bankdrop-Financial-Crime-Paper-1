# Google Colab Compatibility

## Verdict

Google Colab can run the public data-free audit and most standard-library analysis code, but it cannot perform the release's native Windows Media OCR. The recommended arrangement is hybrid: use the authorised Windows environment for source-level OCR and controlled production, and use GitHub Actions or Colab for public audit and aggregate inspection.

## Capability Matrix

| Task | Colab status | Boundary |
|---|---|---|
| Clone and inspect the public repository | Supported | No controlled evidence is required. |
| Run all public unit tests and the integrity verifier | Supported | Use the release-supported CPython 3.11 environment. |
| Inspect committed aggregate CSV, JSON, and Markdown outputs | Supported | These outputs cannot reconstruct the controlled corpus. |
| Run Phase 1 | Technically portable | Requires authorised access to the Markdown vault. |
| Run Phase 2 with Windows Media OCR | Not supported | Colab uses Linux and does not provide the pinned WinRT OCR environment. |
| Replay Phase 2 from a complete Windows-produced OCR cache | Technically supported | Requires the controlled vault and a complete provenance-matched cache; institutional, ethics, privacy, and cloud-processing approval must permit their use in Colab. |
| Run Phases 3 and 4 | Technically portable | Requires the controlled Phase 1-2 outputs. |
| Build derived aggregates | Technically portable | Requires the controlled Phase 3 output. |
| Recompute human-validation summaries | Technically portable | Requires the controlled coder and adjudication files, which must not be uploaded without authorisation. |
| Reproduce the complete source-level release from public GitHub alone | Not possible | Raw notes, screenshots, OCR cache, and record-level validation material are deliberately excluded. |

## Public Audit In Colab

Use a fresh runtime and pin the tagged release being audited:

```python
!git clone --branch v1.3.0 --depth 1 https://github.com/milind92/Bankdrop-Financial-Crime-Paper-1.git
%cd Bankdrop-Financial-Crime-Paper-1
!python --version
!python -m unittest discover -s tests -v
!python code/verify_repository.py
```

The supported audit environment is CPython 3.11 and has no third-party package requirements. If `python --version` reports another version, do not describe that run as exact environment replication; use a CPython 3.11 environment or the release's GitHub Actions result. A passing audit confirms repository structure and internal consistency; it does not reproduce the controlled evidence or independently verify source-level results.

## Controlled Cache Replay

On a non-Windows system, Phase 2 can only replay a complete cache created under the recorded Windows OCR configuration:

```python
import os
os.environ["BANK_DROP_OCR_CACHE_ONLY"] = "1"
```

The cache must contain a successful row for every eligible image with matching image and OCR-configuration SHA-256 values. The script fails closed if any match is missing. Cache replay is not new OCR and the raw cache remains controlled.

## Privacy And Method Lock

Do not upload the vault, screenshots, raw OCR, evidence packets, coder workbooks, or record-level adjudication to Colab unless the ethics protocol, institutional data governance, legal rights, and the responsible data custodian expressly permit processing in that cloud environment.

Substituting Tesseract, EasyOCR, a hosted OCR API, or another Linux-compatible engine would create a different empirical pipeline. Such a change requires a new version, documented environment and provenance, a complete downstream rerun, comparison with the locked release, and review of whether human validation must be repeated. It must not be described as exact reproduction of version 1.3.0.
