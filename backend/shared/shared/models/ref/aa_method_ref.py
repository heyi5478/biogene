"""``ref.aa_method_ref`` — amino-acid analyser method catalogue (← 1.0 ``AAM``)."""

from __future__ import annotations

from shared.models.base import Base
from shared.models.ref._base import _RefMixin, ref_unique_code_constraint


class AaMethodRef(Base, _RefMixin):
    __tablename__ = "aa_method_ref"
    __table_args__ = (
        ref_unique_code_constraint("aa_method_ref"),
        {"schema": "ref"},
    )
