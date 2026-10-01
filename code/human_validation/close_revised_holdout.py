"""Lock independent revised-holdout judgments, adjudicate, then score.

Record-level inputs and outputs remain controlled. Machine predictions are
opened only by the final score command after the human reference lock exists.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


SAMPLE_SPEC = importlib.util.spec_from_file_location(
    "bank_drop_revised_sample", Path(__file__).with_name("prepare_revised_holdout.py")
)
if SAMPLE_SPEC is None or SAMPLE_SPEC.loader is None:
    raise RuntimeError("Cannot load revised holdout sampler")
sample = importlib.util.module_from_spec(SAMPLE_SPEC)
SAMPLE_SPEC.loader.exec_module(sample)


DECISIONS = {"present", "absent", "ambiguous", "insufficient_evidence", "out_of_scope_record"}
NONBINARY = {"ambiguous", "insufficient_evidence"}
CODER_FIELDS = ["case_id", "target_type", "code", "decision", "rationale", "flags"]
PACKET_FIELDS = ["case_id", "target_type", "code", "source_unit_sha256", "packet_file", "packet_sha256",
                 "privacy_reviewer", "context_reviewer", "packet_checked"]
REFERENCE_FIELDS = ["case_id", "target_type", "code", "coder_1_decision",
                    "coder_2_decision", "final_decision", "adjudicator", "rationale"]
RESULT_FIELDS = [
    "target_type", "code", "frame_n", "sample_n", "predicted_positive_frame_n",
    "predicted_negative_frame_n", "short_sample_n", "coder_exact_agreement_n",
    "weighted_coder_agreement", "coder_agreement_ci95_low", "coder_agreement_ci95_high",
    "weighted_cohen_kappa", "final_present_sample_n", "final_absent_sample_n",
    "final_ambiguous_sample_n", "final_insufficient_sample_n", "reference_status",
    "estimated_tp", "estimated_fp", "estimated_tn", "estimated_fn",
    "ppv", "ppv_ci95_low", "ppv_ci95_high", "sensitivity",
    "sensitivity_ci95_low", "sensitivity_ci95_high", "npv", "npv_ci95_low",
    "npv_ci95_high", "specificity", "specificity_ci95_low", "specificity_ci95_high",
    "sensitivity_interval_status",
]
MACHINE_REQUIRED = set(sample.FRAME_FIELDS) | {
    "case_id", "stratum_frame_n", "stratum_sample_n", "inclusion_probability", "analysis_weight",
}


def read_exact(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fields:
            raise ValueError(f"Unexpected or missing columns in {path.name}")
        rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"Missing or malformed rows in {path.name}")
    return rows


def unique_rows(rows: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    result = {}
    for row in rows:
        case_id = row["case_id"]
        if not case_id or case_id in result:
            raise ValueError(f"Blank or duplicate case ID in {label}")
        result[case_id] = row
    return result


def identity_matches(rows: dict[str, dict[str, str]],
                     expected: dict[str, dict[str, str]], label: str) -> None:
    if set(rows) != set(expected) or any(
        (row["target_type"], row["code"]) !=
        (expected[case_id]["target_type"], expected[case_id]["code"])
        for case_id, row in rows.items()
    ):
        raise ValueError(f"Case IDs or target identities differ in {label}")


def sample_templates(sample_dir: Path) -> tuple[dict[str, object], dict[str, dict[str, str]]]:
    sample_dir = sample.outside_public(sample_dir)
    manifest_path = sample_dir / "selection_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    hashes = manifest.get("output_sha256", {})
    required_files = {"coordinator_machine_key.csv", "coder_1_blank.csv", "coder_2_blank.csv",
                      "packet_manifest_template.csv"}
    if (manifest.get("status") != "holdout_drawn_human_coding_pending"
            or not isinstance(hashes, dict) or set(hashes) != required_files
            or any(sample.sha_file(sample_dir / name) != hashes[name] for name in required_files)):
        raise ValueError("Selected sample or blinded templates are missing or changed")
    first = unique_rows(read_exact(sample_dir / "coder_1_blank.csv", CODER_FIELDS), "coder 1 template")
    second = unique_rows(read_exact(sample_dir / "coder_2_blank.csv", CODER_FIELDS), "coder 2 template")
    identity_matches(second, first, "coder templates")
    if (len(first) != manifest.get("sampled_case_target_n")
            or any(row["decision"] or row["rationale"] or row["flags"] for row in first.values())):
        raise ValueError("Blinded coder templates are not empty or complete")
    packet_template = unique_rows(
        read_exact(sample_dir / "packet_manifest_template.csv", PACKET_FIELDS), "packet template"
    )
    identity_matches(packet_template, first, "packet template")
    if any(not re.fullmatch(r"[0-9a-f]{64}", row["source_unit_sha256"])
           or any(row[field] for field in PACKET_FIELDS[4:])
           for row in packet_template.values()):
        raise ValueError("Packet manifest template is not blank")
    for case_id, row in first.items():
        row["source_unit_sha256"] = packet_template[case_id]["source_unit_sha256"]
    return manifest, first


def checked_coder_rows(path: Path, template: dict[str, dict[str, str]],
                       label: str) -> dict[str, dict[str, str]]:
    rows = unique_rows(read_exact(sample.outside_public(path), CODER_FIELDS), label)
    identity_matches(rows, template, label)
    for row in rows.values():
        if row["decision"] not in DECISIONS:
            raise ValueError(f"Blank or invalid {label} judgment")
        if row["decision"] not in {"present", "absent"} and not row["rationale"].strip():
            raise ValueError(f"Nonbinary {label} judgment needs a rationale")
    return rows


def checked_packet_rows(path: Path, packet_root: Path,
                        template: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    rows = unique_rows(read_exact(sample.outside_public(path), PACKET_FIELDS), "packet manifest")
    identity_matches(rows, template, "packet manifest")
    if any(row["source_unit_sha256"] != template[case_id]["source_unit_sha256"]
           for case_id, row in rows.items()):
        raise ValueError("Packet source-unit hashes differ from the frozen sample")
    packet_root = sample.outside_public(packet_root)
    for row in rows.values():
        relative = Path(row["packet_file"])
        if not row["packet_file"] or relative.is_absolute():
            raise ValueError("Packet path must be relative to the controlled packet root")
        actual = (packet_root / relative).resolve()
        if actual == packet_root or packet_root not in actual.parents:
            raise ValueError("Packet path escapes the controlled packet root")
        if (not actual.is_file() or not row["privacy_reviewer"].strip()
                or not row["context_reviewer"].strip()
                or row["privacy_reviewer"].strip() == row["context_reviewer"].strip()
                or row["packet_checked"] != "yes"
                or sample.sha_file(actual) != row["packet_sha256"]):
            raise ValueError("Packet content hash or two-person review is incomplete")
    return rows


def lock_coders(sample_dir: Path, coder_1: Path, coder_2: Path,
                packet_manifest: Path, packet_root: Path, coder_1_name: str,
                coder_2_name: str, output_dir: Path) -> dict[str, object]:
    output_dir = sample.fresh_directory(output_dir)
    sample_manifest, template = sample_templates(sample_dir)
    if (not coder_1_name.strip() or not coder_2_name.strip()
            or coder_1_name.strip() == coder_2_name.strip()):
        raise ValueError("Two distinct coder names are required")
    first = checked_coder_rows(coder_1, template, "coder 1")
    second = checked_coder_rows(coder_2, template, "coder 2")
    checked_packet_rows(packet_manifest, packet_root, template)
    agreement = sum(first[case_id]["decision"] == second[case_id]["decision"] for case_id in template)
    report = {
        "status": "independent_human_decisions_locked_predictions_unseen",
        "article_ready": False,
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "sample_manifest_sha256": sample.sha_file(sample_dir / "selection_manifest.json"),
        "coder_1_sha256": sample.sha_file(coder_1),
        "coder_2_sha256": sample.sha_file(coder_2),
        "packet_manifest_sha256": sample.sha_file(packet_manifest),
        "coder_names": [coder_1_name.strip(), coder_2_name.strip()],
        "case_target_n": len(template), "pre_adjudication_exact_agreement_n": agreement,
        "pre_adjudication_disagreement_n": len(template) - agreement,
        "machine_predictions_opened": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "coder_lock_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def locked_coders(sample_dir: Path, lock_dir: Path, coder_1: Path, coder_2: Path,
                  packet_manifest: Path, packet_root: Path
                  ) -> tuple[dict[str, object], dict[str, dict[str, str]],
                             dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    sample_dir, lock_dir = sample.outside_public(sample_dir), sample.outside_public(lock_dir)
    manifest, template = sample_templates(sample_dir)
    lock = json.loads((lock_dir / "coder_lock_manifest.json").read_text(encoding="utf-8"))
    if (lock.get("status") != "independent_human_decisions_locked_predictions_unseen"
            or lock.get("machine_predictions_opened") is not False
            or lock.get("sample_manifest_sha256") != sample.sha_file(sample_dir / "selection_manifest.json")
            or lock.get("coder_1_sha256") != sample.sha_file(coder_1)
            or lock.get("coder_2_sha256") != sample.sha_file(coder_2)
            or lock.get("packet_manifest_sha256") != sample.sha_file(packet_manifest)
            or lock.get("case_target_n") != manifest.get("sampled_case_target_n")):
        raise ValueError("Frozen coder/packet material changed or lock is invalid")
    first = checked_coder_rows(coder_1, template, "coder 1")
    second = checked_coder_rows(coder_2, template, "coder 2")
    checked_packet_rows(packet_manifest, packet_root, template)
    agreements = sum(first[case_id]["decision"] == second[case_id]["decision"] for case_id in template)
    if (agreements != lock.get("pre_adjudication_exact_agreement_n")
            or len(template) - agreements != lock.get("pre_adjudication_disagreement_n")):
        raise ValueError("Frozen coder agreement count changed")
    return lock, template, first, second


def prepare_reference(sample_dir: Path, lock_dir: Path, coder_1: Path, coder_2: Path,
                      packet_manifest: Path, packet_root: Path,
                      output_dir: Path) -> dict[str, object]:
    output_dir = sample.fresh_directory(output_dir)
    lock, template, first, second = locked_coders(
        sample_dir, lock_dir, coder_1, coder_2, packet_manifest, packet_root
    )
    rows = []
    for case_id in template:
        left, right = first[case_id]["decision"], second[case_id]["decision"]
        rows.append({
            "case_id": case_id, "target_type": template[case_id]["target_type"],
            "code": template[case_id]["code"], "coder_1_decision": left,
            "coder_2_decision": right,
            "final_decision": left if left == right else "",
            "adjudicator": "", "rationale": "",
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    sample.write_csv(output_dir / "reference_decisions_template.csv", REFERENCE_FIELDS, rows)
    report = {
        "status": "reference_template_prepared_adjudication_pending",
        "article_ready": False,
        "coder_lock_sha256": sample.sha_file(lock_dir / "coder_lock_manifest.json"),
        "reference_template_sha256": sample.sha_file(output_dir / "reference_decisions_template.csv"),
        "case_target_n": len(rows), "disagreements_n": lock["pre_adjudication_disagreement_n"],
    }
    (output_dir / "reference_template_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def checked_reference(path: Path, template: dict[str, dict[str, str]],
                      first: dict[str, dict[str, str]], second: dict[str, dict[str, str]]
                      ) -> dict[str, dict[str, str]]:
    rows = unique_rows(read_exact(sample.outside_public(path), REFERENCE_FIELDS), "reference decisions")
    identity_matches(rows, template, "reference decisions")
    for case_id, row in rows.items():
        left, right = first[case_id]["decision"], second[case_id]["decision"]
        if ((row["coder_1_decision"], row["coder_2_decision"]) != (left, right)
                or row["final_decision"] not in DECISIONS):
            raise ValueError("Reference decision or frozen coder decisions are missing or changed")
        if ((left != right or row["final_decision"] != left)
                and (not row["adjudicator"].strip() or not row["rationale"].strip())):
            raise ValueError("Adjudicated change or disagreement needs named rationale")
    return rows


def lock_reference(sample_dir: Path, lock_dir: Path, coder_1: Path, coder_2: Path,
                   packet_manifest: Path, packet_root: Path,
                   reference: Path, output_dir: Path) -> dict[str, object]:
    output_dir = sample.fresh_directory(output_dir)
    lock, template, first, second = locked_coders(
        sample_dir, lock_dir, coder_1, coder_2, packet_manifest, packet_root
    )
    rows = checked_reference(reference, template, first, second)
    report = {
        "status": "human_reference_locked_predictions_unseen", "article_ready": False,
        "locked_at_utc": datetime.now(timezone.utc).isoformat(),
        "coder_lock_sha256": sample.sha_file(lock_dir / "coder_lock_manifest.json"),
        "reference_sha256": sample.sha_file(reference),
        "case_target_n": len(rows),
        "adjudicated_disagreements_n": lock["pre_adjudication_disagreement_n"],
        "machine_predictions_opened": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reference_lock_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def locked_reference(sample_dir: Path, lock_dir: Path, coder_1: Path, coder_2: Path,
                     packet_manifest: Path, packet_root: Path, reference: Path,
                     reference_lock_dir: Path
                     ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]],
                                dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    _, template, first, second = locked_coders(
        sample_dir, lock_dir, coder_1, coder_2, packet_manifest, packet_root
    )
    rows = checked_reference(reference, template, first, second)
    reference_lock_dir = sample.outside_public(reference_lock_dir)
    frozen = json.loads((reference_lock_dir / "reference_lock_manifest.json").read_text(encoding="utf-8"))
    if (frozen.get("status") != "human_reference_locked_predictions_unseen"
            or frozen.get("machine_predictions_opened") is not False
            or frozen.get("coder_lock_sha256") != sample.sha_file(lock_dir / "coder_lock_manifest.json")
            or frozen.get("reference_sha256") != sample.sha_file(reference)
            or frozen.get("case_target_n") != len(template)):
        raise ValueError("Human reference changed after pre-unblinding lock")
    return template, first, second, rows


def hypergeom_tail_count(population_n: int, successes_n: int, draw_n: int,
                         observed_n: int, upper_tail: bool) -> int:
    low = max(0, draw_n - (population_n - successes_n))
    high = min(draw_n, successes_n)
    if upper_tail:
        low = max(low, observed_n)
    else:
        high = min(high, observed_n)
    return sum(math.comb(successes_n, x) * math.comb(population_n - successes_n, draw_n - x)
               for x in range(low, high + 1))


def exact_success_bounds(population_n: int, draw_n: int, observed_present_n: int,
                         unresolved_n: int, stratum_count: int) -> tuple[int, int]:
    """Conservative 95% simultaneous bounds across one target's strata.

    Equal-tail hypergeometric inversion uses tail alpha/(2H)=1/(40H).
    Unknown human decisions are unioned over all possible binary assignments.
    """
    if (not 1 <= draw_n <= population_n or not 0 <= observed_present_n <= draw_n
            or not 0 <= unresolved_n <= draw_n - observed_present_n
            or stratum_count < 1):
        raise ValueError("Invalid finite-population interval inputs")
    if draw_n == population_n:
        return observed_present_n, observed_present_n + unresolved_n
    denominator = math.comb(population_n, draw_n)
    multiplier = 40 * stratum_count
    lower_observed = observed_present_n
    upper_observed = observed_present_n + unresolved_n
    # P_K(X >= s) increases in K; invert its lower acceptance boundary.
    left, right = lower_observed, population_n - draw_n + lower_observed
    while left < right:
        middle = (left + right) // 2
        accepted = (hypergeom_tail_count(population_n, middle, draw_n,
                                         lower_observed, True) * multiplier >= denominator)
        if accepted:
            right = middle
        else:
            left = middle + 1
    lower = left
    # P_K(X <= s) decreases in K; invert its upper acceptance boundary.
    left, right = upper_observed, population_n - draw_n + upper_observed
    while left < right:
        middle = (left + right + 1) // 2
        accepted = (hypergeom_tail_count(population_n, middle, draw_n,
                                         upper_observed, False) * multiplier >= denominator)
        if accepted:
            left = middle
        else:
            right = middle - 1
    return lower, right


def ratio(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def score_target(rows: list[dict[str, object]]) -> dict[str, object]:
    groups: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[row["stratum"]].append(row)  # type: ignore[index]
    H = len(groups)
    interval_counts = {}
    point_counts = {}
    agreement_bounds = {}
    agreement_points = {}
    for key, members in groups.items():
        N = int(members[0]["N"])
        n = len(members)
        present = sum(row["final"] == "present" for row in members)
        unresolved = sum(row["final"] in NONBINARY for row in members)
        agreed = sum(row["coder_1"] == row["coder_2"] for row in members)
        interval_counts[key] = exact_success_bounds(N, n, present, unresolved, H)
        point_counts[key] = N * present / n
        agreement_bounds[key] = exact_success_bounds(N, n, agreed, 0, H)
        agreement_points[key] = N * agreed / n
    N_total = sum(int(members[0]["N"]) for members in groups.values())
    N_pos = sum(int(members[0]["N"]) for key, members in groups.items() if key[2] == "1")
    N_neg = N_total - N_pos
    TP_lo = sum(bounds[0] for key, bounds in interval_counts.items() if key[2] == "1")
    TP_hi = sum(bounds[1] for key, bounds in interval_counts.items() if key[2] == "1")
    FN_lo = sum(bounds[0] for key, bounds in interval_counts.items() if key[2] == "0")
    FN_hi = sum(bounds[1] for key, bounds in interval_counts.items() if key[2] == "0")
    TP_hat = sum(value for key, value in point_counts.items() if key[2] == "1")
    FN_hat = sum(value for key, value in point_counts.items() if key[2] == "0")
    unknown = sum(row["final"] in NONBINARY for row in rows)
    out_scope = sum(row["final"] == "out_of_scope_record" for row in rows)
    if out_scope:
        raise ValueError("Out-of-scope human decision invalidates the approved holdout frame")
    if unknown:
        TP = FP = TN = FN = None
        ppv = sensitivity = npv = specificity = None
    else:
        TP, FN = TP_hat, FN_hat
        FP, TN = N_pos - TP, N_neg - FN
        ppv, sensitivity = ratio(TP, N_pos), ratio(TP, TP + FN)
        npv, specificity = ratio(TN, N_neg), ratio(TN, TN + FP)
    sensitivity_bounds = (
        (ratio(TP_lo, TP_lo + FN_hi), ratio(TP_hi, TP_hi + FN_lo))
        if TP_lo + FN_lo > 0 else (None, None)
    )
    TN_lo, TN_hi = N_neg - FN_hi, N_neg - FN_lo
    FP_lo, FP_hi = N_pos - TP_hi, N_pos - TP_lo
    specificity_bounds = (
        (ratio(TN_lo, TN_lo + FP_hi), ratio(TN_hi, TN_hi + FP_lo))
        if TN_lo + FP_lo > 0 else (None, None)
    )
    matrix: Counter[tuple[str, str]] = Counter()
    for row in rows:
        matrix[(str(row["coder_1"]), str(row["coder_2"]))] += float(row["N"]) / float(row["n"])
    agreement = sum(agreement_points.values()) / N_total
    marg1 = Counter()
    marg2 = Counter()
    for (left, right), weighted in matrix.items():
        marg1[left] += weighted
        marg2[right] += weighted
    expected = sum(marg1[key] * marg2[key] for key in DECISIONS) / (N_total * N_total)
    kappa = ((agreement - expected) / (1 - expected)
             if 1 - expected > 1e-12 else None)
    by_decision = Counter(str(row["final"]) for row in rows)
    first = rows[0]
    return {
        "target_type": first["target_type"], "code": first["code"],
        "frame_n": N_total, "sample_n": len(rows),
        "predicted_positive_frame_n": N_pos, "predicted_negative_frame_n": N_neg,
        "short_sample_n": sum(row["length_band"] == "short" for row in rows),
        "coder_exact_agreement_n": sum(row["coder_1"] == row["coder_2"] for row in rows),
        "weighted_coder_agreement": agreement,
        "coder_agreement_ci95_low": sum(pair[0] for pair in agreement_bounds.values()) / N_total,
        "coder_agreement_ci95_high": sum(pair[1] for pair in agreement_bounds.values()) / N_total,
        "weighted_cohen_kappa": kappa,
        "final_present_sample_n": by_decision["present"],
        "final_absent_sample_n": by_decision["absent"],
        "final_ambiguous_sample_n": by_decision["ambiguous"],
        "final_insufficient_sample_n": by_decision["insufficient_evidence"],
        "reference_status": "complete_binary" if not unknown else "nonbinary_bounds_only",
        "estimated_tp": TP, "estimated_fp": FP, "estimated_tn": TN, "estimated_fn": FN,
        "ppv": ppv,
        "ppv_ci95_low": ratio(TP_lo, N_pos), "ppv_ci95_high": ratio(TP_hi, N_pos),
        "sensitivity": sensitivity,
        "sensitivity_ci95_low": sensitivity_bounds[0],
        "sensitivity_ci95_high": sensitivity_bounds[1],
        "npv": npv,
        "npv_ci95_low": ratio(N_neg - FN_hi, N_neg),
        "npv_ci95_high": ratio(N_neg - FN_lo, N_neg),
        "specificity": specificity,
        "specificity_ci95_low": specificity_bounds[0],
        "specificity_ci95_high": specificity_bounds[1],
        "sensitivity_interval_status": (
            "defined" if sensitivity_bounds[0] is not None else
            "human_positive_population_may_be_zero"
        ),
    }


def verified_machine(sample_dir: Path, frame_dir: Path, plan_path: Path,
                     template: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    sample_dir, frame_dir, plan_path = (sample.outside_public(path)
                                        for path in (sample_dir, frame_dir, plan_path))
    manifest, _ = sample_templates(sample_dir)
    frame_path = frame_dir / "validation_frame.csv"
    frame_manifest = json.loads((frame_dir / "frame_manifest.json").read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (manifest.get("frame_sha256") != sample.sha_file(frame_path)
            or manifest.get("plan_sha256") != sample.sha_file(plan_path)
            or frame_manifest.get("frame_sha256") != sample.sha_file(frame_path)
            or plan.get("frame_sha256") != sample.sha_file(frame_path)
            or plan.get("input_sha256") != manifest.get("input_sha256")
            or plan.get("status") != "approved"
            or plan.get("selection_seed") != manifest.get("selection_seed")):
        raise ValueError("Approved sampling frame or plan changed after draw")
    frame = sample.read_csv(frame_path, set(sample.FRAME_FIELDS))
    if len(frame) != manifest.get("case_target_frame_n"):
        raise ValueError("Locked case-target frame size changed")
    groups = sample.frame_strata(frame)
    allocations = {}
    for row in plan.get("allocations", []):
        key = sample.stratum(row)
        if key in allocations or key not in groups or row.get("frame_n") != len(groups[key]):
            raise ValueError("Approved allocation differs from locked frame")
        allocations[key] = row.get("sample_n")
    if set(allocations) != set(groups) or any(
        isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(groups[key])
        for key, n in allocations.items()
    ):
        raise ValueError("Approved allocation is incomplete or invalid")
    expected_draw = sample.select_rows(groups, allocations, plan["selection_seed"])
    expected = {(row["unit_id"], row["target_type"], row["code"]): (row, N, n)
                for row, N, n in expected_draw}
    with (sample_dir / "coordinator_machine_key.csv").open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not MACHINE_REQUIRED.issubset(reader.fieldnames):
            raise ValueError("Coordinator machine-key columns are missing")
        machine = unique_rows(list(reader), "coordinator machine key")
    identity_matches(machine, template, "coordinator machine key")
    packet_template = unique_rows(
        read_exact(sample_dir / "packet_manifest_template.csv", PACKET_FIELDS), "packet template"
    )
    if any(packet_template[case_id]["source_unit_sha256"] != row["combined_text_sha256"]
           for case_id, row in machine.items()):
        raise ValueError("Packet source-unit hashes differ from the coordinator key")
    if len(machine) != len(expected):
        raise ValueError("Coordinator key size differs from reproducible probability draw")
    seen = set()
    for row in machine.values():
        key = (row["unit_id"], row["target_type"], row["code"])
        if key not in expected or key in seen:
            raise ValueError("Coordinator key differs from reproducible probability draw")
        seen.add(key)
        frame_row, N, n = expected[key]
        if any(row[field] != frame_row[field] for field in sample.FRAME_FIELDS):
            raise ValueError("Coordinator key metadata differs from approved frame")
        if (int(row["stratum_frame_n"]) != N or int(row["stratum_sample_n"]) != n
                or not math.isclose(float(row["inclusion_probability"]), n / N, rel_tol=1e-12)
                or not math.isclose(float(row["analysis_weight"]), N / n, rel_tol=1e-12)):
            raise ValueError("Coordinator key inclusion probabilities or weights are wrong")
    return machine


def score(sample_dir: Path, frame_dir: Path, plan_path: Path, lock_dir: Path,
          coder_1: Path, coder_2: Path, packet_manifest: Path, packet_root: Path,
          reference: Path, reference_lock_dir: Path,
          output_dir: Path) -> dict[str, object]:
    output_dir = sample.fresh_directory(output_dir)
    template, first, second, reference_rows = locked_reference(
        sample_dir, lock_dir, coder_1, coder_2, packet_manifest, packet_root,
        reference, reference_lock_dir,
    )
    machine = verified_machine(sample_dir, frame_dir, plan_path, template)
    targets: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for case_id, row in machine.items():
        target = (row["target_type"], row["code"])
        targets[target].append({
            "target_type": target[0], "code": target[1],
            "stratum": sample.stratum(row), "N": int(row["stratum_frame_n"]),
            "n": int(row["stratum_sample_n"]), "length_band": row["length_band"],
            "coder_1": first[case_id]["decision"],
            "coder_2": second[case_id]["decision"],
            "final": reference_rows[case_id]["final_decision"],
        })
    results = [score_target(rows) for _, rows in sorted(targets.items())]
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "revised_holdout_performance_controlled.csv"
    sample.write_csv(result_path, RESULT_FIELDS, results)
    report = {
        "status": "provisional_revised_holdout_scored_other_article_gates_pending",
        "article_ready": False,
        "sample_manifest_sha256": sample.sha_file(sample_dir / "selection_manifest.json"),
        "frame_sha256": sample.sha_file(frame_dir / "validation_frame.csv"),
        "approved_plan_sha256": sample.sha_file(plan_path),
        "coder_lock_sha256": sample.sha_file(lock_dir / "coder_lock_manifest.json"),
        "reference_lock_sha256": sample.sha_file(reference_lock_dir / "reference_lock_manifest.json"),
        "machine_key_sha256": sample.sha_file(sample_dir / "coordinator_machine_key.csv"),
        "performance_csv_sha256": sample.sha_file(result_path),
        "target_count": len(results),
        "case_target_n": len(machine),
        "targets_with_nonbinary_reference_n": sum(row["reference_status"] != "complete_binary" for row in results),
        "interval_method": "Per-target conservative at-least-95-percent intervals from equal-tail finite-population hypergeometric inversion, Bonferroni across independent sampling strata; undefined sensitivity is suppressed.",
        "coverage_boundary": "Intervals address random selection from the approved finite capture-unit frame, not source selection, OCR error, construct validity, coder error, or external-market prevalence.",
    }
    (output_dir / "revised_holdout_score_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command_name in ("lock-coders", "prepare-reference", "lock-reference", "score"):
        command = commands.add_parser(command_name)
        command.add_argument("--sample-dir", type=Path, required=True)
        command.add_argument("--coder-1", type=Path, required=True)
        command.add_argument("--coder-2", type=Path, required=True)
        command.add_argument("--packet-manifest", type=Path, required=True)
        command.add_argument("--packet-root", type=Path, required=True)
        command.add_argument("--output-dir", type=Path, required=True)
        if command_name == "lock-coders":
            command.add_argument("--coder-1-name", required=True)
            command.add_argument("--coder-2-name", required=True)
        else:
            command.add_argument("--coder-lock-dir", type=Path, required=True)
        if command_name in {"lock-reference", "score"}:
            command.add_argument("--reference", type=Path, required=True)
        if command_name == "score":
            command.add_argument("--reference-lock-dir", type=Path, required=True)
            command.add_argument("--frame-dir", type=Path, required=True)
            command.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "lock-coders":
            report = lock_coders(args.sample_dir, args.coder_1, args.coder_2,
                                 args.packet_manifest, args.packet_root,
                                 args.coder_1_name, args.coder_2_name, args.output_dir)
        elif args.command == "prepare-reference":
            report = prepare_reference(args.sample_dir, args.coder_lock_dir,
                                       args.coder_1, args.coder_2,
                                       args.packet_manifest, args.packet_root, args.output_dir)
        elif args.command == "lock-reference":
            report = lock_reference(args.sample_dir, args.coder_lock_dir,
                                    args.coder_1, args.coder_2,
                                    args.packet_manifest, args.packet_root,
                                    args.reference, args.output_dir)
        else:
            report = score(args.sample_dir, args.frame_dir, args.plan,
                           args.coder_lock_dir, args.coder_1, args.coder_2,
                           args.packet_manifest, args.packet_root,
                           args.reference, args.reference_lock_dir, args.output_dir)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
