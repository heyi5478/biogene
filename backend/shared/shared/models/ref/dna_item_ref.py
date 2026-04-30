"""``ref.dna_item_ref`` — DNA-bank order catalogue (← 1.0 ``DNAITEM``)."""

from __future__ import annotations

from shared.models.base import Base
from shared.models.ref._base import _RefMixin, ref_unique_code_constraint


class DnaItemRef(Base, _RefMixin):
    __tablename__ = "dna_item_ref"
    __table_args__ = (
        ref_unique_code_constraint("dna_item_ref"),
        {"schema": "ref"},
    )
