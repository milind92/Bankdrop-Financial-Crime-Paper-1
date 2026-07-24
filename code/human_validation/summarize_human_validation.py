#!/usr/bin/env python3
"""Summarise blinded human validation without publishing record-level data.

The command accepts the controlled machine key and two independently completed
coder sheets.  An adjudication sheet is optional; without one, only records on
which the coders agree receive a final human decision.  Outputs contain grouped
and overall aggregates only.
"""

from __future__ import annotations

import argparse
import csv
import math
import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence


DECISION_ORDER = (
    "present",
    "absent",
    "ambiguous",
    "insufficient_evidence",
    "out_of_scope_record",
)
DECISIONS = frozenset(DECISION_ORDER)
BINARY_DECISIONS = frozenset({"present", "absent"})
MACHINE_PRESENT = frozenset({"1", "present", "true", "yes"})
MACHINE_ABSENT = frozenset({"0", "absent", "false", "no"})
Z_95 = 1.959963984540054

BOOTSTRAP_REPLICATES = 1000
MACHINE_REQUIRED = ("record_id", "target_type", "code", "model_present")
CODER_REQUIRED = ("record_id", "decision")
ADJUDICATION_REQUIRED = (
    "record_id",
    "coder_1_decision",
    "coder_2_decision",
    "adjudicated_decision",
)

OUTPUT_FIELDS = (
    "scope", "target_type", "code", "sample_records_n",
    "coder_pair_complete_n", "agreement_n", "agreement_rate",
    "agreement_ci95_low", "agreement_ci95_high", "kappa_evaluable_n",
    "cohen_kappa", "cohen_kappa_bootstrap_ci95_low",
    "cohen_kappa_bootstrap_ci95_high", "gwet_ac1",
    "gwet_ac1_bootstrap_ci95_low", "gwet_ac1_bootstrap_ci95_high",
    "coder_1_present_n", "coder_1_absent_n", "coder_1_ambiguous_n",
    "coder_1_insufficient_evidence_n", "coder_1_out_of_scope_record_n",
    "coder_2_present_n", "coder_2_absent_n", "coder_2_ambiguous_n",
    "coder_2_insufficient_evidence_n", "coder_2_out_of_scope_record_n",
    "unresolved_n", "final_present_n", "final_absent_n",
    "final_ambiguous_n", "final_insufficient_evidence_n",
    "final_out_of_scope_record_n", "excluded_from_confusion_n",
    "coder_1_present_coder_2_absent_n",
    "coder_1_absent_coder_2_present_n", "other_disagreement_n",
    "confusion_evaluable_n", "tp", "fp", "tn", "fn",
    "precision", "precision_ci95_low", "precision_ci95_high",
    "negative_predictive_value", "negative_predictive_value_ci95_low",
    "negative_predictive_value_ci95_high", "sensitivity",
    "sensitivity_ci95_low", "sensitivity_ci95_high", "specificity",
    "specificity_ci95_low", "specificity_ci95_high", "accuracy",
    "accuracy_ci95_low", "accuracy_ci95_high", "f1_score",
    "balanced_accuracy", "analysis_weight_supplied_n",
    "weighted_confusion_weight_sum", "weighted_confusion_effective_n",
    "weighted_tp", "weighted_fp", "weighted_tn", "weighted_fn",
    "weighted_precision", "weighted_precision_approx_ci95_low",
    "weighted_precision_approx_ci95_high",
    "weighted_negative_predictive_value",
    "weighted_negative_predictive_value_approx_ci95_low",
    "weighted_negative_predictive_value_approx_ci95_high",
    "weighted_sensitivity", "weighted_sensitivity_approx_ci95_low",
    "weighted_sensitivity_approx_ci95_high", "weighted_specificity",
    "weighted_specificity_approx_ci95_low",
    "weighted_specificity_approx_ci95_high", "weighted_accuracy",
    "weighted_accuracy_approx_ci95_low",
    "weighted_accuracy_approx_ci95_high", "weighted_f1_score",
    "weighted_balanced_accuracy",
)

SAMPLING_LIMITATION = (
    "Unweighted classification metrics describe this validation sample and cannot "
    "estimate corpus prevalence. Predictive values depend on the sampled class "
    "composition. When positive analysis_weight values are supplied, weighted "
    "point estimates require those weights to be valid for the sampling design; "
    "their approximate intervals use Kish effective sample sizes and do not account "
    "for clustering, finite-population corrections, or weight estimation."
)


class ValidationInputError(ValueError):
    """Raised when a controlled input fails integrity checks."""


@dataclass(frozen=True)
class ValidationRecord:
    target_type: str
    code: str
    model_present: bool
    coder_1: str
    coder_2: str
    final_decision: str
    analysis_weight: float | None


def read_csv_rows(path: Path, required: Sequence[str], label: str) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValidationInputError(f"{label} does not exist or is not a file: {path}")
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValidationInputError(f"{label} has no header row")
            headers = [header.strip() if header is not None else "" for header in reader.fieldnames]
            if not all(headers) or len(headers) != len(set(headers)):
                raise ValidationInputError(f"{label} has blank or duplicate column names")
            missing = [column for column in required if column not in headers]
            if missing:
                raise ValidationInputError(
                    f"{label} is missing required column(s): {', '.join(missing)}"
                )
            rows: list[dict[str, str]] = []
            for line_number, raw in enumerate(reader, 2):
                if None in raw:
                    raise ValidationInputError(
                        f"{label} row {line_number} has more fields than the header"
                    )
                row = {
                    str(key).strip(): (value or "").strip()
                    for key, value in raw.items()
                }
                rows.append(row)
    except UnicodeDecodeError as exc:
        raise ValidationInputError(f"{label} is not valid UTF-8 CSV") from exc
    if not rows:
        raise ValidationInputError(f"{label} contains no data rows")
    return rows


def index_unique(rows: Iterable[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        record_id = row.get("record_id", "").strip()
        if not record_id:
            raise ValidationInputError(f"{label} row {row_number} has a blank record_id")
        if record_id in indexed:
            raise ValidationInputError(f"{label} has duplicate record_id: {record_id}")
        indexed[record_id] = row
    return indexed


def normalize_decision(value: str, label: str, record_id: str, allow_incomplete: bool) -> str:
    decision = value.strip().lower()
    if not decision:
        if allow_incomplete:
            return ""
        raise ValidationInputError(f"{label} has a blank decision for record_id {record_id}")
    if decision not in DECISIONS:
        allowed = ", ".join(sorted(DECISIONS))
        raise ValidationInputError(
            f"{label} has invalid decision {value!r} for record_id {record_id}; "
            f"allowed values are {allowed}"
        )
    return decision


def normalize_model_present(value: str, record_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized in MACHINE_PRESENT:
        return True
    if normalized in MACHINE_ABSENT:
        return False
    raise ValidationInputError(
        f"machine key has invalid model_present {value!r} for record_id {record_id}; "
        "use 1/0 or present/absent"
    )


def normalize_analysis_weight(row: Mapping[str, str], record_id: str) -> float | None:
    if "analysis_weight" not in row:
        return None
    value = row["analysis_weight"].strip()
    if not value:
        raise ValidationInputError(
            f"machine key has a blank analysis_weight for record_id {record_id}"
        )
    try:
        weight = float(value)
    except ValueError as exc:
        raise ValidationInputError(
            f"machine key has non-numeric analysis_weight {value!r} "
            f"for record_id {record_id}"
        ) from exc
    if not math.isfinite(weight) or weight <= 0:
        raise ValidationInputError(
            f"machine key analysis_weight must be finite and positive "
            f"for record_id {record_id}"
        )
    return weight


def require_same_record_ids(
    machine: Mapping[str, object], other: Mapping[str, object], label: str
) -> None:
    missing = sorted(set(machine) - set(other))
    extra = sorted(set(other) - set(machine))
    if missing or extra:
        parts = []
        if missing:
            parts.append(f"missing {len(missing)} machine record(s)")
        if extra:
            parts.append(f"contains {len(extra)} unknown record(s)")
        raise ValidationInputError(f"{label} record_id set mismatch: {'; '.join(parts)}")


def validate_optional_identity_columns(
    row: Mapping[str, str], machine_row: Mapping[str, str], label: str, record_id: str
) -> None:
    for column in ("target_type", "code"):
        value = row.get(column, "").strip()
        if value and value != machine_row[column]:
            raise ValidationInputError(
                f"{label} {column} does not match the machine key for record_id {record_id}"
            )


def load_records(
    machine_key: Path,
    coder_1: Path,
    coder_2: Path,
    adjudication: Path | None,
    allow_incomplete: bool,
) -> list[ValidationRecord]:
    machine = index_unique(read_csv_rows(machine_key, MACHINE_REQUIRED, "machine key"), "machine key")
    first = index_unique(read_csv_rows(coder_1, CODER_REQUIRED, "coder 1 sheet"), "coder 1 sheet")
    second = index_unique(read_csv_rows(coder_2, CODER_REQUIRED, "coder 2 sheet"), "coder 2 sheet")
    final_rows = (
        index_unique(
            read_csv_rows(adjudication, ADJUDICATION_REQUIRED, "adjudication sheet"),
            "adjudication sheet",
        )
        if adjudication is not None
        else None
    )

    require_same_record_ids(machine, first, "coder 1 sheet")
    require_same_record_ids(machine, second, "coder 2 sheet")
    if final_rows is not None:
        require_same_record_ids(machine, final_rows, "adjudication sheet")

    records: list[ValidationRecord] = []
    for record_id, machine_row in machine.items():
        target_type = machine_row["target_type"].strip()
        code = machine_row["code"].strip()
        if not target_type or not code:
            raise ValidationInputError(
                f"machine key has blank target_type or code for record_id {record_id}"
            )
        validate_optional_identity_columns(first[record_id], machine_row, "coder 1 sheet", record_id)
        validate_optional_identity_columns(second[record_id], machine_row, "coder 2 sheet", record_id)
        decision_1 = normalize_decision(
            first[record_id]["decision"], "coder 1 sheet", record_id, allow_incomplete
        )
        decision_2 = normalize_decision(
            second[record_id]["decision"], "coder 2 sheet", record_id, allow_incomplete
        )

        if final_rows is not None:
            adjudication_row = final_rows[record_id]
            validate_optional_identity_columns(
                adjudication_row, machine_row, "adjudication sheet", record_id
            )
            for column, expected in (
                ("coder_1_decision", decision_1),
                ("coder_2_decision", decision_2),
            ):
                normalized = normalize_decision(
                    adjudication_row[column], "adjudication sheet", record_id, allow_incomplete
                )
                if normalized and expected and normalized != expected:
                    raise ValidationInputError(
                        f"adjudication sheet {column} does not match its coder sheet "
                        f"for record_id {record_id}"
                    )
            final_decision = normalize_decision(
                adjudication_row["adjudicated_decision"],
                "adjudication sheet",
                record_id,
                allow_incomplete,
            )
        else:
            final_decision = decision_1 if decision_1 and decision_1 == decision_2 else ""

        records.append(
            ValidationRecord(
                target_type=target_type,
                code=code,
                model_present=normalize_model_present(machine_row["model_present"], record_id),
                coder_1=decision_1,
                coder_2=decision_2,
                final_decision=final_decision,
                analysis_weight=normalize_analysis_weight(machine_row, record_id),
            )
        )
    return records


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def wilson_interval(
    successes: float, total: float
) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    proportion = successes / total
    z2 = Z_95 * Z_95
    denominator = 1.0 + z2 / total
    centre = (proportion + z2 / (2.0 * total)) / denominator
    margin = (
        Z_95
        * math.sqrt((proportion * (1.0 - proportion) + z2 / (4.0 * total)) / total)
        / denominator
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def cohens_kappa(binary_pairs: Sequence[tuple[str, str]]) -> float | None:
    if not binary_pairs:
        return None
    observed = sum(left == right for left, right in binary_pairs) / len(binary_pairs)
    first_present = sum(left == "present" for left, _ in binary_pairs) / len(binary_pairs)
    second_present = sum(right == "present" for _, right in binary_pairs) / len(binary_pairs)
    expected = (
        first_present * second_present
        + (1.0 - first_present) * (1.0 - second_present)
    )
    if math.isclose(expected, 1.0):
        return None
    return (observed - expected) / (1.0 - expected)


def gwet_ac1(binary_pairs: Sequence[tuple[str, str]]) -> float | None:
    """Return Gwet's AC1 for two raters and the binary decision subset."""
    if not binary_pairs:
        return None
    observed = sum(left == right for left, right in binary_pairs) / len(binary_pairs)
    present_ratings = sum(
        decision == "present" for pair in binary_pairs for decision in pair
    )
    present_prevalence = present_ratings / (2.0 * len(binary_pairs))
    chance_agreement = 2.0 * present_prevalence * (1.0 - present_prevalence)
    return (observed - chance_agreement) / (1.0 - chance_agreement)


def percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return ordered[lower_index]
    fraction = position - lower_index
    return ordered[lower_index] + fraction * (
        ordered[upper_index] - ordered[lower_index]
    )


def paired_bootstrap_interval(
    binary_pairs: Sequence[tuple[str, str]],
    statistic: Callable[[Sequence[tuple[str, str]]], float | None],
    seed_material: str,
) -> tuple[float | None, float | None]:
    """Return a deterministic paired-record percentile bootstrap interval."""
    if len(binary_pairs) < 2:
        return None, None
    seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample = [
            binary_pairs[rng.randrange(len(binary_pairs))]
            for _ in range(len(binary_pairs))
        ]
        estimate = statistic(sample)
        if estimate is not None and math.isfinite(estimate):
            estimates.append(estimate)
    if len(estimates) < max(100, BOOTSTRAP_REPLICATES // 10):
        return None, None
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def add_metric(
    result: dict[str, object], name: str, successes: float, total: float
) -> None:
    low, high = wilson_interval(successes, total)
    result[name] = safe_ratio(successes, total)
    result[f"{name}_ci95_low"] = low
    result[f"{name}_ci95_high"] = high


def kish_effective_n(weights: Sequence[float]) -> float | None:
    if not weights:
        return None
    squared_sum = sum(weight * weight for weight in weights)
    return (sum(weights) ** 2) / squared_sum if squared_sum else None


def add_weighted_metric(
    result: dict[str, object],
    name: str,
    success_weight: float,
    total_weight: float,
    denominator_weights: Sequence[float],
) -> None:
    estimate = safe_ratio(success_weight, total_weight)
    effective_n = kish_effective_n(denominator_weights)
    low: float | None = None
    high: float | None = None
    if estimate is not None and effective_n is not None:
        low, high = wilson_interval(estimate * effective_n, effective_n)
    result[name] = estimate
    result[f"{name}_approx_ci95_low"] = low
    result[f"{name}_approx_ci95_high"] = high


def summarise_group(
    records: Sequence[ValidationRecord], scope: str, target_type: str, code: str
) -> dict[str, object]:
    completed_pairs = [record for record in records if record.coder_1 and record.coder_2]
    agreement_n = sum(record.coder_1 == record.coder_2 for record in completed_pairs)
    binary_pair_records = [
        record
        for record in completed_pairs
        if record.coder_1 in BINARY_DECISIONS and record.coder_2 in BINARY_DECISIONS
    ]
    binary_pairs = [(record.coder_1, record.coder_2) for record in binary_pair_records]
    seed_prefix = f"{scope}|{target_type}|{code}|{len(binary_pairs)}"
    kappa_low, kappa_high = paired_bootstrap_interval(
        binary_pairs, cohens_kappa, f"{seed_prefix}|kappa"
    )
    ac1_low, ac1_high = paired_bootstrap_interval(
        binary_pairs, gwet_ac1, f"{seed_prefix}|ac1"
    )

    confusion_records = [
        record for record in records if record.final_decision in BINARY_DECISIONS
    ]
    tp = sum(
        record.model_present and record.final_decision == "present"
        for record in confusion_records
    )
    fp = sum(
        record.model_present and record.final_decision == "absent"
        for record in confusion_records
    )
    tn = sum(
        (not record.model_present) and record.final_decision == "absent"
        for record in confusion_records
    )
    fn = sum(
        (not record.model_present) and record.final_decision == "present"
        for record in confusion_records
    )

    first_present_second_absent = sum(
        record.coder_1 == "present" and record.coder_2 == "absent"
        for record in completed_pairs
    )
    first_absent_second_present = sum(
        record.coder_1 == "absent" and record.coder_2 == "present"
        for record in completed_pairs
    )
    disagreement_n = len(completed_pairs) - agreement_n

    result: dict[str, object] = {
        "scope": scope,
        "target_type": target_type,
        "code": code,
        "sample_records_n": len(records),
        "coder_pair_complete_n": len(completed_pairs),
        "agreement_n": agreement_n,
        "kappa_evaluable_n": len(binary_pairs),
        "cohen_kappa": cohens_kappa(binary_pairs),
        "cohen_kappa_bootstrap_ci95_low": kappa_low,
        "cohen_kappa_bootstrap_ci95_high": kappa_high,
        "gwet_ac1": gwet_ac1(binary_pairs),
        "gwet_ac1_bootstrap_ci95_low": ac1_low,
        "gwet_ac1_bootstrap_ci95_high": ac1_high,
        "unresolved_n": sum(not record.final_decision for record in records),
        "excluded_from_confusion_n": len(records) - len(confusion_records),
        "coder_1_present_coder_2_absent_n": first_present_second_absent,
        "coder_1_absent_coder_2_present_n": first_absent_second_present,
        "other_disagreement_n": (
            disagreement_n
            - first_present_second_absent
            - first_absent_second_present
        ),
        "confusion_evaluable_n": len(confusion_records),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "f1_score": safe_ratio(2.0 * tp, 2.0 * tp + fp + fn),
        "analysis_weight_supplied_n": sum(
            record.analysis_weight is not None for record in records
        ),
    }
    for decision in DECISION_ORDER:
        result[f"coder_1_{decision}_n"] = sum(
            record.coder_1 == decision for record in records
        )
        result[f"coder_2_{decision}_n"] = sum(
            record.coder_2 == decision for record in records
        )
        result[f"final_{decision}_n"] = sum(
            record.final_decision == decision for record in records
        )

    add_metric(result, "agreement_rate", agreement_n, len(completed_pairs))
    add_metric(result, "precision", tp, tp + fp)
    add_metric(result, "negative_predictive_value", tn, tn + fn)
    add_metric(result, "sensitivity", tp, tp + fn)
    add_metric(result, "specificity", tn, tn + fp)
    add_metric(result, "accuracy", tp + tn, len(confusion_records))
    sensitivity = result["sensitivity"]
    specificity = result["specificity"]
    result["balanced_accuracy"] = (
        (float(sensitivity) + float(specificity)) / 2.0
        if sensitivity is not None and specificity is not None
        else None
    )

    if result["analysis_weight_supplied_n"]:
        weighted_tp = sum(
            float(record.analysis_weight)
            for record in confusion_records
            if record.model_present and record.final_decision == "present"
        )
        weighted_fp = sum(
            float(record.analysis_weight)
            for record in confusion_records
            if record.model_present and record.final_decision == "absent"
        )
        weighted_tn = sum(
            float(record.analysis_weight)
            for record in confusion_records
            if (not record.model_present) and record.final_decision == "absent"
        )
        weighted_fn = sum(
            float(record.analysis_weight)
            for record in confusion_records
            if (not record.model_present) and record.final_decision == "present"
        )
        confusion_weights = [
            float(record.analysis_weight) for record in confusion_records
        ]
        predicted_present_weights = [
            float(record.analysis_weight)
            for record in confusion_records
            if record.model_present
        ]
        predicted_absent_weights = [
            float(record.analysis_weight)
            for record in confusion_records
            if not record.model_present
        ]
        human_present_weights = [
            float(record.analysis_weight)
            for record in confusion_records
            if record.final_decision == "present"
        ]
        human_absent_weights = [
            float(record.analysis_weight)
            for record in confusion_records
            if record.final_decision == "absent"
        ]
        result.update(
            weighted_confusion_weight_sum=sum(confusion_weights),
            weighted_confusion_effective_n=kish_effective_n(confusion_weights),
            weighted_tp=weighted_tp,
            weighted_fp=weighted_fp,
            weighted_tn=weighted_tn,
            weighted_fn=weighted_fn,
            weighted_f1_score=safe_ratio(
                2.0 * weighted_tp,
                2.0 * weighted_tp + weighted_fp + weighted_fn,
            ),
        )
        add_weighted_metric(
            result, "weighted_precision", weighted_tp,
            weighted_tp + weighted_fp, predicted_present_weights,
        )
        add_weighted_metric(
            result, "weighted_negative_predictive_value", weighted_tn,
            weighted_tn + weighted_fn, predicted_absent_weights,
        )
        add_weighted_metric(
            result, "weighted_sensitivity", weighted_tp,
            weighted_tp + weighted_fn, human_present_weights,
        )
        add_weighted_metric(
            result, "weighted_specificity", weighted_tn,
            weighted_tn + weighted_fp, human_absent_weights,
        )
        add_weighted_metric(
            result, "weighted_accuracy", weighted_tp + weighted_tn,
            sum(confusion_weights), confusion_weights,
        )
        weighted_sensitivity = result["weighted_sensitivity"]
        weighted_specificity = result["weighted_specificity"]
        result["weighted_balanced_accuracy"] = (
            (float(weighted_sensitivity) + float(weighted_specificity)) / 2.0
            if weighted_sensitivity is not None
            and weighted_specificity is not None
            else None
        )
    return result


def summarise(records: Sequence[ValidationRecord]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[ValidationRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.target_type, record.code)].append(record)
    rows = [summarise_group(records, "overall", "ALL", "ALL")]
    rows.extend(
        summarise_group(group_records, "target", target_type, code)
        for (target_type, code), group_records in sorted(grouped.items())
    )
    return rows


def format_csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return value


def write_aggregate_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: format_csv_value(row.get(field)) for field in OUTPUT_FIELDS})


def format_metric(value: object) -> str:
    return "NA" if value is None else f"{float(value):.3f}"


def format_interval(low: object, high: object) -> str:
    if low is None or high is None:
        return "NA"
    return f"{float(low):.3f} to {float(high):.3f}"


def render_markdown(rows: Sequence[Mapping[str, object]], adjudicated: bool) -> str:
    overall = rows[0]
    final_counts = "; ".join(
        f"{decision}={overall[f'final_{decision}_n']}"
        for decision in DECISION_ORDER
    )
    lines = [
        "# Human validation aggregate results",
        "",
        "## Interpretation boundary",
        "",
        SAMPLING_LIMITATION,
        "",
        (
            "Final classifications use the supplied adjudication decisions."
            if adjudicated
            else "No adjudication file was supplied. Final classification metrics use only records "
            "where both coders made the same decision; disagreements and incomplete records remain unresolved."
        ),
        (
            "Raw agreement includes all five completed decision categories. Cohen's "
            "kappa and Gwet's AC1 use only pairs for which both coders selected "
            "present or absent. Confusion metrics use only final present/absent "
            "decisions. Blank metrics mean the denominator was zero or the statistic "
            "was mathematically undefined."
        ),
        "",
        "## Overall",
        "",
        f"- Sample records: {overall['sample_records_n']}",
        f"- Complete coder pairs: {overall['coder_pair_complete_n']}",
        (
            f"- Exact agreement: {overall['agreement_n']}/"
            f"{overall['coder_pair_complete_n']} "
            f"({format_metric(overall['agreement_rate'])})"
        ),
        (
            f"- Cohen's kappa (binary pairs): {format_metric(overall['cohen_kappa'])}; "
            "paired-record bootstrap 95% interval "
            f"{format_interval(overall['cohen_kappa_bootstrap_ci95_low'], overall['cohen_kappa_bootstrap_ci95_high'])}"
        ),
        (
            f"- Gwet's AC1 (binary pairs): {format_metric(overall['gwet_ac1'])}; "
            "paired-record bootstrap 95% interval "
            f"{format_interval(overall['gwet_ac1_bootstrap_ci95_low'], overall['gwet_ac1_bootstrap_ci95_high'])}"
        ),
        f"- Final decision counts: {final_counts}",
        f"- Final binary classifications: {overall['confusion_evaluable_n']}",
        (
            f"- Excluded from the confusion matrix: "
            f"{overall['excluded_from_confusion_n']} "
            f"(including unresolved={overall['unresolved_n']})"
        ),
    ]
    if int(overall["analysis_weight_supplied_n"]):
        lines.extend(
            [
                (
                    "- Analysis weights supplied for "
                    f"{overall['analysis_weight_supplied_n']} records."
                ),
                (
                    "- Weighted accuracy: "
                    f"{format_metric(overall['weighted_accuracy'])}; approximate 95% interval "
                    f"{format_interval(overall['weighted_accuracy_approx_ci95_low'], overall['weighted_accuracy_approx_ci95_high'])}."
                ),
            ]
        )

    lines.extend(
        [
            "",
            "## Per-target aggregates",
            "",
            "| Target type | Code | n | Agreement | Kappa | AC1 | Excluded | TP | FP | TN | FN | Precision | NPV | Sensitivity | Specificity | Accuracy | Weighted accuracy |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows[1:]:
        display = dict(row)
        display.update(
            agreement=(
                f"{row['agreement_n']}/{row['coder_pair_complete_n']} "
                f"({format_metric(row['agreement_rate'])})"
            ),
            kappa=format_metric(row["cohen_kappa"]),
            ac1=format_metric(row["gwet_ac1"]),
            precision=format_metric(row["precision"]),
            npv=format_metric(row["negative_predictive_value"]),
            sensitivity=format_metric(row["sensitivity"]),
            specificity=format_metric(row["specificity"]),
            accuracy=format_metric(row["accuracy"]),
            weighted_accuracy=format_metric(row.get("weighted_accuracy")),
        )
        lines.append(
            "| {target_type} | {code} | {sample_records_n} | {agreement} | "
            "{kappa} | {ac1} | {excluded_from_confusion_n} | {tp} | {fp} | "
            "{tn} | {fn} | {precision} | {npv} | {sensitivity} | "
            "{specificity} | {accuracy} | {weighted_accuracy} |".format(**display)
        )

    lines.extend(
        [
            "",
            "## Interval methods and limits",
            "",
            (
                "The CSV reports Wilson 95% intervals for exact agreement and "
                "unweighted confusion-derived proportions. Kappa and AC1 intervals "
                f"are deterministic paired-record percentile bootstrap intervals "
                f"with {BOOTSTRAP_REPLICATES} resamples; they are blank when too few "
                "defined resamples exist. Weighted proportion intervals are labelled "
                "approximate and use Kish effective sample sizes. None of these "
                "intervals adjusts for source or duplicate clustering, a finite "
                "population, or estimated weights."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def ensure_safe_output_paths(inputs: Sequence[Path], output_csv: Path, output_markdown: Path) -> None:
    input_paths = {path.resolve() for path in inputs}
    csv_path = output_csv.resolve()
    markdown_path = output_markdown.resolve()
    if csv_path == markdown_path:
        raise ValidationInputError("CSV and Markdown outputs must be different files")
    if csv_path in input_paths or markdown_path in input_paths:
        raise ValidationInputError("An aggregate output path must not overwrite a controlled input")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute aggregate agreement and classification metrics for human validation."
    )
    parser.add_argument("--machine-key", required=True, type=Path)
    parser.add_argument("--coder-1", required=True, type=Path)
    parser.add_argument("--coder-2", required=True, type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--output-markdown", required=True, type=Path)
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow blank coder/adjudication decisions; incomplete records are excluded as documented.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inputs = [args.machine_key, args.coder_1, args.coder_2]
    if args.adjudication is not None:
        inputs.append(args.adjudication)
    ensure_safe_output_paths(inputs, args.output_csv, args.output_markdown)
    records = load_records(
        args.machine_key,
        args.coder_1,
        args.coder_2,
        args.adjudication,
        args.allow_incomplete,
    )
    rows = summarise(records)
    markdown = render_markdown(rows, adjudicated=args.adjudication is not None)
    write_aggregate_csv(args.output_csv, rows)
    args.output_markdown.parent.mkdir(parents=True, exist_ok=True)
    args.output_markdown.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationInputError as exc:
        raise SystemExit(f"validation input error: {exc}") from exc
