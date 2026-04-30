"""Shared PostgreSQL ENUM types reused across schemas.

Defined as :class:`sqlalchemy.dialects.postgresql.ENUM` with
``create_type=False`` so the types are owned by the alembic baseline
migration (``CREATE TYPE … AS ENUM …``), not by individual ``CREATE TABLE``
statements. This keeps schema/type ordering explicit in migrations and
lets multiple tables reuse the same type without races.

Type names are bare (no schema prefix) so they live in ``public`` and are
visible to every schema via ``search_path``.
"""

from __future__ import annotations

from sqlalchemy.dialects.postgresql import ENUM

SexEnum = ENUM(
    "男",
    "女",
    name="sex",
    create_type=False,
)

PatientSourceEnum = ENUM(
    "main",
    "external",
    "nbs",
    name="patient_source",
    create_type=False,
)

LinkKindEnum = ENUM(
    "same_person",
    "probable",
    "manual",
    name="link_kind",
    create_type=False,
)

__all__ = ["SexEnum", "PatientSourceEnum", "LinkKindEnum"]
