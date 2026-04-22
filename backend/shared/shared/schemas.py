"""Pydantic v2 schemas for the FastAPI services.

Field names mirror the camelCase keys of ``backend/mock-data/*.json`` so JSON
responses match the frontend ``Patient`` TypeScript type without renaming. The
models are intentionally permissive about unknown/optional fields to tolerate
schema drift in the mock files.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

PatientSource = Literal["main", "external", "nbs"]


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class Patient(_Base):
    patientId: str
    source: PatientSource
    name: str
    birthday: str
    sex: Literal["男", "女"]
    chartno: str | None = None
    externalChartno: str | None = None
    nbsId: str | None = None
    category: str | None = None
    linkedPatientIds: list[str] = []
    diagnosis: str | None = None
    diagnosis2: str | None = None
    diagnosis3: str | None = None


class AaRecord(_Base):
    patientId: str
    sampleName: str
    specimenType: str
    result: str
    Gln: float | None = None
    Citr: float | None = None
    Ala: float | None = None
    Arg: float | None = None
    Leu: float | None = None
    Val: float | None = None
    Phe: float | None = None
    Tyr: float | None = None


class MsmsRecord(_Base):
    patientId: str
    sampleName: str
    specimenType: str
    result: str
    Ala: float | None = None
    Arg: float | None = None
    Cit: float | None = None
    Gly: float | None = None
    Leu: float | None = None
    Met: float | None = None
    Phe: float | None = None
    Tyr: float | None = None
    Val: float | None = None
    C0: float | None = None
    C2: float | None = None
    C3: float | None = None
    C5: float | None = None


class BiomarkerRecord(_Base):
    patientId: str
    sampleName: str
    dbsLysoGb3: float | None = None
    dbsLysoGL1: float | None = None
    dbsLysoSM: float | None = None
    plasmaLysoGb3: float | None = None
    plasmaLysoGL1: float | None = None
    plasmaLysoSM: float | None = None


class OutbankRecord(_Base):
    patientId: str
    sampleno: str
    shipdate: str
    assay: str
    result: str


class DnabankRecord(_Base):
    patientId: str
    orderno: str
    order: str
    orderMemo: str | None = None
    keyword: str | None = None
    specimenno: str
    specimen: str


class AadcRecord(_Base):
    patientId: str
    sampleName: str
    conc: float
    date: str | None = None


class AldRecord(_Base):
    patientId: str
    sampleName: str
    conc: float
    date: str | None = None


class MmaRecord(_Base):
    patientId: str
    sampleName: str
    conc: float
    date: str | None = None


class Mps2Record(_Base):
    patientId: str
    sampleName: str
    MPS2: float | None = None
    TPP1: float | None = None
    MPS4A: float | None = None
    MPS6: float | None = None


class LsdRecord(_Base):
    patientId: str
    sampleName: str
    GAA: float | None = None
    GLA: float | None = None
    ABG: float | None = None
    IDUA: float | None = None
    ABG_GAA: float | None = None


class EnzymeRecord(_Base):
    patientId: str
    sampleName: str
    specimenType: str
    technician: str
    result: str
    MPS1: float | None = None
    enzymeMPS2: float | None = None


class GagRecord(_Base):
    patientId: str
    sampleName: str
    specimenType: str
    technician: str
    result: str
    DMGGAG: float | None = None
    CREATININE: float | None = None


class BdRecord(_Base):
    patientId: str
    sampleId: str
    collectDate: str
    result: str
    biotinidaseActivity: float | None = None


class TgalSubRecord(_Base):
    sampleId: str
    collectDate: str
    totalGalactose: float | None = None
    result: str


class CahRecord(_Base):
    patientId: str
    cahId: str
    sampleId: str
    collectDate: str
    result: str
    ohp17: float | None = None
    tgal: list[TgalSubRecord] = []


class TshSubRecord(_Base):
    sampleId: str
    collectDate: str
    tsh: float | None = None
    result: str


class DmdRecord(_Base):
    patientId: str
    dmdId: str
    sampleId: str
    collectDate: str
    result: str
    ck: float | None = None
    tsh: list[TshSubRecord] = []


class G6pdRecord(_Base):
    patientId: str
    sampleId: str
    collectDate: str
    result: str
    g6pdActivity: float | None = None


class SmaScidRecord(_Base):
    patientId: str
    sampleId: str
    collectDate: str
    result: str
    smn1Copies: int | None = None
    trec: float | None = None


class LabBundle(_Base):
    """Per-patient payload returned by svc-lab."""

    aa: list[AaRecord] = []
    msms: list[MsmsRecord] = []
    biomarker: list[BiomarkerRecord] = []
    outbank: list[OutbankRecord] = []
    dnabank: list[DnabankRecord] = []


class DiseaseBundle(_Base):
    """Per-patient payload returned by svc-disease.

    NBS sub-tables (``cah_tgal`` / ``dmd_tsh``) are nested inside their parent
    ``cah`` / ``dmd`` rows instead of being exposed as sibling arrays.
    """

    aadc: list[AadcRecord] = []
    ald: list[AldRecord] = []
    mma: list[MmaRecord] = []
    mps2: list[Mps2Record] = []
    lsd: list[LsdRecord] = []
    enzyme: list[EnzymeRecord] = []
    gag: list[GagRecord] = []
    bd: list[BdRecord] = []
    cah: list[CahRecord] = []
    dmd: list[DmdRecord] = []
    g6pd: list[G6pdRecord] = []
    smaScid: list[SmaScidRecord] = []


class PatientBundle(Patient):
    """Gateway aggregate: patient base fields + all per-module arrays."""

    aa: list[AaRecord] = []
    msms: list[MsmsRecord] = []
    biomarker: list[BiomarkerRecord] = []
    outbank: list[OutbankRecord] = []
    dnabank: list[DnabankRecord] = []
    aadc: list[AadcRecord] = []
    ald: list[AldRecord] = []
    mma: list[MmaRecord] = []
    mps2: list[Mps2Record] = []
    lsd: list[LsdRecord] = []
    enzyme: list[EnzymeRecord] = []
    gag: list[GagRecord] = []
    bd: list[BdRecord] = []
    cah: list[CahRecord] = []
    dmd: list[DmdRecord] = []
    g6pd: list[G6pdRecord] = []
    smaScid: list[SmaScidRecord] = []


__all__ = [
    "PatientSource",
    "Patient",
    "AaRecord",
    "MsmsRecord",
    "BiomarkerRecord",
    "OutbankRecord",
    "DnabankRecord",
    "AadcRecord",
    "AldRecord",
    "MmaRecord",
    "Mps2Record",
    "LsdRecord",
    "EnzymeRecord",
    "GagRecord",
    "BdRecord",
    "CahRecord",
    "TgalSubRecord",
    "DmdRecord",
    "TshSubRecord",
    "G6pdRecord",
    "SmaScidRecord",
    "LabBundle",
    "DiseaseBundle",
    "PatientBundle",
]
