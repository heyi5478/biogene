"""``ref`` schema — lookup tables seeded from the 1.0 reference DB.

These are small, slow-changing dimension tables loaded once from
``gene.mdb`` (see §10.3). The 1.0 source tables (``AAM``, ``MSM``,
``DNAITEM``, ``ENZYMEITEM``, ``COMMAND``) had varying column sets; we
unify them under a generic ``(code, label, description)`` shape and add
table-specific columns as the actual contents are surveyed.
"""

from .aa_method_ref import AaMethodRef
from .msms_method_ref import MsmsMethodRef
from .enzyme_item_ref import EnzymeItemRef
from .dna_item_ref import DnaItemRef
from .command_phrase import CommandPhrase

__all__ = [
    "AaMethodRef",
    "MsmsMethodRef",
    "EnzymeItemRef",
    "DnaItemRef",
    "CommandPhrase",
]
