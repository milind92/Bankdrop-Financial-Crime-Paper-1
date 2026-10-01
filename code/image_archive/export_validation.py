"""Export only verified aggregate author-validation results from controlled storage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
TARGETS = {"bank_drop_sale", "bank_log_sale", "fullz_identity_package",
           "email_access_takeover", "bank_log_plus_email_access"}


def sha(path: Path, public: bool = False) -> str:
    content = path.read_bytes()
    if public:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verified_inputs(controlled: Path) -> tuple[dict, list[dict], dict]:
    scoring = controlled / "simple_icr" / "scoring_results"
    audit_dir = controlled / "validation_claim_audit_20261002"
    audit = json.loads((audit_dir / "verified_aggregate_audit.json").read_text(encoding="utf-8"))
    manifest = json.loads((scoring / "scoring_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "adjudicated validation calculated"
    inputs = {"Milind": controlled / "completed_author_sheets" / "Milind_sheet.csv",
              "Ausma": controlled / "completed_author_sheets" / "Ausma_sheet.csv",
              "adjudication": scoring / "adjudication_completed.csv",
              "private_key": controlled / "coordinator_private" / "simple_icr_coordinator_key.csv"}
    for name, path in inputs.items():
        assert sha(path) == audit["input_sha256"][name], f"Controlled input changed: {name}"
    for name, field in {"Milind": "Milind_completed_sha256", "Ausma": "Ausma_completed_sha256",
                        "adjudication": "adjudicated_sha256", "private_key": "private_key_sha256"}.items():
        assert manifest[field] == audit["input_sha256"][name], f"Scoring input hash differs: {name}"
    for name, expected in audit["validated_output_sha256"].items():
        assert sha(scoring / name) == expected, f"Scoring output changed: {name}"
    assert audit["scorer_validation_reproduced_in_memory"]
    assert sha(controlled / "simple_icr" / "score_simple_icr.py") == audit["scorer_script_sha256"]
    assert sha(audit_dir / "verify_completed_claim.py") == audit["audit_script_sha256"]
    assert audit["overall"]["paired_judgments"] == 249 and audit["overall"]["distinct_images"] == 205
    agreement = read(scoring / "intercoder_agreement.csv")
    assert len(agreement) == 6 and {r["target"] for r in agreement} == TARGETS | {"all_five_targets"}
    validation = {r["target"]: r for r in read(scoring / "weighted_rule_validation.csv")}
    assert set(validation) == set(audit["targets"]) == TARGETS
    return audit, agreement, validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controlled-root", type=Path, required=True)
    args = parser.parse_args()
    controlled = args.controlled_root.resolve()
    assert not controlled.is_relative_to(REPO), "Controlled inputs must remain outside this checkout"
    audit, agreement, validation = verified_inputs(controlled)
    # Explicit fields only: no image IDs, individual answers, reasons or sample key.
    public_agreement = [{field: row[field] for field in
                         ("target", "paired_items", "five_category_agreements",
                          "five_category_percent_agreement", "five_category_cohens_kappa")}
                        for row in agreement]
    public_validation = []
    for code in sorted(TARGETS):
        checked, score = audit["targets"][code], validation[code]
        raw = checked["raw_adjudicated_counts"]
        nonbinary = sum(n for label, n in raw.items() if label not in {"tp", "fp", "tn", "fn"})
        census = checked["all_rule_positives_reviewed"]
        public_validation.append({
            "target": code,
            "paired_judgments": checked["agreement"]["paired_judgments"],
            "reviewed_rule_positive_n": checked["sample_positive_n"],
            "archive_rule_positive_n": checked["archive_rule_positive_n"],
            "reviewed_rule_negative_n": checked["sample_negative_n"],
            "archive_rule_negative_n": checked["archive_rule_negative_n"],
            "sample_tp": raw.get("tp", 0), "sample_fp": raw.get("fp", 0),
            "sample_fn": raw.get("fn", 0), "sample_tn": raw.get("tn", 0),
            "sample_nonbinary_n": nonbinary,
            "weighted_tp": score["weighted_tp"], "weighted_fp": score["weighted_fp"],
            "weighted_positive_predictive_value": score["positive_predictive_value"],
            "ppv_descriptive_bootstrap_low": "" if census else score["positive_predictive_value_bootstrap_low"],
            "ppv_descriptive_bootstrap_high": "" if census else score["positive_predictive_value_bootstrap_high"],
            "uncertainty_basis": "finite_positive_census" if census else "descriptive_within_stratum_bootstrap",
        })
    destination = REPO / "outputs" / "image_validation_20261002"
    destination.mkdir(parents=True, exist_ok=True)
    write(destination / "intercoder_agreement.csv", public_agreement)
    write(destination / "rule_validity.csv", public_validation)
    metadata = {
        "status": "completed author assessment; independent arithmetic and fixed-archive replay verified",
        "primary_image_frame_n": 1037, "paired_judgments": 249, "distinct_reviewed_images": 205,
        "assessed_targets_n": 5, "substantive_rules_without_human_validity_assessment_n": 13,
        "exact_agreements": 243, "disagreements": 6, "adjudication_rows": audit["adjudication_rows"],
        "final_category_counts": audit["final_category_counts"],
        "prior_packet_exposed_assignments": 143, "assignments_not_mapped_to_prior_packet": 106,
        "author_process_basis": "Author-reported independent coding; packet masking verified. CSV contents alone do not establish coding conduct.",
        "uncertainty": "1,000 seeded within-stratum resamples; 2.5th/97.5th percentile descriptive ranges. Census strata fixed; not calibrated intervals for external populations or human-label error.",
        "positive_census_target": "bank_log_plus_email_access",
        "positive_census_human_present_n": 16, "positive_census_n": 19,
        "construct_boundary": "Package or explicit linkage of bank-log/account access with email, cookie, recovery or session access; includes tutorials, requests and recommendations as well as listings.",
        "all_reviewed_rule_positives_have_binary_final_labels": True,
        "negative_sample_boundary": "Nonbinary outcomes are retained. Sampled negatives, including zero observed misses for one target, do not establish perfect archive recall or NPV.",
        "controlled_input_file_sha256": audit["input_sha256"],
        "controlled_scoring_output_sha256": audit["validated_output_sha256"],
        "controlled_audit_script_sha256": audit["audit_script_sha256"],
        "controlled_independent_audit_sha256": sha(controlled / "validation_claim_audit_20261002" / "verified_aggregate_audit.json"),
        "public_scorer_sha256": sha(REPO / "code" / "image_archive" / "score_author_validation.py", public=True),
        "public_exporter_sha256": sha(Path(__file__), public=True),
        "public_output_sha256": {name: sha(destination / name, public=True)
                                 for name in ("intercoder_agreement.csv", "rule_validity.csv")},
        "public_report_sha256": sha(REPO / "docs" / "IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md", public=True),
        "public_hash_method": "SHA-256 of UTF-8 bytes after CRLF-to-LF normalisation",
        "record_level_data_released": False,
        "interpretation_decision": "Final author interpretation and article wording remain with Milind.",
    }
    (destination / "validation_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print("Exported six aggregate agreement rows, five PPV rows and file-level validation provenance")


if __name__ == "__main__":
    main()
