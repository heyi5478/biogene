"""``main.patient`` — base patient record for in-house cases."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models.enums import PatientSourceEnum, SexEnum
from shared.models._common import TimestampsMixin


class Patient(Base, TimestampsMixin):
    __tablename__ = "patient"
    __table_args__ = (
        Index("ix_patient_name", "name"),
        Index("ix_patient_birthday", "birthday"),
        {"schema": "main"},
    )

    patientId: Mapped[uuid.UUID] = mapped_column(
        "patient_id", UUID(as_uuid=True), primary_key=True
    )
    source: Mapped[str] = mapped_column(PatientSourceEnum, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    birthday: Mapped[date] = mapped_column(nullable=False)
    sex: Mapped[str] = mapped_column(SexEnum, nullable=False)
    chartno: Mapped[Optional[str]] = mapped_column(String(32))
    externalChartno: Mapped[Optional[str]] = mapped_column("external_chartno", String(32))
    nbsId: Mapped[Optional[str]] = mapped_column("nbs_id", String(32))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    diagnosis: Mapped[Optional[str]] = mapped_column(String(256))
    diagnosis2: Mapped[Optional[str]] = mapped_column(String(256))
    diagnosis3: Mapped[Optional[str]] = mapped_column(String(256))
    # Added by 1.0 ETL (§8.6) — populated from the legacy `patient`
    # Chinese-named table (referring physician); always null for 2.0 rows.
    referring_doctor: Mapped[Optional[str]] = mapped_column(String(64))
