"""``external.msms`` — tandem MS/MS DBS panel for outside referrals."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Msms(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "msms"
    __table_args__ = ({"schema": "external"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("external")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[str] = mapped_column("specimen_type", String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    Ala: Mapped[Optional[Decimal]] = mapped_column("ala", Numeric(10, 3))
    Arg: Mapped[Optional[Decimal]] = mapped_column("arg", Numeric(10, 3))
    Cit: Mapped[Optional[Decimal]] = mapped_column("cit", Numeric(10, 3))
    Gly: Mapped[Optional[Decimal]] = mapped_column("gly", Numeric(10, 3))
    Leu: Mapped[Optional[Decimal]] = mapped_column("leu", Numeric(10, 3))
    Met: Mapped[Optional[Decimal]] = mapped_column("met", Numeric(10, 3))
    Phe: Mapped[Optional[Decimal]] = mapped_column("phe", Numeric(10, 3))
    Tyr: Mapped[Optional[Decimal]] = mapped_column("tyr", Numeric(10, 3))
    Val: Mapped[Optional[Decimal]] = mapped_column("val", Numeric(10, 3))
    C0: Mapped[Optional[Decimal]] = mapped_column("c0", Numeric(10, 3))
    C2: Mapped[Optional[Decimal]] = mapped_column("c2", Numeric(10, 3))
    C3: Mapped[Optional[Decimal]] = mapped_column("c3", Numeric(10, 3))
    C5: Mapped[Optional[Decimal]] = mapped_column("c5", Numeric(10, 3))
