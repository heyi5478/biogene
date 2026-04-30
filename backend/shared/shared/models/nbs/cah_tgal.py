"""``nbs.cah_tgal`` — Total Galactose follow-ups attached to a CAH parent row.

FK: ``cah_id`` references ``nbs.cah(cah_id)`` ON DELETE CASCADE. No direct
``patient_id`` column — the linkage is ``cah_tgal → cah → patient``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column


class CahTgal(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "cah_tgal"
    __table_args__ = ({"schema": "nbs"},)

    id: Mapped[int] = id_pk_column()
    cahId: Mapped[str] = mapped_column(
        "cah_id",
        String(64),
        ForeignKey(
            "nbs.cah.cah_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sampleId: Mapped[str] = mapped_column("sample_id", String(64), nullable=False)
    collectDate: Mapped[date] = mapped_column("collect_date", nullable=False)
    totalGalactose: Mapped[Optional[Decimal]] = mapped_column(
        "total_galactose", Numeric(10, 3)
    )
    result: Mapped[str] = mapped_column(String(64), nullable=False)
