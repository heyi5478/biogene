"""``external`` schema — outside-referral patients (pre-existing 2.0 ``2.0外院資料庫`` MySQL DB).

Same record set as ``main`` minus ``dnabank`` (DNA bank is in-house only).
``§12.3`` of the change adds ``lsd``, ``gag``, and external-specific tables
that mirror ``main``'s disease modules.
"""

from .patient import Patient
from .aa import Aa
from .msms import Msms
from .biomarker import Biomarker
from .opd import Opd
from .outbank import Outbank
from .enzyme import Enzyme
from .lsd import Lsd
from .gag import Gag

__all__ = [
    "Patient",
    "Aa",
    "Msms",
    "Biomarker",
    "Opd",
    "Outbank",
    "Enzyme",
    "Lsd",
    "Gag",
]
