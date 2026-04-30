"""``ref.msms_method_ref`` — MS/MS method catalogue (← 1.0 ``MSM``)."""

from __future__ import annotations

from shared.models.base import Base
from shared.models.ref._base import _RefMixin, ref_unique_code_constraint


class MsmsMethodRef(Base, _RefMixin):
    __tablename__ = "msms_method_ref"
    __table_args__ = (
        ref_unique_code_constraint("msms_method_ref"),
        {"schema": "ref"},
    )
