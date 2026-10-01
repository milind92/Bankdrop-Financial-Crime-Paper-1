"""Check the simple controlled packet and score two real independent author sheets.

Examples (run in this folder):
  py -3.14 score_simple_icr.py --check-packet
  py -3.14 score_simple_icr.py --self-test
  py -3.14 score_simple_icr.py --milind Milind_completed.csv --ausma Ausma_completed.csv
  py -3.14 score_simple_icr.py --milind Milind_completed.csv --ausma Ausma_completed.csv --adjudicated scoring_results/adjudication_completed.csv

For a public checkout, pass --packet-dir and --output-dir pointing to controlled
storage. The blank sheets are never interpreted as results. The coordinator key is kept
outside the shareable packet; all scoring outputs stay in controlled storage.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEY = HERE.parent / "coordinator_private" / "simple_icr_coordinator_key.csv"
ALLOWED = {"present", "absent", "ambiguous", "unreadable", "out_of_scope"}
TARGETS = {"bank_drop_sale", "bank_log_sale", "fullz_identity_package",
           "email_access_takeover", "bank_log_plus_email_access"}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, records: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(records[0]) if records else [])
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def kappa(first: list[str], second: list[str]) -> float | None:
    assert len(first) == len(second), "Reliability requires complete paired answers"
    assert set(first) | set(second) <= ALLOWED, "Unknown answer category"
    if not first:
        return None
    observed = sum(a == b for a, b in zip(first, second)) / len(first)
    a, b = Counter(first), Counter(second)
    expected = sum(a[c] * b[c] for c in ALLOWED) / len(first) ** 2
    return None if math.isclose(expected, 1) else (observed - expected) / (1 - expected)


def packet_check() -> tuple[list[dict[str, str]], dict]:
    assert KEY.is_file(), "Private coordinator key is required on the coordinator computer"
    manifest = json.loads((HERE / "packet_manifest.json").read_text(encoding="utf-8"))
    key = read(KEY)
    assert len(key) == manifest["case_target_rows_per_author"] == 249
    assert len({r["item_id"] for r in key}) == len(key)
    assert {r["target"] for r in key} == TARGETS
    assert len({r["image_sha256"] for r in key}) == manifest["distinct_images"] == 205
    assert sha(KEY) == manifest["private_key_sha256"]
    assert sum(int(r["prior_packet_exposure"]) for r in key) == manifest["prior_packet_exposed_assignments"]
    assert sha(HERE.parent / "results" / "image_level_matrix_controlled.csv") == manifest["frame_sha256"]
    by_id = {r["item_id"]: r for r in key}
    for author in ("Milind", "Ausma"):
        path = HERE / f"{author}_sheet.csv"
        assert sha(path) == manifest[f"{author}_sheet_sha256"]
        sheet = read(path)
        assert len(sheet) == len(key)
        assert {r["item_id"] for r in sheet} == set(by_id)
        for row in sheet:
            master = by_id[row["item_id"]]
            assert all(row[field] == master[field] for field in
                       ("image_id", "image_file", "target", "question"))
            assert row["decision"] == row["reason"] == ""
        page = (HERE / f"{author}_review.html").read_text(encoding="utf-8")
        assert "machine_positive" not in page and "stratum_population_n" not in page
        data = re.search(r'<script id="packet" type="application/json">(.*?)</script>', page, re.S)
        assert data
        display = json.loads(data.group(1))
        assert display["name"] == author and display["rows"] == sheet, "Viewer and blank sheet differ"
        script = re.search(r"<script>\s*(.*?)\s*</script>", page, re.S)
        assert script
        checked = subprocess.run(["node", "--check", "-"], input=script.group(1),
                                 text=True, capture_output=True)
        assert checked.returncode == 0, checked.stderr
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for row in key:
        assert row["machine_positive"] in {"0", "1"}
        assert row["ocr_length"] in {"short", "long"}
        assert row["prior_packet_exposure"] in {"0", "1"}
        assert row["image_id"] == "I" + row["image_sha256"][:16]
        assert row["image_file"] == f"images/{row['image_id']}.png"
        n, N = int(row["stratum_sample_n"]), int(row["stratum_population_n"])
        assert 0 < n <= N
        strata[(row["target"], row["machine_positive"], row["ocr_length"],
                row["prior_packet_exposure"])].append(row)
    for group in strata.values():
        assert len({(r["stratum_population_n"], r["stratum_sample_n"]) for r in group}) == 1
        assert len(group) == int(group[0]["stratum_sample_n"])
        assert len({r["image_sha256"] for r in group}) == len(group)
    for target in TARGETS:
        assert sum(int(group[0]["stratum_population_n"]) for stratum, group in strata.items()
                   if stratum[0] == target) == 1037
    for digest, filename in {(r["image_sha256"], r["image_file"]) for r in key}:
        assert sha(HERE / filename) == digest
    assert len(list((HERE / "images").glob("*.png"))) == 205
    assert not (HERE / "simple_icr_coordinator_key.csv").exists()
    return key, manifest


def author_answers(path: Path, key: dict[str, dict]) -> dict[str, dict]:
    sheet = read(path)
    assert len(sheet) == len(key), "Every assigned item needs one row"
    result = {}
    for row in sheet:
        item = row["item_id"]
        assert item in key and item not in result
        assert all(row[field] == key[item][field] for field in
                   ("image_id", "image_file", "target", "question"))
        decision = row["decision"].strip().lower()
        assert decision in ALLOWED, (path.name, item, decision)
        result[item] = {"decision": decision, "reason": row.get("reason", "")}
    return result


def agreement(key: list[dict], first: dict, second: dict) -> list[dict]:
    groups = {"all_five_targets": key}
    groups.update({target: [r for r in key if r["target"] == target]
                   for target in sorted(TARGETS)})
    output = []
    for target, rows in groups.items():
        a = [first[r["item_id"]]["decision"] for r in rows]
        b = [second[r["item_id"]]["decision"] for r in rows]
        binary = [(x, y) for x, y in zip(a, b)
                  if x in {"present", "absent"} and y in {"present", "absent"}]
        output.append({"target": target, "paired_items": len(rows),
                       "five_category_agreements": sum(x == y for x, y in zip(a, b)),
                       "five_category_percent_agreement": round(sum(x == y for x, y in zip(a, b)) / len(rows), 6),
                       "five_category_cohens_kappa": "" if kappa(a, b) is None else round(kappa(a, b), 6),
                       "paired_binary_evaluable": len(binary),
                       "binary_agreements": sum(x == y for x, y in binary),
                       "Milind_present": a.count("present"), "Ausma_present": b.count("present"),
                       "Milind_nonbinary": sum(x not in {"present", "absent"} for x in a),
                       "Ausma_nonbinary": sum(x not in {"present", "absent"} for x in b)})
    return output


def weighted_cells(sample: list[dict]) -> Counter:
    cells = Counter()
    for row in sample:
        weight = int(row["stratum_population_n"]) / int(row["stratum_sample_n"])
        decision = row["final_decision"]
        if decision == "present":
            cell = "tp" if row["machine_positive"] == "1" else "fn"
        elif decision == "absent":
            cell = "fp" if row["machine_positive"] == "1" else "tn"
        else:
            cell = decision
        cells[cell] += weight
    return cells


def ratios(cells: Counter) -> dict[str, float | None]:
    tp, fp, tn, fn = (cells[x] for x in ("tp", "fp", "tn", "fn"))
    def ratio(n, d):
        return n / d if d else None
    return {"positive_predictive_value": ratio(tp, tp + fp),
            "negative_predictive_value": ratio(tn, tn + fn),
            "sensitivity": ratio(tp, tp + fn),
            "specificity": ratio(tn, tn + fp)}


def uncertainty(sample: list[dict], iterations=1000) -> dict[str, tuple]:
    """Descriptive percentile intervals from seeded within-stratum resampling."""
    groups = defaultdict(list)
    for row in sample:
        groups[(row["machine_positive"], row["ocr_length"], row["prior_packet_exposure"])].append(row)
    rng = random.Random(20261002)
    values = defaultdict(list)
    for _ in range(iterations):
        draw = []
        for group in groups.values():
            if len(group) == int(group[0]["stratum_population_n"]):
                draw.extend(group)
            else:
                draw.extend(rng.choices(group, k=len(group)))
        for metric, value in ratios(weighted_cells(draw)).items():
            if value is not None:
                values[metric].append(value)
    result = {}
    for name in ratios(Counter()):
        ordered = sorted(values[name])
        result[name] = ((ordered[int(.025 * (len(ordered) - 1))],
                         ordered[int(.975 * (len(ordered) - 1))])
                        if len(ordered) >= iterations * .9 else (None, None))
    return result


def validation(key: list[dict], decisions: dict[str, str]) -> list[dict]:
    output = []
    for target in sorted(TARGETS):
        sample = [dict(r, final_decision=decisions[r["item_id"]])
                  for r in key if r["target"] == target]
        cells = weighted_cells(sample)
        strata = {(r["machine_positive"], r["ocr_length"], r["prior_packet_exposure"]):
                  int(r["stratum_population_n"]) for r in sample}
        assert sum(strata.values()) == 1037 and math.isclose(sum(cells.values()), 1037, abs_tol=1e-6)
        record = {"target": target, "sample_items": len(sample),
                  "rule_positive_images": sum(n for s, n in strata.items() if s[0] == "1"),
                  "rule_negative_images": sum(n for s, n in strata.items() if s[0] == "0")}
        for cell in ("tp", "fp", "tn", "fn", "ambiguous", "unreadable", "out_of_scope"):
            record["weighted_" + cell] = round(cells[cell], 3)
        intervals = uncertainty(sample)
        for metric, value in ratios(cells).items():
            record[metric] = "" if value is None else round(value, 5)
            lo, hi = intervals[metric]
            record[metric + "_bootstrap_low"] = "" if lo is None else round(lo, 5)
            record[metric + "_bootstrap_high"] = "" if hi is None else round(hi, 5)
        output.append(record)
    return output


def final_answers(disputed: list[dict], key: dict, first: dict,
                  supplied: list[dict]) -> dict[str, str]:
    """Validate complete adjudication provenance before using any final labels."""
    expected = {r["item_id"]: r for r in disputed}
    assert len(supplied) == len(expected), "Resolve every disagreement/nonbinary pair"
    resolved = {}
    for row in supplied:
        item = row["item_id"]
        assert item in expected and item not in resolved, "Unexpected/duplicate adjudication"
        assert all(row.get(field) == value for field, value in expected[item].items()
                   if field not in {"final_decision", "final_reason"}), "Adjudication identity or original response changed"
        decision = row["final_decision"].strip().lower()
        assert decision in ALLOWED, "Invalid final category"
        assert row.get("final_reason", "").strip(), "A final decision needs a recorded reason"
        resolved[item] = decision
    return {item: resolved.get(item, first[item]["decision"]) for item in key}


def main() -> None:
    global HERE, KEY
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", type=Path, default=HERE,
                        help="Controlled simple_icr folder; required when running from the public checkout")
    parser.add_argument("--output-dir", type=Path,
                        help="Controlled score directory; defaults to packet-dir/scoring_results")
    parser.add_argument("--check-packet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--milind", type=Path)
    parser.add_argument("--ausma", type=Path)
    parser.add_argument("--adjudicated", type=Path)
    args = parser.parse_args()
    HERE = args.packet_dir.resolve()
    KEY = HERE.parent / "coordinator_private" / "simple_icr_coordinator_key.csv"
    output = (args.output_dir or HERE / "scoring_results").resolve()
    public_root = Path(__file__).resolve().parents[2]
    if (public_root / "workflow_manifest.json").is_file():
        assert not HERE.is_relative_to(public_root), "The source packet must remain outside the public repository"
        assert not output.is_relative_to(public_root), "Scoring outputs must remain outside the public repository"
    key, _ = packet_check()
    print("Packet verified: 249 items per author, 205 original screenshots, five targets")
    if args.self_test:
        assert kappa(["present", "absent"], ["present", "absent"]) == 1
        assert kappa(["present", "present", "absent", "absent"],
                     ["present", "absent", "present", "absent"]) == 0
        assert weighted_cells([{"stratum_population_n": "2", "stratum_sample_n": "1",
                                "final_decision": "present", "machine_positive": "1"}])["tp"] == 2
        synthetic = {r["item_id"]: "absent" for r in key}
        assert len(validation(key, synthetic)) == 5
        print("Synthetic arithmetic check passed; no author results written")
        return
    if args.check_packet:
        return
    if not args.milind or not args.ausma:
        parser.error("Supply both completed author CSV files, or --check-packet")
    by_id = {r["item_id"]: r for r in key}
    milind = author_answers(args.milind, by_id)
    ausma = author_answers(args.ausma, by_id)
    agreement_file = output / "intercoder_agreement.csv"
    agreement_rows = agreement(key, milind, ausma)
    disputed = []
    for row in key:
        item = row["item_id"]
        a, b = milind[item], ausma[item]
        if a["decision"] != b["decision"] or a["decision"] not in {"present", "absent"}:
            disputed.append({"item_id": item, "image_id": row["image_id"],
                             "image_file": row["image_file"], "target": row["target"],
                             "Milind_decision": a["decision"], "Milind_reason": a["reason"],
                             "Ausma_decision": b["decision"], "Ausma_reason": b["reason"],
                             "final_decision": "", "final_reason": ""})
    columns = ["item_id", "image_id", "image_file", "target", "Milind_decision",
               "Milind_reason", "Ausma_decision", "Ausma_reason", "final_decision", "final_reason"]
    template = output / "adjudication_template.csv"
    metrics_file = output / "weighted_rule_validation.csv"
    manifest_file = output / "scoring_manifest.json"
    destinations = {p.resolve() for p in (agreement_file, template, metrics_file, manifest_file)}
    for source in (args.milind, args.ausma, args.adjudicated):
        assert source is None or source.resolve() not in destinations, "A scoring input cannot be an output file"
    validation_rows = None
    if args.adjudicated:
        final = final_answers(disputed, by_id, milind, read(args.adjudicated))
        validation_rows = validation(key, final)
    # No derived output is written until every supplied input has been checked.
    output.mkdir(parents=True, exist_ok=True)
    write(agreement_file, agreement_rows)
    write(template, disputed, columns)
    if validation_rows is not None:
        write(metrics_file, validation_rows)
    elif metrics_file.exists():
        metrics_file.unlink()
    manifest = {"status": "adjudicated validation calculated" if args.adjudicated
                else "independent agreement calculated; adjudication pending",
                "Milind_completed_sha256": sha(args.milind),
                "Ausma_completed_sha256": sha(args.ausma),
                "adjudicated_sha256": sha(args.adjudicated) if args.adjudicated else None,
                "agreement_sha256": sha(agreement_file), "adjudication_template_sha256": sha(template),
                "weighted_rule_validation_sha256": sha(metrics_file) if args.adjudicated else None,
                "scorer_sha256": sha(Path(__file__)),
                "private_key_sha256": sha(KEY),
                "packet_manifest_sha256": sha(HERE / "packet_manifest.json"),
                "uncertainty": "1,000 seeded within-stratum resamples; descriptive percentile intervals"}
    manifest_file.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest["status"])


if __name__ == "__main__":
    main()
