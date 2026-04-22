#!/usr/bin/env python3
"""Generate deterministic JSON mock data for db_main / db_external / db_nbs.

Usage:
    python backend/scripts/generate_mock.py

Writes ~36 JSON files under backend/mock-data/. Re-running on the same
seed data produces byte-identical output (UUID v5 with stable seeds).
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import NAMESPACE_OID, uuid5

ROOT = Path(__file__).resolve().parents[1] / "mock-data"


def pid(source: str, natural_key: str) -> str:
    """patientId = uuid5(NAMESPACE_OID, f'{source}:{naturalKey}')."""
    return str(uuid5(NAMESPACE_OID, f"{source}:{natural_key}"))


def rid(source: str, table: str, natural_key: str) -> str:
    """Sample/sub-row id = uuid5(NAMESPACE_OID, f'{source}:{table}:{naturalKey}')."""
    return str(uuid5(NAMESPACE_OID, f"{source}:{table}:{natural_key}"))


def write_table(db_dir: str, table: str, rows: list[dict]) -> None:
    out = ROOT / db_dir / f"{table}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# db_main — 14 tables: patient + 13 sample tables
# ---------------------------------------------------------------------------

MAIN_PATIENTS = [
    {
        "chartno": "A1234567",
        "name": "陳志明",
        "birthday": "1985-03-15",
        "sex": "男",
        "diagnosis": "Fabry disease (E75.21)",
        "diagnosis2": "Chronic kidney disease, stage 3 (N18.3)",
        "diagnosis3": "Left ventricular hypertrophy (I51.7)",
    },
    {
        "chartno": "B2345678",
        "name": "林雅婷",
        "birthday": "2018-07-22",
        "sex": "女",
        "diagnosis": "Phenylketonuria (E70.0)",
        "diagnosis2": "Developmental delay (F88)",
    },
    {
        "chartno": "C3456789",
        "name": "張偉翔",
        "birthday": "2020-01-08",
        "sex": "男",
        "diagnosis": "Mucopolysaccharidosis type II (E76.1)",
        "diagnosis2": "Hepatosplenomegaly (R16.2)",
        "diagnosis3": "Hearing loss (H91.9)",
    },
    {
        "chartno": "D4567890",
        "name": "黃淑芬",
        "birthday": "1992-11-03",
        "sex": "女",
        "diagnosis": "Gaucher disease type 1 (E75.22)",
    },
    {
        "chartno": "E5678901",
        "name": "王建國",
        "birthday": "2015-05-18",
        "sex": "男",
        "diagnosis": "AADC deficiency (E70.8)",
        "diagnosis2": "Dystonia (G24.9)",
    },
]


MAIN_OPD = {
    "A1234567": [
        {"visitDate": "2025-12-10", "sex": "男", "birthday": "1985-03-15", "diagCode": "E75.21", "diagName": "Fabry disease", "subDiag1": "Chronic kidney disease, stage 3"},
        {"visitDate": "2025-09-05", "sex": "男", "birthday": "1985-03-15", "diagCode": "E75.21", "diagName": "Fabry disease", "subDiag1": "Left ventricular hypertrophy"},
        {"visitDate": "2025-06-12", "sex": "男", "birthday": "1985-03-15", "diagCode": "E75.21", "diagName": "Fabry disease", "subDiag1": "Proteinuria"},
    ],
    "B2345678": [
        {"visitDate": "2025-11-28", "sex": "女", "birthday": "2018-07-22", "diagCode": "E70.0", "diagName": "Phenylketonuria", "subDiag1": "Developmental delay"},
        {"visitDate": "2025-08-15", "sex": "女", "birthday": "2018-07-22", "diagCode": "E70.0", "diagName": "Phenylketonuria", "subDiag1": "Growth retardation"},
    ],
    "C3456789": [
        {"visitDate": "2025-12-01", "sex": "男", "birthday": "2020-01-08", "diagCode": "E76.1", "diagName": "Mucopolysaccharidosis type II", "subDiag1": "Hepatosplenomegaly", "subDiag2": "Hearing loss"},
        {"visitDate": "2025-09-18", "sex": "男", "birthday": "2020-01-08", "diagCode": "E76.1", "diagName": "Mucopolysaccharidosis type II", "subDiag1": "Hepatosplenomegaly"},
        {"visitDate": "2025-06-20", "sex": "男", "birthday": "2020-01-08", "diagCode": "E76.1", "diagName": "Mucopolysaccharidosis type II", "subDiag1": "Growth retardation"},
        {"visitDate": "2025-03-10", "sex": "男", "birthday": "2020-01-08", "diagCode": "E76.1", "diagName": "Mucopolysaccharidosis type II", "subDiag1": "Hepatosplenomegaly"},
    ],
    "D4567890": [
        {"visitDate": "2025-10-22", "sex": "女", "birthday": "1992-11-03", "diagCode": "E75.22", "diagName": "Gaucher disease type 1", "subDiag1": "Thrombocytopenia"},
    ],
    "E5678901": [
        {"visitDate": "2025-11-15", "sex": "男", "birthday": "2015-05-18", "diagCode": "E70.8", "diagName": "AADC deficiency", "subDiag1": "Dystonia"},
        {"visitDate": "2025-08-20", "sex": "男", "birthday": "2015-05-18", "diagCode": "E70.8", "diagName": "AADC deficiency", "subDiag1": "Oculogyric crisis"},
    ],
}


MAIN_AA = {
    "A1234567": [
        {"sampleName": "AA-2025-0412", "specimenType": "Plasma", "result": "Normal", "Gln": 520, "Citr": 28, "Ala": 310, "Arg": 85, "Leu": 120, "Val": 195, "Phe": 52, "Tyr": 58},
    ],
    "B2345678": [
        {"sampleName": "AA-2025-0520", "specimenType": "Plasma", "result": "Abnormal", "Gln": 480, "Citr": 32, "Ala": 295, "Arg": 78, "Leu": 115, "Val": 188, "Phe": 890, "Tyr": 42},
        {"sampleName": "AA-2025-0318", "specimenType": "Plasma", "result": "Abnormal", "Gln": 510, "Citr": 30, "Ala": 305, "Arg": 82, "Leu": 122, "Val": 192, "Phe": 1120, "Tyr": 38},
    ],
    "E5678901": [
        {"sampleName": "AA-2025-0610", "specimenType": "CSF", "result": "Abnormal", "Gln": 380, "Citr": 22, "Ala": 245, "Arg": 65, "Leu": 98, "Val": 165, "Phe": 48, "Tyr": 35},
    ],
}


MAIN_MSMS = {
    "A1234567": [
        {"sampleName": "MS-2025-0388", "specimenType": "DBS", "result": "Normal", "Ala": 280, "Arg": 12.5, "Cit": 18.3, "Gly": 310, "Leu": 145, "Met": 22, "Phe": 48, "Tyr": 62, "Val": 155, "C0": 32, "C2": 18, "C3": 2.1, "C5": 0.18},
    ],
    "B2345678": [
        {"sampleName": "MS-2025-0492", "specimenType": "DBS", "result": "Abnormal", "Ala": 265, "Arg": 11.8, "Cit": 16.5, "Gly": 298, "Leu": 138, "Met": 20, "Phe": 385, "Tyr": 35, "Val": 148, "C0": 28, "C2": 16, "C3": 1.8, "C5": 0.15},
    ],
    "C3456789": [
        {"sampleName": "MS-2025-0510", "specimenType": "DBS", "result": "Normal", "Ala": 272, "Arg": 13.0, "Cit": 17.8, "Gly": 305, "Leu": 142, "Met": 21, "Phe": 50, "Tyr": 60, "Val": 152, "C0": 30, "C2": 17, "C3": 2.0, "C5": 0.16},
    ],
    "E5678901": [
        {"sampleName": "MS-2025-0598", "specimenType": "DBS", "result": "Normal", "Ala": 258, "Arg": 10.5, "Cit": 15.8, "Gly": 288, "Leu": 132, "Met": 18, "Phe": 45, "Tyr": 55, "Val": 142, "C0": 26, "C2": 14, "C3": 1.6, "C5": 0.14},
    ],
}


MAIN_BIOMARKER = {
    "A1234567": [
        {"sampleName": "BM-2025-0156", "dbsLysoGb3": 12.8, "dbsLysoGL1": 5.2, "dbsLysoSM": 28.4, "plasmaLysoGb3": 18.6, "plasmaLysoGL1": 7.8, "plasmaLysoSM": 32.1},
    ],
    "C3456789": [
        {"sampleName": "BM-2025-0210", "dbsLysoGb3": 3.2, "dbsLysoGL1": 2.1, "dbsLysoSM": 8.5},
    ],
    "D4567890": [
        {"sampleName": "BM-2025-0285", "dbsLysoGb3": 2.8, "dbsLysoGL1": 45.2, "dbsLysoSM": 12.5, "plasmaLysoGb3": 3.5, "plasmaLysoGL1": 68.8},
    ],
}


MAIN_AADC = {
    "A1234567": [{"sampleName": "AADC-2025-0089", "conc": 42.5, "date": "2025-10-15"}],
    "E5678901": [
        {"sampleName": "AADC-2025-0125", "conc": 2.8, "date": "2025-11-15"},
        {"sampleName": "AADC-2025-0098", "conc": 3.1, "date": "2025-08-20"},
    ],
}


MAIN_ALD = {
    "A1234567": [{"sampleName": "ALD-2025-0034", "conc": 0.85, "date": "2025-10-15"}],
}


MAIN_MMA = {
    "A1234567": [{"sampleName": "MMA-2025-0067", "conc": 0.32, "date": "2025-10-15"}],
    "B2345678": [{"sampleName": "MMA-2025-0095", "conc": 0.28, "date": "2025-09-20"}],
}


MAIN_MPS2 = {
    "A1234567": [{"sampleName": "MPS-2025-0045", "MPS2": 8.5, "TPP1": 12.3, "MPS4A": 15.8, "MPS6": 22.1}],
    "C3456789": [{"sampleName": "MPS-2025-0088", "MPS2": 1.2, "TPP1": 14.5, "MPS4A": 18.2, "MPS6": 25.6}],
}


MAIN_LSD = {
    "A1234567": [{"sampleName": "LSD-2025-0078", "GAA": 5.2, "GLA": 0.8, "ABG": 8.5, "IDUA": 12.3, "ABG_GAA": 1.63}],
    "C3456789": [{"sampleName": "LSD-2025-0120", "GAA": 6.8, "GLA": 4.2, "ABG": 9.1, "IDUA": 11.8, "ABG_GAA": 1.34}],
    "D4567890": [{"sampleName": "LSD-2025-0155", "GAA": 8.2, "GLA": 5.5, "ABG": 0.3, "IDUA": 14.2, "ABG_GAA": 0.04}],
}


MAIN_ENZYME = {
    "A1234567": [{"sampleName": "ENZ-2025-0112", "specimenType": "Leukocyte", "technician": "王小芳", "result": "Deficient", "MPS1": 2.1, "enzymeMPS2": 45.8}],
    "C3456789": [
        {"sampleName": "ENZ-2025-0178", "specimenType": "Leukocyte", "technician": "陳建宏", "result": "Deficient", "MPS1": 15.2, "enzymeMPS2": 0.8},
        {"sampleName": "ENZ-2025-0145", "specimenType": "Plasma", "technician": "王小芳", "result": "Deficient", "MPS1": 18.5, "enzymeMPS2": 1.2},
    ],
    "D4567890": [{"sampleName": "ENZ-2025-0201", "specimenType": "Leukocyte", "technician": "陳建宏", "result": "Deficient", "MPS1": 22.5, "enzymeMPS2": 48.2}],
}


MAIN_GAG = {
    "A1234567": [{"sampleName": "GAG-2025-0056", "specimenType": "Urine", "technician": "林美玲", "result": "Elevated", "DMGGAG": 185.2, "CREATININE": 42.5}],
    "C3456789": [
        {"sampleName": "GAG-2025-0098", "specimenType": "Urine", "technician": "林美玲", "result": "Elevated", "DMGGAG": 425.8, "CREATININE": 38.2},
        {"sampleName": "GAG-2025-0072", "specimenType": "Urine", "technician": "林美玲", "result": "Elevated", "DMGGAG": 398.5, "CREATININE": 40.1},
    ],
}


MAIN_DNABANK = {
    "A1234567": [{"orderno": "DNA-2025-001", "order": "GLA gene sequencing", "orderMemo": "Fabry suspected", "keyword": "Fabry;GLA", "specimenno": "D-2025-0128", "specimen": "Whole blood"}],
    "B2345678": [{"orderno": "DNA-2025-008", "order": "PAH gene sequencing", "orderMemo": "PKU confirmed", "keyword": "PKU;PAH", "specimenno": "D-2025-0256", "specimen": "Whole blood"}],
    "C3456789": [
        {"orderno": "DNA-2025-015", "order": "IDS gene sequencing", "orderMemo": "MPS II confirmed", "keyword": "MPS2;IDS;Hunter", "specimenno": "D-2025-0388", "specimen": "Whole blood"},
        {"orderno": "DNA-2025-016", "order": "IDS gene deletion analysis", "orderMemo": "", "keyword": "MPS2;IDS", "specimenno": "D-2025-0389", "specimen": "Fibroblast"},
    ],
    "D4567890": [{"orderno": "DNA-2025-022", "order": "GBA gene sequencing", "orderMemo": "Gaucher suspected", "keyword": "Gaucher;GBA", "specimenno": "D-2025-0456", "specimen": "Whole blood"}],
    "E5678901": [{"orderno": "DNA-2025-028", "order": "DDC gene sequencing", "orderMemo": "AADC deficiency", "keyword": "AADC;DDC", "specimenno": "D-2025-0512", "specimen": "Whole blood"}],
}


MAIN_OUTBANK = {
    "A1234567": [{"sampleno": "OUT-2025-0034", "shipdate": "2025-11-02", "assay": "GLA gene full sequencing", "result": "c.644A>G (p.N215S) heterozygous"}],
    "B2345678": [{"sampleno": "OUT-2025-0089", "shipdate": "2025-10-05", "assay": "PAH gene panel", "result": "c.728G>A (p.R243Q) compound heterozygous"}],
    "C3456789": [
        {"sampleno": "OUT-2025-0112", "shipdate": "2025-08-15", "assay": "IDS gene full analysis", "result": "c.1402C>T (p.R468W) hemizygous"},
        {"sampleno": "OUT-2025-0145", "shipdate": "2025-11-20", "assay": "MPS panel NGS", "result": "Pending"},
    ],
    "D4567890": [{"sampleno": "OUT-2025-0178", "shipdate": "2025-09-28", "assay": "GBA gene sequencing", "result": "c.1226A>G (p.N409S) homozygous"}],
    "E5678901": [{"sampleno": "OUT-2025-0201", "shipdate": "2025-07-10", "assay": "DDC gene analysis", "result": "c.714+4A>T splice site mutation homozygous"}],
}


# ---------------------------------------------------------------------------
# db_external — 9 tables: patient + opd + 7 lab tables
# ---------------------------------------------------------------------------

EXTERNAL_PATIENTS = [
    {"externalChartno": "X-HSPH-1001", "name": "外院001", "birthday": "1978-02-14", "sex": "男", "diagnosis": "Pompe disease (E74.02)", "category": "opd_case"},
    {"externalChartno": "X-KMUH-2044", "name": "外院002", "birthday": "2001-10-30", "sex": "女", "diagnosis": "Krabbe disease (E75.23)"},
    {"externalChartno": "X-NTUH-3150", "name": "外院003", "birthday": "1995-06-07", "sex": "男"},
]


EXTERNAL_OPD = {
    "X-HSPH-1001": [
        {"visitDate": "2025-10-12", "sex": "男", "birthday": "1978-02-14", "diagCode": "E74.02", "diagName": "Pompe disease", "subDiag1": "Muscle weakness"},
    ],
    "X-KMUH-2044": [
        {"visitDate": "2025-09-01", "sex": "女", "birthday": "2001-10-30", "diagCode": "E75.23", "diagName": "Krabbe disease"},
    ],
}


EXTERNAL_AA = {
    "X-NTUH-3150": [
        {"sampleName": "EXT-AA-0012", "specimenType": "Plasma", "result": "Abnormal", "Gln": 610, "Citr": 35, "Ala": 340, "Arg": 95, "Leu": 140, "Val": 210, "Phe": 250, "Tyr": 70},
    ],
}


EXTERNAL_MSMS = {
    "X-HSPH-1001": [
        {"sampleName": "EXT-MS-0023", "specimenType": "DBS", "result": "Abnormal", "Ala": 290, "Arg": 13.2, "Cit": 19.0, "Gly": 315, "Leu": 148, "Met": 23, "Phe": 52, "Tyr": 64, "Val": 160, "C0": 34, "C2": 19, "C3": 2.2, "C5": 0.2},
    ],
}


EXTERNAL_BIOMARKER = {
    "X-KMUH-2044": [
        {"sampleName": "EXT-BM-0015", "dbsLysoGb3": 2.1, "dbsLysoGL1": 3.0, "dbsLysoSM": 9.0},
    ],
}


EXTERNAL_LSD = {
    "X-HSPH-1001": [
        {"sampleName": "EXT-LSD-0008", "GAA": 0.6, "GLA": 7.8, "ABG": 10.2, "IDUA": 13.0, "ABG_GAA": 17.0},
    ],
}


EXTERNAL_ENZYME = {
    "X-HSPH-1001": [
        {"sampleName": "EXT-ENZ-0044", "specimenType": "Leukocyte", "technician": "外院Tech", "result": "Deficient", "MPS1": 20.0, "enzymeMPS2": 40.0},
    ],
    "X-KMUH-2044": [
        {"sampleName": "EXT-ENZ-0052", "specimenType": "Leukocyte", "technician": "外院Tech", "result": "Deficient", "MPS1": 18.0, "enzymeMPS2": 44.0},
    ],
}


EXTERNAL_GAG = {
    "X-NTUH-3150": [
        {"sampleName": "EXT-GAG-0003", "specimenType": "Urine", "technician": "外院Tech", "result": "Borderline", "DMGGAG": 180.0, "CREATININE": 50.0},
    ],
}


EXTERNAL_OUTBANK = {
    "X-HSPH-1001": [
        {"sampleno": "EXT-OUT-0077", "shipdate": "2025-09-10", "assay": "GAA gene sequencing", "result": "c.1935C>A (p.D645E) heterozygous"},
    ],
}


# ---------------------------------------------------------------------------
# db_nbs — 13 tables: patient + opd + 5 NBS modules + 2 sub-tables + 4 shared
# ---------------------------------------------------------------------------

NBS_PATIENTS = [
    {"nbsId": "NBS-2025-0001", "name": "新篩嬰001", "birthday": "2025-01-05", "sex": "男", "category": "nbs"},
    {"nbsId": "NBS-2025-0002", "name": "新篩嬰002", "birthday": "2025-02-18", "sex": "女", "category": "nbs"},
    {"nbsId": "NBS-2025-0003", "name": "新篩嬰003", "birthday": "2025-03-11", "sex": "男", "category": "nbs"},
    {"nbsId": "NBS-2025-0004", "name": "新篩嬰004", "birthday": "2025-03-27", "sex": "女", "category": "self_pay"},
    {"nbsId": "NBS-2025-0005", "name": "新篩嬰005", "birthday": "2025-04-02", "sex": "男", "category": "nbs"},
]


NBS_OPD = {
    "NBS-2025-0001": [
        {"visitDate": "2025-02-10", "sex": "男", "birthday": "2025-01-05", "diagCode": "Z13.228", "diagName": "NBS follow-up"},
    ],
    "NBS-2025-0004": [
        {"visitDate": "2025-04-05", "sex": "女", "birthday": "2025-03-27", "diagCode": "Z13.228", "diagName": "NBS follow-up", "subDiag1": "Self-pay extended panel"},
    ],
}


NBS_BD = {
    "NBS-2025-0001": [
        {"sampleId": "NBS-BD-0001", "collectDate": "2025-01-08", "result": "Normal", "biotinidaseActivity": 78.5},
    ],
    "NBS-2025-0002": [
        {"sampleId": "NBS-BD-0002", "collectDate": "2025-02-21", "result": "Abnormal", "biotinidaseActivity": 3.8},
    ],
    "NBS-2025-0003": [
        {"sampleId": "NBS-BD-0003", "collectDate": "2025-03-14", "result": "Normal", "biotinidaseActivity": 65.2},
    ],
}


NBS_CAH = {
    "NBS-2025-0001": [
        {"cahId": "NBS-CAH-0001", "sampleId": "NBS-CAH-S-0001", "collectDate": "2025-01-08", "result": "Normal", "ohp17": 18.5},
    ],
    "NBS-2025-0003": [
        {"cahId": "NBS-CAH-0003", "sampleId": "NBS-CAH-S-0003", "collectDate": "2025-03-14", "result": "Abnormal", "ohp17": 92.0},
    ],
}


NBS_CAH_TGAL = {
    "NBS-CAH-0003": [
        {"sampleId": "NBS-TGAL-0003a", "collectDate": "2025-03-20", "totalGalactose": 8.5, "result": "Normal"},
        {"sampleId": "NBS-TGAL-0003b", "collectDate": "2025-03-28", "totalGalactose": 6.2, "result": "Normal"},
    ],
}


NBS_DMD = {
    "NBS-2025-0002": [
        {"dmdId": "NBS-DMD-0002", "sampleId": "NBS-DMD-S-0002", "collectDate": "2025-02-21", "result": "Abnormal", "ck": 1250.0},
    ],
    "NBS-2025-0005": [
        {"dmdId": "NBS-DMD-0005", "sampleId": "NBS-DMD-S-0005", "collectDate": "2025-04-05", "result": "Normal", "ck": 180.0},
    ],
}


NBS_DMD_TSH = {
    "NBS-DMD-0002": [
        {"sampleId": "NBS-TSH-0002a", "collectDate": "2025-02-28", "tsh": 5.8, "result": "Normal"},
    ],
}


NBS_G6PD = {
    "NBS-2025-0001": [
        {"sampleId": "NBS-G6PD-0001", "collectDate": "2025-01-08", "result": "Normal", "g6pdActivity": 12.8},
    ],
    "NBS-2025-0004": [
        {"sampleId": "NBS-G6PD-0004", "collectDate": "2025-04-01", "result": "Abnormal", "g6pdActivity": 1.5},
    ],
    "NBS-2025-0005": [
        {"sampleId": "NBS-G6PD-0005", "collectDate": "2025-04-05", "result": "Normal", "g6pdActivity": 14.2},
    ],
}


NBS_SMA_SCID = {
    "NBS-2025-0001": [
        {"sampleId": "NBS-SS-0001", "collectDate": "2025-01-08", "result": "Normal", "smn1Copies": 2, "trec": 85.0},
    ],
    "NBS-2025-0002": [
        {"sampleId": "NBS-SS-0002", "collectDate": "2025-02-21", "result": "Abnormal", "smn1Copies": 0, "trec": 72.0},
    ],
    "NBS-2025-0005": [
        {"sampleId": "NBS-SS-0005", "collectDate": "2025-04-05", "result": "Abnormal", "smn1Copies": 2, "trec": 8.5},
    ],
}


# Shared tables for NBS (follow-up lab work)
NBS_AA = {
    "NBS-2025-0002": [
        {"sampleName": "NBS-AA-0002", "specimenType": "Plasma", "result": "Normal", "Gln": 490, "Citr": 27, "Ala": 305, "Arg": 80, "Leu": 118, "Val": 186, "Phe": 55, "Tyr": 58},
    ],
}


NBS_MSMS = {
    "NBS-2025-0001": [
        {"sampleName": "NBS-MS-0001", "specimenType": "DBS", "result": "Normal", "Ala": 275, "Arg": 12.8, "Cit": 17.5, "Gly": 300, "Leu": 140, "Met": 21, "Phe": 49, "Tyr": 60, "Val": 150, "C0": 29, "C2": 16, "C3": 1.9, "C5": 0.17},
    ],
    "NBS-2025-0002": [
        {"sampleName": "NBS-MS-0002", "specimenType": "DBS", "result": "Normal", "Ala": 280, "Arg": 12.0, "Cit": 18.0, "Gly": 308, "Leu": 144, "Met": 22, "Phe": 46, "Tyr": 58, "Val": 156, "C0": 30, "C2": 17, "C3": 2.0, "C5": 0.16},
    ],
}


NBS_BIOMARKER = {
    "NBS-2025-0004": [
        {"sampleName": "NBS-BM-0004", "dbsLysoGb3": 1.8, "dbsLysoGL1": 2.2, "dbsLysoSM": 7.5},
    ],
}


NBS_OUTBANK = {
    "NBS-2025-0002": [
        {"sampleno": "NBS-OUT-0002", "shipdate": "2025-03-01", "assay": "DMD MLPA", "result": "Exon 45 deletion"},
    ],
    "NBS-2025-0005": [
        {"sampleno": "NBS-OUT-0005", "shipdate": "2025-04-12", "assay": "SMN1/SMN2 copy number", "result": "SMN1 = 2, SMN2 = 1"},
    ],
}


# ---------------------------------------------------------------------------
# Build & write
# ---------------------------------------------------------------------------

def build_patient_rows(
    source: str,
    natural_key_field: str,
    patients: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for p in patients:
        row = {"patientId": pid(source, p[natural_key_field]), "source": source, **p, "linkedPatientIds": []}
        rows.append(row)
    return rows


def attach_patient_fk(
    source: str,
    key_map: dict[str, list[dict]],
) -> list[dict]:
    """Flatten {naturalKey: [rows]} → [row{patientId, ...}]."""
    out: list[dict] = []
    for natural_key, rows in key_map.items():
        patient_id = pid(source, natural_key)
        for row in rows:
            out.append({"patientId": patient_id, **row})
    return out


def attach_parent_fk(
    parent_id_field: str,
    key_map: dict[str, list[dict]],
) -> list[dict]:
    """For sub-tables: {parentId: [rows]} → [row{parentIdField: parentId, ...}]."""
    out: list[dict] = []
    for parent_id, rows in key_map.items():
        for row in rows:
            out.append({parent_id_field: parent_id, **row})
    return out


def build_main() -> None:
    source = "main"
    write_table("db_main", "patient", build_patient_rows(source, "chartno", MAIN_PATIENTS))
    write_table("db_main", "opd", attach_patient_fk(source,MAIN_OPD))
    write_table("db_main", "aa", attach_patient_fk(source,MAIN_AA))
    write_table("db_main", "msms", attach_patient_fk(source,MAIN_MSMS))
    write_table("db_main", "biomarker", attach_patient_fk(source,MAIN_BIOMARKER))
    write_table("db_main", "aadc", attach_patient_fk(source,MAIN_AADC))
    write_table("db_main", "ald", attach_patient_fk(source,MAIN_ALD))
    write_table("db_main", "mma", attach_patient_fk(source,MAIN_MMA))
    write_table("db_main", "mps2", attach_patient_fk(source,MAIN_MPS2))
    write_table("db_main", "lsd", attach_patient_fk(source,MAIN_LSD))
    write_table("db_main", "enzyme", attach_patient_fk(source,MAIN_ENZYME))
    write_table("db_main", "gag", attach_patient_fk(source,MAIN_GAG))
    write_table("db_main", "dnabank", attach_patient_fk(source,MAIN_DNABANK))
    write_table("db_main", "outbank", attach_patient_fk(source,MAIN_OUTBANK))


def build_external() -> None:
    source = "external"
    write_table("db_external", "patient", build_patient_rows(source, "externalChartno", EXTERNAL_PATIENTS))
    write_table("db_external", "opd", attach_patient_fk(source,EXTERNAL_OPD))
    write_table("db_external", "aa", attach_patient_fk(source,EXTERNAL_AA))
    write_table("db_external", "msms", attach_patient_fk(source,EXTERNAL_MSMS))
    write_table("db_external", "biomarker", attach_patient_fk(source,EXTERNAL_BIOMARKER))
    write_table("db_external", "lsd", attach_patient_fk(source,EXTERNAL_LSD))
    write_table("db_external", "enzyme", attach_patient_fk(source,EXTERNAL_ENZYME))
    write_table("db_external", "gag", attach_patient_fk(source,EXTERNAL_GAG))
    write_table("db_external", "outbank", attach_patient_fk(source,EXTERNAL_OUTBANK))


def build_nbs() -> None:
    source = "nbs"
    write_table("db_nbs", "patient", build_patient_rows(source, "nbsId", NBS_PATIENTS))
    write_table("db_nbs", "opd", attach_patient_fk(source,NBS_OPD))
    write_table("db_nbs", "bd", attach_patient_fk(source,NBS_BD))
    write_table("db_nbs", "cah", attach_patient_fk(source,NBS_CAH))
    write_table("db_nbs", "cah_tgal", attach_parent_fk("cahId", NBS_CAH_TGAL))
    write_table("db_nbs", "dmd", attach_patient_fk(source,NBS_DMD))
    write_table("db_nbs", "dmd_tsh", attach_parent_fk("dmdId", NBS_DMD_TSH))
    write_table("db_nbs", "g6pd", attach_patient_fk(source,NBS_G6PD))
    write_table("db_nbs", "sma_scid", attach_patient_fk(source,NBS_SMA_SCID))
    write_table("db_nbs", "aa", attach_patient_fk(source,NBS_AA))
    write_table("db_nbs", "msms", attach_patient_fk(source,NBS_MSMS))
    write_table("db_nbs", "biomarker", attach_patient_fk(source,NBS_BIOMARKER))
    write_table("db_nbs", "outbank", attach_patient_fk(source,NBS_OUTBANK))


def main() -> None:
    build_main()
    build_external()
    build_nbs()

    # Remove .gitkeep (no longer needed once JSON files exist)
    for d in ("db_main", "db_external", "db_nbs"):
        keep = ROOT / d / ".gitkeep"
        if keep.exists() and any(p.suffix == ".json" for p in (ROOT / d).iterdir()):
            keep.unlink()

    # Report
    for d in ("db_main", "db_external", "db_nbs"):
        files = sorted(p.name for p in (ROOT / d).iterdir() if p.suffix == ".json")
        print(f"{d}: {len(files)} files — {', '.join(files)}")


if __name__ == "__main__":
    main()
