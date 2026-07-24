"""Build a Phase 3 overview from controlled aggregate outputs."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("BANK_DROP_WORKSPACE", REPOSITORY_ROOT))
OUTPUTS = Path(os.environ.get("BANK_DROP_OUTPUTS_DIR", WORKSPACE / "outputs"))
BASE = OUTPUTS / "phase3_typology_coding"


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    typology = read_csv("typology_summary.csv")
    objectives = read_csv("criminal_objective_summary.csv")
    aml = read_csv("aml_indicator_summary_by_source.csv")
    metadata = json.loads((BASE / "run_metadata.json").read_text(encoding="utf-8"))

    lines = [
        "# Phase 3 Analytic Overview",
        "",
        "## Scope",
        "",
        f"- Notes coded: {metadata['note_count']}",
        f"- Typology codes: {metadata['typology_code_count']}",
        f"- AML indicator candidates: {metadata['aml_indicator_count']}",
        f"- Evidence snippets: {metadata['evidence_snippet_rows']}",
        "",
        "## Top Typologies",
        "",
        "| Rank | Code | Label | Notes | Hits |",
        "|---:|---|---|---:|---:|",
    ]
    for index, row in enumerate(typology[:13], 1):
        lines.append(f"| {index} | `{row['code']}` | {row['label']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Criminal Objective Summary",
        "",
        "| Rank | Criminal objective | Notes | Hits |",
        "|---:|---|---:|---:|",
    ])
    for index, row in enumerate(objectives, 1):
        lines.append(f"| {index} | {row['criminal_objective']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Highest Source-Level AML Indicator Signals",
        "",
        "| Rank | Indicator | Source | Notes | Hits |",
        "|---:|---|---|---:|---:|",
    ])
    for index, row in enumerate(sorted(aml, key=lambda item: int(item["note_count"]), reverse=True)[:20], 1):
        lines.append(f"| {index} | {row['label']} | {row['source']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Use And Limits",
        "",
        "This is deterministic baseline coding over Markdown plus OCR text. It guides sampling, manual validation, and Phase 4 financial-crime interpretation; it is not final qualitative coding by itself.",
    ])
    output = BASE / "PHASE3_ANALYTIC_OVERVIEW.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()