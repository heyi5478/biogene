// Field names and casing MUST match the backend gateway response exactly
// (camelCase, as produced by `backend.shared.schemas`).

export type PatientSource = 'main' | 'external' | 'nbs';

export interface Patient {
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
  opd: OpdRecord[];
  aa: AaSample[];
  msms: MsmsSample[];
  biomarker: BiomarkerSample[];
  aadc: AadcSample[];
  ald: AldSample[];
  mma: MmaSample[];
  mps2: Mps2Sample[];
  lsd: LsdSample[];
  enzyme: EnzymeSample[];
  gag: GagSample[];
  dnabank: DnabankRecord[];
  outbank: OutbankRecord[];
  bd: BdSample[];
  cah: CahSample[];
  dmd: DmdSample[];
  g6pd: G6pdSample[];
  smaScid: SmaScidSample[];
}

export interface OpdRecord {
  visitDate: string;
  sex: string;
  birthday: string;
  diagCode: string;
  diagName: string;
  subDiag1?: string;
  subDiag2?: string;
}

export interface AaSample {
  sampleName: string;
  specimenType: string;
  result: string;
  Gln?: number;
  Citr?: number;
  Ala?: number;
  Arg?: number;
  Leu?: number;
  Val?: number;
  Phe?: number;
  Tyr?: number;
}

export interface MsmsSample {
  sampleName: string;
  specimenType: string;
  result: string;
  Ala?: number;
  Arg?: number;
  Cit?: number;
  Gly?: number;
  Leu?: number;
  Met?: number;
  Phe?: number;
  Tyr?: number;
  Val?: number;
  C0?: number;
  C2?: number;
  C3?: number;
  C5?: number;
}

export interface BiomarkerSample {
  sampleName: string;
  dbsLysoGb3?: number;
  dbsLysoGL1?: number;
  dbsLysoSM?: number;
  plasmaLysoGb3?: number;
  plasmaLysoGL1?: number;
  plasmaLysoSM?: number;
}

export interface AadcSample {
  sampleName: string;
  conc: number;
  date?: string;
}

export interface AldSample {
  sampleName: string;
  conc: number;
  date?: string;
}

export interface MmaSample {
  sampleName: string;
  conc: number;
  date?: string;
}

export interface Mps2Sample {
  sampleName: string;
  MPS2?: number;
  TPP1?: number;
  MPS4A?: number;
  MPS6?: number;
}

export interface LsdSample {
  sampleName: string;
  GAA?: number;
  GLA?: number;
  ABG?: number;
  IDUA?: number;
  ABG_GAA?: number;
}

export interface EnzymeSample {
  sampleName: string;
  specimenType: string;
  technician: string;
  result: string;
  MPS1?: number;
  enzymeMPS2?: number;
}

export interface GagSample {
  sampleName: string;
  specimenType: string;
  technician: string;
  result: string;
  DMGGAG?: number;
  CREATININE?: number;
}

export interface DnabankRecord {
  orderno: string;
  order: string;
  orderMemo?: string;
  keyword?: string;
  specimenno: string;
  specimen: string;
}

export interface OutbankRecord {
  sampleno: string;
  shipdate: string;
  assay: string;
  result: string;
}

export interface BdSample {
  sampleId: string;
  collectDate: string;
  result: string;
  biotinidaseActivity?: number;
}

export interface TgalSubSample {
  sampleId: string;
  collectDate: string;
  totalGalactose?: number;
  result: string;
}

export interface CahSample {
  cahId: string;
  sampleId: string;
  collectDate: string;
  result: string;
  ohp17?: number;
  tgal?: TgalSubSample[];
}

export interface TshSubSample {
  sampleId: string;
  collectDate: string;
  tsh?: number;
  result: string;
}

export interface DmdSample {
  dmdId: string;
  sampleId: string;
  collectDate: string;
  result: string;
  ck?: number;
  tsh?: TshSubSample[];
}

export interface G6pdSample {
  sampleId: string;
  collectDate: string;
  result: string;
  g6pdActivity?: number;
}

export interface SmaScidSample {
  sampleId: string;
  collectDate: string;
  result: string;
  smn1Copies?: number;
  trec?: number;
}
