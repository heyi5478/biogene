#!/usr/bin/env python3
"""One-off transform+load for ntubiogene gene.mdb backup → PostgreSQL.

Bypasses backend/etl/transform.py + load_pg.py because they expect a
schema where sample tables key on `chartno`. This .mdb keys on `no`
(sampleno) and the patient link is recovered via the `sample` table.

Empirically validated join (≥99.9% hit on five lab tables):

    <LAB>.no  =  sample.sampleno  →  sample.chartno  →  patient_id

Where patient_id = uuid5(NAMESPACE_OID, "main:" + chartno), matching
backend/etl/transform.py's existing convention.

Tables loaded:
  main.patient   from ptinfo + 中文 patient table (COALESCE merge on PK)
  main.aa        from AADATA   (sample item=AA)
  main.msms      from MSDATA   (sample item=MS/MS) — numeric values left NULL,
                                MSDATA columns DATA01..DATA42 are positional/unlabeled
  main.enzyme    from ENZYMEDATA (sample item=ENZYME) — only MPS1/MPS2 mapped
  main.gcms      from GCDATA   (sample item=GCMS)
  main.gag       from MPSUDATA (sample item=MPS_Urine)
  main.dnabank   from DNADATA  (sample item=DNA) — ~69% hit only

Skipped (out of scope for this stage test):
  AAREPORT/MSREPORT (separate report workflow)
  ref tables (seed_ref_from_mdb.py also doesn't match)
  BLOB files (extract_blobs_mdb.py is unimplemented)
  users/operator/doctor/CELLDATA/opd_tmp (ETL exclusion list)
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import sql

NAMESPACE_OID = uuid.NAMESPACE_OID


def patient_uuid(chartno: str) -> str:
    return str(uuid.uuid5(NAMESPACE_OID, f"main:{chartno}"))


def db_url() -> str:
    url = os.environ.get(
        "DATABASE_URL", "postgresql://gimc:gimc@localhost:5432/gimc"
    )
    return url.replace("+asyncpg", "").replace("+psycopg", "")


def parse_date(s):
    if not s:
        return None
    s = s.strip().strip('"')
    if not s:
        return None
    if " " in s:
        s = s.split()[0]
    for fmt in ("%Y-%m-%d", "%m/%d/%y", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_sex(s):
    if not s:
        return "男"
    s = s.strip().upper()
    if s in ("M", "男"):
        return "男"
    if s in ("F", "女"):
        return "女"
    if s == "1":
        return "男"
    if s == "2":
        return "女"
    return "男"


def parse_num(s):
    if s is None:
        return None
    s = s.strip() if isinstance(s, str) else s
    if s == "":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def trunc(s, n):
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    return s[:n]


def load_csv(path: Path):
    if not path.exists():
        print(f"  (missing) {path.name}")
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("out_dir", type=Path)
    args = p.parse_args()

    out = args.out_dir
    if not out.is_dir():
        sys.exit(f"not a directory: {out}")

    print("=== Reading source CSVs ===")
    ptinfo = load_csv(out / "ptinfo.csv")
    patient_zh = load_csv(out / "patient.csv")
    sample = load_csv(out / "sample.csv")
    print(f"  ptinfo:      {len(ptinfo)}")
    print(f"  patient(zh): {len(patient_zh)}")
    print(f"  sample:      {len(sample)}")

    # chartno -> patient_id
    chartno_to_pid = {}
    for r in ptinfo:
        c = (r.get("chartno") or "").strip()
        if c:
            chartno_to_pid[c] = patient_uuid(c)
    for r in patient_zh:
        c = (r.get("chartno") or "").strip()
        if c and c not in chartno_to_pid:
            chartno_to_pid[c] = patient_uuid(c)
    print(f"  chartno_to_pid: {len(chartno_to_pid)}")

    # sampleno -> patient_id + metadata
    sn_pid = {}
    sn_specimen = {}
    sn_recedate = {}
    sn_technician = {}
    for r in sample:
        sn = (r.get("sampleno") or "").strip()
        cn = (r.get("chartno") or "").strip()
        if sn and cn in chartno_to_pid:
            sn_pid[sn] = chartno_to_pid[cn]
            sn_specimen[sn] = (r.get("catalog") or "").strip()
            sn_recedate[sn] = parse_date(r.get("recedate"))
            sn_technician[sn] = (r.get("name") or "").strip()
    print(f"  sampleno_to_pid: {len(sn_pid)}")

    # ---- patient ----
    print("\n=== Building patient rows ===")
    patient_by_pid = {}
    for r in ptinfo:
        c = (r.get("chartno") or "").strip()
        if not c:
            continue
        pid = chartno_to_pid[c]
        patient_by_pid[pid] = {
            "patient_id": pid,
            "source": "main",
            "chartno": c,
            "name": trunc(r.get("ptname") or "", 128) or "未命名",
            "birthday": parse_date(r.get("birthday")) or "1900-01-01",
            "sex": parse_sex(r.get("sex")),
            "diagnosis": trunc(r.get("diagnosis1"), 256),
            "diagnosis2": trunc(r.get("diagnosis2"), 256),
            "diagnosis3": trunc(r.get("diagnosis3"), 256),
            "referring_doctor": None,
        }
    for r in patient_zh:
        c = (r.get("chartno") or "").strip()
        if not c:
            continue
        pid = chartno_to_pid[c]
        existing = patient_by_pid.setdefault(pid, {
            "patient_id": pid, "source": "main", "chartno": c,
            "name": "未命名", "birthday": "1900-01-01", "sex": "男",
            "diagnosis": None, "diagnosis2": None, "diagnosis3": None,
            "referring_doctor": None,
        })
        v = (r.get("ptname") or "").strip()
        if v:
            existing["name"] = trunc(v, 128)
        v = parse_date(r.get("birthday"))
        if v:
            existing["birthday"] = v
        v = (r.get("sex") or "").strip()
        if v:
            existing["sex"] = parse_sex(v)
        v = trunc(r.get("diagnosis"), 256)
        if v:
            existing["diagnosis"] = v
        for src_col in ("referring_doctor", "doctor"):
            v = trunc(r.get(src_col), 64)
            if v:
                existing["referring_doctor"] = v
                break
    patient_rows = list(patient_by_pid.values())
    print(f"  patient_rows: {len(patient_rows)}")

    # ---- lab tables ----
    def join_pid(r):
        no = (r.get("no") or "").strip()
        return no, sn_pid.get(no)

    def base_lab(r, specimen_default, want_technician=False):
        no, pid = join_pid(r)
        if not pid:
            return None
        row = {
            "patient_id": pid,
            "sample_name": trunc(no, 64) or "",
            "specimen_type": trunc(sn_specimen.get(no), 32) or specimen_default,
            "result": trunc(r.get("interpretation"), 64) or "",
            "ntubiogene_sampleno": trunc(no, 64),
            "v2_source_schema": "1.0-mdb",
        }
        if want_technician:
            row["technician"] = trunc(sn_technician.get(no), 64) or ""
        return row

    print("\n=== Building lab table rows ===")
    aa_rows = []
    for r in load_csv(out / "AADATA.csv"):
        row = base_lab(r, "Plasma")
        if not row:
            continue
        for src, tgt in (("GLN","gln"),("CITR","citr"),("ALA","ala"),
                         ("ARG","arg"),("LEU","leu"),("VAL","val"),
                         ("PHE","phe"),("TYR","tyr")):
            row[tgt] = parse_num(r.get(src))
        aa_rows.append(row)
    print(f"  aa:      {len(aa_rows)}")

    msms_rows = []
    for r in load_csv(out / "MSDATA.csv"):
        row = base_lab(r, "DBS")
        if row:
            msms_rows.append(row)
    print(f"  msms:    {len(msms_rows)}  (numeric cols left NULL — DATA01..DATA42 positional)")

    enzyme_rows = []
    for r in load_csv(out / "ENZYMEDATA.csv"):
        row = base_lab(r, "DBS", want_technician=True)
        if not row:
            continue
        row["mps1"] = parse_num(r.get("MPS1"))
        row["enzyme_mps2"] = parse_num(r.get("MPS2"))
        enzyme_rows.append(row)
    print(f"  enzyme:  {len(enzyme_rows)}")

    gcms_rows = []
    for r in load_csv(out / "GCDATA.csv"):
        no, pid = join_pid(r)
        if not pid:
            continue
        gcms_rows.append({
            "patient_id": pid,
            "sample_name": trunc(no, 64) or "",
            "specimen_type": trunc(sn_specimen.get(no), 32),
            "result": trunc(r.get("interpretation"), 64),
            "raw_data_path": None,
            "collect_date": sn_recedate.get(no),
            "notes": trunc(r.get("remark"), 4000),
            "ntubiogene_sampleno": trunc(no, 64),
            "v2_source_schema": "1.0-mdb",
        })
    print(f"  gcms:    {len(gcms_rows)}")

    gag_rows = []
    for r in load_csv(out / "MPSUDATA.csv"):
        no, pid = join_pid(r)
        if not pid:
            continue
        gag_rows.append({
            "patient_id": pid,
            "sample_name": trunc(no, 64) or "",
            "specimen_type": trunc(sn_specimen.get(no), 32) or "Urine",
            "technician": trunc(sn_technician.get(no), 64) or "",
            "result": trunc(r.get("interpretation"), 64) or "",
            "od": parse_num(r.get("OD")),
            "urine_creatinine": parse_num(r.get("urineCreatinine")),
            "dmggag": parse_num(r.get("DMBGAG")),
            "mggag": parse_num(r.get("MGGAG")),
            "creatinine": parse_num(r.get("CREATININE")),
            "twos": parse_num(r.get("twoS")),
            "twos_cre": parse_num(r.get("twoSCre")),
            "ntubiogene_sampleno": trunc(no, 64),
            "v2_source_schema": "1.0-mdb",
        })
    print(f"  gag:     {len(gag_rows)}")

    dnabank_rows = []
    for r in load_csv(out / "DNADATA.csv"):
        no, pid = join_pid(r)
        if not pid:
            continue
        dnabank_rows.append({
            "patient_id": pid,
            "orderno": trunc(no, 64) or "",
            "order": trunc(r.get("item"), 256) or "DNA",
            "order_memo": trunc(r.get("interpretation"), 256),
            "keyword": None,
            "specimenno": trunc(no, 64) or "",
            "specimen": "DNA",
            "ntubiogene_sampleno": trunc(no, 64),
            "v2_source_schema": "1.0-mdb",
        })
    print(f"  dnabank: {len(dnabank_rows)}  (DNADATA hit-rate is ~69%, expected)")

    # ---- DB write ----
    print(f"\n=== Connecting to PG ({db_url().split('@')[-1]}) ===")
    with psycopg.connect(db_url()) as conn:
        # patient: UPSERT
        pcols = ["patient_id", "source", "name", "birthday", "sex",
                 "chartno", "diagnosis", "diagnosis2", "diagnosis3",
                 "referring_doctor"]
        placeholders = ", ".join(["%s"] * len(pcols))
        set_clause = ", ".join(
            f"{c} = COALESCE(main.patient.{c}, EXCLUDED.{c})"
            for c in pcols if c != "patient_id"
        )
        stmt = (f"INSERT INTO main.patient ({', '.join(pcols)}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT (patient_id) DO UPDATE SET {set_clause}")
        with conn.cursor() as cur:
            for r in patient_rows:
                cur.execute(stmt, [r.get(c) for c in pcols])
        print(f"  main.patient   {len(patient_rows)} rows upserted")

        # sample tables: DELETE + COPY
        def copy_table(rows, table, cols):
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DELETE FROM main.{}").format(
                    sql.Identifier(table)))
            if not rows:
                print(f"  main.{table:<9} 0 rows (skipped)")
                return
            with conn.cursor() as cur:
                copy_sql = sql.SQL("COPY main.{} ({}) FROM STDIN").format(
                    sql.Identifier(table),
                    sql.SQL(", ").join(sql.Identifier(c) for c in cols),
                )
                with cur.copy(copy_sql) as cp:
                    for r in rows:
                        cp.write_row([r.get(c) for c in cols])
            print(f"  main.{table:<9} {len(rows)} rows COPY")

        copy_table(aa_rows, "aa",
                   ["patient_id", "sample_name", "specimen_type", "result",
                    "gln", "citr", "ala", "arg", "leu", "val", "phe", "tyr",
                    "ntubiogene_sampleno", "v2_source_schema"])
        copy_table(msms_rows, "msms",
                   ["patient_id", "sample_name", "specimen_type", "result",
                    "ntubiogene_sampleno", "v2_source_schema"])
        copy_table(enzyme_rows, "enzyme",
                   ["patient_id", "sample_name", "specimen_type", "technician",
                    "result", "mps1", "enzyme_mps2",
                    "ntubiogene_sampleno", "v2_source_schema"])
        copy_table(gcms_rows, "gcms",
                   ["patient_id", "sample_name", "specimen_type", "result",
                    "raw_data_path", "collect_date", "notes",
                    "ntubiogene_sampleno", "v2_source_schema"])
        copy_table(gag_rows, "gag",
                   ["patient_id", "sample_name", "specimen_type", "technician",
                    "result", "od", "urine_creatinine", "dmggag", "mggag",
                    "creatinine", "twos", "twos_cre",
                    "ntubiogene_sampleno", "v2_source_schema"])
        copy_table(dnabank_rows, "dnabank",
                   ["patient_id", "orderno", "order", "order_memo", "keyword",
                    "specimenno", "specimen",
                    "ntubiogene_sampleno", "v2_source_schema"])

        conn.commit()

    print("\nimport_ntubiogene.py done")


if __name__ == "__main__":
    sys.exit(main() or 0)
