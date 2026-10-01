"""Count revised typology pairs within approved spans and across capture units.

Inputs and outputs remain controlled. The resulting counts are provisional
until corpus, construct, OCR, and human-validation gates are complete.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUALITY_FLAG = "market_access_limitation"
ARTIFACT_FIELDS = [
    "unit_id", "artifact_id", "artifact_kind", "source", "collection_date",
    "target_type", "code", "present", "hit_count", "pattern_count",
    "artifact_word_count", "artifact_text_sha256",
]
PAIR_FIELDS = [
    "scope", "source", "approved_units_n", "approved_artifacts_n",
    "code_a", "code_b", "units_with_both_codes_n",
    "units_with_both_in_same_artifact_n", "cross_artifact_only_units_n",
    "artifacts_with_both_codes_n",
]


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f"Missing or duplicate columns in {path.name}")
        if not required.issubset(reader.fieldnames):
            raise ValueError(f"Required columns missing in {path.name}")
        return list(reader)


def nonnegative(value: str, label: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid count in {label}") from exc
    if number < 0:
        raise ValueError(f"Negative count in {label}")
    return number


def outside_public(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT.resolve() in resolved.parents:
        raise ValueError("Revised record-level inputs and outputs must remain outside the public repository")
    return resolved


def build(phase3_dir: Path, evidence_corpus: Path, output_dir: Path) -> dict[str, object]:
    phase3_dir = outside_public(phase3_dir)
    evidence_corpus = outside_public(evidence_corpus)
    output_dir = outside_public(output_dir)
    if output_dir == phase3_dir or output_dir in phase3_dir.parents or phase3_dir in output_dir.parents:
        raise ValueError("Pair outputs must be separate from controlled Phase 3 inputs")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Pair output directory is not empty")
    meta_path = phase3_dir / "run_metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    if (metadata.get("analysis_mode") != "author_reviewed_artifact_bounded_source_text"
            or metadata.get("artifact_coding_schema_version") != 1
            or metadata.get("article_ready") is not False
            or metadata.get("historical_human_validation_applicable") is not False):
        raise ValueError("A provisional reviewed-evidence Phase 3 run is required")
    evidence_sha = sha_file(evidence_corpus)
    evidence_manifest_path = evidence_corpus.parent / "evidence_build_manifest.json"
    evidence_manifest = json.loads(evidence_manifest_path.read_text(encoding="utf-8"))
    if (metadata.get("evidence_corpus_sha256") != evidence_sha
            or evidence_manifest.get("evidence_jsonl_sha256") != evidence_sha
            or evidence_manifest.get("schema_version") != 3
            or evidence_manifest.get("status") != "source_screening_complete_target_validation_pending"):
        raise ValueError("Approved evidence corpus hash or screening manifest does not match Phase 3")
    evidence_units = {}
    evidence_artifacts = {}
    with evidence_corpus.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            unit_id = row.get("note_id")
            if not unit_id or unit_id in evidence_units:
                raise ValueError("Approved evidence has missing or duplicate unit IDs")
            evidence_units[unit_id] = (row.get("source"), row.get("collection_date"))
            for artifact in row.get("artifacts", []):
                key = (unit_id, artifact.get("artifact_id"))
                if not key[1] or key in evidence_artifacts:
                    raise ValueError("Approved evidence has missing or duplicate span IDs")
                evidence_artifacts[key] = (
                    artifact.get("kind"), row.get("source"),
                    artifact.get("collection_date"), artifact.get("text_sha256")
                )
    if len(evidence_units) != evidence_manifest.get("approved_evidence_units"):
        raise ValueError("Approved evidence unit count differs from screening manifest")

    combined_path = phase3_dir / "combined_corpus_with_ocr.csv"
    typology_path = phase3_dir / "typology_coding_long.csv"
    aml_path = phase3_dir / "aml_indicator_coding_long.csv"
    artifact_path = phase3_dir / "artifact_coding_long.csv"
    units = {}
    unit_dates = {}
    for row in read_csv(combined_path, {"note_id", "source", "collection_date"}):
        unit_id = row["note_id"]
        if not unit_id or unit_id in units or not row["source"].strip():
            raise ValueError("Missing or duplicate approved unit identity")
        units[unit_id] = row["source"]
        unit_dates[unit_id] = row["collection_date"]
    if len(units) != metadata.get("note_count") or not units:
        raise ValueError("Approved unit count does not match revised Phase 3")
    if set(units) != set(evidence_units) or any(
        (units[key], unit_dates[key]) != evidence_units[key] for key in units
    ):
        raise ValueError("Revised Phase 3 units differ from approved evidence")

    note_targets: dict[tuple[str, str, str], tuple[int, int]] = {}
    codes: dict[str, set[str]] = defaultdict(set)
    for target_type, path, code_field in (
        ("typology", typology_path, "code"),
        ("aml_candidate", aml_path, "aml_indicator"),
    ):
        for row in read_csv(path, {"note_id", "source", code_field, "present", "hit_count"}):
            unit_id, code = row["note_id"], row[code_field]
            key = (unit_id, target_type, code)
            if unit_id not in units or row["source"] != units[unit_id] or not code or key in note_targets:
                raise ValueError("Revised unit coding has missing, conflicting, or duplicate targets")
            hits = nonnegative(row["hit_count"], "unit coding")
            if row["present"] not in {"0", "1"} or int(row["present"]) != int(hits > 0):
                raise ValueError("Revised unit coding presence disagrees with hit count")
            note_targets[key] = (int(row["present"]), hits)
            codes[target_type].add(code)
    if (len(codes["typology"]) != metadata.get("typology_code_count")
            or len(codes["aml_candidate"]) != metadata.get("aml_indicator_count")
            or QUALITY_FLAG not in codes["typology"]
            or len(codes["typology"] - {QUALITY_FLAG}) != metadata.get("substantive_typology_code_count")):
        raise ValueError("Target code inventory differs from revised Phase 3 metadata")
    expected_note_targets = {
        (unit_id, target_type, code)
        for unit_id in units for target_type, target_codes in codes.items()
        for code in target_codes
    }
    if set(note_targets) != expected_note_targets:
        raise ValueError("Revised unit coding omits an approved unit-target row")

    artifact_rows = read_csv(artifact_path, set(ARTIFACT_FIELDS))
    if len(artifact_rows) != metadata.get("artifact_coding_rows"):
        raise ValueError("Artifact coding row count differs from revised Phase 3 metadata")
    artifacts: dict[tuple[str, str], dict[str, object]] = {}
    summed_hits: dict[tuple[str, str, str], int] = defaultdict(int)
    for row in artifact_rows:
        unit_id, artifact_id = row["unit_id"], row["artifact_id"]
        target_type, code = row["target_type"], row["code"]
        if (unit_id not in units or not artifact_id or row["source"] != units[unit_id]
                or target_type not in codes or code not in codes[target_type]
                or row["artifact_kind"] not in {"markdown_source_span", "image_ocr"}
                or re.fullmatch(r"[0-9a-f]{64}", row["artifact_text_sha256"]) is None):
            raise ValueError("Artifact coding has invalid identity, source, or target")
        hits = nonnegative(row["hit_count"], "artifact hits")
        patterns = nonnegative(row["pattern_count"], "artifact patterns")
        nonnegative(row["artifact_word_count"], "artifact words")
        if row["present"] not in {"0", "1"} or int(row["present"]) != int(hits > 0) or bool(patterns) != bool(hits):
            raise ValueError("Artifact coding presence, patterns, and hits disagree")
        key = (unit_id, artifact_id)
        identity = (row["artifact_kind"], row["source"], row["collection_date"], row["artifact_word_count"], row["artifact_text_sha256"])
        if evidence_artifacts.get(key) != (
            row["artifact_kind"], row["source"],
            row["collection_date"], row["artifact_text_sha256"]
        ):
            raise ValueError("Artifact coding identity differs from approved evidence")
        artifact = artifacts.setdefault(key, {"identity": identity, "targets": {}})
        if artifact["identity"] != identity or (target_type, code) in artifact["targets"]:
            raise ValueError("Artifact has conflicting identity or duplicate target rows")
        artifact["targets"][(target_type, code)] = hits
        summed_hits[(unit_id, target_type, code)] += hits
    expected_artifact_targets = {(target_type, code) for target_type, target_codes in codes.items() for code in target_codes}
    if len(artifacts) != metadata.get("approved_source_artifacts") or not artifacts:
        raise ValueError("Approved artifact count does not match revised Phase 3")
    if set(artifacts) != set(evidence_artifacts):
        raise ValueError("Revised Phase 3 artifact set differs from approved evidence")
    if any(set(artifact["targets"]) != expected_artifact_targets for artifact in artifacts.values()):
        raise ValueError("Artifact coding omits a target row")
    if any(summed_hits[key] != hits for key, (_, hits) in note_targets.items()):
        raise ValueError("Artifact hits do not reconcile with unit-level coding")

    substantive = sorted(codes["typology"] - {QUALITY_FLAG})
    sources = sorted(set(units.values()))
    scopes = [("all", "", set(units))] + [
        ("source", source, {unit_id for unit_id, unit_source in units.items() if unit_source == source})
        for source in sources
    ]
    pair_rows = []
    for scope, source, scope_units in scopes:
        scope_artifacts = {key for key in artifacts if key[0] in scope_units}
        unit_presence = {
            code: {unit_id for unit_id in scope_units if note_targets[(unit_id, "typology", code)][0]}
            for code in substantive
        }
        artifact_presence = {
            code: {key for key in scope_artifacts if artifacts[key]["targets"][("typology", code)] > 0}
            for code in substantive
        }
        for code_a, code_b in combinations(substantive, 2):
            both_units = unit_presence[code_a] & unit_presence[code_b]
            both_artifacts = artifact_presence[code_a] & artifact_presence[code_b]
            same_artifact_units = {key[0] for key in both_artifacts}
            if not same_artifact_units.issubset(both_units):
                raise ValueError("Same-artifact pair does not reconcile with unit-level coding")
            pair_rows.append({
                "scope": scope,
                "source": source,
                "approved_units_n": len(scope_units),
                "approved_artifacts_n": len(scope_artifacts),
                "code_a": code_a,
                "code_b": code_b,
                "units_with_both_codes_n": len(both_units),
                "units_with_both_in_same_artifact_n": len(same_artifact_units),
                "cross_artifact_only_units_n": len(both_units - same_artifact_units),
                "artifacts_with_both_codes_n": len(both_artifacts),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "revised_typology_pair_boundaries.csv"
    with result_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        writer.writerows(pair_rows)
    report = {
        "status": "provisional_artifact_boundary_diagnostic_not_article_ready",
        "article_ready": False,
        "historical_human_validation_applicable": False,
        "approved_units_n": len(units),
        "approved_artifacts_n": len(artifacts),
        "substantive_typology_codes_n": len(substantive),
        "source_groups_n": len(sources),
        "pair_rows_n": len(pair_rows),
        "evidence_corpus_sha256": evidence_sha,
        "input_sha256": {
            path.name: sha_file(path)
            for path in (evidence_corpus, evidence_manifest_path, meta_path,
                         combined_path, typology_path, aml_path, artifact_path)
        },
        "pair_table_sha256": sha_file(result_path),
        "interpretive_boundary": "Counts describe approved text spans and capture units, not unique posts, actors, transactions, or coordination. Pair claims require target validation and source/duplicate sensitivity review.",
    }
    (output_dir / "revised_typology_pair_manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase3-dir", required=True, type=Path)
    parser.add_argument("--evidence-corpus", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = build(args.phase3_dir, args.evidence_corpus, args.output_dir)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
