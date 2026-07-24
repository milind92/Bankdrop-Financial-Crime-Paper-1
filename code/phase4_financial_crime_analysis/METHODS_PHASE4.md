# Phase 4 Financial-Crime Analysis: Methods Note

## Purpose

Phase 4 translates deterministic Phase 3 outputs into a structured financial-crime analysis package focused on typologies, criminal objectives, AML indicator candidates, source profiles, and publication-oriented limitations. It does not call an LLM or external API.

## Inputs

The phase reads controlled Phase 3 summary tables and controlled evidence snippets. Evidence snippets are used only inside the controlled environment and are not included in this repository.

## Outputs

- `FINANCIAL_CRIME_ANALYSIS_REPORT.md`
- `financial_crime_findings.csv`
- `aml_red_flags_summary.csv`
- `source_profile_summary.csv`
- `phase4_recommendations.csv`
- run metadata and checkpoint summary

## Reproduction Command

From the repository root after setting the controlled paths:

```powershell
python .\code\phase4_financial_crime_analysis\run_phase4_analysis.py
```

## Interpretation Limits

Phase 4 is a structured synthesis of deterministic coding. Its findings should be reported as corpus signals and AML indicator candidates, not confirmed transactions or external prevalence estimates. Publication claims require human validation against controlled evidence.