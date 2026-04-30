"""``ref.command_phrase`` — interpretation phrase catalogue (← 1.0 ``COMMAND``).

D9 (the per-test-vs-global question) is still open in design notes. We
default to "global" (no test-type discriminator column) until production
data clarifies usage; if needed, add a ``test_type`` column in a follow-up.
"""

from __future__ import annotations

from shared.models.base import Base
from shared.models.ref._base import _RefMixin, ref_unique_code_constraint


class CommandPhrase(Base, _RefMixin):
    __tablename__ = "command_phrase"
    __table_args__ = (
        ref_unique_code_constraint("command_phrase"),
        {"schema": "ref"},
    )
