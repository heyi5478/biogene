"""``main.lsd`` — Lysosomal storage disease enzyme panel (GAA / GLA / ABG / IDUA)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Lsd(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "lsd"
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    GAA: Mapped[Optional[Decimal]] = mapped_column("gaa", Numeric(10, 3))
    GLA: Mapped[Optional[Decimal]] = mapped_column("gla", Numeric(10, 3))
    ABG: Mapped[Optional[Decimal]] = mapped_column("abg", Numeric(10, 3))
    IDUA: Mapped[Optional[Decimal]] = mapped_column("idua", Numeric(10, 3))
    ABG_GAA: Mapped[Optional[Decimal]] = mapped_column("abg_gaa", Numeric(10, 3))
