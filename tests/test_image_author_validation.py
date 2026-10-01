from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("image_author_scorer", ROOT / "code/image_archive/score_author_validation.py")
scorer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scorer)
VERIFY_SPEC = importlib.util.spec_from_file_location("image_validation_integrity", ROOT / "code/image_archive/verify_validation.py")
release_checker = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(release_checker)


@contextmanager
def working_fixture():
    # Match the other fixtures: managed Windows blocks newly created system-temp directories.
    parent = (ROOT.parents[1] / "outputs" / "paper1_validation_test_fixtures").resolve()
    folder = parent / uuid.uuid4().hex
    folder.mkdir(parents=True)
    try:
        yield folder
    finally:
        assert folder.resolve().is_relative_to(parent)
        shutil.rmtree(folder)


class ImageAuthorValidationTests(unittest.TestCase):
    def disputed(self):
        return {"item_id": "synthetic", "image_id": "synthetic-image", "image_file": "images/synthetic.png",
                "target": "bank_drop_sale", "Milind_decision": "present", "Milind_reason": "visible offer",
                "Ausma_decision": "ambiguous", "Ausma_reason": "unclear offer",
                "final_decision": "", "final_reason": ""}

    def test_reliability_requires_complete_paired_categories(self):
        with self.assertRaises(AssertionError):
            scorer.kappa(["present"], [])
        with self.assertRaises(AssertionError):
            scorer.kappa(["unknown"], ["unknown"])
        self.assertEqual(scorer.kappa(["present", "present", "absent", "absent"],
                                      ["present", "absent", "present", "absent"]), 0)

    def test_nonbinary_agreement_is_not_discarded(self):
        first = ["present", "absent", "ambiguous", "out_of_scope"]
        second = ["present", "absent", "absent", "out_of_scope"]
        # Observed 3/4; chance agreement 1/4; kappa 2/3.
        self.assertAlmostEqual(scorer.kappa(first, second), 2 / 3)

    def test_stratum_weights_change_raw_precision(self):
        rows = [{"stratum_population_n": "90", "stratum_sample_n": "1", "machine_positive": "1", "final_decision": "present"},
                {"stratum_population_n": "10", "stratum_sample_n": "1", "machine_positive": "1", "final_decision": "absent"}]
        self.assertAlmostEqual(scorer.ratios(scorer.weighted_cells(rows))["positive_predictive_value"], .9)

    def test_nonbinary_outcome_is_not_a_false_positive(self):
        rows = [{"stratum_population_n": "8", "stratum_sample_n": "1", "machine_positive": "1", "final_decision": "out_of_scope"}]
        cells = scorer.weighted_cells(rows)
        self.assertEqual(cells["out_of_scope"], 8)
        self.assertEqual(cells["fp"], 0)
        self.assertIsNone(scorer.ratios(cells)["positive_predictive_value"])

    def test_adjudication_checks_identities_answers_and_reason(self):
        expected = self.disputed()
        supplied = dict(expected, final_decision="present", final_reason="resolved visible offer")
        key = {"synthetic": {}}
        answers = {"synthetic": {"decision": "present"}}
        self.assertEqual(scorer.final_answers([expected], key, answers, [supplied]), {"synthetic": "present"})
        for field, changed in (("image_id", "other"), ("target", "other"),
                               ("Milind_reason", "changed"), ("Ausma_decision", "absent"),
                               ("final_reason", " "), ("final_decision", "invalid")):
            with self.subTest(field=field), self.assertRaises(AssertionError):
                scorer.final_answers([expected], key, answers, [dict(supplied, **{field: changed})])

    def fixture(self, folder):
        packet = folder / "packet"
        packet.mkdir()
        private = folder / "coordinator_private"
        private.mkdir()
        (private / "simple_icr_coordinator_key.csv").write_text("synthetic key\n", encoding="utf-8")
        (packet / "packet_manifest.json").write_text("{}", encoding="utf-8")
        rows = [{"item_id": f"S{i}", "image_id": f"S{i}", "image_file": f"images/S{i}.png",
                 "target": target, "question": "synthetic question", "decision": "absent", "reason": "synthetic reason"}
                for i, target in enumerate(sorted(scorer.TARGETS))]
        key = [{field: value for field, value in row.items() if field not in {"decision", "reason"}} for row in rows]
        milind = folder / "milind.csv"
        ausma = folder / "ausma.csv"
        scorer.write(milind, rows)
        other = copy.deepcopy(rows)
        other[0]["decision"] = "ambiguous"
        scorer.write(ausma, other)
        return packet, key, milind, ausma

    def test_invalid_adjudication_writes_no_outputs(self):
        with working_fixture() as temporary:
            folder = Path(temporary)
            packet, key, milind, ausma = self.fixture(folder)
            final = dict(self.disputed(), item_id=key[0]["item_id"], final_decision="absent", final_reason="reason")
            adjudication = folder / "final.csv"
            scorer.write(adjudication, [final])
            output = folder / "output"
            arguments = ["score", "--packet-dir", str(packet), "--output-dir", str(output),
                         "--milind", str(milind), "--ausma", str(ausma), "--adjudicated", str(adjudication)]
            with mock.patch.object(scorer, "packet_check", return_value=(key, {})), mock.patch.object(sys, "argv", arguments):
                with self.assertRaises(AssertionError):
                    scorer.main()
            self.assertFalse(output.exists())

    def test_pending_rerun_removes_stale_validity_and_keeps_author_inputs(self):
        with working_fixture() as temporary:
            folder = Path(temporary)
            packet, key, milind, ausma = self.fixture(folder)
            originals = (milind.read_bytes(), ausma.read_bytes())
            output = folder / "output"
            output.mkdir()
            stale = output / "weighted_rule_validation.csv"
            stale.write_text("stale result", encoding="utf-8")
            arguments = ["score", "--packet-dir", str(packet), "--output-dir", str(output),
                         "--milind", str(milind), "--ausma", str(ausma)]
            with mock.patch.object(scorer, "packet_check", return_value=(key, {})), mock.patch.object(sys, "argv", arguments):
                scorer.main()
            self.assertFalse(stale.exists())
            manifest = json.loads((output / "scoring_manifest.json").read_text(encoding="utf-8"))
            self.assertIsNone(manifest["weighted_rule_validation_sha256"])
            self.assertEqual((milind.read_bytes(), ausma.read_bytes()), originals)

    def test_scoring_input_cannot_alias_an_output(self):
        with working_fixture() as temporary:
            folder = Path(temporary)
            packet, key, milind, ausma = self.fixture(folder)
            output = folder / "output"
            output.mkdir()
            supplied = output / "adjudication_template.csv"
            supplied.write_text("keep unchanged", encoding="utf-8")
            arguments = ["score", "--packet-dir", str(packet), "--output-dir", str(output),
                         "--milind", str(milind), "--ausma", str(ausma), "--adjudicated", str(supplied)]
            with mock.patch.object(scorer, "packet_check", return_value=(key, {})), mock.patch.object(sys, "argv", arguments):
                with self.assertRaises(AssertionError):
                    scorer.main()
            self.assertEqual(supplied.read_text(encoding="utf-8"), "keep unchanged")
            self.assertFalse((output / "intercoder_agreement.csv").exists())

    def test_controlled_output_cannot_enter_public_checkout(self):
        arguments = ["score", "--packet-dir", str(Path(tempfile.gettempdir()) / "synthetic-packet"),
                     "--output-dir", str(ROOT / "outputs" / "forbidden-scoring")]
        with mock.patch.object(sys, "argv", arguments), self.assertRaises(AssertionError):
            scorer.main()

    def test_released_assessment_reconciles(self):
        errors = []
        self.assertGreater(release_checker.check(ROOT, errors), 0)
        self.assertEqual(errors, [])

    def test_changed_released_kappa_is_rejected(self):
        with working_fixture() as folder:
            for relative in ("outputs/image_validation_20261002/intercoder_agreement.csv",
                             "outputs/image_validation_20261002/rule_validity.csv",
                             "outputs/image_validation_20261002/validation_metadata.json",
                             "code/image_archive/score_author_validation.py",
                             "code/image_archive/export_validation.py",
                             "docs/IMAGE_ARCHIVE_ANALYSIS_2026-10-02.md"):
                destination = folder / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, destination)
            agreement = folder / "outputs/image_validation_20261002/intercoder_agreement.csv"
            text = agreement.read_text(encoding="utf-8")
            self.assertIn("0.955039", text)
            agreement.write_text(text.replace("0.955039", "0.945039"), encoding="utf-8")
            errors = []
            self.assertEqual(release_checker.check(folder, errors), 0)
            self.assertTrue(any("output hash changed" in error for error in errors))

    def test_missing_assessment_is_reported_as_an_integrity_error(self):
        with working_fixture() as folder:
            errors = []
            self.assertEqual(release_checker.check(folder, errors), 0)
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
