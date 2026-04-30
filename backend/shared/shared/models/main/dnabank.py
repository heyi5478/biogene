"""``main.dnabank`` — DNA bank order/specimen log (only in main schema)."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models._common import EtlMetaMixin, TimestampsMixin, id_pk_column, patient_id_fk_column


class Dnabank(Base, TimestampsMixin, EtlMetaMixin):
    __tablename__ = "dnabank"
    __table_args__ = ({"schema": "main"},)

    id: Mapped[int] = id_pk_column()
    patientId: Mapped[uuid.UUID] = patient_id_fk_column("main")

    orderno: Mapped[str] = mapped_column(String(64), nullable=False)
    # NOTE: ``order`` is a reserved word in SQL — quoted by SQLAlchemy automatically
    # because we set the column name explicitly to lowercase ``order``.
    order: Mapped[str] = mapped_column(String(256), nullable=False)
    orderMemo: Mapped[Optional[str]] = mapped_column("order_memo", String(256))
    keyword: Mapped[Optional[str]] = mapped_column(String(256))
    specimenno: Mapped[str] = mapped_column(String(64), nullable=False)
    specimen: Mapped[str] = mapped_column(String(64), nullable=False)
