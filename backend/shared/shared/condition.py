"""Condition evaluator ported one-to-one from
``frontend/src/components/ConditionResults.tsx`` (lines 237-279).

Reproduces the eleven-operator semantics so server-side condition matches
stay bit-equal with the pre-change browser-side ``evaluateConditions``
function. Imported by all three downstream services (svc-patient,
svc-lab, svc-disease) so each one shares the same evaluator.

The eleven operators:
    contains, eq, neq, gt, gte, lt, lte, between, before, after,
    has_data, no_data

Coercion mirrors JavaScript's ``Number()`` and ``String()`` so a value of
``None`` (which Python uses for both JSON ``null`` and missing keys) maps
to ``NaN`` for numeric comparisons (always fails) and ``"null"`` for
string comparisons (matches the JSON-loaded JS ``null`` path).
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

OPERATORS: tuple[str, ...] = (
    "contains",
    "eq",
    "neq",
    "gt",
    "gte",
    "lt",
    "lte",
    "between",
    "before",
    "after",
    "has_data",
    "no_data",
)


def _to_js_number(val: Any) -> float:
    if val is None:
        return math.nan
    if val is True:
        return 1.0
    if val is False:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if s == "":
            return 0.0
        try:
            return float(s)
        except ValueError:
            return math.nan
    return math.nan


def _to_js_string(val: Any) -> str:
    if val is None:
        return "null"
    if val is True:
        return "true"
    if val is False:
        return "false"
    if isinstance(val, float):
        if math.isnan(val):
            return "NaN"
        if math.isinf(val):
            return "Infinity" if val > 0 else "-Infinity"
        if val.is_integer():
            return str(int(val))
        return str(val)
    return str(val)


def eval_condition(
    record: Mapping[str, Any],
    field: str,
    op: str,
    value: str = "",
    value2: str = "",
) -> bool:
    val = record.get(field)

    if op == "has_data":
        return val is not None and val != ""
    if op == "no_data":
        return val is None or val == ""
    if op == "eq":
        return _to_js_string(val) == value
    if op == "neq":
        return _to_js_string(val) != value
    if op == "contains":
        haystack = (str(val) if val is not None else "").lower()
        return value.lower() in haystack
    if op in ("gt", "gte", "lt", "lte"):
        n = _to_js_number(val)
        v = _to_js_number(value)
        if math.isnan(n) or math.isnan(v):
            return False
        if op == "gt":
            return n > v
        if op == "gte":
            return n >= v
        if op == "lt":
            return n < v
        return n <= v
    if op == "between":
        n = _to_js_number(val)
        lo = _to_js_number(value)
        hi = _to_js_number(value2)
        if math.isnan(n) or math.isnan(lo) or math.isnan(hi):
            return False
        return lo <= n <= hi
    if op == "after":
        return _to_js_string(val) > value
    if op == "before":
        return _to_js_string(val) < value
    return False


def match_records(
    records: Iterable[Mapping[str, Any]],
    field: str,
    op: str,
    value: str = "",
    value2: str = "",
) -> bool:
    """True if any record in ``records`` satisfies the condition."""
    return any(eval_condition(rec, field, op, value, value2) for rec in records)


# ---------------------------------------------------------------------------
# Module / field metadata for hit summaries (port of MODULE_DEFINITIONS and
# MODULE_FIELDS in frontend/src/types/medical.ts; only the {code, label}
# pairs needed by getHitSummary in ConditionResults.tsx:281-299).
# ---------------------------------------------------------------------------

MODULE_CODES: dict[str, str] = {
    "basic": "基本資料",
    "opd": "OPD",
    "aadc": "AADC",
    "ald": "ALD",
    "mma": "MMA",
    "mps2": "MPS",
    "aa": "AA",
    "msms": "MS/MS",
    "biomarker": "Biomarker",
    "lsd": "LSD",
    "enzyme": "Enzyme",
    "gag": "GAG",
    "dnabank": "DNAbank",
    "outbank": "Outbank",
    "bd": "BD",
    "cah": "CAH",
    "dmd": "DMD",
    "g6pd": "G6PD",
    "smaScid": "SMA/SCID",
}

FIELD_LABELS: dict[str, dict[str, str]] = {
    "basic": {
        "chartno": "病歷號",
        "name": "姓名",
        "sex": "性別",
        "birthday": "生日",
        "diagnosis": "主診斷",
        "diagnosis2": "次診斷1",
        "diagnosis3": "次診斷2",
    },
    "opd": {
        "visitDate": "看診日",
        "diagCode": "主診斷碼",
        "diagName": "主診斷名稱",
        "subDiag1": "次診斷名稱1",
    },
    "aa": {
        "sampleName": "Sample Name",
        "specimenType": "檢體類別",
        "result": "Result",
        "Gln": "Gln",
        "Citr": "Citr",
        "Ala": "Ala",
        "Arg": "Arg",
        "Leu": "Leu",
        "Val": "Val",
        "Phe": "Phe",
        "Tyr": "Tyr",
    },
    "msms": {
        "sampleName": "Sample Name",
        "specimenType": "檢體類別",
        "result": "Result",
        "Ala": "Ala",
        "Arg": "Arg",
        "Cit": "Cit",
        "Gly": "Gly",
        "Leu": "Leu",
        "Met": "Met",
        "Phe": "Phe",
        "Tyr": "Tyr",
        "Val": "Val",
        "C0": "C0",
        "C2": "C2",
        "C3": "C3",
        "C5": "C5",
    },
    "biomarker": {
        "sampleName": "Sample Name",
        "dbsLysoGb3": "DBS LysoGb3",
        "dbsLysoGL1": "DBS LysoGL1",
        "dbsLysoSM": "DBS Lyso-SM",
        "plasmaLysoGb3": "Plasma LysoGb3",
        "plasmaLysoGL1": "Plasma LysoGL1",
        "plasmaLysoSM": "Plasma Lyso-SM",
    },
    "aadc": {"sampleName": "Sample Name", "conc": "濃度 (Conc)", "date": "日期"},
    "ald": {"sampleName": "Sample Name", "conc": "濃度 (Conc)", "date": "日期"},
    "mma": {"sampleName": "Sample Name", "conc": "濃度 (Conc)", "date": "日期"},
    "mps2": {
        "sampleName": "Sample Name",
        "MPS2": "MPS2",
        "TPP1": "TPP1",
        "MPS4A": "MPS4A",
        "MPS6": "MPS6",
    },
    "lsd": {
        "sampleName": "Sample Name",
        "GAA": "GAA",
        "GLA": "GLA",
        "ABG": "ABG",
        "IDUA": "IDUA",
        "ABG_GAA": "ABG/GAA",
    },
    "enzyme": {
        "sampleName": "Sample Name",
        "specimenType": "檢體類別",
        "result": "Result",
        "MPS1": "MPS1",
        "enzymeMPS2": "Enzyme-MPS2",
    },
    "gag": {
        "sampleName": "Sample Name",
        "specimenType": "檢體類別",
        "result": "Result",
        "DMGGAG": "DMGGAG",
        "CREATININE": "Creatinine",
    },
    "dnabank": {
        "orderno": "訂單編號",
        "order": "檢測項目",
        "orderMemo": "備註",
        "keyword": "關鍵字",
        "specimenno": "檢體編號",
        "specimen": "檢體類別",
    },
    "outbank": {
        "sampleno": "樣本編號",
        "shipdate": "送驗日期",
        "assay": "Assay",
        "result": "結果",
    },
    "bd": {
        "sampleId": "Sample ID",
        "collectDate": "採檢日期",
        "result": "Result",
        "biotinidaseActivity": "Biotinidase 活性",
    },
    "cah": {
        "sampleId": "Sample ID",
        "collectDate": "採檢日期",
        "result": "Result",
        "ohp17": "17-OHP",
    },
    "dmd": {
        "sampleId": "Sample ID",
        "collectDate": "採檢日期",
        "result": "Result",
        "ck": "CK",
    },
    "g6pd": {
        "sampleId": "Sample ID",
        "collectDate": "採檢日期",
        "result": "Result",
        "g6pdActivity": "G6PD 活性",
    },
    "smaScid": {
        "sampleId": "Sample ID",
        "collectDate": "採檢日期",
        "result": "Result",
        "smn1Copies": "SMN1 Copies",
        "trec": "TREC",
    },
}


def hit_summary(
    records: Iterable[Mapping[str, Any]],
    module_id: str,
    field: str,
) -> str | None:
    """Mirror ``getHitSummary`` from ConditionResults.tsx (lines 281-299).

    Returns ``"{moduleCode}/{fieldLabel}={value}"`` for the first record
    whose ``field`` is non-null/non-undefined, or ``None`` if no such
    record exists.
    """
    for rec in records:
        val = rec.get(field)
        if val is None:
            continue
        mod_code = MODULE_CODES.get(module_id, module_id)
        field_label = FIELD_LABELS.get(module_id, {}).get(field, field)
        return f"{mod_code}/{field_label}={_to_js_string(val)}"
    return None


__all__ = [
    "OPERATORS",
    "MODULE_CODES",
    "FIELD_LABELS",
    "eval_condition",
    "match_records",
    "hit_summary",
]
