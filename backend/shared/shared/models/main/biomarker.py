"""``main.biomarker`` — Lyso-Gb3 / Lyso-GL1 / Lyso-SM biomarker panel."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Biomarker(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "biomarker"
    __table_args__ = (
        Index(
            "ix_biomarker_lyso_high",
            "dbs_lyso_gb3",
            postgresql_where=text("dbs_lyso_gb3 > 5"),
        ),
        {"schema": "main"},
    )

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    dbsLysoGb3: Mapped[Optional[Decimal]] = mapped_column("dbs_lyso_gb3", Numeric(10, 3))
    dbsLysoGL1: Mapped[Optional[Decimal]] = mapped_column("dbs_lyso_gl1", Numeric(10, 3))
    dbsLysoSM: Mapped[Optional[Decimal]] = mapped_column("dbs_lyso_sm", Numeric(10, 3))
    plasmaLysoGb3: Mapped[Optional[Decimal]] = mapped_column("plasma_lyso_gb3", Numeric(10, 3))
    plasmaLysoGL1: Mapped[Optional[Decimal]] = mapped_column("plasma_lyso_gl1", Numeric(10, 3))
    plasmaLysoSM: Mapped[Optional[Decimal]] = mapped_column("plasma_lyso_sm", Numeric(10, 3))
