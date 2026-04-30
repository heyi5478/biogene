"""Row-count baseline for verify.py check #1 (§11.1).

In DEV the baseline is the mock JSON under ``backend/mock-data/``.
In production, replace this dict with one generated from the source 2.0
MySQL databases (e.g. ``mysql -e "SELECT 'main', 'patient', COUNT(*) FROM
\`2.0\`.patient ..."`` piped into a script that emits this shape).

Top-level keys are mock-data dir names (so they match the dict key
returned by ``data_loader.load_all()``); inner keys are table names.
"""

EXPECTED_COUNTS: dict[str, dict[str, int]] = {
    "db_main": {
        "patient": 5,
        "aa": 4,
        "msms": 4,
        "biomarker": 3,
        "opd": 12,
        "dnabank": 6,
        "outbank": 6,
        "enzyme": 4,
        "aadc": 3,
        "ald": 1,
        "mma": 2,
        "mps2": 2,
        "lsd": 3,
        "gag": 3,
    },
    "db_external": {
        "patient": 3,
        "aa": 1,
        "msms": 1,
        "biomarker": 1,
        "opd": 2,
        "outbank": 1,
        "enzyme": 2,
        "lsd": 1,
        "gag": 1,
    },
    "db_nbs": {
        "patient": 5,
        "aa": 1,
        "msms": 2,
        "biomarker": 1,
        "opd": 2,
        "outbank": 2,
        "bd": 3,
        "cah": 2,
        "cah_tgal": 2,
        "dmd": 2,
        "dmd_tsh": 1,
        "g6pd": 3,
        "sma_scid": 3,
    },
}
