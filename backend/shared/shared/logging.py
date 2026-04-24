"""Shared FastAPI logging helpers used by every backend service.

Three public helpers:

* :func:`configure_logging` — reads ``LOG_LEVEL`` (default ``INFO``) and wires
  :func:`logging.basicConfig` once per process.
* :func:`install_middleware` — one HTTP middleware that owns request-id
  generation, response-header echo, and the access-log line.
* :func:`install_exception_handlers` — catch-all ``Exception`` handler that
  logs a stack trace and returns ``500 {"error": "internal", "requestId": rid}``.

Services wire these in right after ``app = FastAPI(...)``::

    from shared.logging import (
        configure_logging, install_middleware, install_exception_handlers,
    )

    log = configure_logging("svc-lab")
    app = FastAPI(title="svc-lab", lifespan=lifespan)
    install_middleware(app, log)
    install_exception_handlers(app, log)
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"


def configure_logging(service_name: str) -> logging.Logger:
    """Configure root logging from ``LOG_LEVEL`` and return the service logger."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format=_LOG_FORMAT)
    return logging.getLogger(service_name)


def install_middleware(app: FastAPI, log: logging.Logger) -> None:
    """Register the request-id + access-log middleware on ``app``."""

    @app.middleware("http")
    async def _access_log(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = rid

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        response.headers["X-Request-ID"] = rid

        client = request.client.host if request.client else "-"
        ua = request.headers.get("user-agent", "-")
        req_bytes = request.headers.get("content-length", "-")

        log.info(
            'request_id=%s method=%s path=%s status=%d elapsed_ms=%.1f '
            'client=%s ua="%s" req_bytes=%s',
            rid,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            client,
            ua,
            req_bytes,
        )
        return response


def install_exception_handlers(app: FastAPI, log: logging.Logger) -> None:
    """Register the catch-all ``Exception`` handler on ``app``.

    Existing ``HTTPException`` / ``StarletteHTTPException`` handlers take
    precedence (FastAPI dispatches by exception-type specificity), so the
    domain-specific 404 / 502 responses in gateway and svc-patient are
    unaffected.
    """

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", None) or "-"
        log.exception(
            "unhandled error request_id=%s path=%s", rid, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"error": "internal", "requestId": rid},
        )
