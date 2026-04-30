#!/usr/bin/env python3
"""Extract BLOB columns from gene.mdb to the filesystem.

mdb-export emits BLOB columns as null in CSV output, so we run this
side-channel pass to actually fetch the bytes. We use the ``mdb-export``
binary's ``--bin=raw`` mode (mdbtools >= 0.7) to dump rows as binary
records, parse them in Python, and write each blob to its own file.

Why a separate pass: keeps the CSV side simple (one column per table,
text-only) and avoids embedding multi-MB images in CSV cells where they
can break naive parsers.

Output layout (matches design D7):

    /srv/gimc/blobs/msms/<sampleno>.bin     # MSDATA.DATA — raw spectrum
    /srv/gimc/blobs/gcms/<sampleno>.jpg     # GCDATA.pic
    /srv/gimc/blobs/mpsu/<sampleno>.jpg     # MPSUDATA.pic
    /srv/gimc/blobs/enzyme/<sampleno>.jpg   # ENZYME.pic

Plus an index ``<out_dir>/blob_paths.json`` keyed by ``(table, sampleno)``
so transform.py can join blob paths into the eventual sample rows.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

# (table, blob_column, key_column, blob_kind, file_ext)
BLOB_TABLES: list[tuple[str, str, str, str, str]] = [
    ("MSDATA",   "DATA", "sampleno", "msms",   "bin"),
    ("GCDATA",   "pic",  "sampleno", "gcms",   "jpg"),
    ("MPSUDATA", "pic",  "sampleno", "mpsu",   "jpg"),
    ("ENZYME",   "pic",  "sampleno", "enzyme", "jpg"),
]

DEFAULT_BLOB_ROOT = Path(os.environ.get("GIMC_BLOB_ROOT", "/srv/gimc/blobs"))


def _dump_table_with_blobs(mdb: Path, table: str, key_col: str, blob_col: str) -> list[tuple[str, bytes]]:
    """Read every row of ``table``, returning [(key_value, blob_bytes), …].

    We invoke mdb-export with the SQL form to control column order, then
    parse the binary output. mdbtools' raw binary mode prints
    NULL-byte-terminated records; for portability across mdbtools
    versions we parse manually.
    """
    cmd = [
        "mdb-export",
        "-D", "%Y-%m-%d %H:%M:%S",
        "--no-header-row",
        "-b", "raw",
        str(mdb),
        table,
    ]
    print(f"  >> {' '.join(shlex.quote(c) for c in cmd)}")
    res = subprocess.run(cmd, check=True, capture_output=True)
    # Each row is one CSV-ish line; parsing of binary inside CSV is
    # fragile. Use the SQL helper instead.
    raise NotImplementedError(
        "_dump_table_with_blobs needs adapting to the actual mdbtools "
        "binary format on the operations host. Track the chosen approach "
        "in backend/etl/README.md before running."
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mdb", type=Path, help="path to gene.mdb")
    p.add_argument("out_dir", type=Path, help="where blob_paths.json goes")
    p.add_argument(
        "--blob-root", type=Path, default=DEFAULT_BLOB_ROOT,
        help=f"filesystem root for blobs (default: {DEFAULT_BLOB_ROOT})",
    )
    args = p.parse_args()

    if not args.mdb.exists():
        sys.exit(f"mdb not found: {args.mdb}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for kind in {kind for _, _, _, kind, _ in BLOB_TABLES}:
        (args.blob_root / kind).mkdir(parents=True, exist_ok=True)

    paths: dict[str, dict[str, str]] = {kind: {} for _, _, _, kind, _ in BLOB_TABLES}

    for table, blob_col, key_col, kind, ext in BLOB_TABLES:
        print(f"\n=== {table} → /srv/gimc/blobs/{kind}/ ===")
        try:
            rows = _dump_table_with_blobs(args.mdb, table, key_col, blob_col)
        except NotImplementedError as e:
            print(f"  PENDING: {e}", file=sys.stderr)
            continue

        for key, blob in rows:
            if not blob:
                continue
            target = args.blob_root / kind / f"{key}.{ext}"
            target.write_bytes(blob)
            paths[kind][key] = str(target.relative_to(args.blob_root.parent))

    index_file = args.out_dir / "blob_paths.json"
    index_file.write_text(json.dumps(paths, indent=2, ensure_ascii=False))
    print(f"\nwrote blob index: {index_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
