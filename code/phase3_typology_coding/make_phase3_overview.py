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
DATA_QUALITY_CODES = {"market_access_limitation"}


def read_csv(name: str) -> list[dict[str, str]]:
    with (BASE / name).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    typology = read_csv("typology_summary.csv")
    substantive_typology = [
        row for row in typology if row["code"] not in DATA_QUALITY_CODES
    ]
    collection_quality = [
        row for row in typology if row["code"] in DATA_QUALITY_CODES
    ]
    objectives = read_csv("criminal_objective_summary.csv")
    aml = read_csv("aml_indicator_summary_by_source.csv")
    metadata = json.loads((BASE / "run_metadata.json").read_text(encoding="utf-8"))
    revised = metadata.get("analysis_mode") == "author_reviewed_artifact_bounded_source_text"

    lines = [
        "# Phase 3 Analytic Overview",
        "",
        ("**Revised source-evidence output — validation and journal-use hold.**" if revised else
         "**Historical exploratory output — journal-use hold.** The 980-note structural screen includes researcher and collection-status records. These rule counts are not approved source-evidence or article estimates."),
        "",
        "## Scope",
        "",
        f"- {'Approved evidence units' if revised else 'Notes'} coded: {metadata['note_count']}",
        f"- Substantive typology codes: {len(substantive_typology)}",
        f"- Collection-quality flags: {len(collection_quality)}",
        f"- AML indicator candidates: {metadata['aml_indicator_count']}",
        f"- Evidence snippets: {metadata['evidence_snippet_rows']}",
        "",
        "## Top Typologies",
        "",
        f"| Rank | Code | Label | {'Units' if revised else 'Notes'} | Hits |",
        "|---:|---|---|---:|---:|",
    ]
    for index, row in enumerate(substantive_typology, 1):
        lines.append(f"| {index} | `{row['code']}` | {row['label']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Collection-Quality Flags",
        "",
        f"| Code | Label | {'Units' if revised else 'Notes'} | Hits |",
        "|---|---|---:|---:|",
    ])
    for row in collection_quality:
        lines.append(
            f"| `{row['code']}` | {row['label']} | {row['note_count']} | {row['hit_count']} |"
        )

    lines.extend([
        "",
        "## Criminal Objective Summary",
        "",
        f"| Rank | Criminal objective | {'Units' if revised else 'Notes'} | Hits |",
        "|---:|---|---:|---:|",
    ])
    for index, row in enumerate(objectives, 1):
        lines.append(f"| {index} | {row['criminal_objective']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Highest Source-Level AML Indicator Signals",
        "",
        f"| Rank | Indicator | Source | {'Units' if revised else 'Notes'} | Hits |",
        "|---:|---|---|---:|---:|",
    ])
    for index, row in enumerate(sorted(aml, key=lambda item: int(item["note_count"]), reverse=True)[:20], 1):
        lines.append(f"| {index} | {row['label']} | {row['source']} | {row['note_count']} | {row['hit_count']} |")

    lines.extend([
        "",
        "## Use And Limits",
        "",
        (
            "This is provisional, artefact-bounded coding over reviewed source-text spans. The historical human validation does not validate this revised frame. OCR quality, target-level validation, duplicate/source sensitivity, and contextual interpretation remain pending."
            if revised else
            "This is deterministic baseline coding over Markdown plus OCR text; it is not final qualitative coding by itself. Ausma Bernot and Milind Tiwari completed blinded human validation and adjudication for the historical sample. Interpretive claims must remain within its target-level performance, duplicate-sensitivity, source-dependence, and contextual-evidence boundaries."
        ),
    ])
    output = BASE / "PHASE3_ANALYTIC_OVERVIEW.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
