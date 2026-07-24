import csv
import shutil
import sys
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "human_validation"))

import summarize_human_validation as validation


class HumanValidationTests(unittest.TestCase):
    def setUp(self):
        # Inherit the checkout ACL instead of tempfile's restrictive Windows ACL.
        self.directory = Path(__file__).resolve().parent / f".human-validation-{uuid.uuid4().hex}"
        self.directory.mkdir()

    def tearDown(self):
        shutil.rmtree(self.directory)

    def write_csv(self, name, fieldnames, rows):
        path = self.directory / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def inputs(
        self, models, coder_1, coder_2, adjudicated=None,
        secret_prefix="SECRET", weights=None,
    ):
        machine_rows = []
        first_rows = []
        second_rows = []
        final_rows = []
        for index, model in enumerate(models, 1):
            record_id = f"{secret_prefix}-{index}"
            machine_row = {
                "record_id": record_id,
                "target_type": "typology",
                "code": "bank_drop_sale",
                "model_present": model,
                "relative_path": f"DO-NOT-LEAK/{index}.md",
            }
            if weights is not None:
                machine_row["analysis_weight"] = weights[index - 1]
            machine_rows.append(machine_row)
            first_rows.append({"record_id": record_id, "decision": coder_1[index - 1]})
            second_rows.append({"record_id": record_id, "decision": coder_2[index - 1]})
            if adjudicated is not None:
                final_rows.append(
                    {
                        "record_id": record_id,
                        "coder_1_decision": coder_1[index - 1],
                        "coder_2_decision": coder_2[index - 1],
                        "adjudicated_decision": adjudicated[index - 1],
                    }
                )
        machine_fields = [
            "record_id", "target_type", "code", "model_present", "relative_path"
        ]
        if weights is not None:
            machine_fields.append("analysis_weight")
        machine = self.write_csv("machine.csv", machine_fields, machine_rows)
        first = self.write_csv("coder1.csv", ["record_id", "decision"], first_rows)
        second = self.write_csv("coder2.csv", ["record_id", "decision"], second_rows)
        final = (
            self.write_csv(
                "adjudication.csv",
                [
                    "record_id",
                    "coder_1_decision",
                    "coder_2_decision",
                    "adjudicated_decision",
                ],
                final_rows,
            )
            if adjudicated is not None
            else None
        )
        return machine, first, second, final

    def run_summary(self, inputs, allow_incomplete=False):
        machine, first, second, final = inputs
        output_csv = self.directory / "public.csv"
        output_md = self.directory / "public.md"
        argv = [
            "--machine-key",
            str(machine),
            "--coder-1",
            str(first),
            "--coder-2",
            str(second),
            "--output-csv",
            str(output_csv),
            "--output-markdown",
            str(output_md),
        ]
        if final is not None:
            argv.extend(["--adjudication", str(final)])
        if allow_incomplete:
            argv.append("--allow-incomplete")
        self.assertEqual(validation.main(argv), 0)
        with output_csv.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return rows, output_csv.read_text(encoding="utf-8"), output_md.read_text(encoding="utf-8")

    def test_perfect_agreement_and_perfect_classification(self):
        rows, _, markdown = self.run_summary(
            self.inputs(
                ["1", "0", "1", "0"],
                ["present", "absent", "present", "absent"],
                ["present", "absent", "present", "absent"],
            )
        )
        overall = rows[0]
        self.assertEqual(overall["agreement_rate"], "1.000000")
        self.assertEqual(overall["cohen_kappa"], "1.000000")
        self.assertEqual((overall["tp"], overall["fp"], overall["tn"], overall["fn"]), ("2", "0", "2", "0"))
        self.assertEqual(overall["accuracy"], "1.000000")
        self.assertIn("cannot estimate corpus prevalence", markdown)

    def test_disagreement_uses_adjudicated_decisions(self):
        rows, _, _ = self.run_summary(
            self.inputs(
                ["1", "0"],
                ["present", "absent"],
                ["absent", "present"],
                adjudicated=["present", "absent"],
            )
        )
        overall = rows[0]
        self.assertEqual(overall["agreement_rate"], "0.000000")
        self.assertEqual(overall["cohen_kappa"], "-1.000000")
        self.assertEqual(overall["unresolved_n"], "0")
        self.assertEqual((overall["tp"], overall["tn"]), ("1", "1"))

    def test_ambiguous_decisions_are_excluded_from_binary_metrics(self):
        rows, _, _ = self.run_summary(
            self.inputs(
                ["1", "0", "1"],
                ["ambiguous", "absent", "present"],
                ["ambiguous", "absent", "absent"],
                adjudicated=["ambiguous", "absent", "present"],
            )
        )
        overall = rows[0]
        self.assertEqual(overall["coder_pair_complete_n"], "3")
        self.assertEqual(overall["agreement_n"], "2")
        self.assertEqual(overall["kappa_evaluable_n"], "2")
        self.assertEqual(overall["final_ambiguous_n"], "1")
        self.assertEqual(overall["confusion_evaluable_n"], "2")

    def test_all_five_decisions_are_counted_and_only_binary_is_scored(self):
        decisions = [
            "present",
            "absent",
            "ambiguous",
            "insufficient_evidence",
            "out_of_scope_record",
        ]
        rows, _, markdown = self.run_summary(
            self.inputs(
                ["1", "0", "1", "0", "1"],
                decisions,
                [
                    "present",
                    "absent",
                    "ambiguous",
                    "out_of_scope_record",
                    "insufficient_evidence",
                ],
                adjudicated=decisions,
            )
        )
        overall = rows[0]
        for decision in decisions:
            self.assertEqual(overall[f"coder_1_{decision}_n"], "1")
            self.assertEqual(overall[f"final_{decision}_n"], "1")
        self.assertEqual(overall["coder_pair_complete_n"], "5")
        self.assertEqual(overall["kappa_evaluable_n"], "2")
        self.assertEqual(overall["confusion_evaluable_n"], "2")
        self.assertEqual(overall["excluded_from_confusion_n"], "3")
        self.assertEqual(overall["other_disagreement_n"], "2")
        self.assertIn("insufficient_evidence=1", markdown)
        self.assertIn("out_of_scope_record=1", markdown)

    def test_gwet_ac1_and_bootstrap_intervals_are_reported(self):
        rows, _, markdown = self.run_summary(
            self.inputs(
                ["1", "0", "1", "0", "1", "0", "1", "0"],
                ["present", "absent"] * 4,
                ["present", "absent"] * 4,
            )
        )
        overall = rows[0]
        self.assertEqual(overall["gwet_ac1"], "1.000000")
        self.assertEqual(overall["cohen_kappa"], "1.000000")
        self.assertEqual(overall["gwet_ac1_bootstrap_ci95_low"], "1.000000")
        self.assertEqual(overall["gwet_ac1_bootstrap_ci95_high"], "1.000000")
        self.assertEqual(overall["cohen_kappa_bootstrap_ci95_low"], "1.000000")
        self.assertEqual(overall["cohen_kappa_bootstrap_ci95_high"], "1.000000")
        self.assertIn("paired-record bootstrap", markdown)

    def test_optional_analysis_weights_produce_labelled_weighted_estimates(self):
        rows, _, markdown = self.run_summary(
            self.inputs(
                ["1", "1", "0", "0"],
                ["present", "absent", "absent", "present"],
                ["present", "absent", "absent", "present"],
                weights=["9", "1", "9", "1"],
            )
        )
        overall = rows[0]
        self.assertEqual(overall["accuracy"], "0.500000")
        self.assertEqual(overall["weighted_accuracy"], "0.900000")
        self.assertEqual(overall["weighted_precision"], "0.900000")
        self.assertEqual(overall["weighted_sensitivity"], "0.900000")
        self.assertEqual(overall["weighted_specificity"], "0.900000")
        self.assertEqual(overall["weighted_confusion_weight_sum"], "20.000000")
        self.assertTrue(overall["weighted_accuracy_approx_ci95_low"])
        self.assertIn("approximate 95% interval", markdown)
        self.assertIn("Kish effective sample", markdown)

    def test_analysis_weight_must_be_finite_and_positive(self):
        for bad_weight in ("", "0", "-1", "nan", "inf", "not-a-number"):
            with self.subTest(weight=bad_weight):
                machine, first, second, _ = self.inputs(
                    ["1"], ["present"], ["present"], weights=[bad_weight]
                )
                with self.assertRaises(validation.ValidationInputError):
                    validation.load_records(machine, first, second, None, False)

    def test_schema_duplicate_and_decision_errors_are_rejected(self):
        machine, first, second, _ = self.inputs(["1"], ["present"], ["present"])
        broken = self.write_csv("broken.csv", ["record_id"], [{"record_id": "SECRET-1"}])
        with self.assertRaises(validation.ValidationInputError):
            validation.load_records(machine, broken, second, None, False)

        duplicate = self.write_csv(
            "duplicate.csv",
            ["record_id", "decision"],
            [
                {"record_id": "SECRET-1", "decision": "present"},
                {"record_id": "SECRET-1", "decision": "present"},
            ],
        )
        with self.assertRaises(validation.ValidationInputError):
            validation.load_records(machine, duplicate, second, None, False)

        invalid = self.write_csv(
            "invalid.csv",
            ["record_id", "decision"],
            [{"record_id": "SECRET-1", "decision": "maybe"}],
        )
        with self.assertRaises(validation.ValidationInputError):
            validation.load_records(machine, invalid, second, None, False)

        blank = self.write_csv(
            "blank.csv",
            ["record_id", "decision"],
            [{"record_id": "SECRET-1", "decision": ""}],
        )
        with self.assertRaises(validation.ValidationInputError):
            validation.load_records(machine, blank, second, None, False)
        records = validation.load_records(machine, blank, second, None, True)
        self.assertEqual(records[0].coder_1, "")

    def test_public_outputs_do_not_leak_record_data(self):
        rows, csv_text, markdown = self.run_summary(
            self.inputs(
                ["1", "0"],
                ["present", "absent"],
                ["present", "absent"],
                secret_prefix="VERY-SECRET-ID",
            )
        )
        self.assertGreaterEqual(len(rows), 2)
        combined = csv_text + markdown
        self.assertNotIn("VERY-SECRET-ID", combined)
        self.assertNotIn("DO-NOT-LEAK", combined)
        self.assertNotIn("record_id", csv_text.splitlines()[0])
        self.assertNotIn("relative_path", csv_text.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
