"""Minimal smoke tests for :mod:`shared.data_loader`.

Uses only the standard library so it can run without installing pytest
(``python -m unittest backend.shared.tests.test_data_loader``). The pytest
entrypoint also discovers it.
"""

from __future__ import annotations

import copy
import unittest

from shared.data_loader import load_all, validate


class LoadAllShapeTest(unittest.TestCase):
    """The return value must be keyed by database -> table -> row list."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_all()

    def test_top_level_keys(self) -> None:
        self.assertEqual(
            set(self.data.keys()), {"db_main", "db_external", "db_nbs"}
        )

    def test_each_db_has_patient_table(self) -> None:
        for db, tables in self.data.items():
            self.assertIn("patient", tables, msg=db)
            self.assertIsInstance(tables["patient"], list)
            self.assertGreater(len(tables["patient"]), 0, msg=db)

    def test_patient_rows_have_required_fields(self) -> None:
        for db, tables in self.data.items():
            for i, row in enumerate(tables["patient"]):
                self.assertIn("patientId", row, msg=f"{db} row {i}")
                self.assertIn("source", row, msg=f"{db} row {i}")

    def test_nbs_has_sub_tables(self) -> None:
        self.assertIn("cah_tgal", self.data["db_nbs"])
        self.assertIn("dmd_tsh", self.data["db_nbs"])


class ValidateTest(unittest.TestCase):
    def test_validate_passes_on_clean_data(self) -> None:
        validate()  # should not raise

    def test_validate_raises_on_dangling_fk(self) -> None:
        data = load_all()
        data["db_main"]["aa"] = copy.deepcopy(data["db_main"]["aa"])
        data["db_main"]["aa"].append(
            {"patientId": "not-a-real-id", "sampleName": "X", "specimenType": "Plasma", "result": "Normal"}
        )
        with self.assertRaises(ValueError) as ctx:
            validate(data)
        self.assertIn("not-a-real-id", str(ctx.exception))
        self.assertIn("db_main/aa.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
