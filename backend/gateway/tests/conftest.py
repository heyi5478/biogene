"""Gateway test harness — wires the downstream FastAPI apps in-process.

Instead of spinning up uvicorn workers on ports 8001/8002/8003, we mount
each downstream app via ``httpx.ASGITransport`` and rebind the gateway's
module-level ``_client`` to that routed transport. The downstream
lifespans are triggered through their own ``TestClient.__enter__`` so
their in-memory caches are populated before the gateway receives any
request.
"""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from gateway import app as gw_module
from gateway.app import app as gateway_app
from svc_disease.app import app as svc_disease_app
from svc_lab.app import app as svc_lab_app
from svc_patient.app import app as svc_patient_app


@pytest.fixture(scope="session")
def downstream_lifespans():
    """Trigger downstream lifespans once for the test session."""
    with TestClient(svc_patient_app), TestClient(svc_lab_app), TestClient(svc_disease_app):
        yield


@pytest.fixture()
def gateway_client(downstream_lifespans):
    """Yield a TestClient whose downstream calls hit in-process ASGI apps."""
    with TestClient(gateway_app) as client:
        # Replace the lifespan-created _client with one routed to in-process apps.
        # The gateway's lifespan teardown will close whatever _client points to.
        gw_module._client = httpx.AsyncClient(
            mounts={
                "all://127.0.0.1:8001": httpx.ASGITransport(app=svc_patient_app),
                "all://127.0.0.1:8002": httpx.ASGITransport(app=svc_lab_app),
                "all://127.0.0.1:8003": httpx.ASGITransport(app=svc_disease_app),
            },
        )
        yield client
