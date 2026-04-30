"""``external.gag`` — Glycosaminoglycan urine panel for outside referrals."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Gag(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "gag"
    __table_args__ = ({"schema": "external"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("external")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[str] = mapped_column("specimen_type", String(32), nullable=False)
    technician: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    DMGGAG: Mapped[Optional[Decimal]] = mapped_column("dmggag", Numeric(10, 3))
    CREATININE: Mapped[Optional[Decimal]] = mapped_column("creatinine", Numeric(10, 3))
