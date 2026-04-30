"""Tests for §13 svc-lab gcms additions.

Three things to verify:

1. ``GET /labs/{pid}/gcms`` exists and returns ``GcmsRecord[]``.
2. ``GET /labs/{pid}`` (the LabBundle) includes a ``gcms`` key (empty list
   in mock dev mode since mock-data/db_main/gcms.json is empty).
3. The widened ``GagRecord`` columns (od / urineCreatinine / mggag /
   twos / twosCre) round-trip through Pydantic without rejection.

We use FastAPI's TestClient so the lifespan hook runs and populates
``_index``. Stdlib ``unittest`` only — no pytest dep required.
"""

from __future__ import annotations

import unittest
from fastapi.testclient import TestClient

from shared.schemas import GagRecord, GcmsRecord, LabBundle
from svc_lab.app import app


class GcmsRouteTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_cm = TestClient(app)
        cls.client = cls._client_cm.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_cm.__exit__(None, None, None)

    def test_gcms_route_returns_empty_list_for_unknown(self) -> None:
        r = self.client.get("/labs/00000000-0000-0000-0000-000000000000/gcms")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_gcms_route_returns_empty_list_for_known_with_no_gcms(self) -> None:
        # anchor A1234567 — has aa/msms data but no gcms in mock dev mode
        r = self.client.get("/labs/4e645243-fe58-5f74-b0bf-4271b5fdc0bf/gcms")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_lab_bundle_includes_gcms_key(self) -> None:
        r = self.client.get("/labs/4e645243-fe58-5f74-b0bf-4271b5fdc0bf")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("gcms", body, msg="LabBundle must always carry a gcms array")
        self.assertIsInstance(body["gcms"], list)


class WidenedGagRecordTest(unittest.TestCase):
    """§13.2 — GagRecord widening must accept all six new fields."""

    def test_gag_record_accepts_widened_fields(self) -> None:
        g = GagRecord(
            patientId="x",
            sampleName="GAG-2026-001",
            specimenType="Urine",
            technician="Tech",
            result="Normal",
            DMGGAG=120.5,
            CREATININE=42.0,
            od=1.2,
            urineCreatinine=85.5,
            mggag=180.0,
            twos=4.5,
            twosCre=0.05,
        )
        d = g.model_dump()
        for k in ("od", "urineCreatinine", "mggag", "twos", "twosCre"):
            self.assertIn(k, d)

    def test_gag_record_widened_fields_default_to_none(self) -> None:
        # Backwards-compat: 2.0-only rows must keep their existing shape.
        g = GagRecord(
            patientId="x",
            sampleName="GAG-2025-099",
            specimenType="Urine",
            technician="Tech",
            result="Normal",
        )
        d = g.model_dump()
        self.assertIsNone(d["od"])
        self.assertIsNone(d["urineCreatinine"])


class GcmsRecordSchemaTest(unittest.TestCase):
    """§8.4 / §13 — GcmsRecord must accept its declared fields."""

    def test_gcms_record_minimal(self) -> None:
        g = GcmsRecord(patientId="x", sampleName="GC-2026-001")
        self.assertEqual(g.patientId, "x")
        self.assertIsNone(g.specimenType)
        self.assertIsNone(g.rawDataPath)

    def test_gcms_record_full(self) -> None:
        g = GcmsRecord(
            patientId="x",
            sampleName="GC-2026-001",
            specimenType="Urine",
            result="Abnormal",
            rawDataPath="gcms/GC-2026-001.jpg",
            collectDate="2026-04-15",
            notes="see attached spectrum",
        )
        self.assertEqual(g.rawDataPath, "gcms/GC-2026-001.jpg")


if __name__ == "__main__":
    unittest.main()
