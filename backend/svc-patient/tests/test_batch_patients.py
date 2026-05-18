"""Tests for svc-patient ``POST /patients/batch`` base-row lookup.

Uses ``TestClient`` so the lifespan loads the in-memory caches before
each test runs.
"""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from svc_patient.app import app

# Anchor patient present across the mock-data files.
_KNOWN_PID = "4e645243-fe58-5f74-b0bf-4271b5fdc0bf"


class _AppFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._cm = TestClient(app)
        cls.client = cls._cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._cm.__exit__(None, None, None)


class BatchPatientsTest(_AppFixture):
    def test_known_id_returns_base_row(self) -> None:
        r = self.client.post("/patients/batch", json={"patientIds": [_KNOWN_PID]})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(_KNOWN_PID, body)
        self.assertEqual(body[_KNOWN_PID]["patientId"], _KNOWN_PID)
        # Each value carries the patient's original source field.
        self.assertIn("source", body[_KNOWN_PID])

    def test_unknown_id_is_omitted(self) -> None:
        r = self.client.post(
            "/patients/batch",
            json={"patientIds": [_KNOWN_PID, "no-such-patient"]},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn(_KNOWN_PID, body)
        self.assertNotIn("no-such-patient", body)

    def test_empty_id_list_returns_empty_object(self) -> None:
        r = self.client.post("/patients/batch", json={"patientIds": []})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})


if __name__ == "__main__":
    unittest.main()
