"""Reconcile the released aggregate screenshot-validation tables and hashes."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path


TARGETS = {"bank_drop_sale", "bank_log_sale", "fullz_identity_package",
           "email_access_takeover", "bank_log_plus_email_access"}


def check(root: Path, errors: list[str]) -> int:
    base = root / "outputs" / "image_validation_20261002"
    try:
        metadata = json.loads((base / "validation_metadata.json").read_text(encoding="utf-8"))
        def rows(name):
            with (base / name).open(encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        agreement = rows("intercoder_agreement.csv")
        validity = rows("rule_validity.csv")
        assert len(agreement) == 6 and {r["target"] for r in agreement} == TARGETS | {"all_five_targets"}
        assert len(validity) == 5 and {r["target"] for r in validity} == TARGETS
        assert metadata["primary_image_frame_n"] == 1037 and metadata["distinct_reviewed_images"] == 205
        assert metadata["paired_judgments"] == 249 and metadata["exact_agreements"] == 243
        assert metadata["disagreements"] == 6 and metadata["adjudication_rows"] == 18
        assert metadata["record_level_data_released"] is False
        assert metadata["all_reviewed_rule_positives_have_binary_final_labels"] is True
        assert metadata["prior_packet_exposed_assignments"] + metadata["assignments_not_mapped_to_prior_packet"] == 249
        overall = next(r for r in agreement if r["target"] == "all_five_targets")
        assert int(overall["paired_items"]) == 249 and int(overall["five_category_agreements"]) == 243
        target_agreement = {r["target"]: r for r in agreement if r is not overall}
        assert sum(int(r["paired_items"]) for r in target_agreement.values()) == 249
        assert sum(int(r["five_category_agreements"]) for r in target_agreement.values()) == 243
        for row in agreement:
            n, agreed = int(row["paired_items"]), int(row["five_category_agreements"])
            assert 0 <= agreed <= n and n > 0
            assert math.isclose(float(row["five_category_percent_agreement"]), agreed / n, abs_tol=0.00000051)
            assert -1 <= float(row["five_category_cohens_kappa"]) <= 1
        n_present = n_absent = n_nonbinary = 0
        for row in validity:
            npos, nneg = int(row["reviewed_rule_positive_n"]), int(row["reviewed_rule_negative_n"])
            poppos, popneg = int(row["archive_rule_positive_n"]), int(row["archive_rule_negative_n"])
            tp, fp, fn, tn, nonbinary = (int(row[field]) for field in
                                      ("sample_tp", "sample_fp", "sample_fn", "sample_tn", "sample_nonbinary_n"))
            assert min(tp, fp, fn, tn, nonbinary) >= 0
            assert tp + fp == npos and fn + tn + nonbinary == nneg
            assert poppos + popneg == 1037 and 0 < npos <= poppos and 0 < nneg <= popneg
            assert npos + nneg == int(row["paired_judgments"]) == int(target_agreement[row["target"]]["paired_items"])
            weighted_tp, weighted_fp = float(row["weighted_tp"]), float(row["weighted_fp"])
            assert math.isclose(weighted_tp + weighted_fp, poppos, abs_tol=.0011)
            ppv = float(row["weighted_positive_predictive_value"])
            assert math.isclose(ppv, weighted_tp / (weighted_tp + weighted_fp), abs_tol=.0000051)
            if row["uncertainty_basis"] == "finite_positive_census":
                assert row["target"] == metadata["positive_census_target"] == "bank_log_plus_email_access"
                assert npos == poppos == metadata["positive_census_n"] == 19
                assert tp == metadata["positive_census_human_present_n"] == 16
                assert row["ppv_descriptive_bootstrap_low"] == row["ppv_descriptive_bootstrap_high"] == ""
                assert math.isclose(ppv, tp / npos, abs_tol=.0000051)
            else:
                assert row["uncertainty_basis"] == "descriptive_within_stratum_bootstrap"
                assert 0 <= float(row["ppv_descriptive_bootstrap_low"]) <= ppv <= float(row["ppv_descriptive_bootstrap_high"]) <= 1
            n_present += tp + fn
            n_absent += fp + tn
            n_nonbinary += nonbinary
        outcomes = metadata["final_category_counts"]
        assert outcomes["present"] == n_present == 94 and outcomes["absent"] == n_absent == 142
        assert sum(outcomes.get(c, 0) for c in ("ambiguous", "unreadable", "out_of_scope")) == n_nonbinary == 13
        assert sum(outcomes.values()) == 249
        assert metadata["public_hash_method"] == "SHA-256 of UTF-8 bytes after CRLF-to-LF normalisation"
        def public_sha(path):
            return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        hashes = metadata["public_output_sha256"]
        assert set(hashes) == {"intercoder_agreement.csv", "rule_validity.csv"}
        for name, digest in hashes.items():
            assert public_sha(base / name) == digest, f"Validation output hash changed: {name}"
        for field, relative in {
            "public_scorer_sha256": "code/image_archive/score_author_validation.py",
            "public_exporter_sha256": "code/image_archive/export_validation.py",
            "public_report_sha256": "docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md",
        }.items():
            assert public_sha(root / relative) == metadata[field], f"Validation hash changed: {field}"
        inputs = metadata["controlled_input_file_sha256"]
        assert set(inputs) == {"Milind", "Ausma", "adjudication", "private_key"}
        assert all(re.fullmatch(r"[0-9a-f]{64}", value) for value in inputs.values())
    except (AssertionError, OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        errors.append(f"Completed image author-validation integrity failed: {exc}")
        return 0
    return 6 + 5 * 8 + 8
