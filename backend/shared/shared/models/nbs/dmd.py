"""``nbs.dmd`` — Duchenne muscular dystrophy screen.

Has child sub-table :class:`DmdTsh` referenced via ``dmd_id`` (UNIQUE).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Dmd(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "dmd"
    __table_args__ = (
        UniqueConstraint("dmd_id", name="uq_dmd_dmd_id"),
        {"schema": "nbs"},
    )

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("nbs")

    dmdId: Mapped[str] = mapped_column("dmd_id", String(64), nullable=False)
    sampleId: Mapped[str] = mapped_column("sample_id", String(64), nullable=False)
    collectDate: Mapped[date] = mapped_column("collect_date", nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    ck: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
