"""``nbs`` schema — newborn screening (pre-existing 2.0 ``new_born_screening`` MySQL DB).

Two parent/child pairs of native tables (not JSONB):
- ``cah`` ← ``cah_tgal`` (Total Galactose follow-ups; ``cah_id`` FK ON DELETE CASCADE)
- ``dmd`` ← ``dmd_tsh`` (TSH follow-ups; ``dmd_id`` FK ON DELETE CASCADE)
"""

from .patient import Patient
from .aa import Aa
from .msms import Msms
from .biomarker import Biomarker
from .opd import Opd
from .outbank import Outbank
from .bd import Bd
from .cah import Cah
from .cah_tgal import CahTgal
from .dmd import Dmd
from .dmd_tsh import DmdTsh
from .g6pd import G6pd
from .sma_scid import SmaScid

__all__ = [
    "Patient",
    "Aa",
    "Msms",
    "Biomarker",
    "Opd",
    "Outbank",
    "Bd",
    "Cah",
    "CahTgal",
    "Dmd",
    "DmdTsh",
    "G6pd",
    "SmaScid",
]
