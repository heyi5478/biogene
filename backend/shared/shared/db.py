"""Async SQLAlchemy engine + session helpers for the PostgreSQL backend.

Service code should import :func:`get_session` and :func:`get_engine` from
this module; nothing else should construct engines, so connection-pool
sizing stays in one place.

Configuration comes from the ``DATABASE_URL`` env var (see
``backend/.env.example``). Default driver is ``postgresql+asyncpg``.

Pool sizing follows design D5: ``pool_size=5, max_overflow=10`` per service
process. Four services × 15 = 60 < PostgreSQL default ``max_connections=100``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Final

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

_DEFAULT_URL: Final = "postgresql+asyncpg://gimc:gimc@localhost:5432/gimc"

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

_sync_engine: Engine | None = None
_sync_session_factory: sessionmaker[Session] | None = None


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", _DEFAULT_URL)


def _sync_url(async_url: str) -> str:
    """Translate the async URL the services use to a sync (psycopg) URL.

    The env var is documented as ``postgresql+asyncpg://…`` so
    SQLAlchemy's async engine can pick it up. The sync code paths
    (alembic, data_loader's postgres branch, ETL scripts) need
    ``+psycopg``.
    """
    return async_url.replace("+asyncpg", "+psycopg")


def get_engine() -> AsyncEngine:
    """Lazy-initialise and return the process-wide async engine."""
    global _engine, _session_factory
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            future=True,
        )
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an :class:`AsyncSession` bound to the process engine.

    Usage::

        async with get_session() as session:
            result = await session.execute(stmt)

    Commits are the caller's responsibility; this helper only handles the
    connection lifecycle and rollback on exception.
    """
    if _session_factory is None:
        get_engine()
    assert _session_factory is not None
    session = _session_factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Close all pooled connections — call from FastAPI shutdown hooks."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_sync_engine() -> Engine:
    """Lazy-initialise and return the process-wide *sync* engine.

    Used by data_loader's postgres branch and by ETL scripts. Driver is
    psycopg 3 (translated from the async URL).
    """
    global _sync_engine, _sync_session_factory
    if _sync_engine is None:
        _sync_engine = create_engine(
            _sync_url(get_database_url()),
            pool_size=2,
            max_overflow=4,
            pool_pre_ping=True,
            future=True,
        )
        _sync_session_factory = sessionmaker(_sync_engine, expire_on_commit=False)
    return _sync_engine


def get_sync_session() -> Session:
    """Return a new sync :class:`Session`. Caller is responsible for closing."""
    if _sync_session_factory is None:
        get_sync_engine()
    assert _sync_session_factory is not None
    return _sync_session_factory()


def dispose_sync_engine() -> None:
    global _sync_engine, _sync_session_factory
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _sync_session_factory = None
