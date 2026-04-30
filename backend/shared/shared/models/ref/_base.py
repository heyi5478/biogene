"""Shared shape for ``ref`` lookup tables — keep DRY across the five tables.

Each ref table has an autoincrement ``id`` PK, a unique ``code`` natural
key (the 1.0 source's itemno/methodno/phraseno) and a human-readable
``label``. ``description`` is free-form text. ETL provenance columns
mirror the sample-table convention.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column


class _RefMixin(TimestampsMixin, EtlMetaMixin):
    """Mixin providing ``id`` / ``code`` / ``label`` / ``description``."""

    id: Mapped[int] = id_pk_column()
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)


def ref_unique_code_constraint(table: str) -> UniqueConstraint:
    """Create the table-scoped UNIQUE constraint on ``code``."""
    return UniqueConstraint("code", name=f"uq_{table}_code")
