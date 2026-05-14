"""Tests for svc-lab ``POST /labs/condition-match``."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from svc_lab.app import app


class ConditionMatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)

    def test_aa_specimen_type_eq_plasma(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "aa",
                    "fieldId": "specimenType",
                    "operator": "eq",
                    "value": "Plasma",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/labs/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        matches = r.json()["conditionMatches"]
        self.assertEqual(len(matches), 1)
        # Anchor patient 4e645243...0bf has an aa row with specimenType="Plasma".
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", matches[0])

    def test_biomarker_dbs_lyso_gb3_gt_5(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "biomarker",
                    "fieldId": "dbsLysoGb3",
                    "operator": "gt",
                    "value": "5",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/labs/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        matches = r.json()["conditionMatches"]
        # Mirrors verify-pg check #4: only the anchor patient satisfies.
        self.assertEqual(matches[0], ["4e645243-fe58-5f74-b0bf-4271b5fdc0bf"])

    def test_unknown_module_returns_empty(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "basic",
                    "fieldId": "diagnosis",
                    "operator": "contains",
                    "value": "Fabry",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/labs/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["conditionMatches"], [[]])


if __name__ == "__main__":
    unittest.main()
