"""Thin re-export layer over ``backend/scripts/load_mock.py``.

Services import :func:`load_all` and :func:`validate` from this module instead
of reaching into ``scripts/`` directly, so that the scripts directory can be
reorganised without touching every service.

    from shared.data_loader import load_all, validate

When the mock-data layer is eventually replaced by SQLAlchemy, only this file
(and the script it wraps) needs to change.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from load_mock import load_all, validate  # noqa: E402  (re-export after path fix)

__all__ = ["load_all", "validate"]
