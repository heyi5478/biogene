"""``nbs.dmd_tsh`` — TSH follow-ups attached to a DMD parent row.

FK: ``dmd_id`` references ``nbs.dmd(dmd_id)`` ON DELETE CASCADE. No direct
``patient_id`` column — the linkage is ``dmd_tsh → dmd → patient``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column


class DmdTsh(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "dmd_tsh"
    __table_args__ = (
        Index(
            "ix_dmd_tsh_tsh_notnull",
            "tsh",
            postgresql_where=text("tsh IS NOT NULL"),
        ),
        {"schema": "nbs"},
    )

    id: Mapped[int] = id_pk_column()
    dmdId: Mapped[str] = mapped_column(
        "dmd_id",
        String(64),
        ForeignKey(
            "nbs.dmd.dmd_id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    sampleId: Mapped[str] = mapped_column("sample_id", String(64), nullable=False)
    collectDate: Mapped[date] = mapped_column("collect_date", nullable=False)
    tsh: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
    result: Mapped[str] = mapped_column(String(64), nullable=False)
