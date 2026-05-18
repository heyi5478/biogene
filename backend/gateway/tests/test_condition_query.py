"""Tests for ``POST /patients/condition-query`` on the gateway."""

from __future__ import annotations

import httpx

from gateway import app as gw_module
from gateway.app import app as gateway_app
from svc_disease.app import app as svc_disease_app
from svc_lab.app import app as svc_lab_app
from svc_patient.app import app as svc_patient_app


_FABRY_PID = "4e645243-fe58-5f74-b0bf-4271b5fdc0bf"

# A deliberately broad condition — sex is 男 for ~half the 100 mock
# patients — so the match set spans several pages.
_MALE_CONDITION = {
    "conditions": [
        {
            "moduleId": "basic",
            "fieldId": "sex",
            "operator": "eq",
            "value": "男",
            "value2": "",
        }
    ],
    "logic": "AND",
}


def test_empty_conditions_returns_empty_list(gateway_client) -> None:
    r = gateway_client.post(
        "/patients/condition-query",
        json={"conditions": [], "logic": "AND"},
    )
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


def test_single_basic_diagnosis_condition(gateway_client) -> None:
    r = gateway_client.post(
        "/patients/condition-query",
        json={
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
        },
    )
    assert r.status_code == 200
    items = r.json()["items"]
    ids = [i["patientId"] for i in items]
    assert _FABRY_PID in ids
    fabry = next(i for i in items if i["patientId"] == _FABRY_PID)
    assert "conditionHits" in fabry
    assert any("基本資料/主診斷" in h for h in fabry["conditionHits"])
    # Slim shape — no module arrays.
    assert "aa" not in fabry
    assert "biomarker" not in fabry


def test_and_across_modules(gateway_client) -> None:
    """basic.diagnosis contains Fabry AND biomarker.dbsLysoGb3 > 5 → only the anchor."""
    r = gateway_client.post(
        "/patients/condition-query",
        json={
            "conditions": [
                {
                    "moduleId": "basic",
                    "fieldId": "diagnosis",
                    "operator": "contains",
                    "value": "Fabry",
                    "value2": "",
                },
                {
                    "moduleId": "biomarker",
                    "fieldId": "dbsLysoGb3",
                    "operator": "gt",
                    "value": "5",
                    "value2": "",
                },
            ],
            "logic": "AND",
        },
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert [i["patientId"] for i in items] == [_FABRY_PID]
    # Both conditions should appear in conditionHits for the matched patient.
    hits = items[0]["conditionHits"]
    assert any("基本資料/主診斷" in h for h in hits)
    assert any("Biomarker/DBS LysoGb3" in h for h in hits)


def test_or_across_modules(gateway_client) -> None:
    """basic.diagnosis contains "Fabry" OR biomarker.dbsLysoGb3 > 100 → just the
    Fabry patient (nobody has dbsLysoGb3 > 100). Verifies union semantics."""
    r = gateway_client.post(
        "/patients/condition-query",
        json={
            "conditions": [
                {
                    "moduleId": "basic",
                    "fieldId": "diagnosis",
                    "operator": "contains",
                    "value": "Fabry",
                    "value2": "",
                },
                {
                    "moduleId": "biomarker",
                    "fieldId": "dbsLysoGb3",
                    "operator": "gt",
                    "value": "100",
                    "value2": "",
                },
            ],
            "logic": "OR",
        },
    )
    assert r.status_code == 200
    ids = [i["patientId"] for i in r.json()["items"]]
    assert _FABRY_PID in ids


def test_condition_query_paginates(gateway_client) -> None:
    """A broad condition is sliced into bounded, disjoint pages while
    ``total`` reports the full match count."""
    page1 = gateway_client.post(
        "/patients/condition-query",
        params={"limit": 5, "offset": 0},
        json=_MALE_CONDITION,
    )
    assert page1.status_code == 200
    b1 = page1.json()
    assert b1["limit"] == 5
    assert b1["offset"] == 0
    assert len(b1["items"]) == 5
    assert b1["total"] > 5  # broad condition matches well past one page

    page2 = gateway_client.post(
        "/patients/condition-query",
        params={"limit": 5, "offset": 5},
        json=_MALE_CONDITION,
    )
    assert page2.status_code == 200
    b2 = page2.json()
    # total is the full hit count, identical and stable across pages.
    assert b2["total"] == b1["total"]
    # Consecutive pages never overlap.
    ids1 = {i["patientId"] for i in b1["items"]}
    ids2 = {i["patientId"] for i in b2["items"]}
    assert ids1 & ids2 == set()


def test_condition_query_offset_past_end_is_empty(gateway_client) -> None:
    """An offset beyond ``total`` yields an empty page with status 200 and
    still reports the full match count."""
    full = gateway_client.post(
        "/patients/condition-query",
        params={"limit": 5, "offset": 0},
        json=_MALE_CONDITION,
    )
    total = full.json()["total"]

    r = gateway_client.post(
        "/patients/condition-query",
        params={"limit": 5, "offset": total + 100},
        json=_MALE_CONDITION,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == total


def test_condition_query_rejects_invalid_pagination(gateway_client) -> None:
    """Out-of-range limit/offset are rejected with HTTP 422."""
    for params in ({"limit": 0}, {"limit": 5000}, {"offset": -1}):
        r = gateway_client.post(
            "/patients/condition-query", params=params, json=_MALE_CONDITION
        )
        assert r.status_code == 422, params


def test_downstream_5xx_surfaces_as_502(gateway_client, monkeypatch) -> None:
    """If svc-lab returns 5xx, gateway must return 502 with ``service`` field."""

    async def _failing_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "boom"})

    routed = httpx.AsyncClient(
        mounts={
            "all://127.0.0.1:8001": httpx.ASGITransport(app=svc_patient_app),
            "all://127.0.0.1:8002": httpx.MockTransport(_failing_handler),
            "all://127.0.0.1:8003": httpx.ASGITransport(app=svc_disease_app),
        },
    )
    monkeypatch.setattr(gw_module, "_client", routed)

    r = gateway_client.post(
        "/patients/condition-query",
        json={
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
        },
    )
    assert r.status_code == 502
    assert r.json() == {"error": "upstream_unavailable", "service": "svc-lab"}
