"""``ref.enzyme_item_ref`` — enzyme test catalogue (← 1.0 ``ENZYMEITEM``)."""

from __future__ import annotations

from shared.models.base import Base
from shared.models.ref._base import _RefMixin, ref_unique_code_constraint


class EnzymeItemRef(Base, _RefMixin):
    __tablename__ = "enzyme_item_ref"
    __table_args__ = (
        ref_unique_code_constraint("enzyme_item_ref"),
        {"schema": "ref"},
    )
