"""``links`` schema — cross-schema patient linkage junction.

Replaces the in-memory ``linkedPatientIds: list[str]`` field on Patient with
a normalised junction table. Each logical link is stored once, with
``patient_id_a < patient_id_b`` (lexicographic UUID order) enforced via
CHECK so we never see ``(X,Y)`` and ``(Y,X)`` both inserted.

No FKs — the two ends of a link can come from any of ``main``, ``external``,
``nbs``. PostgreSQL FKs don't fan out polymorphically across schemas, so we
rely on (a) an INSERT trigger to be added later that verifies both IDs
exist somewhere, and (b) a nightly orphan audit (see ``backend/etl/verify.py``).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, PrimaryKeyConstraint, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base
from shared.models.enums import LinkKindEnum


class PatientLink(Base):
    __tablename__ = "patient_link"
    __table_args__ = (
        PrimaryKeyConstraint("patient_id_a", "patient_id_b", name="pk_patient_link"),
        CheckConstraint(
            "patient_id_a < patient_id_b",
            name="patient_link_canonical_pair",
        ),
        Index("ix_link_b", "patient_id_b"),
        {"schema": "links"},
    )

    patient_id_a: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    patient_id_b: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    link_kind: Mapped[str] = mapped_column(LinkKindEnum, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
