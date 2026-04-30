"""Alembic environment for the gimc PostgreSQL database.

Spec contract (`postgres-data-backend`):
- ``include_schemas=True``  — auto-detect changes across all five schemas
- ``version_table_schema='public'``  — single shared migration history
- ``target_metadata`` is the union of every schema's MetaData (we keep one
  shared :class:`MetaData` on ``shared.models.base.Base``, so importing the
  ``shared.models`` package side-effect-registers everything we need)

Connection URL: read from ``DATABASE_URL`` env var. The async URL the
services use (``postgresql+asyncpg://``) is rewritten to the psycopg sync
driver here — alembic doesn't benefit from async and the sync path is
better-supported by the migration helpers.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import shared.models  # noqa: F401  — side-effect: register every table on metadata
from shared.models import metadata as target_metadata

# Alembic Config object
config = context.config

# File-based logging (alembic.ini → handlers/loggers)
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def _resolve_database_url() -> str:
    """Translate the runtime async URL into a sync URL alembic can use.

    Service code uses ``postgresql+asyncpg://``; alembic uses sync, so we swap
    the driver to ``psycopg`` (psycopg 3) which is in our deps.
    """
    url = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://gimc:gimc@localhost:5432/gimc"
    )
    return url.replace("+asyncpg", "+psycopg")


def run_migrations_offline() -> None:
    """Generate SQL that an operator can apply by hand without a live DB."""
    context.configure(
        url=_resolve_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()


def _include_object(object_, name, type_, reflected, compare_to) -> bool:
    """Filter out objects that alembic should leave alone during autogenerate.

    - ``alembic_version`` is alembic's own bookkeeping table; never drop.
    - PostGIS / extension-owned tables (none in this project today) would
      go here too.
    """
    if type_ == "table" and name == "alembic_version":
        return False
    return True


def run_migrations_online() -> None:
    """Connect to the live DB and apply pending revisions."""
    config.set_main_option("sqlalchemy.url", _resolve_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=_include_object,
            version_table_schema="public",
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
