#!/usr/bin/env python3
"""Build a publication-safe per-target human ICR table from aggregate inputs.

The frozen-results JSON is produced in controlled storage after the independent
coder workbooks are locked. The adjudication input must already be aggregated
by target code. No record identifiers, decisions, rationales, or evidence are
written to the public outputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Callable, Mapping, Sequence


SCRIPT_VERSION = "1.0.0"
BOOTSTRAP_REPLICATES = 1000
CATEGORIES = (
    "Present",
    "Absent",
    "Ambiguous",
    "Insufficient evidence",
    "Out of scope record",
)
BINARY_CATEGORIES = frozenset({"Present", "Absent"})
OUTPUT_FIELDS = (
    "code",
    "target_group",
    "paired_units",
    "exact_agreements",
    "disagreements",
    "agreement_percent",
    "agreement_ci95_low_percent",
    "agreement_ci95_high_percent",
    "cohen_kappa",
    "cohen_kappa_bootstrap_ci95_low",
    "cohen_kappa_bootstrap_ci95_high",
    "krippendorff_alpha_nominal",
    "binary_subset_units",
    "binary_subset_exact_agreements",
    "binary_subset_agreement_percent",
    "binary_subset_cohen_kappa",
    "binary_subset_gwet_ac1",
    "binary_subset_gwet_ac1_bootstrap_ci95_low",
    "binary_subset_gwet_ac1_bootstrap_ci95_high",
    "adjudicated_disagreements",
    "final_present",
    "final_absent",
    "final_ambiguous",
    "final_insufficient_evidence",
    "final_out_of_scope_record",
)


class PublicICRError(ValueError):
    """Raised when controlled aggregate inputs do not reconcile."""


def as_int(value: object, label: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise PublicICRError(f"{label} is not an integer") from exc
    if result < 0:
        raise PublicICRError(f"{label} is negative")
    return result


def as_float(value: object, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PublicICRError(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise PublicICRError(f"{label} is not finite")
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdefABCDEF" for character in value)


def wilson_interval(successes: int, total: int) -> tuple[float | None, float | None]:
    if total == 0:
        return None, None
    z = 1.959963984540054
    observed = successes / total
    denominator = 1 + z * z / total
    centre = (observed + z * z / (2 * total)) / denominator
    half = (
        z
        * math.sqrt(
            observed * (1 - observed) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return max(0.0, centre - half), min(1.0, centre + half)


def cohen_kappa(pairs: Sequence[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    observed = sum(left == right for left, right in pairs) / total
    left_counts = {category: 0 for category in CATEGORIES}
    right_counts = {category: 0 for category in CATEGORIES}
    for left, right in pairs:
        left_counts[left] = left_counts.get(left, 0) + 1
        right_counts[right] = right_counts.get(right, 0) + 1
    expected = sum(
        (left_counts[category] / total) * (right_counts[category] / total)
        for category in set(left_counts) | set(right_counts)
    )
    if math.isclose(expected, 1.0):
        return None
    return (observed - expected) / (1 - expected)


def gwet_ac1_binary(pairs: Sequence[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    if any(left not in BINARY_CATEGORIES or right not in BINARY_CATEGORIES for left, right in pairs):
        raise PublicICRError("Gwet AC1 input contains a non-binary decision")
    total = len(pairs)
    observed = sum(left == right for left, right in pairs) / total
    present_ratings = sum(
        (left == "Present") + (right == "Present") for left, right in pairs
    )
    present_share = present_ratings / (2 * total)
    chance = 2 * present_share * (1 - present_share)
    if math.isclose(chance, 1.0):
        return None
    return (observed - chance) / (1 - chance)


def percentile(values: Sequence[float], probability: float) -> float:
    if not values:
        raise PublicICRError("Cannot calculate a percentile from no values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def bootstrap_interval(
    pairs: Sequence[tuple[str, str]],
    metric: Callable[[Sequence[tuple[str, str]]], float | None],
    seed_label: str,
) -> tuple[float | None, float | None]:
    if not pairs:
        return None, None
    seed = int.from_bytes(
        hashlib.sha256(seed_label.encode("utf-8")).digest()[:8], "big"
    )
    generator = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [pairs[generator.randrange(len(pairs))] for _ in pairs]
        value = metric(sample)
        if value is not None and math.isfinite(value):
            estimates.append(value)
    if not estimates:
        return None, None
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def expand_confusion(
    confusion: Mapping[str, Mapping[str, object]]
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for left in CATEGORIES:
        columns = confusion.get(left, {})
        for right in CATEGORIES:
            count = as_int(columns.get(right, 0), f"confusion[{left}][{right}]")
            pairs.extend([(left, right)] * count)
    return pairs


def read_adjudication(path: Path) -> dict[str, dict[str, int]]:
    required = (
        "code",
        "adjudicated_disagreements",
        "final_present",
        "final_absent",
        "final_ambiguous",
        "final_insufficient_evidence",
        "final_out_of_scope_record",
    )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = tuple(reader.fieldnames or ())
        missing = [field for field in required if field not in headers]
        if missing:
            raise PublicICRError(
                f"Adjudication aggregate is missing: {', '.join(missing)}"
            )
        rows: dict[str, dict[str, int]] = {}
        for raw in reader:
            code = (raw.get("code") or "").strip()
            if not code or code in rows:
                raise PublicICRError("Adjudication target codes must be nonblank and unique")
            rows[code] = {
                field: as_int(raw.get(field), f"{code}.{field}")
                for field in required
                if field != "code"
            }
    return rows


def rounded(value: float | None) -> float | str:
    return "" if value is None else round(value, 6)


def build_rows(
    payload: Mapping[str, object],
    adjudication: Mapping[str, Mapping[str, int]],
) -> list[dict[str, object]]:
    per_code = payload.get("per_code")
    if not isinstance(per_code, list) or not per_code:
        raise PublicICRError("Frozen results contain no per_code array")
    rows: list[dict[str, object]] = []
    for source in per_code:
        if not isinstance(source, dict):
            raise PublicICRError("per_code contains a non-object entry")
        code = str(source.get("code") or "").strip()
        if code not in adjudication:
            raise PublicICRError(f"Adjudication aggregate has no row for {code}")
        confusion = source.get("confusion_matrix")
        if not isinstance(confusion, dict):
            raise PublicICRError(f"Frozen results have no confusion matrix for {code}")
        pairs = expand_confusion(confusion)
        n = as_int(source.get("n"), f"{code}.n")
        agreements = as_int(source.get("exact_agreements"), f"{code}.exact_agreements")
        disagreements = as_int(source.get("disagreements"), f"{code}.disagreements")
        if len(pairs) != n or agreements + disagreements != n:
            raise PublicICRError(f"Frozen counts do not reconcile for {code}")
        observed_agreements = sum(left == right for left, right in pairs)
        if observed_agreements != agreements:
            raise PublicICRError(f"Confusion matrix agreements do not reconcile for {code}")
        binary_pairs = [
            pair
            for pair in pairs
            if pair[0] in BINARY_CATEGORIES and pair[1] in BINARY_CATEGORIES
        ]
        binary_agreements = sum(left == right for left, right in binary_pairs)
        if len(binary_pairs) != as_int(source.get("binary_n"), f"{code}.binary_n"):
            raise PublicICRError(f"Binary subset size does not reconcile for {code}")
        if binary_agreements != as_int(
            source.get("binary_exact_agreements"),
            f"{code}.binary_exact_agreements",
        ):
            raise PublicICRError(f"Binary agreements do not reconcile for {code}")

        agreement_low, agreement_high = wilson_interval(agreements, n)
        kappa_low, kappa_high = bootstrap_interval(
            pairs, cohen_kappa, f"bankdrop-paper1-human-icr|{code}|kappa"
        )
        ac1 = gwet_ac1_binary(binary_pairs)
        ac1_low, ac1_high = bootstrap_interval(
            binary_pairs,
            gwet_ac1_binary,
            f"bankdrop-paper1-human-icr|{code}|binary-ac1",
        )
        final = adjudication[code]
        if final["adjudicated_disagreements"] != disagreements:
            raise PublicICRError(
                f"Adjudicated disagreement count does not reconcile for {code}"
            )
        if sum(
            final[field]
            for field in (
                "final_present",
                "final_absent",
                "final_ambiguous",
                "final_insufficient_evidence",
                "final_out_of_scope_record",
            )
        ) != disagreements:
            raise PublicICRError(f"Final adjudication decisions do not sum for {code}")

        rows.append(
            {
                "code": code,
                "target_group": source.get("target_group"),
                "paired_units": n,
                "exact_agreements": agreements,
                "disagreements": disagreements,
                "agreement_percent": round(100 * agreements / n, 3),
                "agreement_ci95_low_percent": round(100 * agreement_low, 3),
                "agreement_ci95_high_percent": round(100 * agreement_high, 3),
                "cohen_kappa": rounded(
                    as_float(source.get("cohen_kappa"), f"{code}.cohen_kappa")
                ),
                "cohen_kappa_bootstrap_ci95_low": rounded(kappa_low),
                "cohen_kappa_bootstrap_ci95_high": rounded(kappa_high),
                "krippendorff_alpha_nominal": rounded(
                    as_float(
                        source.get("krippendorff_alpha_nominal"),
                        f"{code}.krippendorff_alpha_nominal",
                    )
                ),
                "binary_subset_units": len(binary_pairs),
                "binary_subset_exact_agreements": binary_agreements,
                "binary_subset_agreement_percent": round(
                    100 * binary_agreements / len(binary_pairs), 3
                )
                if binary_pairs
                else "",
                "binary_subset_cohen_kappa": rounded(
                    as_float(
                        source.get("binary_cohen_kappa"),
                        f"{code}.binary_cohen_kappa",
                    )
                ),
                "binary_subset_gwet_ac1": rounded(ac1),
                "binary_subset_gwet_ac1_bootstrap_ci95_low": rounded(ac1_low),
                "binary_subset_gwet_ac1_bootstrap_ci95_high": rounded(ac1_high),
                **final,
            }
        )
    if set(adjudication) != {str(row["code"]) for row in rows}:
        raise PublicICRError("Adjudication aggregate contains unknown target codes")
    return sorted(rows, key=lambda row: str(row["code"]))


def write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def interval(low: object, high: object) -> str:
    return f"{float(low):.3f}–{float(high):.3f}"


def render_markdown(
    payload: Mapping[str, object], rows: Sequence[Mapping[str, object]]
) -> str:
    summary = payload.get("unreconciled_human_icr")
    if not isinstance(summary, dict):
        raise PublicICRError("Frozen results contain no overall ICR summary")
    full = summary.get("five_category_metrics")
    binary = summary.get("present_absent_subset")
    if not isinstance(full, dict) or not isinstance(binary, dict):
        raise PublicICRError("Frozen results contain incomplete overall metrics")

    table_rows = []
    for row in rows:
        table_rows.append(
            "| {code} | {n} | {agreement:.1f}% ({agreement_ci}) | "
            "{kappa:.3f} ({kappa_ci}) | {ac1:.3f} ({ac1_ci}) | {adjudicated} | "
            "{present}/{absent}/{ambiguous}/{insufficient}/{out_scope} |".format(
                code=row["code"],
                n=int(row["paired_units"]),
                agreement=float(row["agreement_percent"]),
                agreement_ci=interval(
                    row["agreement_ci95_low_percent"],
                    row["agreement_ci95_high_percent"],
                ),
                kappa=float(row["cohen_kappa"]),
                kappa_ci=interval(
                    row["cohen_kappa_bootstrap_ci95_low"],
                    row["cohen_kappa_bootstrap_ci95_high"],
                ),
                ac1=float(row["binary_subset_gwet_ac1"]),
                ac1_ci=interval(
                    row["binary_subset_gwet_ac1_bootstrap_ci95_low"],
                    row["binary_subset_gwet_ac1_bootstrap_ci95_high"],
                ),
                adjudicated=int(row["adjudicated_disagreements"]),
                present=int(row["final_present"]),
                absent=int(row["final_absent"]),
                ambiguous=int(row["final_ambiguous"]),
                insufficient=int(row["final_insufficient_evidence"]),
                out_scope=int(row["final_out_of_scope_record"]),
            )
        )

    return (
        "# Human ICR Results by Target\n\n"
        "- Independent human coders: Ausma and Milind\n"
        "- Coordinator: none\n"
        "Independent coding was frozen before disagreement review.\n\n"
        "## Overall frozen result\n\n"
        f"- Paired case-target units: {int(full['n']):,}\n"
        f"- Exact agreement: {float(full['agreement_percent']):.1f}%\n"
        f"- Cohen's kappa: {float(full['cohen_kappa']):.3f}\n"
        f"- Nominal Krippendorff's alpha: "
        f"{float(full['krippendorff_alpha_nominal']):.3f}\n"
        f"- Present/Absent subset: {int(binary['n']):,} units; "
        f"{float(binary['agreement_percent']):.1f}% agreement; "
        f"kappa {float(binary['cohen_kappa']):.3f}\n"
        "- All 59 frozen disagreements were adjudicated jointly after the "
        "reliability calculation; consensus decisions did not replace the "
        "independent coder responses.\n\n"
        "## Publication-safe target-level results\n\n"
        "| Target code | Paired units | Agreement (Wilson 95% CI) | "
        "Kappa (bootstrap 95% CI) | Binary Gwet AC1 (bootstrap 95% CI) | "
        "Adjudicated | Final P/A/Am/IE/OOS |\n"
        "|---|---:|---:|---:|---:|---:|---:|\n"
        + "\n".join(table_rows)
        + "\n\n"
        "P = Present; A = Absent; Am = Ambiguous; IE = Insufficient evidence; "
        "OOS = Out of scope record. Gwet's AC1 is calculated only for pairs in "
        "which both coders selected Present or Absent. Non-binary decisions are "
        "excluded from that sensitivity metric and are not recoded.\n\n"
        "## Interval and interpretation boundary\n\n"
        f"Agreement intervals are Wilson score intervals. Kappa and binary "
        f"Gwet AC1 intervals are deterministic percentile intervals from "
        f"{BOOTSTRAP_REPLICATES:,} paired-unit bootstrap replicates within each "
        "target. They describe uncertainty within the controlled validation "
        "sample; they do not estimate corpus or market prevalence. No p-values "
        "or multiple-comparison claims are made. These are human intercoder "
        "reliability results, not sensitivity, specificity, or predictive-value "
        "estimates against an external ground truth.\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen-results", required=True, type=Path)
    parser.add_argument("--adjudication-by-target", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    parser.add_argument("--output-metadata", required=True, type=Path)
    parser.add_argument("--adjudication-workbook-sha256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.frozen_results.read_text(encoding="utf-8-sig"))
        adjudication = read_adjudication(args.adjudication_by_target)
        rows = build_rows(payload, adjudication)
        write_csv(args.output_csv, rows)
        args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.output_markdown.write_text(
            render_markdown(payload, rows), encoding="utf-8"
        )
        workbook_hash = (args.adjudication_workbook_sha256 or "").strip().lower()
        if workbook_hash and not valid_sha256(workbook_hash):
            raise PublicICRError("Adjudication workbook SHA-256 is invalid")
        frozen_sources = payload.get("sources", [])
        frozen_workbook_hashes = []
        if isinstance(frozen_sources, list):
            for source in frozen_sources:
                if not isinstance(source, dict):
                    continue
                coder = str(source.get("coder") or "").strip()
                digest = str(source.get("sha256") or "").strip().lower()
                if coder and valid_sha256(digest):
                    frozen_workbook_hashes.append(
                        {"coder": coder, "sha256": digest}
                    )
        metadata = {
            "script_version": SCRIPT_VERSION,
            "controlled_input_sha256": {
                "frozen_icr_results_json": sha256_file(args.frozen_results),
                "adjudication_by_target_aggregate_csv": sha256_file(
                    args.adjudication_by_target
                ),
                "completed_adjudication_workbook": workbook_hash,
            },
            "frozen_coder_workbook_sha256": frozen_workbook_hashes,
            "target_count": len(rows),
            "paired_units": sum(int(row["paired_units"]) for row in rows),
            "disagreements": sum(int(row["disagreements"]) for row in rows),
            "adjudicated_disagreements": sum(
                int(row["adjudicated_disagreements"]) for row in rows
            ),
            "interval_methods": {
                "agreement": "Wilson 95% score interval",
                "cohen_kappa": f"{BOOTSTRAP_REPLICATES} deterministic paired-unit percentile bootstrap replicates within target",
                "binary_gwet_ac1": f"{BOOTSTRAP_REPLICATES} deterministic paired-unit percentile bootstrap replicates within target",
            },
            "privacy_boundary": "File-level hashes and grouped target statistics only; no case identifiers, coder-level rows, rationales, evidence, or signatures.",
        }
        args.output_metadata.parent.mkdir(parents=True, exist_ok=True)
        args.output_metadata.write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
    except (json.JSONDecodeError, OSError, PublicICRError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(
        json.dumps(
            {
                "script_version": SCRIPT_VERSION,
                "targets": len(rows),
                "paired_units": sum(int(row["paired_units"]) for row in rows),
                "disagreements": sum(int(row["disagreements"]) for row in rows),
                "adjudicated_disagreements": sum(
                    int(row["adjudicated_disagreements"]) for row in rows
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
