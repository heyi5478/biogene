import {
  AaSample,
  AadcSample,
  AldSample,
  BdSample,
  BiomarkerSample,
  CahSample,
  DmdSample,
  DnabankRecord,
  EnzymeSample,
  G6pdSample,
  GagSample,
  LsdSample,
  MmaSample,
  Mps2Sample,
  MsmsSample,
  OpdRecord,
  OutbankRecord,
  Patient,
  PatientSource,
  SmaScidSample,
  TgalSubSample,
  TshSubSample,
} from '@/types/medical';

// --- db_main JSON ---
import mainPatient from '../../../backend/mock-data/db_main/patient.json';
import mainOpd from '../../../backend/mock-data/db_main/opd.json';
import mainAa from '../../../backend/mock-data/db_main/aa.json';
import mainMsms from '../../../backend/mock-data/db_main/msms.json';
import mainBiomarker from '../../../backend/mock-data/db_main/biomarker.json';
import mainAadc from '../../../backend/mock-data/db_main/aadc.json';
import mainAld from '../../../backend/mock-data/db_main/ald.json';
import mainMma from '../../../backend/mock-data/db_main/mma.json';
import mainMps2 from '../../../backend/mock-data/db_main/mps2.json';
import mainLsd from '../../../backend/mock-data/db_main/lsd.json';
import mainEnzyme from '../../../backend/mock-data/db_main/enzyme.json';
import mainGag from '../../../backend/mock-data/db_main/gag.json';
import mainDnabank from '../../../backend/mock-data/db_main/dnabank.json';
import mainOutbank from '../../../backend/mock-data/db_main/outbank.json';

// --- db_external JSON ---
import extPatient from '../../../backend/mock-data/db_external/patient.json';
import extOpd from '../../../backend/mock-data/db_external/opd.json';
import extAa from '../../../backend/mock-data/db_external/aa.json';
import extMsms from '../../../backend/mock-data/db_external/msms.json';
import extBiomarker from '../../../backend/mock-data/db_external/biomarker.json';
import extLsd from '../../../backend/mock-data/db_external/lsd.json';
import extEnzyme from '../../../backend/mock-data/db_external/enzyme.json';
import extGag from '../../../backend/mock-data/db_external/gag.json';
import extOutbank from '../../../backend/mock-data/db_external/outbank.json';

// --- db_nbs JSON ---
import nbsPatient from '../../../backend/mock-data/db_nbs/patient.json';
import nbsOpd from '../../../backend/mock-data/db_nbs/opd.json';
import nbsBd from '../../../backend/mock-data/db_nbs/bd.json';
import nbsCah from '../../../backend/mock-data/db_nbs/cah.json';
import nbsCahTgal from '../../../backend/mock-data/db_nbs/cah_tgal.json';
import nbsDmd from '../../../backend/mock-data/db_nbs/dmd.json';
import nbsDmdTsh from '../../../backend/mock-data/db_nbs/dmd_tsh.json';
import nbsG6pd from '../../../backend/mock-data/db_nbs/g6pd.json';
import nbsSmaScid from '../../../backend/mock-data/db_nbs/sma_scid.json';
import nbsAa from '../../../backend/mock-data/db_nbs/aa.json';
import nbsMsms from '../../../backend/mock-data/db_nbs/msms.json';
import nbsBiomarker from '../../../backend/mock-data/db_nbs/biomarker.json';
import nbsOutbank from '../../../backend/mock-data/db_nbs/outbank.json';

type WithPatientId<T> = T & { patientId: string };

function groupByPatient<T extends { patientId: string }>(
  rows: T[],
): Map<string, T[]> {
  const map = new Map<string, T[]>();
  for (const row of rows) {
    const list = map.get(row.patientId);
    if (list) list.push(row);
    else map.set(row.patientId, [row]);
  }
  return map;
}

function pick<T extends { patientId: string }, K extends keyof T>(
  rows: T[],
  exclude: K,
): Omit<T, K>[] {
  return rows.map(({ [exclude]: _drop, ...rest }) => rest) as Omit<T, K>[];
}

interface PatientRow {
  patientId: string;
  source: PatientSource;
  chartno?: string;
  externalChartno?: string;
  nbsId?: string;
  category?: string;
  linkedPatientIds?: string[];
  name: string;
  birthday: string;
  sex: '男' | '女';
  diagnosis?: string;
  diagnosis2?: string;
  diagnosis3?: string;
}

function buildPatient(
  p: PatientRow,
  groups: {
    opd: Map<string, WithPatientId<OpdRecord>[]>;
    aa: Map<string, WithPatientId<AaSample>[]>;
    msms: Map<string, WithPatientId<MsmsSample>[]>;
    biomarker: Map<string, WithPatientId<BiomarkerSample>[]>;
    aadc: Map<string, WithPatientId<AadcSample>[]>;
    ald: Map<string, WithPatientId<AldSample>[]>;
    mma: Map<string, WithPatientId<MmaSample>[]>;
    mps2: Map<string, WithPatientId<Mps2Sample>[]>;
    lsd: Map<string, WithPatientId<LsdSample>[]>;
    enzyme: Map<string, WithPatientId<EnzymeSample>[]>;
    gag: Map<string, WithPatientId<GagSample>[]>;
    dnabank: Map<string, WithPatientId<DnabankRecord>[]>;
    outbank: Map<string, WithPatientId<OutbankRecord>[]>;
    bd: Map<string, WithPatientId<BdSample>[]>;
    cah: Map<string, WithPatientId<CahSample>[]>;
    dmd: Map<string, WithPatientId<DmdSample>[]>;
    g6pd: Map<string, WithPatientId<G6pdSample>[]>;
    smaScid: Map<string, WithPatientId<SmaScidSample>[]>;
  },
): Patient {
  const id = p.patientId;
  return {
    ...p,
    opd: pick(groups.opd.get(id) ?? [], 'patientId'),
    aa: pick(groups.aa.get(id) ?? [], 'patientId'),
    msms: pick(groups.msms.get(id) ?? [], 'patientId'),
    biomarker: pick(groups.biomarker.get(id) ?? [], 'patientId'),
    aadc: pick(groups.aadc.get(id) ?? [], 'patientId'),
    ald: pick(groups.ald.get(id) ?? [], 'patientId'),
    mma: pick(groups.mma.get(id) ?? [], 'patientId'),
    mps2: pick(groups.mps2.get(id) ?? [], 'patientId'),
    lsd: pick(groups.lsd.get(id) ?? [], 'patientId'),
    enzyme: pick(groups.enzyme.get(id) ?? [], 'patientId'),
    gag: pick(groups.gag.get(id) ?? [], 'patientId'),
    dnabank: pick(groups.dnabank.get(id) ?? [], 'patientId'),
    outbank: pick(groups.outbank.get(id) ?? [], 'patientId'),
    bd: pick(groups.bd.get(id) ?? [], 'patientId'),
    cah: pick(groups.cah.get(id) ?? [], 'patientId'),
    dmd: pick(groups.dmd.get(id) ?? [], 'patientId'),
    g6pd: pick(groups.g6pd.get(id) ?? [], 'patientId'),
    smaScid: pick(groups.smaScid.get(id) ?? [], 'patientId'),
  };
}

// Empty maps for tables that don't exist in a given database (e.g. db_main has
// no bd/cah/..., db_external has no aadc/ald/..., etc.). buildPatient calls
// .get() against them, so we just need an empty Map.
const EMPTY = <T>() => new Map<string, WithPatientId<T>[]>();

// --- Attach tgal sub-rows to their parent cah rows by cahId ---
function joinCahTgal(
  cahRows: WithPatientId<CahSample>[],
  tgalRows: (TgalSubSample & { cahId: string })[],
): WithPatientId<CahSample>[] {
  const tgalByCah = new Map<string, TgalSubSample[]>();
  for (const row of tgalRows) {
    const { cahId, ...rest } = row;
    const list = tgalByCah.get(cahId);
    if (list) list.push(rest);
    else tgalByCah.set(cahId, [rest]);
  }
  return cahRows.map((cah) => ({
    ...cah,
    tgal: tgalByCah.get(cah.cahId) ?? [],
  }));
}

// --- Attach tsh sub-rows to their parent dmd rows by dmdId ---
function joinDmdTsh(
  dmdRows: WithPatientId<DmdSample>[],
  tshRows: (TshSubSample & { dmdId: string })[],
): WithPatientId<DmdSample>[] {
  const tshByDmd = new Map<string, TshSubSample[]>();
  for (const row of tshRows) {
    const { dmdId, ...rest } = row;
    const list = tshByDmd.get(dmdId);
    if (list) list.push(rest);
    else tshByDmd.set(dmdId, [rest]);
  }
  return dmdRows.map((dmd) => ({
    ...dmd,
    tsh: tshByDmd.get(dmd.dmdId) ?? [],
  }));
}

const nbsCahJoined = joinCahTgal(
  nbsCah as WithPatientId<CahSample>[],
  nbsCahTgal as (TgalSubSample & { cahId: string })[],
);
const nbsDmdJoined = joinDmdTsh(
  nbsDmd as WithPatientId<DmdSample>[],
  nbsDmdTsh as (TshSubSample & { dmdId: string })[],
);

const mainPatients: Patient[] = (mainPatient as PatientRow[]).map((p) =>
  buildPatient(p, {
    opd: groupByPatient(mainOpd as WithPatientId<OpdRecord>[]),
    aa: groupByPatient(mainAa as WithPatientId<AaSample>[]),
    msms: groupByPatient(mainMsms as WithPatientId<MsmsSample>[]),
    biomarker: groupByPatient(mainBiomarker as WithPatientId<BiomarkerSample>[]),
    aadc: groupByPatient(mainAadc as WithPatientId<AadcSample>[]),
    ald: groupByPatient(mainAld as WithPatientId<AldSample>[]),
    mma: groupByPatient(mainMma as WithPatientId<MmaSample>[]),
    mps2: groupByPatient(mainMps2 as WithPatientId<Mps2Sample>[]),
    lsd: groupByPatient(mainLsd as WithPatientId<LsdSample>[]),
    enzyme: groupByPatient(mainEnzyme as WithPatientId<EnzymeSample>[]),
    gag: groupByPatient(mainGag as WithPatientId<GagSample>[]),
    dnabank: groupByPatient(mainDnabank as WithPatientId<DnabankRecord>[]),
    outbank: groupByPatient(mainOutbank as WithPatientId<OutbankRecord>[]),
    bd: EMPTY<BdSample>(),
    cah: EMPTY<CahSample>(),
    dmd: EMPTY<DmdSample>(),
    g6pd: EMPTY<G6pdSample>(),
    smaScid: EMPTY<SmaScidSample>(),
  }),
);

const externalPatients: Patient[] = (extPatient as PatientRow[]).map((p) =>
  buildPatient(p, {
    opd: groupByPatient(extOpd as WithPatientId<OpdRecord>[]),
    aa: groupByPatient(extAa as WithPatientId<AaSample>[]),
    msms: groupByPatient(extMsms as WithPatientId<MsmsSample>[]),
    biomarker: groupByPatient(extBiomarker as WithPatientId<BiomarkerSample>[]),
    aadc: EMPTY<AadcSample>(),
    ald: EMPTY<AldSample>(),
    mma: EMPTY<MmaSample>(),
    mps2: EMPTY<Mps2Sample>(),
    lsd: groupByPatient(extLsd as WithPatientId<LsdSample>[]),
    enzyme: groupByPatient(extEnzyme as WithPatientId<EnzymeSample>[]),
    gag: groupByPatient(extGag as WithPatientId<GagSample>[]),
    dnabank: EMPTY<DnabankRecord>(),
    outbank: groupByPatient(extOutbank as WithPatientId<OutbankRecord>[]),
    bd: EMPTY<BdSample>(),
    cah: EMPTY<CahSample>(),
    dmd: EMPTY<DmdSample>(),
    g6pd: EMPTY<G6pdSample>(),
    smaScid: EMPTY<SmaScidSample>(),
  }),
);

const nbsPatients: Patient[] = (nbsPatient as PatientRow[]).map((p) =>
  buildPatient(p, {
    opd: groupByPatient(nbsOpd as WithPatientId<OpdRecord>[]),
    aa: groupByPatient(nbsAa as WithPatientId<AaSample>[]),
    msms: groupByPatient(nbsMsms as WithPatientId<MsmsSample>[]),
    biomarker: groupByPatient(nbsBiomarker as WithPatientId<BiomarkerSample>[]),
    aadc: EMPTY<AadcSample>(),
    ald: EMPTY<AldSample>(),
    mma: EMPTY<MmaSample>(),
    mps2: EMPTY<Mps2Sample>(),
    lsd: EMPTY<LsdSample>(),
    enzyme: EMPTY<EnzymeSample>(),
    gag: EMPTY<GagSample>(),
    dnabank: EMPTY<DnabankRecord>(),
    outbank: groupByPatient(nbsOutbank as WithPatientId<OutbankRecord>[]),
    bd: groupByPatient(nbsBd as WithPatientId<BdSample>[]),
    cah: groupByPatient(nbsCahJoined),
    dmd: groupByPatient(nbsDmdJoined),
    g6pd: groupByPatient(nbsG6pd as WithPatientId<G6pdSample>[]),
    smaScid: groupByPatient(nbsSmaScid as WithPatientId<SmaScidSample>[]),
  }),
);

export const mockPatients: Patient[] = [
  ...mainPatients,
  ...externalPatients,
  ...nbsPatients,
];
