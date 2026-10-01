"""Prepare and draw a controlled revised-evidence human-validation holdout.

This tool creates no human decisions or performance estimates. It refuses the
historical mixed-record Phase 3 run and keeps every record-level file outside
the public repository.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import secrets
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUALITY_FLAG = "market_access_limitation"
SHORT_WORD_LIMIT = 30
FRAME_FIELDS = [
    "unit_id", "source", "modality", "duplicate_cluster_hash",
    "duplicate_cluster_size", "combined_text_sha256", "combined_word_count",
    "length_band", "target_type", "code", "predicted_present",
]
STRATUM_FIELDS = ("target_type", "code", "predicted_present", "length_band")
INPUT_FILES = {
    "evidence_corpus": "approved_evidence_units.jsonl",
    "evidence_manifest": "evidence_build_manifest.json",
    "phase3_metadata": "run_metadata.json",
    "phase3_combined": "combined_corpus_with_ocr.csv",
    "phase3_typology": "typology_coding_long.csv",
    "phase3_aml": "aml_indicator_coding_long.csv",
    "phase3_artifacts": "artifact_coding_long.csv",
    "phase3_codebook": "CODEBOOK_PHASE3.md",
}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def outside_public(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT.resolve() or ROOT.resolve() in resolved.parents:
        raise ValueError("Record-level holdout inputs and outputs must remain outside the public repository")
    return resolved


def fresh_directory(path: Path) -> Path:
    path = outside_public(path)
    if path.exists() and any(path.iterdir()):
        raise ValueError("Output directory is not empty")
    return path


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Missing or duplicate CSV columns in {path.name}")
        if not required.issubset(reader.fieldnames):
            raise ValueError(f"Required CSV columns missing in {path.name}")
        return list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def count(value: str, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {label}") from exc
    if number < 0:
        raise ValueError(f"Negative integer for {label}")
    return number


def binary(value: str, label: str) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"Invalid binary value for {label}")
    return int(value)


def stratum(row: dict[str, str]) -> tuple[str, str, str, str]:
    return tuple(row[field] for field in STRATUM_FIELDS)  # type: ignore[return-value]


def build_frame(
    phase3_dir: Path, evidence_corpus: Path, pilot_units: Path, human_codebook: Path
) -> tuple[list[dict[str, str]], dict[str, str], dict[str, object]]:
    phase3_dir = outside_public(phase3_dir)
    evidence_corpus = outside_public(evidence_corpus)
    pilot_units = outside_public(pilot_units)
    human_codebook = outside_public(human_codebook)
    paths = {
        "evidence_corpus": evidence_corpus,
        "evidence_manifest": evidence_corpus.parent / INPUT_FILES["evidence_manifest"],
        "phase3_metadata": phase3_dir / INPUT_FILES["phase3_metadata"],
        "phase3_combined": phase3_dir / INPUT_FILES["phase3_combined"],
        "phase3_typology": phase3_dir / INPUT_FILES["phase3_typology"],
        "phase3_aml": phase3_dir / INPUT_FILES["phase3_aml"],
        "phase3_artifacts": phase3_dir / INPUT_FILES["phase3_artifacts"],
        "phase3_codebook": phase3_dir / INPUT_FILES["phase3_codebook"],
        "pilot_units": pilot_units,
        "human_codebook": human_codebook,
    }
    hashes = {name: sha_file(path) for name, path in paths.items()}
    metadata = json.loads(paths["phase3_metadata"].read_text(encoding="utf-8"))
    evidence_manifest = json.loads(paths["evidence_manifest"].read_text(encoding="utf-8"))
    if (metadata.get("analysis_mode") != "author_reviewed_artifact_bounded_source_text"
            or metadata.get("article_ready") is not False
            or metadata.get("historical_human_validation_applicable") is not False
            or metadata.get("artifact_coding_schema_version") != 1):
        raise ValueError("A provisional reviewed-evidence Phase 3 run is required")
    if (metadata.get("evidence_corpus_sha256") != hashes["evidence_corpus"]
            or evidence_manifest.get("evidence_jsonl_sha256") != hashes["evidence_corpus"]
            or evidence_manifest.get("schema_version") != 3
            or evidence_manifest.get("status") != "source_screening_complete_target_validation_pending"):
        raise ValueError("Approved evidence corpus does not match Phase 3 and screening manifest")
    if metadata.get("codebook_sha256") != hashes["phase3_codebook"]:
        raise ValueError("Phase 3 codebook hash is missing or mismatched")
    if not human_codebook.read_text(encoding="utf-8").strip():
        raise ValueError("The human decision codebook is empty")

    units: dict[str, dict[str, str]] = {}
    artifact_identity: dict[tuple[str, str], tuple[str, str, str]] = {}
    with evidence_corpus.open(encoding="utf-8") as handle:
        for line in handle:
            unit = json.loads(line)
            unit_id, source = unit.get("note_id"), unit.get("source")
            artifacts = unit.get("artifacts")
            if not unit_id or unit_id in units or not source or not isinstance(artifacts, list) or not artifacts:
                raise ValueError("Approved evidence has an invalid unit identity or no source spans")
            texts = []
            kinds = set()
            for artifact in artifacts:
                artifact_id, kind, value = artifact.get("artifact_id"), artifact.get("kind"), artifact.get("text")
                if (not artifact_id or (unit_id, artifact_id) in artifact_identity
                        or kind not in {"markdown_source_span", "image_ocr"}
                        or not isinstance(value, str) or not value.strip()
                        or sha_text(value) != artifact.get("text_sha256")):
                    raise ValueError("Approved evidence has a duplicate or invalid source span")
                artifact_identity[(unit_id, artifact_id)] = (kind, source, artifact["text_sha256"])
                texts.append(value)
                kinds.add(kind)
            joined = "\n\n".join(texts)
            units[unit_id] = {
                "source": source,
                "combined_text_sha256": sha_text(joined),
                "combined_word_count": str(len(re.findall(r"\b\w+\b", joined))),
                "modality": "both" if len(kinds) == 2 else ("markdown" if "markdown_source_span" in kinds else "ocr"),
            }
    if not units or len(units) != metadata.get("note_count") or len(units) != evidence_manifest.get("approved_evidence_units"):
        raise ValueError("Approved evidence unit count differs from screening or Phase 3")
    if len(artifact_identity) != metadata.get("approved_source_artifacts"):
        raise ValueError("Approved source span count differs from Phase 3")

    combined = read_csv(paths["phase3_combined"], {
        "note_id", "source", "combined_text_sha256", "combined_word_count",
        "markdown_present", "ocr_present",
    })
    seen_units = set()
    for row in combined:
        unit_id = row["note_id"]
        if unit_id not in units or unit_id in seen_units:
            raise ValueError("Phase 3 combined table has a missing or duplicate approved unit")
        seen_units.add(unit_id)
        expected = units[unit_id]
        modality = "both" if row["markdown_present"] == row["ocr_present"] == "1" else (
            "markdown" if row["markdown_present"] == "1" and row["ocr_present"] == "0" else
            "ocr" if row["markdown_present"] == "0" and row["ocr_present"] == "1" else "invalid"
        )
        if (row["source"] != expected["source"] or row["combined_text_sha256"] != expected["combined_text_sha256"]
                or row["combined_word_count"] != expected["combined_word_count"]
                or modality != expected["modality"]):
            raise ValueError("Phase 3 combined text or modality differs from approved evidence")
    if seen_units != set(units):
        raise ValueError("Phase 3 combined table omits approved units")

    predictions: dict[tuple[str, str, str], int] = {}
    hit_counts: dict[tuple[str, str, str], int] = {}
    codes: dict[str, set[str]] = defaultdict(set)
    for target_type, path, code_field in (
        ("typology", paths["phase3_typology"], "code"),
        ("aml_candidate", paths["phase3_aml"], "aml_indicator"),
    ):
        for row in read_csv(path, {"note_id", "source", code_field, "present", "hit_count"}):
            unit_id, code = row["note_id"], row[code_field]
            key = (unit_id, target_type, code)
            if unit_id not in units or row["source"] != units[unit_id]["source"] or not code or key in predictions:
                raise ValueError("Phase 3 coding has an invalid or duplicate unit-target row")
            present, hits = binary(row["present"], "unit prediction"), count(row["hit_count"], "unit hits")
            if present != int(hits > 0):
                raise ValueError("Unit prediction and hit count disagree")
            predictions[key], hit_counts[key] = present, hits
            codes[target_type].add(code)
    if (len(codes["typology"]) != metadata.get("typology_code_count")
            or len(codes["aml_candidate"]) != metadata.get("aml_indicator_count")
            or QUALITY_FLAG not in codes["typology"]
            or set(predictions) != {
                (unit_id, target_type, code)
                for unit_id in units for target_type, target_codes in codes.items() for code in target_codes
            }):
        raise ValueError("Phase 3 unit-target matrix is incomplete")

    valid_target_pairs = {(target_type, code) for target_type, group in codes.items() for code in group}
    artifact_hits: Counter[tuple[str, str, str]] = Counter()
    seen_artifact_targets = set()
    for row in read_csv(paths["phase3_artifacts"], {
        "unit_id", "artifact_id", "artifact_kind", "source", "target_type", "code",
        "present", "hit_count", "artifact_text_sha256",
    }):
        unit_id, artifact_id = row["unit_id"], row["artifact_id"]
        target_type, code = row["target_type"], row["code"]
        key = (unit_id, artifact_id, target_type, code)
        if (key in seen_artifact_targets or (unit_id, artifact_id) not in artifact_identity
                or (target_type, code) not in valid_target_pairs
                or (row["artifact_kind"], row["source"], row["artifact_text_sha256"])
                != artifact_identity[(unit_id, artifact_id)]):
            raise ValueError("Phase 3 span-target matrix has an invalid identity")
        seen_artifact_targets.add(key)
        hits = count(row["hit_count"], "span hits")
        if binary(row["present"], "span prediction") != int(hits > 0):
            raise ValueError("Span prediction and hit count disagree")
        artifact_hits[(unit_id, target_type, code)] += hits
    if (len(seen_artifact_targets) != metadata.get("artifact_coding_rows")
            or len(seen_artifact_targets) != len(artifact_identity) * sum(map(len, codes.values()))
            or any(artifact_hits[key] != hits for key, hits in hit_counts.items())):
        raise ValueError("Phase 3 span coding is incomplete or does not reconcile to unit coding")

    pilot_rows = read_csv(pilot_units, {"unit_id"})
    pilot_ids = [row["unit_id"].strip() for row in pilot_rows]
    if len(pilot_ids) != len(set(pilot_ids)) or any(unit_id not in units for unit_id in pilot_ids):
        raise ValueError("Pilot exclusion list has duplicate or unknown unit IDs")
    excluded_hashes = {units[unit_id]["combined_text_sha256"] for unit_id in pilot_ids}
    eligible = {unit_id: row for unit_id, row in units.items()
                if row["combined_text_sha256"] not in excluded_hashes}
    if not eligible:
        raise ValueError("No approved source units remain after pilot exclusions")
    clusters = Counter(row["combined_text_sha256"] for row in eligible.values())
    frame = []
    for unit_id, unit in sorted(eligible.items()):
        for target_type, target_codes in sorted(codes.items()):
            for code in sorted(target_codes):
                if (target_type, code) == ("typology", QUALITY_FLAG):
                    continue
                frame.append({
                    "unit_id": unit_id, "source": unit["source"], "modality": unit["modality"],
                    "duplicate_cluster_hash": unit["combined_text_sha256"],
                    "duplicate_cluster_size": str(clusters[unit["combined_text_sha256"]]),
                    "combined_text_sha256": unit["combined_text_sha256"],
                    "combined_word_count": unit["combined_word_count"],
                    "length_band": "short" if int(unit["combined_word_count"]) < SHORT_WORD_LIMIT else "long",
                    "target_type": target_type, "code": code,
                    "predicted_present": str(predictions[(unit_id, target_type, code)]),
                })
    diagnostics = {
        "approved_units": len(units), "pilot_units_listed": len(pilot_ids),
        "pilot_and_exact_duplicate_units_excluded": len(units) - len(eligible),
        "eligible_units": len(eligible), "target_codes": sum(map(len, codes.values())) - 1,
        "short_units": sum(int(row["combined_word_count"]) < SHORT_WORD_LIMIT for row in eligible.values()),
        "source_groups": len({row["source"] for row in eligible.values()}),
        "source_unit_counts": dict(sorted(Counter(row["source"] for row in eligible.values()).items())),
        "modality_unit_counts": dict(sorted(Counter(row["modality"] for row in eligible.values()).items())),
        "duplicate_clusters": len(clusters),
        "duplicate_excess_units": len(eligible) - len(clusters),
    }
    return frame, hashes, diagnostics


def frame_strata(frame: list[dict[str, str]]) -> dict[tuple[str, str, str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in frame:
        groups[stratum(row)].append(row)
    return dict(sorted(groups.items()))


def select_rows(
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]],
    allocations: dict[tuple[str, str, str, str], int], seed: int
) -> list[tuple[dict[str, str], int, int]]:
    rng = random.Random(seed)
    selected = []
    for key, rows in sorted(groups.items()):
        n = allocations[key]
        for row in rng.sample(sorted(rows, key=lambda item: item["unit_id"]), n):
            selected.append((row, len(rows), n))
    rng.shuffle(selected)
    return selected


def prepare(phase3_dir: Path, evidence_corpus: Path, pilot_units: Path,
            human_codebook: Path, output_dir: Path) -> dict[str, object]:
    output_dir = fresh_directory(output_dir)
    if (output_dir == phase3_dir.resolve() or output_dir in phase3_dir.resolve().parents
            or phase3_dir.resolve() in output_dir.parents
            or output_dir == evidence_corpus.parent.resolve()
            or evidence_corpus.parent.resolve() in output_dir.parents):
        raise ValueError("Prepared frame must be separate from Phase 3 and evidence outputs")
    frame, hashes, diagnostics = build_frame(phase3_dir, evidence_corpus, pilot_units, human_codebook)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_path = output_dir / "validation_frame.csv"
    write_csv(frame_path, FRAME_FIELDS, frame)
    allocations = []
    for key, rows in frame_strata(frame).items():
        allocation: dict[str, object] = dict(zip(STRATUM_FIELDS, key))
        allocation.update({"frame_n": len(rows), "sample_n": None})
        allocations.append(allocation)
    targets = sorted({(row["target_type"], row["code"]) for row in frame})
    plan = {
        "schema_version": 1, "status": "draft", "frame_sha256": sha_file(frame_path),
        "input_sha256": hashes, "short_word_limit_exclusive": SHORT_WORD_LIMIT,
        "primary_estimands": ["positive_predictive_value", "sensitivity"],
        "precision_rationale": "",
        "target_precision_rationale": {f"{target_type}:{code}": "" for target_type, code in targets},
        "pilot_exclusions_finalized": False,
        "prior_exposure_overlap_status": "",
        "prior_exposure_audit_rationale": "",
        "target_definitions_frozen": False, "approved_by": [], "approval_date": "",
        "selection_seed": None, "allocations": allocations,
    }
    (output_dir / "allocation_plan_template.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "status": "frame_prepared_plan_pending", "article_ready": False,
        "frame_sha256": plan["frame_sha256"], "input_sha256": hashes,
        "diagnostics": diagnostics, "strata_n": len(allocations),
        "case_target_frame_n": len(frame),
    }
    (output_dir / "frame_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def draw(phase3_dir: Path, evidence_corpus: Path, pilot_units: Path,
         human_codebook: Path, frame_dir: Path, plan_path: Path,
         output_dir: Path) -> dict[str, object]:
    output_dir = fresh_directory(output_dir)
    frame_dir, plan_path = outside_public(frame_dir), outside_public(plan_path)
    if output_dir == frame_dir or output_dir in frame_dir.parents or frame_dir in output_dir.parents:
        raise ValueError("Sample output must be separate from the prepared frame")
    if (output_dir == phase3_dir.resolve() or output_dir in phase3_dir.resolve().parents
            or phase3_dir.resolve() in output_dir.parents
            or output_dir == evidence_corpus.parent.resolve()
            or evidence_corpus.parent.resolve() in output_dir.parents):
        raise ValueError("Sample output must be separate from Phase 3 and evidence outputs")
    frame, hashes, diagnostics = build_frame(phase3_dir, evidence_corpus, pilot_units, human_codebook)
    frame_path = frame_dir / "validation_frame.csv"
    manifest = json.loads((frame_dir / "frame_manifest.json").read_text(encoding="utf-8"))
    stored_frame = read_csv(frame_path, set(FRAME_FIELDS))
    if (stored_frame != frame or manifest.get("status") != "frame_prepared_plan_pending"
            or manifest.get("frame_sha256") != sha_file(frame_path)
            or manifest.get("input_sha256") != hashes):
        raise ValueError("Prepared frame no longer matches frozen approved evidence and Phase 3")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    approvals = plan.get("approved_by")
    try:
        date.fromisoformat(plan.get("approval_date", ""))
    except (TypeError, ValueError) as exc:
        raise ValueError("Plan needs a valid author approval date") from exc
    seed = plan.get("selection_seed")
    target_rationales = plan.get("target_precision_rationale")
    expected_target_keys = {f"{row['target_type']}:{row['code']}" for row in frame}
    if (plan.get("schema_version") != 1 or plan.get("status") != "approved"
            or plan.get("frame_sha256") != sha_file(frame_path)
            or plan.get("input_sha256") != hashes
            or plan.get("short_word_limit_exclusive") != SHORT_WORD_LIMIT
            or plan.get("primary_estimands") != ["positive_predictive_value", "sensitivity"]
            or not isinstance(plan.get("precision_rationale"), str)
            or len(plan["precision_rationale"].strip()) < 20
            or not isinstance(target_rationales, dict)
            or set(target_rationales) != expected_target_keys
            or any(not isinstance(value, str) or len(value.strip()) < 20
                   for value in target_rationales.values())
            or plan.get("pilot_exclusions_finalized") is not True
            or plan.get("prior_exposure_overlap_status") not in {"mapped_and_excluded", "cannot_establish"}
            or not isinstance(plan.get("prior_exposure_audit_rationale"), str)
            or len(plan["prior_exposure_audit_rationale"].strip()) < 30
            or plan.get("target_definitions_frozen") is not True
            or not isinstance(approvals, list) or len(approvals) < 2
            or len({name.strip() for name in approvals if isinstance(name, str) and name.strip()}) < 2
            or isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**64):
        raise ValueError("Author-approved, hash-bound allocation plan is incomplete or invalid")
    groups = frame_strata(frame)
    allocation_rows = plan.get("allocations")
    if not isinstance(allocation_rows, list):
        raise ValueError("Plan allocations are missing")
    allocations = {}
    for row in allocation_rows:
        if not isinstance(row, dict) or any(field not in row for field in STRATUM_FIELDS):
            raise ValueError("Plan allocation has missing stratum fields")
        key = stratum(row)
        if key in allocations or key not in groups or row.get("frame_n") != len(groups[key]):
            raise ValueError("Plan allocation does not match the approved frame")
        n = row.get("sample_n")
        if isinstance(n, bool) or not isinstance(n, int) or not (1 <= n <= len(groups[key])):
            raise ValueError("Every nonempty stratum needs a valid positive sample quota")
        if len(groups[key]) > 1 and n < 2:
            raise ValueError("Non-census strata require at least two draws for design variance")
        allocations[key] = n
    if set(allocations) != set(groups):
        raise ValueError("Plan omits one or more nonempty predicted-status and length strata")

    selected = select_rows(groups, allocations, seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    machine, coder = [], []
    case_ids = set()
    for row, frame_n, sample_n in selected:
        case_id = "V" + secrets.token_hex(12)
        while case_id in case_ids:
            case_id = "V" + secrets.token_hex(12)
        case_ids.add(case_id)
        machine.append({
            "case_id": case_id, **row, "stratum_frame_n": frame_n,
            "stratum_sample_n": sample_n,
            "inclusion_probability": format(sample_n / frame_n, ".17g"),
            "analysis_weight": format(frame_n / sample_n, ".17g"),
        })
        coder.append({
            "case_id": case_id, "target_type": row["target_type"],
            "code": row["code"], "decision": "", "rationale": "", "flags": "",
        })
    machine_fields = ["case_id", *FRAME_FIELDS, "stratum_frame_n", "stratum_sample_n",
                      "inclusion_probability", "analysis_weight"]
    machine_path = output_dir / "coordinator_machine_key.csv"
    write_csv(machine_path, machine_fields, machine)
    for coder_name in ("coder_1_blank.csv", "coder_2_blank.csv"):
        write_csv(output_dir / coder_name, ["case_id", "target_type", "code", "decision", "rationale", "flags"], coder)
    write_csv(
        output_dir / "packet_manifest_template.csv",
        ["case_id", "target_type", "code", "source_unit_sha256", "packet_file", "packet_sha256",
         "privacy_reviewer", "context_reviewer", "packet_checked"],
        [{"case_id": row["case_id"], "target_type": row["target_type"],
          "code": row["code"], "source_unit_sha256": machine[index]["combined_text_sha256"],
          "packet_file": "", "packet_sha256": "",
          "privacy_reviewer": "", "context_reviewer": "", "packet_checked": ""}
         for index, row in enumerate(coder)],
    )
    report = {
        "status": "holdout_drawn_human_coding_pending", "article_ready": False,
        "frame_sha256": sha_file(frame_path), "plan_sha256": sha_file(plan_path),
        "input_sha256": hashes, "selection_seed": seed,
        "approved_by": approvals, "approval_date": plan["approval_date"],
        "prior_exposure_overlap_status": plan["prior_exposure_overlap_status"],
        "frame_diagnostics": diagnostics, "case_target_frame_n": len(frame),
        "sampled_case_target_n": len(machine),
        "sampled_unique_units_n": len({row["unit_id"] for row in machine}),
        "sampled_short_case_target_n": sum(row["length_band"] == "short" for row in machine),
        "sampled_by_source": dict(sorted(Counter(row["source"] for row in machine).items())),
        "sampled_by_modality": dict(sorted(Counter(row["modality"] for row in machine).items())),
        "strata_n": len(groups),
        "output_sha256": {path.name: sha_file(path) for path in sorted(output_dir.glob("*.csv"))},
        "packet_status": "controlled_evidence_packets_not_built",
        "human_decisions_complete": False,
        "performance_estimates_complete": False,
    }
    (output_dir / "selection_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command_name in ("prepare", "draw"):
        command = sub.add_parser(command_name)
        command.add_argument("--phase3-dir", required=True, type=Path)
        command.add_argument("--evidence-corpus", required=True, type=Path)
        command.add_argument("--pilot-units", required=True, type=Path)
        command.add_argument("--human-codebook", required=True, type=Path)
        command.add_argument("--output-dir", required=True, type=Path)
        if command_name == "draw":
            command.add_argument("--frame-dir", required=True, type=Path)
            command.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = (prepare(args.phase3_dir, args.evidence_corpus, args.pilot_units,
                          args.human_codebook, args.output_dir)
                  if args.command == "prepare" else
                  draw(args.phase3_dir, args.evidence_corpus, args.pilot_units,
                       args.human_codebook, args.frame_dir, args.plan, args.output_dir))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
