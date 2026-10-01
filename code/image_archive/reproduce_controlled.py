"""Controlled, reproducible screenshot-level Paper 1 analysis.

Run with: python reproduce_controlled.py --vault ... --source-zip ... --audit-dir ... --legacy-icr-dir ... --output-dir ...
No third-party package, network service, or generative model is used.
The archival OCR is an input; this program does not claim to verify transcription.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import random
import re
import shutil
import sys
import zipfile
import statistics
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree as ET


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CODER = REPO / "code" / "phase3_typology_coding" / "run_phase3_typology.py"
VAULT = SOURCE_ZIP = OLD_ICR = AUDIT = PHASE1 = PHASE2 = PHASE3 = OUT = None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_rules():
    spec = importlib.util.spec_from_file_location("paper1_phase3_rules", CODER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def one_binary(text: str, patterns: list[re.Pattern]) -> tuple[int, int, int]:
    matched = [len(list(p.finditer(text))) for p in patterns]
    return int(any(matched)), sum(matched), sum(n > 0 for n in matched)


def load_prior_exposure() -> tuple[set[str], dict]:
    """Conservatively map PNG basenames that appeared in either July coder packet."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    names: set[str] = set()
    summary = {}
    for path in sorted(OLD_ICR.glob("*.xlsx")):
        with zipfile.ZipFile(path) as zf:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in zf.namelist():
                xml = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                shared = ["".join(e.itertext()) for e in xml.findall("m:si", ns)]
            xml = ET.fromstring(zf.read("xl/worksheets/sheet5.xml"))
            count = 0
            for row in xml.findall(".//m:sheetData/m:row", ns):
                value = ""
                for cell in row.findall("m:c", ns):
                    if not cell.attrib.get("r", "").startswith("B"):
                        continue
                    kind = cell.attrib.get("t", "")
                    raw = cell.find("m:v", ns)
                    if kind == "s" and raw is not None:
                        value = shared[int(raw.text)]
                    elif kind == "inlineStr":
                        inline = cell.find("m:is", ns)
                        value = "".join(inline.itertext()) if inline is not None else ""
                    elif raw is not None:
                        value = raw.text or ""
                    break
                if not value:
                    continue
                count += 1
                for match in re.findall(r"[\w .()\-]+\.png", value, flags=re.I):
                    names.add(Path(match.strip()).name.casefold())
            summary[path.name] = {"nonempty_sheet5_column_b_rows": count, "sha256": sha_file(path)}
    return names, summary


def main() -> None:
    global VAULT, SOURCE_ZIP, OLD_ICR, AUDIT, PHASE1, PHASE2, PHASE3, OUT
    parser = argparse.ArgumentParser(description="Reproduce the fixed screenshot archive analysis in controlled storage")
    parser.add_argument("--vault", type=Path, required=True, help="Extracted frozen source archive root")
    parser.add_argument("--source-zip", type=Path, required=True, help="Original frozen archive ZIP")
    parser.add_argument("--audit-dir", type=Path, required=True, help="Controlled audit directory with current_code_replay_20261001")
    parser.add_argument("--legacy-icr-dir", type=Path, required=True, help="Controlled July XLSX directory")
    parser.add_argument("--output-dir", type=Path, required=True, help="Controlled result directory outside this public repository")
    args = parser.parse_args()
    VAULT, SOURCE_ZIP = args.vault.resolve(), args.source_zip.resolve()
    OLD_ICR, AUDIT, OUT = args.legacy_icr_dir.resolve(), args.audit_dir.resolve(), args.output_dir.resolve()
    assert not OUT.is_relative_to(REPO.resolve()), "Controlled output may not be written inside the public repository"
    assert VAULT.is_dir() and SOURCE_ZIP.is_file() and OLD_ICR.is_dir() and AUDIT.is_dir()
    replay = AUDIT / "current_code_replay_20261001"
    PHASE1, PHASE2, PHASE3 = (replay / part for part in
                                ("phase1_markdown_baseline", "phase2_image_ocr", "phase3_typology_coding"))
    assert all(part.is_dir() for part in (PHASE1, PHASE2, PHASE3))
    OUT.mkdir(parents=True, exist_ok=True)

    rules = load_rules()
    substantive = [c for c in rules.CODEBOOK if c not in rules.DATA_QUALITY_CODES]
    quality = sorted(rules.DATA_QUALITY_CODES)
    targets = [("typology", c, rules.CODEBOOK[c]) for c in substantive]
    targets += [("aml_candidate", c, rules.AML_INDICATORS[c]) for c in rules.AML_INDICATORS]
    compiled = {c: rules.compile_patterns(entry["patterns"]) for _, c, entry in targets}
    compiled.update({c: rules.compile_patterns(rules.CODEBOOK[c]["patterns"]) for c in quality})
    target_order = [c for _, c, _ in targets]

    index = read_csv(PHASE1 / "corpus_index.csv")
    refs = read_csv(PHASE1 / "image_references.csv")
    joined = read_csv(PHASE2 / "ocr_joined_image_references.csv")
    ocr = read_csv(PHASE2 / "ocr_text_by_image.csv")
    note_ocr = read_csv(PHASE2 / "ocr_text_by_note.csv")
    old_typ = read_csv(PHASE3 / "typology_coding_long.csv")
    old_aml = read_csv(PHASE3 / "aml_indicator_coding_long.csv")
    orphans = read_csv(AUDIT / "unreferenced_png_controlled.csv")
    assert len(index) == 980 and len(refs) == len(joined) == 1140
    assert len(ocr) == 1043 and len(orphans) == 58
    assert len({row["note_id"] for row in index}) == 980

    joined_by_key = {(r["note_id"], r["image_index_in_note"]): r for r in joined}
    for ref in refs:
        item = joined_by_key[(ref["note_id"], ref["image_index_in_note"])]
        assert item["image_resolution_status"] == ref["image_resolution_status"]
        assert item["image_sha256"] == ref["image_sha256"]
    resolution = Counter(r["image_resolution_status"] for r in refs)
    assert resolution == {"resolved": 1048, "missing": 7, "external": 85}, resolution

    references_by_hash: dict[str, list[dict]] = defaultdict(list)
    for row in joined:
        if row["image_resolution_status"] == "resolved":
            references_by_hash[row["image_sha256"]].append(row)
    assert len(references_by_hash) == 1037

    ocr_by_path = {r["image_relative_path"]: r for r in ocr}
    assert len(ocr_by_path) == 1043
    image_rows: list[dict] = []
    image_text: dict[str, str] = {}
    image_path: dict[str, Path] = {}
    image_codes: dict[str, dict[str, int]] = {}
    manifest_input = {
        "frozen_source_zip": sha_file(SOURCE_ZIP),
        "phase1_corpus_index": sha_file(PHASE1 / "corpus_index.csv"),
        "phase1_image_references": sha_file(PHASE1 / "image_references.csv"),
        "phase2_image_ocr": sha_file(PHASE2 / "ocr_text_by_image.csv"),
        "phase2_joined_refs": sha_file(PHASE2 / "ocr_joined_image_references.csv"),
        "phase2_note_ocr": sha_file(PHASE2 / "ocr_text_by_note.csv"),
        "phase3_rule_source": sha_file(CODER),
    }
    with zipfile.ZipFile(SOURCE_ZIP) as frozen:
        archive_names = set(frozen.namelist())
        for digest, linked in sorted(references_by_hash.items()):
            paths = sorted({r["image_relative_path"] for r in linked})
            texts = {ocr_by_path[p]["ocr_text"] for p in paths}
            statuses = {ocr_by_path[p]["ocr_status"] for p in paths}
            word_counts = {int(ocr_by_path[p]["ocr_word_count"]) for p in paths}
            char_counts = {int(ocr_by_path[p]["ocr_char_count"]) for p in paths}
            assert len(texts) == len(statuses) == len(word_counts) == len(char_counts) == 1, (digest, paths)
            text = next(iter(texts))
            status = next(iter(statuses))
            assert status == "ok", (digest, status)
            for rel in paths:
                src = (VAULT / rel).resolve()
                assert src.is_relative_to(VAULT.resolve()), src
                assert src.is_file() and sha_file(src) == digest, src
                assert ocr_by_path[rel]["image_sha256"] == digest
                archived = "DW Project/" + Path(rel).as_posix()
                assert archived in archive_names, archived
                assert hashlib.sha256(frozen.read(archived)).hexdigest() == digest, archived
            sources = sorted({r["source"] for r in linked})
            notes = sorted({r["note_id"] for r in linked})
            primary_source = sources[0] if len(sources) == 1 else "MULTIPLE_ARCHIVE_GROUPS"
            counts = {c: one_binary(text, compiled[c]) for c in target_order + quality}
            image_codes[digest] = {c: counts[c][0] for c in counts}
            image_text[digest] = text
            image_path[digest] = VAULT / paths[0]
            row = {
                "case_id": "I" + digest[:16],
                "image_sha256": digest,
                "image_relative_path": paths[0],
                "path_count": len(paths),
                "reference_occurrences": len(linked),
                "linked_note_count": len(notes),
                "linked_note_ids": ";".join(notes),
                "archive_group": primary_source,
                "archive_groups_all": ";".join(sources),
                "ocr_status": status,
                "ocr_word_count": next(iter(word_counts)),
                "ocr_char_count": next(iter(char_counts)),
                "ocr_text_sha256": sha_text(text),
                "prior_packet_basename_exposure": "",
            }
            for c, triple in counts.items():
                row[c] = triple[0]
                row[c + "_hits"] = triple[1]
            image_rows.append(row)

    prior_names, prior_summary = load_prior_exposure()
    name_to_hashes: dict[str, set[str]] = defaultdict(set)
    for digest, linked in references_by_hash.items():
        for row in linked:
            name_to_hashes[Path(row["image_relative_path"]).name.casefold()].add(digest)
    exposed = set().union(*(name_to_hashes.get(name, set()) for name in prior_names)) if prior_names else set()
    for row in image_rows:
        row["prior_packet_basename_exposure"] = int(row["image_sha256"] in exposed)
    assert len(image_rows) == 1037
    write_csv(OUT / "image_level_matrix_controlled.csv", image_rows)

    # Every frequency below is a count of archived screenshot OCR rule positives.
    summary = []
    n = len(image_rows)
    for family, code, entry in targets + [("quality_flag", q, rules.CODEBOOK[q]) for q in quality]:
        k = sum(r[code] for r in image_rows)
        summary.append({
            "family": family, "code": code, "label": entry["label"],
            "positive_images": k, "denominator_images": n,
            "percent_of_images": f"{100 * k/n:.2f}",
            "total_regex_hits": sum(r[code + "_hits"] for r in image_rows),
            "interpretation": "OCR lexical rule positive; source claim unverified",
        })
    write_csv(OUT / "rule_summary.csv", summary)

    pattern_rows = []
    for family, code, entry in targets + [("quality_flag", q, rules.CODEBOOK[q]) for q in quality]:
        for number, pattern in enumerate(compiled[code], start=1):
            positives = 0
            hits = 0
            for row in image_rows:
                matches = list(pattern.finditer(image_text[row["image_sha256"]]))
                positives += bool(matches)
                hits += len(matches)
            pattern_rows.append({"family": family, "code": code, "pattern_number": number,
                                 "pattern": entry["patterns"][number - 1],
                                 "images_matched": positives, "total_matches": hits,
                                 "code_positive_images": sum(r[code] for r in image_rows)})
    write_csv(OUT / "pattern_level_diagnostics.csv", pattern_rows)

    groups = sorted({r["archive_group"] for r in image_rows})
    group_rows = []
    for group in groups:
        subset = [r for r in image_rows if r["archive_group"] == group]
        for code in target_order + quality:
            group_rows.append({"archive_group": group, "code": code,
                               "images": len(subset), "rule_positive_images": sum(r[code] for r in subset)})
    write_csv(OUT / "archive_group_counts_controlled.csv", group_rows)
    leave_one_rows = []
    for group in groups:
        removed = [r for r in image_rows if r["archive_group"] == group]
        kept = [r for r in image_rows if r["archive_group"] != group]
        for code in target_order + quality:
            leave_one_rows.append({"omitted_archive_group": group, "code": code,
                                   "omitted_images": len(removed), "remaining_images": len(kept),
                                   "remaining_positive_images": sum(r[code] for r in kept),
                                   "remaining_percent": f"{100*sum(r[code] for r in kept)/len(kept):.2f}"})
    write_csv(OUT / "leave_one_archive_group_out_controlled.csv", leave_one_rows)

    # Within-screenshot pair co-occurrence only. No edge implies a transaction.
    pair_rows = []
    for a, b in combinations(target_order, 2):
        both = sum(r[a] and r[b] for r in image_rows)
        if both:
            pair_rows.append({"code_a": a, "code_b": b, "images_with_both": both,
                              "image_denominator": n})
    pair_rows.sort(key=lambda r: (-r["images_with_both"], r["code_a"], r["code_b"]))
    write_csv(OUT / "within_image_cooccurrence.csv", pair_rows,
              ["code_a", "code_b", "images_with_both", "image_denominator"])
    overlap_rows = []
    for a, b in combinations(target_order, 2):
        pa = sum(r[a] for r in image_rows)
        pb = sum(r[b] for r in image_rows)
        both = sum(r[a] and r[b] for r in image_rows)
        if both:
            overlap_rows.append({"code_a": a, "code_b": b,
                                 "positive_a": pa, "positive_b": pb, "both": both,
                                 "same_binary_vector": int(pa == pb == both),
                                 "a_subset_b": int(pa == both), "b_subset_a": int(pb == both),
                                 "jaccard": f"{both/(pa+pb-both):.4f}"})
    write_csv(OUT / "rule_overlap_diagnostics.csv", overlap_rows)

    length_sensitivity = []
    long_images = [r for r in image_rows if r["ocr_word_count"] >= 30]
    for code in target_order + quality:
        length_sensitivity.append({"code": code, "all_images": n,
                                   "all_positive_images": sum(r[code] for r in image_rows),
                                   "at_least_30_ocr_words_images": len(long_images),
                                   "at_least_30_ocr_words_positive": sum(r[code] for r in long_images)})
    write_csv(OUT / "ocr_length_sensitivity.csv", length_sensitivity)

    # Exact OCR-text deduplication is separate from content-hash deduplication.
    text_groups: dict[str, list[dict]] = defaultdict(list)
    for row in image_rows:
        text_groups[row["ocr_text_sha256"]].append(row)
    representatives = [sorted(v, key=lambda x: x["image_sha256"])[0] for v in text_groups.values()]
    assert len(representatives) <= n
    dedup_rows = []
    for code in target_order + quality:
        base = sum(r[code] for r in image_rows)
        unique = sum(r[code] for r in representatives)
        dedup_rows.append({"code": code, "image_hash_n": n,
                           "image_hash_positive_n": base,
                           "unique_exact_ocr_text_n": len(representatives),
                           "unique_exact_ocr_text_positive_n": unique,
                           "base_percent": f"{100*base/n:.2f}",
                           "exact_ocr_dedup_percent": f"{100*unique/len(representatives):.2f}"})
    write_csv(OUT / "exact_ocr_text_sensitivity.csv", dedup_rows)

    # A unit-matched diagnostic for the old note-combined coding and OCR alone.
    old_map: dict[tuple[str, str], int] = {}
    for r in old_typ:
        old_map[(r["note_id"], r["code"])] = int(r["present"])
    for r in old_aml:
        old_map[(r["note_id"], r["aml_indicator"])] = int(r["present"])
    linked_notes = {r["note_id"] for r in joined if r["image_resolution_status"] == "resolved"}
    note_text = {r["note_id"]: r["joined_ocr_text"] for r in note_ocr}
    note_hashes: dict[str, set[str]] = defaultdict(set)
    for digest, linked in references_by_hash.items():
        for r in linked:
            note_hashes[r["note_id"]].add(digest)
    note_rows = []
    for code in target_order + quality:
        old_n = ocr_only_n = any_image_n = 0
        old_only = ocr_only_only = 0
        for note_id in linked_notes:
            old = old_map[(note_id, code)]
            ocr_only = one_binary(note_text[note_id], compiled[code])[0]
            any_image = int(any(image_codes[d][code] for d in note_hashes[note_id]))
            old_n += old
            ocr_only_n += ocr_only
            any_image_n += any_image
            old_only += int(old and not any_image)
            ocr_only_only += int(ocr_only and not any_image)
        note_rows.append({"code": code, "linked_note_n": len(linked_notes),
                          "old_note_plus_ocr_positive_n": old_n,
                          "note_joined_ocr_positive_n": ocr_only_n,
                          "any_single_image_ocr_positive_n": any_image_n,
                          "old_positive_without_single_image_positive_n": old_only,
                          "joined_ocr_positive_without_single_image_positive_n": ocr_only_only})
    write_csv(OUT / "linked_note_modality_sensitivity.csv", note_rows)
    historical_comparison = []
    for code in target_order + quality:
        old_all = sum(old_map[(r["note_id"], code)] for r in index)
        new_image = sum(r[code] for r in image_rows)
        historical_comparison.append({
            "code": code,
            "historical_mixed_markdown_note_n": len(index),
            "historical_mixed_markdown_positive_n": old_all,
            "historical_mixed_markdown_percent": f"{100*old_all/len(index):.2f}",
            "new_referenced_image_hash_n": n,
            "new_image_ocr_positive_n": new_image,
            "new_image_ocr_percent": f"{100*new_image/n:.2f}",
            "warning": "Different units and content modalities; percentage difference is not a temporal change",
        })
    write_csv(OUT / "historical_mixed_note_vs_image_counts.csv", historical_comparison)

    orphan_novel = {r["sha256"] for r in orphans if r["same_content_as_referenced_image"] == "0"}
    assert len(orphan_novel) == 35
    flow = {
        "markdown_paths": 999, "png_paths": 1101, "historical_screened_markdown_notes": 980,
        "historical_notes_with_resolved_image": len(linked_notes),
        "historical_notes_without_resolved_image": len(index) - len(linked_notes),
        "image_reference_occurrences": len(refs),
        "resolved_reference_occurrences": resolution["resolved"],
        "missing_reference_occurrences": resolution["missing"],
        "external_reference_occurrences": resolution["external"],
        "referenced_local_png_paths": len(ocr),
        "unique_referenced_local_image_hashes_primary": n,
        "unreferenced_png_paths": len(orphans),
        "unreferenced_png_paths_duplicate_of_primary": sum(r["same_content_as_referenced_image"] == "1" for r in orphans),
        "unreferenced_novel_png_hashes_outside_primary": len(orphan_novel),
        "prior_july_coder_packet_image_hashes_conservatively_mapped": len(exposed),
        "exact_ocr_text_groups": len(representatives),
        "zero_word_ocr_images": sum(r["ocr_word_count"] == 0 for r in image_rows),
        "short_under_30_word_ocr_images": sum(r["ocr_word_count"] < 30 for r in image_rows),
        "multi_archive_group_image_hashes": sum(r["archive_group"] == "MULTIPLE_ARCHIVE_GROUPS" for r in image_rows),
        "archive_groups_with_primary_images": len(groups),
        "median_ocr_words_per_image": statistics.median(r["ocr_word_count"] for r in image_rows),
        "minimum_ocr_words_per_image": min(r["ocr_word_count"] for r in image_rows),
        "maximum_ocr_words_per_image": max(r["ocr_word_count"] for r in image_rows),
    }
    (OUT / "flow.json").write_text(json.dumps(flow, indent=2) + "\n", encoding="utf-8")

    output_files = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != "analysis_manifest.json")
    (OUT / "analysis_manifest.json").write_text(json.dumps({
        "scope": "fixed archived screenshot OCR rules; controlled outputs",
        "primary_unit": "SHA-256-unique locally referenced PNG content",
        "image_n": n,
        "inputs_sha256": manifest_input,
        "reproducer_sha256": sha_file(Path(__file__)),
        "outputs_sha256": {p.name: sha_file(p) for p in output_files},
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Verified and analysed {n} unique referenced screenshot contents")


if __name__ == "__main__":
    main()
