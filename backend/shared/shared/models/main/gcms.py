"""``main.gcms`` — Gas chromatography / MS records (1.0 GCDATA).

No 2.0 equivalent. Raw spectrum images (GCDATA.pic) live under
``/srv/gimc/blobs/gcms/<sampleno>.jpg``; we store only the path.
"""

from __future__ import annotations

import uuid
from datetime import date as DateT
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Gcms(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "gcms"
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    sampleName: Mapped[str] = mapped_column("sample_name", String(64), nullable=False)
    specimenType: Mapped[Optional[str]] = mapped_column("specimen_type", String(32))
    result: Mapped[Optional[str]] = mapped_column(String(64))
    rawDataPath: Mapped[Optional[str]] = mapped_column("raw_data_path", Text)
    collectDate: Mapped[Optional[DateT]] = mapped_column("collect_date")
    notes: Mapped[Optional[str]] = mapped_column(Text)
