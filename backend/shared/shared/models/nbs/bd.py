"""``nbs.bd`` — biotinidase deficiency screen."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Bd(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "bd"
    __table_args__ = ({"schema": "nbs"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("nbs")

    sampleId: Mapped[str] = mapped_column("sample_id", String(64), nullable=False)
    collectDate: Mapped[date] = mapped_column("collect_date", nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    biotinidaseActivity: Mapped[Optional[Decimal]] = mapped_column(
        "biotinidase_activity", Numeric(10, 3)
    )
