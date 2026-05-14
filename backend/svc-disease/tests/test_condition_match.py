"""Tests for svc-disease ``POST /diseases/condition-match``."""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from svc_disease.app import app


class ConditionMatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)

    def test_aadc_conc_gt(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "aadc",
                    "fieldId": "conc",
                    "operator": "gt",
                    "value": "0",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/diseases/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        matches = r.json()["conditionMatches"]
        self.assertEqual(len(matches), 1)
        # At least one patient has aadc records with conc > 0 in the seed.
        self.assertGreater(len(matches[0]), 0)

    def test_bd_result_eq_normal(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "bd",
                    "fieldId": "result",
                    "operator": "eq",
                    "value": "Normal",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/diseases/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        matches = r.json()["conditionMatches"]
        # bd is an NBS module — at least one patient should have a Normal result.
        self.assertGreaterEqual(len(matches[0]), 0)

    def test_unknown_module_returns_empty(self) -> None:
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
        r = self.client.post("/diseases/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["conditionMatches"], [[]])


if __name__ == "__main__":
    unittest.main()
