"""``nbs.cah`` — congenital adrenal hyperplasia screen.

Has child sub-table :class:`CahTgal` referenced via ``cah_id`` (UNIQUE).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Cah(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "cah"
    __table_args__ = (
        UniqueConstraint("cah_id", name="uq_cah_cah_id"),
        Index(
            "ix_cah_ohp17_notnull",
            "ohp17",
            postgresql_where=text("ohp17 IS NOT NULL"),
        ),
        {"schema": "nbs"},
    )

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("nbs")

    cahId: Mapped[str] = mapped_column("cah_id", String(64), nullable=False)
    sampleId: Mapped[str] = mapped_column("sample_id", String(64), nullable=False)
    collectDate: Mapped[date] = mapped_column("collect_date", nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    ohp17: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
