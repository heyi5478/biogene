"""``main.aa`` — amino-acid plasma panel."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Aa(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "aa"
    __table_args__ = (
        Index(
            "ix_aa_leu_notnull",
            "leu",
            postgresql_where=text("leu IS NOT NULL"),
        ),
        {"schema": "main"},
    )

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[str] = mapped_column("specimen_type", String(32), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    Gln: Mapped[Optional[Decimal]] = mapped_column("gln", Numeric(10, 3))
    Citr: Mapped[Optional[Decimal]] = mapped_column("citr", Numeric(10, 3))
    Ala: Mapped[Optional[Decimal]] = mapped_column("ala", Numeric(10, 3))
    Arg: Mapped[Optional[Decimal]] = mapped_column("arg", Numeric(10, 3))
    Leu: Mapped[Optional[Decimal]] = mapped_column("leu", Numeric(10, 3))
    Val: Mapped[Optional[Decimal]] = mapped_column("val", Numeric(10, 3))
    Phe: Mapped[Optional[Decimal]] = mapped_column("phe", Numeric(10, 3))
    Tyr: Mapped[Optional[Decimal]] = mapped_column("tyr", Numeric(10, 3))
