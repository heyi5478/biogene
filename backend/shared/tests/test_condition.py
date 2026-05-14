"""Tests for the shared condition evaluator (operator semantics + parity).

The operator semantics MUST match the JS evaluator at
``frontend/src/components/ConditionResults.tsx`` (lines 237-279). Each of
the eleven operators has at least one positive and one negative case here;
parity tests at the bottom run against representative records loaded from
``backend/mock-data/db_main/{aa,biomarker,opd,patient}.json`` to guard
against drift between the JS source and the Python port.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from shared.condition import (
    eval_condition,
    hit_summary,
    match_records,
)

MOCK_DIR = Path(__file__).resolve().parents[2] / "mock-data" / "db_main"


def _load(name: str) -> list[dict]:
    with (MOCK_DIR / f"{name}.json").open(encoding="utf-8") as fh:
        return json.load(fh)


class OperatorSemanticsTest(unittest.TestCase):
    """Positive + negative case for each of the eleven operators."""

    # ----- has_data / no_data
    def test_has_data_true_for_present_value(self) -> None:
        self.assertTrue(eval_condition({"x": 1}, "x", "has_data"))

    def test_has_data_false_for_none(self) -> None:
        self.assertFalse(eval_condition({"x": None}, "x", "has_data"))

    def test_has_data_false_for_empty_string(self) -> None:
        self.assertFalse(eval_condition({"x": ""}, "x", "has_data"))

    def test_no_data_true_for_missing_key(self) -> None:
        self.assertTrue(eval_condition({}, "x", "no_data"))

    def test_no_data_false_for_present_value(self) -> None:
        self.assertFalse(eval_condition({"x": 0}, "x", "no_data"))

    # ----- eq / neq
    def test_eq_string_match(self) -> None:
        self.assertTrue(eval_condition({"sex": "男"}, "sex", "eq", "男"))

    def test_eq_number_to_string_match(self) -> None:
        self.assertTrue(eval_condition({"n": 5}, "n", "eq", "5"))

    def test_eq_no_match(self) -> None:
        self.assertFalse(eval_condition({"sex": "女"}, "sex", "eq", "男"))

    def test_neq_match(self) -> None:
        self.assertTrue(eval_condition({"sex": "女"}, "sex", "neq", "男"))

    def test_neq_no_match(self) -> None:
        self.assertFalse(eval_condition({"sex": "男"}, "sex", "neq", "男"))

    # ----- contains
    def test_contains_match(self) -> None:
        self.assertTrue(
            eval_condition(
                {"diagnosis": "Fabry disease (E75.21)"},
                "diagnosis",
                "contains",
                "fabry",
            )
        )

    def test_contains_no_match(self) -> None:
        self.assertFalse(
            eval_condition({"diagnosis": "Fabry"}, "diagnosis", "contains", "Pompe")
        )

    def test_contains_handles_none(self) -> None:
        self.assertFalse(eval_condition({"x": None}, "x", "contains", "anything"))

    # ----- gt / gte / lt / lte
    def test_gt_match(self) -> None:
        self.assertTrue(eval_condition({"n": 12.8}, "n", "gt", "5"))

    def test_gt_no_match(self) -> None:
        self.assertFalse(eval_condition({"n": 3.2}, "n", "gt", "5"))

    def test_gt_none_returns_false(self) -> None:
        self.assertFalse(eval_condition({"n": None}, "n", "gt", "5"))

    def test_gte_boundary(self) -> None:
        self.assertTrue(eval_condition({"n": 5}, "n", "gte", "5"))
        self.assertFalse(eval_condition({"n": 4.99}, "n", "gte", "5"))

    def test_lt_match(self) -> None:
        self.assertTrue(eval_condition({"n": 4.99}, "n", "lt", "5"))

    def test_lt_no_match(self) -> None:
        self.assertFalse(eval_condition({"n": 5}, "n", "lt", "5"))

    def test_lte_boundary(self) -> None:
        self.assertTrue(eval_condition({"n": 5}, "n", "lte", "5"))
        self.assertFalse(eval_condition({"n": 5.01}, "n", "lte", "5"))

    # ----- between
    def test_between_inclusive_match(self) -> None:
        self.assertTrue(eval_condition({"n": 5}, "n", "between", "0", "10"))
        self.assertTrue(eval_condition({"n": 0}, "n", "between", "0", "10"))
        self.assertTrue(eval_condition({"n": 10}, "n", "between", "0", "10"))

    def test_between_no_match(self) -> None:
        self.assertFalse(eval_condition({"n": 11}, "n", "between", "0", "10"))

    def test_between_none_returns_false(self) -> None:
        self.assertFalse(eval_condition({"n": None}, "n", "between", "0", "10"))

    # ----- after / before
    def test_after_match(self) -> None:
        self.assertTrue(
            eval_condition(
                {"shipdate": "2025-06-15"},
                "shipdate",
                "after",
                "2025-01-01",
            )
        )

    def test_after_no_match(self) -> None:
        self.assertFalse(
            eval_condition(
                {"shipdate": "2024-12-31"},
                "shipdate",
                "after",
                "2025-01-01",
            )
        )

    def test_before_match(self) -> None:
        self.assertTrue(
            eval_condition(
                {"birthday": "1985-03-15"},
                "birthday",
                "before",
                "2000-01-01",
            )
        )

    def test_before_no_match(self) -> None:
        self.assertFalse(
            eval_condition(
                {"birthday": "2020-03-15"},
                "birthday",
                "before",
                "2000-01-01",
            )
        )


class UnknownOperatorTest(unittest.TestCase):
    def test_unknown_operator_returns_false(self) -> None:
        self.assertFalse(eval_condition({"x": 1}, "x", "weird_op", "1"))


class MatchRecordsTest(unittest.TestCase):
    def test_match_records_any_semantics(self) -> None:
        records = [{"n": 1}, {"n": 5}, {"n": 10}]
        self.assertTrue(match_records(records, "n", "gt", "7"))
        self.assertFalse(match_records(records, "n", "gt", "100"))

    def test_match_records_empty_iterable(self) -> None:
        self.assertFalse(match_records([], "n", "gt", "1"))


class HitSummaryTest(unittest.TestCase):
    def test_summary_uses_module_code_and_field_label(self) -> None:
        records = [{"dbsLysoGb3": 12.8, "patientId": "p1"}]
        self.assertEqual(
            hit_summary(records, "biomarker", "dbsLysoGb3"),
            "Biomarker/DBS LysoGb3=12.8",
        )

    def test_summary_returns_none_when_no_value(self) -> None:
        self.assertIsNone(hit_summary([{"x": None}], "biomarker", "dbsLysoGb3"))

    def test_summary_skips_records_with_null_value(self) -> None:
        records = [{"dbsLysoGb3": None}, {"dbsLysoGb3": 7.0}]
        self.assertEqual(
            hit_summary(records, "biomarker", "dbsLysoGb3"),
            "Biomarker/DBS LysoGb3=7",
        )


class MockDataParityTest(unittest.TestCase):
    """Parity against the seeded mock dataset.

    These cases anchor the evaluator to known records so any silent drift
    between the JS source (ConditionResults.tsx) and the Python port shows
    up as a failed assertion here, not in the SPA.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.patients = _load("patient")
        cls.opd = _load("opd")
        cls.aa = _load("aa")
        cls.biomarker = _load("biomarker")

    def test_basic_diagnosis_contains_fabry(self) -> None:
        # Patient 4e645243...0bf has diagnosis "Fabry disease (E75.21)".
        matched = [
            p
            for p in self.patients
            if eval_condition(p, "diagnosis", "contains", "Fabry")
        ]
        ids = {p["patientId"] for p in matched}
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", ids)

    def test_biomarker_dbs_lyso_gb3_gt_5(self) -> None:
        # Mirrors verify-pg check #4: only patient 4e645243...0bf has dbsLysoGb3 > 5.
        matched_pids = {
            row["patientId"]
            for row in self.biomarker
            if eval_condition(row, "dbsLysoGb3", "gt", "5")
        }
        self.assertEqual(
            matched_pids, {"4e645243-fe58-5f74-b0bf-4271b5fdc0bf"}
        )

    def test_aa_phe_between_50_60(self) -> None:
        # Patient 4e645243...0bf has Phe=52, which is in [50, 60].
        matched_pids = {
            row["patientId"]
            for row in self.aa
            if eval_condition(row, "Phe", "between", "50", "60")
        }
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", matched_pids)

    def test_opd_visit_date_after_2025(self) -> None:
        matched_pids = {
            row["patientId"]
            for row in self.opd
            if eval_condition(row, "visitDate", "after", "2025-01-01")
        }
        # Patient 4e645243...0bf has visits on 2025-12-10 and 2025-09-05.
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", matched_pids)

    def test_aa_specimen_type_eq_plasma(self) -> None:
        matched = [
            row
            for row in self.aa
            if eval_condition(row, "specimenType", "eq", "Plasma")
        ]
        self.assertGreater(len(matched), 0)

    def test_match_records_aggregates_per_patient(self) -> None:
        # Group biomarker rows by patient and assert match_records picks the right ones.
        by_pid: dict[str, list[dict]] = {}
        for row in self.biomarker:
            by_pid.setdefault(row["patientId"], []).append(row)
        matched_pids = {
            pid
            for pid, rows in by_pid.items()
            if match_records(rows, "dbsLysoGb3", "gt", "5")
        }
        self.assertEqual(
            matched_pids, {"4e645243-fe58-5f74-b0bf-4271b5fdc0bf"}
        )


if __name__ == "__main__":
    unittest.main()
