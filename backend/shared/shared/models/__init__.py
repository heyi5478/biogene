"""SQLAlchemy 2.0 declarative models for the `gimc` PostgreSQL database.

Five sub-packages, one per schema:

- :mod:`shared.models.main`    — public test/disease tables for in-house patients
- :mod:`shared.models.external` — same record types for outside referrals (no dnabank)
- :mod:`shared.models.nbs`     — newborn screening, including `cah_tgal` / `dmd_tsh` sub-tables
- :mod:`shared.models.links`   — cross-schema patient linkage (`patient_link` junction)
- :mod:`shared.models.ref`     — lookup tables seeded from the 1.0 reference DB

The :data:`metadata` exported here is the union of all five schemas' MetaData
objects — alembic's ``env.py`` uses it as ``target_metadata``.
"""

from __future__ import annotations

from .base import Base, metadata

# Side-effect imports register every table on the shared MetaData object so
# alembic's ``target_metadata`` sees them without each migration having to
# re-import them. Order doesn't matter (autogen sorts by FK dependencies).
from . import main as _main  # noqa: F401, E402
from . import external as _external  # noqa: F401, E402
from . import nbs as _nbs  # noqa: F401, E402
from . import links as _links  # noqa: F401, E402
from . import ref as _ref  # noqa: F401, E402

__all__ = ["Base", "metadata"]
