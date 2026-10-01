"""Audit exact repeated approved source spans and capture-unit signatures.

This is a controlled provisional sensitivity analysis. A repeated text
signature is not a count of duplicate posts, actors, or transactions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUALITY_FLAG = "market_access_limitation"
SENSITIVITY_FIELDS = [
    "target_type", "code", "approved_units_n", "approved_positive_units_n",
    "approved_positive_percent", "exact_span_signature_groups_n",
    "positive_signature_groups_n", "positive_signature_percent",
    "positive_excess_from_exact_repeats_n",
]
SOURCE_FIELDS = [
    "source", "approved_units_n", "exact_span_signature_groups_n",
    "exact_repeat_excess_units_n",
]


@dataclass
class CheckedRun:
    units: dict[str, dict[str, object]]
    predictions: dict[tuple[str, str, str], int]
    artifact_predictions: dict[tuple[str, str, str, str], int]
    targets: dict[str, set[str]]
    labels: dict[tuple[str, str], str]
    input_sha256: dict[str, str]
    evidence_manifest: dict[str, object]
    phase3_metadata: dict[str, object]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def outside_public(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT.resolve() in resolved.parents:
        raise ValueError("Revised evidence and sensitivity outputs must remain outside the public repository")
    return resolved


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Missing or duplicate CSV columns: {path.name}")
        if not required.issubset(reader.fieldnames):
            raise ValueError(f"Required CSV columns missing: {path.name}")
        return list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def count(value: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid nonnegative hit count") from exc
    if result < 0:
        raise ValueError("Negative hit count")
    return result


def codebook_labels(path: Path) -> dict[tuple[str, str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    section = "typology"
    labels: dict[tuple[str, str], str] = {}
    for index, line in enumerate(lines):
        if line == "# AML Indicator Candidates":
            section = "aml_candidate"
        elif line.startswith("## "):
            code = line[3:].strip()
            if (not code or index + 1 >= len(lines)
                    or not lines[index + 1].startswith("- Label: ")):
                raise ValueError("Revised Phase 3 codebook has an invalid target definition")
            label = lines[index + 1][len("- Label: "):].strip()
            key = (section, code)
            if not label or key in labels:
                raise ValueError("Revised Phase 3 codebook has a duplicate or blank target")
            labels[key] = label
    if not labels:
        raise ValueError("Revised Phase 3 codebook has no target definitions")
    return labels


def signature(artifacts: list[dict[str, object]]) -> str:
    """Hash the multiset of approved span contents and modality boundaries."""
    parts = sorted((str(item["kind"]), str(item["text_sha256"])) for item in artifacts)
    return sha_text(json.dumps(parts, ensure_ascii=False, separators=(",", ":")))


def sensitivity_rows(
    units: dict[str, dict[str, object]],
    predictions: dict[tuple[str, str, str], int],
    targets: dict[str, set[str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    groups: dict[str, list[str]] = defaultdict(list)
    source_groups: dict[str, list[str]] = defaultdict(list)
    artifact_contents: Counter[tuple[str, str]] = Counter()
    for unit_id, unit in units.items():
        sig = str(unit["signature"])
        groups[sig].append(unit_id)
        source_groups[str(unit["source"])].append(unit_id)
        for artifact in unit["artifacts"]:  # type: ignore[union-attr]
            artifact_contents[(str(artifact["kind"]), str(artifact["text_sha256"]))] += 1
    result = []
    for target_type, codes in sorted(targets.items()):
        for code in sorted(codes):
            positive_units = sum(predictions[(unit_id, target_type, code)] for unit_id in units)
            positive_signatures = 0
            for ids in groups.values():
                values = {predictions[(unit_id, target_type, code)] for unit_id in ids}
                if len(values) != 1:
                    raise ValueError("Identical approved-span signatures have conflicting deterministic predictions")
                positive_signatures += next(iter(values))
            result.append({
                "target_type": target_type, "code": code,
                "approved_units_n": len(units),
                "approved_positive_units_n": positive_units,
                "approved_positive_percent": format(100 * positive_units / len(units), ".6f"),
                "exact_span_signature_groups_n": len(groups),
                "positive_signature_groups_n": positive_signatures,
                "positive_signature_percent": format(100 * positive_signatures / len(groups), ".6f"),
                "positive_excess_from_exact_repeats_n": positive_units - positive_signatures,
            })
    by_source = []
    for source, ids in sorted(source_groups.items()):
        distinct = len({units[unit_id]["signature"] for unit_id in ids})
        by_source.append({
            "source": source, "approved_units_n": len(ids),
            "exact_span_signature_groups_n": distinct,
            "exact_repeat_excess_units_n": len(ids) - distinct,
        })
    report = {
        "approved_units_n": len(units),
        "exact_span_signature_groups_n": len(groups),
        "exact_repeat_excess_units_n": len(units) - len(groups),
        "cross_source_repeat_signature_groups_n": sum(
            len({units[unit_id]["source"] for unit_id in ids}) > 1
            for ids in groups.values()
        ),
        "approved_span_assignments_n": sum(artifact_contents.values()),
        "distinct_span_content_signatures_n": len(artifact_contents),
        "reused_span_content_signatures_n": sum(value > 1 for value in artifact_contents.values()),
        "article_ready": False,
    }
    return result, by_source, report


def load_checked_run(phase3_dir: Path, evidence_corpus: Path) -> CheckedRun:
    phase3_dir = outside_public(phase3_dir)
    evidence_corpus = outside_public(evidence_corpus)
    paths = {
        "evidence_corpus": evidence_corpus,
        "evidence_manifest": evidence_corpus.parent / "evidence_build_manifest.json",
        "phase3_metadata": phase3_dir / "run_metadata.json",
        "phase3_codebook": phase3_dir / "CODEBOOK_PHASE3.md",
        "phase3_combined": phase3_dir / "combined_corpus_with_ocr.csv",
        "phase3_typology": phase3_dir / "typology_coding_long.csv",
        "phase3_aml": phase3_dir / "aml_indicator_coding_long.csv",
        "phase3_artifacts": phase3_dir / "artifact_coding_long.csv",
    }
    hashes = {name: sha_file(path) for name, path in paths.items()}
    evidence_manifest = json.loads(paths["evidence_manifest"].read_text(encoding="utf-8"))
    metadata = json.loads(paths["phase3_metadata"].read_text(encoding="utf-8"))
    if not isinstance(evidence_manifest, dict) or not isinstance(metadata, dict):
        raise ValueError("Evidence and Phase 3 manifests must be JSON objects")
    if (evidence_manifest.get("schema_version") != 3
            or evidence_manifest.get("evidence_jsonl_sha256") != hashes["evidence_corpus"]
            or evidence_manifest.get("status") != "source_screening_complete_target_validation_pending"
            or evidence_manifest.get("article_ready") is not False
            or metadata.get("analysis_mode") != "author_reviewed_artifact_bounded_source_text"
            or metadata.get("evidence_corpus_sha256") != hashes["evidence_corpus"]
            or metadata.get("codebook_sha256") != hashes["phase3_codebook"]
            or metadata.get("artifact_coding_schema_version") != 1
            or metadata.get("article_ready") is not False
            or metadata.get("historical_human_validation_applicable") is not False):
        raise ValueError("A hash-matched provisional reviewed-evidence Phase 3 run is required")

    units: dict[str, dict[str, object]] = {}
    artifact_identity: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    with evidence_corpus.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("Approved evidence row must be a JSON object")
            unit_id, source, artifacts = row.get("note_id"), row.get("source"), row.get("artifacts")
            if (not isinstance(unit_id, str) or not unit_id or unit_id in units
                    or not isinstance(source, str) or not source.strip()
                    or not isinstance(artifacts, list) or not artifacts):
                raise ValueError("Approved evidence has an invalid or duplicate unit")
            checked = []
            for artifact in artifacts:
                if not isinstance(artifact, dict):
                    raise ValueError("Approved source span must be a JSON object")
                artifact_id, kind, value = artifact.get("artifact_id"), artifact.get("kind"), artifact.get("text")
                if (not isinstance(artifact_id, str) or not artifact_id
                        or (unit_id, artifact_id) in artifact_identity
                        or kind not in {"markdown_source_span", "image_ocr"}
                        or not isinstance(value, str) or not value.strip()
                        or artifact.get("text_sha256") != sha_text(value)
                        or not isinstance(artifact.get("collection_date"), str)):
                    raise ValueError("Approved evidence has an invalid or duplicate source span")
                artifact_identity[(unit_id, artifact_id)] = (
                    kind, source, str(artifact["collection_date"]), str(artifact["text_sha256"])
                )
                checked.append(artifact)
            dates = {item["collection_date"] for item in checked}
            expected_unit_date = next(iter(dates)) if len(dates) == 1 and "" not in dates else ""
            if row.get("collection_date") != expected_unit_date:
                raise ValueError("Approved unit date disagrees with its source-span dates")
            units[unit_id] = {
                "source": source, "collection_date": row.get("collection_date"),
                "artifacts": checked, "signature": signature(checked),
                "joined_text": "\n\n".join(str(item["text"]) for item in checked),
            }
    if not units or len(units) != evidence_manifest.get("approved_evidence_units") or len(units) != metadata.get("note_count"):
        raise ValueError("Approved unit count differs from screening or Phase 3")
    if len(artifact_identity) != metadata.get("approved_source_artifacts"):
        raise ValueError("Approved span count differs from Phase 3")

    combined = read_csv(paths["phase3_combined"], {
        "note_id", "source", "collection_date", "combined_text", "combined_text_sha256",
    })
    seen_units = set()
    for row in combined:
        unit_id = row["note_id"]
        if unit_id not in units or unit_id in seen_units:
            raise ValueError("Revised combined table has an invalid or duplicate unit")
        seen_units.add(unit_id)
        unit = units[unit_id]
        if (row["source"] != unit["source"] or row["collection_date"] != unit["collection_date"]
                or row["combined_text"] != unit["joined_text"]
                or row["combined_text_sha256"] != sha_text(row["combined_text"])):
            raise ValueError("Revised combined text differs from approved spans")
    if seen_units != set(units):
        raise ValueError("Revised combined table omits approved units")

    predictions: dict[tuple[str, str, str], int] = {}
    hits: dict[tuple[str, str, str], int] = {}
    targets: dict[str, set[str]] = defaultdict(set)
    labels: dict[tuple[str, str], str] = {}
    for target_type, path, code_field in (
        ("typology", paths["phase3_typology"], "code"),
        ("aml_candidate", paths["phase3_aml"], "aml_indicator"),
    ):
        for row in read_csv(path, {"note_id", "source", "collection_date", code_field, "label", "present", "hit_count"}):
            unit_id, code = row["note_id"], row[code_field]
            key = (unit_id, target_type, code)
            n = count(row["hit_count"])
            label_key = (target_type, code)
            if (unit_id not in units or row["source"] != units[unit_id]["source"]
                    or row["collection_date"] != units[unit_id]["collection_date"]
                    or not code or key in predictions or row["present"] not in {"0", "1"}
                    or int(row["present"]) != int(n > 0) or not row["label"].strip()
                    or (label_key in labels and labels[label_key] != row["label"])):
                raise ValueError("Revised target matrix has invalid unit, source, date, or prediction")
            predictions[key], hits[key] = int(row["present"]), n
            targets[target_type].add(code)
            labels[label_key] = row["label"]
    if (len(targets["typology"]) != metadata.get("typology_code_count")
            or len(targets["aml_candidate"]) != metadata.get("aml_indicator_count")
            or QUALITY_FLAG not in targets["typology"]):
        raise ValueError("Revised target inventory differs from Phase 3 metadata")
    expected = {
        (unit_id, target_type, code)
        for unit_id in units for target_type, codes in targets.items() for code in codes
    }
    if set(predictions) != expected:
        raise ValueError("Revised target matrix omits an approved unit-target row")
    if labels != codebook_labels(paths["phase3_codebook"]):
        raise ValueError("Revised target labels or inventory disagree with the generated codebook")

    artifact_hits: Counter[tuple[str, str, str]] = Counter()
    artifact_predictions: dict[tuple[str, str, str, str], int] = {}
    seen_artifact_targets = set()
    for row in read_csv(paths["phase3_artifacts"], {
        "unit_id", "artifact_id", "artifact_kind", "source", "collection_date",
        "target_type", "code", "present", "hit_count", "artifact_text_sha256",
    }):
        unit_id, artifact_id = row["unit_id"], row["artifact_id"]
        target_type, code = row["target_type"], row["code"]
        key = (unit_id, artifact_id, target_type, code)
        n = count(row["hit_count"])
        if (key in seen_artifact_targets or (unit_id, artifact_id) not in artifact_identity
                or code not in targets.get(target_type, set())
                or (row["artifact_kind"], row["source"], row["collection_date"], row["artifact_text_sha256"])
                != artifact_identity[(unit_id, artifact_id)]
                or row["present"] not in {"0", "1"} or int(row["present"]) != int(n > 0)):
            raise ValueError("Revised artefact matrix has invalid identity or prediction")
        seen_artifact_targets.add(key)
        artifact_predictions[key] = int(row["present"])
        artifact_hits[(unit_id, target_type, code)] += n
    if (len(seen_artifact_targets) != metadata.get("artifact_coding_rows")
            or len(seen_artifact_targets) != len(artifact_identity) * sum(map(len, targets.values()))
            or any(artifact_hits[key] != value for key, value in hits.items())):
        raise ValueError("Revised artefact hits do not reconcile to unit coding")

    return CheckedRun(units, predictions, artifact_predictions, dict(targets), labels,
                      hashes, evidence_manifest, metadata)


def build(phase3_dir: Path, evidence_corpus: Path, output_dir: Path) -> dict[str, object]:
    phase3_dir = outside_public(phase3_dir)
    evidence_corpus = outside_public(evidence_corpus)
    output_dir = outside_public(output_dir)
    if (output_dir == phase3_dir or output_dir in phase3_dir.parents
            or phase3_dir in output_dir.parents or output_dir == evidence_corpus.parent
            or output_dir in evidence_corpus.parents
            or evidence_corpus.parent in output_dir.parents):
        raise ValueError("Sensitivity output must be separate from controlled inputs")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Sensitivity output directory is not empty")
    checked = load_checked_run(phase3_dir, evidence_corpus)

    substantive_targets = {
        "typology": checked.targets["typology"] - {QUALITY_FLAG},
        "aml_candidate": checked.targets["aml_candidate"],
    }
    rows, sources, report = sensitivity_rows(checked.units, checked.predictions, substantive_targets)
    report.update({
        "status": "provisional_exact_span_signature_sensitivity",
        "method": "exact multiset of approved (modality, text SHA-256) spans per capture unit",
        "analysis_script_sha256": sha_file(Path(__file__)),
        "method_document_sha256": sha_file(Path(__file__).with_name("METHODS_REVISED_DUPLICATE_SENSITIVITY.md")),
        "historical_mixed_note_duplicate_count_comparable": False,
        "input_sha256": checked.input_sha256,
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    sensitivity_path = output_dir / "revised_duplicate_sensitivity_controlled.csv"
    source_path = output_dir / "revised_source_signature_summary_controlled.csv"
    write_csv(sensitivity_path, SENSITIVITY_FIELDS, rows)
    write_csv(source_path, SOURCE_FIELDS, sources)
    report["output_sha256"] = {
        sensitivity_path.name: sha_file(sensitivity_path),
        source_path.name: sha_file(source_path),
    }
    (output_dir / "revised_duplicate_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-dir", type=Path, required=True)
    parser.add_argument("--evidence-corpus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = build(args.phase3_dir, args.evidence_corpus, args.output_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in (
        "status", "approved_units_n", "exact_span_signature_groups_n",
        "exact_repeat_excess_units_n", "article_ready",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
