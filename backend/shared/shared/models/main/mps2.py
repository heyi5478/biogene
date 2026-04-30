"""``main.mps2`` — Mucopolysaccharidoses panel (MPS2 / TPP1 / MPS4A / MPS6)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Mps2(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "mps2"
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    MPS2: Mapped[Optional[Decimal]] = mapped_column("mps2", Numeric(10, 3))
    TPP1: Mapped[Optional[Decimal]] = mapped_column("tpp1", Numeric(10, 3))
    MPS4A: Mapped[Optional[Decimal]] = mapped_column("mps4a", Numeric(10, 3))
    MPS6: Mapped[Optional[Decimal]] = mapped_column("mps6", Numeric(10, 3))
