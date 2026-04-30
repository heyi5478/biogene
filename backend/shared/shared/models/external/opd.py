"""``external.opd`` — outpatient visits for outside referrals."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Opd(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "opd"
    __table_args__ = ({"schema": "external"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("external")

    visitDate: Mapped[date] = mapped_column("visit_date", nullable=False)
    sex: Mapped[str] = mapped_column(String(2), nullable=False)
    birthday: Mapped[date] = mapped_column(nullable=False)
    diagCode: Mapped[str] = mapped_column("diag_code", String(32), nullable=False)
    diagName: Mapped[str] = mapped_column("diag_name", String(256), nullable=False)
    subDiag1: Mapped[Optional[str]] = mapped_column("sub_diag1", String(256))
    subDiag2: Mapped[Optional[str]] = mapped_column("sub_diag2", String(256))
