"""Cross-schema column mixins and FK factories.

Mixins inject identical timestamp/ETL columns into every sample table; the
``patient_id_fk_column`` factory wires the FK to the right ``{schema}.patient``
table without hardcoding a schema prefix in each model module.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Identity, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, MappedColumn, mapped_column


def id_pk_column() -> MappedColumn[int]:
    """``id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY``.

    Caller must still annotate ``id: Mapped[int] = id_pk_column()`` so the
    declarative form recognises the column as mapped.
    """
    return mapped_column(BigInteger, Identity(always=True), primary_key=True)


def patient_id_fk_column(schema: str) -> MappedColumn[uuid.UUID]:
    """``patient_id UUID NOT NULL`` referencing ``{schema}.patient.patient_id``.

    Caller must annotate ``patientId: Mapped[uuid.UUID] = patient_id_fk_column(...)``.
    """
    return mapped_column(
        "patient_id",
        UUID(as_uuid=True),
        ForeignKey(
            f"{schema}.patient.patient_id",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )


class TimestampsMixin:
    """``created_at`` / ``updated_at`` TIMESTAMPTZ DEFAULT now()."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EtlMetaMixin:
    """ETL provenance: which legacy sampleno / schema this row came from.

    Both nullable — populated by ``backend/etl/`` scripts during one-shot
    ingest, blank for rows seeded from JSON in dev.
    """

    ntubiogene_sampleno: Mapped[Optional[str]] = mapped_column(String(64))
    v2_source_schema: Mapped[Optional[str]] = mapped_column(String(32))


__all__ = [
    "id_pk_column",
    "patient_id_fk_column",
    "TimestampsMixin",
    "EtlMetaMixin",
]
