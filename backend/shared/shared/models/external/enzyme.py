"""``external.enzyme`` — enzyme activity assays for outside referrals."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Enzyme(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "enzyme"
    __table_args__ = ({"schema": "external"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("external")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[str] = mapped_column("specimen_type", String(32), nullable=False)
    technician: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    MPS1: Mapped[Optional[Decimal]] = mapped_column("mps1", Numeric(10, 3))
    enzymeMPS2: Mapped[Optional[Decimal]] = mapped_column("enzyme_mps2", Numeric(10, 3))
