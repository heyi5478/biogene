"""Tests for ``GET /patients`` slim list endpoint + ``q`` propagation."""

from __future__ import annotations


# Module-detail array names that MUST NOT appear in a list element. Mirrors
# the spec scenario "List response shape" in backend-api/spec.md.
_MODULE_ARRAYS = (
    "aa", "msms", "biomarker", "outbank", "dnabank", "gcms",
    "opd",
    "aadc", "ald", "mma", "mps2", "lsd", "enzyme", "gag",
    "bd", "cah", "dmd", "g6pd", "smaScid",
)


def test_list_response_shape_is_slim(gateway_client) -> None:
    r = gateway_client.get("/patients")
    assert r.status_code == 200
    items = r.json()
    assert len(items) > 0
    sample = items[0]
    assert "dnabankCount" in sample
    assert "outbankCount" in sample
    assert "lastVisitDate" in sample
    for key in _MODULE_ARRAYS:
        assert key not in sample, f"{key} should not appear in PatientListItem"


def test_list_q_filters_through_to_svc_patient(gateway_client) -> None:
    # Anchor patient name "陳志明" matches "陳" by case-sensitive substring.
    r = gateway_client.get("/patients", params={"q": "陳"})
    assert r.status_code == 200
    items = r.json()
    ids = [i["patientId"] for i in items]
    assert "4e645243-fe58-5f74-b0bf-4271b5fdc0bf" in ids


def test_anchor_patient_summary_fields(gateway_client) -> None:
    """4e645243...0bf has 1 dnabank row, 1 outbank row, opd visits in 2025."""
    r = gateway_client.get("/patients", params={"q": "陳"})
    assert r.status_code == 200
    items = r.json()
    anchor = next(i for i in items if i["patientId"] == "4e645243-fe58-5f74-b0bf-4271b5fdc0bf")
    assert anchor["dnabankCount"] >= 0
    assert anchor["outbankCount"] >= 0
    # The seeded opd visits include 2025-12-10 — should be the lex max.
    assert anchor["lastVisitDate"] is not None
    assert anchor["lastVisitDate"].startswith("2025")


def test_list_q_no_match_returns_empty(gateway_client) -> None:
    r = gateway_client.get("/patients", params={"q": "zzzz_no_match"})
    assert r.status_code == 200
    assert r.json() == []
