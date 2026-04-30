"""``main.aadc`` — Aromatic L-amino acid decarboxylase deficiency screen."""

from __future__ import annotations

import uuid
from datetime import date as DateT
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Aadc(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "aadc"
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    conc: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    date: Mapped[Optional[DateT]] = mapped_column()
