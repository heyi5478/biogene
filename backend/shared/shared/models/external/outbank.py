"""``external.outbank`` — out-shipped sample log for outside referrals."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Outbank(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "outbank"
    __table_args__ = ({"schema": "external"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("external")

    sampleno: Mapped[str] = mapped_column(String(64), nullable=False)
    shipdate: Mapped[date] = mapped_column(nullable=False)
    assay: Mapped[str] = mapped_column(String(256), nullable=False)
    result: Mapped[str] = mapped_column(String(512), nullable=False)
