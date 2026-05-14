"""Tests for svc-patient ``q`` filter and ``/patients/condition-match``.

Uses ``TestClient`` so the lifespan loads the in-memory caches before
each test class. Mirrors the case-sensitive-name / case-insensitive-id
filter semantics from ``frontend/src/pages/Index.tsx:81-91``.
"""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from svc_patient.app import app


class _AppFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)


class ListPatientsQTest(_AppFixture):
    def test_list_no_q_returns_all(self) -> None:
        r = self.client.get("/patients")
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()), 13)

    def test_list_q_matches_name_substring(self) -> None:
        # Anchor patient has name "陳志明"; expect at least the "陳" substring hit.
        r = self.client.get("/patients", params={"q": "陳"})
        self.assertEqual(r.status_code, 200)
        ids = [p["patientId"] for p in r.json()]
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", ids)

    def test_list_q_matches_chartno_case_insensitive(self) -> None:
        r = self.client.get("/patients", params={"q": "a12"})
        self.assertEqual(r.status_code, 200)
        ids = [p["patientId"] for p in r.json()]
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", ids)

    def test_list_q_no_match_returns_empty(self) -> None:
        r = self.client.get("/patients", params={"q": "zzzz_no_match"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])


class ConditionMatchTest(_AppFixture):
    def test_basic_diagnosis_contains_fabry(self) -> None:
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
        r = self.client.post("/patients/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        matches = r.json()["conditionMatches"]
        self.assertEqual(len(matches), 1)
        self.assertIn("4e645243-fe58-5f74-b0bf-4271b5fdc0bf", matches[0])

    def test_basic_no_match_returns_empty_inner_list(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "basic",
                    "fieldId": "diagnosis",
                    "operator": "contains",
                    "value": "zzz_no_diagnosis_zzz",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/patients/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["conditionMatches"], [[]])

    def test_opd_module_walks_visit_history(self) -> None:
        body = {
            "conditions": [
                {
                    "moduleId": "opd",
                    "fieldId": "diagCode",
                    "operator": "eq",
                    "value": "E75.21",
                    "value2": "",
                }
            ],
            "logic": "AND",
        }
        r = self.client.post("/patients/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertIn(
            "4e645243-fe58-5f74-b0bf-4271b5fdc0bf",
            r.json()["conditionMatches"][0],
        )

    def test_unknown_module_returns_empty_inner_list(self) -> None:
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
        r = self.client.post("/patients/condition-match", json=body)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["conditionMatches"], [[]])


if __name__ == "__main__":
    unittest.main()
