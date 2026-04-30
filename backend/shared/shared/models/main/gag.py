"""``main.gag`` — Glycosaminoglycan urine panel.

Will be widened by §8.4 (the 1.0 ETL) to also store ``od``,
``urine_creatinine``, ``mggag``, ``twos``, ``twos_cre`` from the legacy
MPSUDATA table. For now the v2 column set matches schemas.GagRecord.
"""

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
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[str] = mapped_column("specimen_type", String(32), nullable=False)
    technician: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    DMGGAG: Mapped[Optional[Decimal]] = mapped_column("dmggag", Numeric(10, 3))
    CREATININE: Mapped[Optional[Decimal]] = mapped_column("creatinine", Numeric(10, 3))
    # 1.0 ETL widening (§8.4) — absorbs the full MPSUDATA panel.
    od: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    urineCreatinine: Mapped[Optional[Decimal]] = mapped_column("urine_creatinine", Numeric(10, 3))
    mggag: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    twos: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    twosCre: Mapped[Optional[Decimal]] = mapped_column("twos_cre", Numeric(10, 3))
