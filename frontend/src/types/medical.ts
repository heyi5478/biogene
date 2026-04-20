export type ModuleId =
  | 'basic'
  | 'opd'
  | 'aadc'
  | 'ald'
  | 'mma'
  | 'mps2'
  | 'aa'
  | 'msms'
  | 'biomarker'
  | 'lsd'
  | 'enzyme'
  | 'gag'
  | 'dnabank'
  | 'outbank';

export interface ModuleInfo {
  id: ModuleId;
  code: string;
  name: string;
  description: string;
  tooltip: string;
  group: 'patient' | 'disease' | 'lab' | 'specimen';
}

export interface Patient {
  chartno: string;
  name: string;
  birthday: string;
  sex: '男' | '女';
  diagnosis: string;
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

export const MODULE_DEFINITIONS: ModuleInfo[] = [
  {
    id: 'basic',
    code: '基本資料',
    name: '基本資料',
    description: '病歷號、生日、性別、診斷等病人主檔資料',
    tooltip: '顯示病人基本主檔資訊',
    group: 'patient',
  },
  {
    id: 'opd',
    code: 'OPD',
    name: '門診紀錄',
    description: '看診日、主診斷碼、主診斷名稱、次診斷等門診追蹤資料',
    tooltip: '顯示門診追蹤紀錄與診斷資訊',
    group: 'patient',
  },
  {
    id: 'aadc',
    code: 'AADC',
    name: 'AADC 相關檢測',
    description: '查 AADC 模組樣本與濃度結果',
    tooltip: '顯示 AADC 模組樣本與濃度結果',
    group: 'disease',
  },
  {
    id: 'ald',
    code: 'ALD',
    name: 'ALD 相關檢測',
    description: '查 ALD 模組樣本與濃度結果',
    tooltip: '顯示 ALD 模組樣本與濃度結果',
    group: 'disease',
  },
  {
    id: 'mma',
    code: 'MMA',
    name: 'MMA 相關檢測',
    description: '查 MMA 模組樣本與濃度結果',
    tooltip: '顯示 MMA 模組樣本與濃度結果',
    group: 'disease',
  },
  {
    id: 'mps2',
    code: 'MPS',
    name: 'MPS / 相關 target panel',
    description: '包含 MPS2、MPS4A、MPS6、TPP1 等 target',
    tooltip: '顯示 MPS2、MPS4A、MPS6、TPP1 等 target panel 結果',
    group: 'disease',
  },
  {
    id: 'aa',
    code: 'AA',
    name: '胺基酸分析（AA）',
    description: '查胺基酸檢驗結果與個別 analyte 數值',
    tooltip: '顯示胺基酸分析結果與個別 analyte 數值，如 Gln、Citr',
    group: 'lab',
  },
  {
    id: 'msms',
    code: 'MS/MS',
    name: '串聯質譜篩檢（MS/MS）',
    description: '查 MS/MS 篩檢結果與個別 analyte 資料',
    tooltip: '顯示串聯質譜篩檢與相關 analyte，如 Ala、Arg、Cit',
    group: 'lab',
  },
  {
    id: 'biomarker',
    code: 'Biomarker',
    name: '生物標記（Biomarker）',
    description: '查 DBS / Plasma biomarker',
    tooltip: '顯示 DBS / Plasma biomarker，如 LysoGb3、LysoGL1',
    group: 'lab',
  },
  {
    id: 'lsd',
    code: 'LSD',
    name: 'LSD 多重酵素 panel',
    description: '查 GAA、GLA、ABG、IDUA 等 panel',
    tooltip: '顯示 lysosomal storage disease 多重酵素 panel',
    group: 'lab',
  },
  {
    id: 'enzyme',
    code: 'Enzyme',
    name: '酵素檢驗',
    description: '查酵素活性、檢體類別、技術人員與結果',
    tooltip: '顯示酵素活性檢驗結果',
    group: 'lab',
  },
  {
    id: 'gag',
    code: 'GAG',
    name: 'GAG 定量',
    description: '查 GAG、Creatinine 及相關結果',
    tooltip: '顯示 GAG、Creatinine 定量結果，用於 MPS 評估',
    group: 'lab',
  },
  {
    id: 'dnabank',
    code: 'DNAbank',
    name: 'DNA 檢體庫',
    description: '查 DNA 樣本編號、樣本類型、備註與管理資訊',
    tooltip: '顯示 DNA 樣本與檢體管理資訊',
    group: 'specimen',
  },
  {
    id: 'outbank',
    code: 'Outbank',
    name: '外送檢體',
    description: '查外送檢體編號、送驗日期、assay 與結果',
    tooltip: '顯示外送檢體、送驗日期、assay 與結果',
    group: 'specimen',
  },
];

export interface PresetConfig {
  id: string;
  name: string;
  icon: string;
  modules: ModuleId[];
}

export const PRESETS: PresetConfig[] = [
  { id: 'summary', name: '病人摘要', icon: 'user', modules: ['basic', 'opd'] },
  {
    id: 'metabolic',
    name: '代謝篩檢',
    icon: 'flask',
    modules: ['aa', 'msms', 'mma', 'aadc', 'ald'],
  },
  {
    id: 'lsd-mps',
    name: 'LSD / MPS 相關',
    icon: 'microscope',
    modules: ['biomarker', 'lsd', 'enzyme', 'gag', 'mps2'],
  },
  {
    id: 'specimen',
    name: '檢體管理',
    icon: 'tube',
    modules: ['dnabank', 'outbank'],
  },
];

export type FieldType = 'text' | 'number' | 'date' | 'category';

export interface FieldDefinition {
  id: string;
  label: string;
  type: FieldType;
  options?: string[];
}

export type Operator =
  | 'eq'
  | 'neq'
  | 'contains'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'between'
  | 'before'
  | 'after'
  | 'has_data'
  | 'no_data';

export interface OperatorInfo {
  id: Operator;
  label: string;
  valueCount: 0 | 1 | 2;
}

export const OPERATORS_BY_TYPE: Record<FieldType, OperatorInfo[]> = {
  text: [
    { id: 'contains', label: '包含', valueCount: 1 },
    { id: 'eq', label: '等於', valueCount: 1 },
    { id: 'neq', label: '不等於', valueCount: 1 },
    { id: 'has_data', label: '有資料', valueCount: 0 },
    { id: 'no_data', label: '無資料', valueCount: 0 },
  ],
  number: [
    { id: 'gt', label: '>', valueCount: 1 },
    { id: 'gte', label: '≥', valueCount: 1 },
    { id: 'lt', label: '<', valueCount: 1 },
    { id: 'lte', label: '≤', valueCount: 1 },
    { id: 'eq', label: '=', valueCount: 1 },
    { id: 'between', label: '介於', valueCount: 2 },
    { id: 'has_data', label: '有資料', valueCount: 0 },
    { id: 'no_data', label: '無資料', valueCount: 0 },
  ],
  date: [
    { id: 'after', label: '晚於', valueCount: 1 },
    { id: 'before', label: '早於', valueCount: 1 },
    { id: 'between', label: '介於', valueCount: 2 },
    { id: 'eq', label: '等於', valueCount: 1 },
  ],
  category: [
    { id: 'eq', label: '等於', valueCount: 1 },
    { id: 'neq', label: '不等於', valueCount: 1 },
    { id: 'has_data', label: '有資料', valueCount: 0 },
    { id: 'no_data', label: '無資料', valueCount: 0 },
  ],
};

export interface ConditionRow {
  id: string;
  moduleId: ModuleId | '';
  fieldId: string;
  operator: Operator;
  value: string;
  value2: string;
}

export type ConditionLogic = 'AND' | 'OR';

export const MODULE_FIELDS: Record<ModuleId, FieldDefinition[]> = {
  basic: [
    { id: 'chartno', label: '病歷號', type: 'text' },
    { id: 'name', label: '姓名', type: 'text' },
    { id: 'sex', label: '性別', type: 'category', options: ['男', '女'] },
    { id: 'birthday', label: '生日', type: 'date' },
    { id: 'diagnosis', label: '主診斷', type: 'text' },
    { id: 'diagnosis2', label: '次診斷1', type: 'text' },
    { id: 'diagnosis3', label: '次診斷2', type: 'text' },
  ],
  opd: [
    { id: 'visitDate', label: '看診日', type: 'date' },
    { id: 'diagCode', label: '主診斷碼', type: 'text' },
    { id: 'diagName', label: '主診斷名稱', type: 'text' },
    { id: 'subDiag1', label: '次診斷名稱1', type: 'text' },
  ],
  aa: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    {
      id: 'specimenType',
      label: '檢體類別',
      type: 'category',
      options: ['Plasma', 'CSF', 'Urine'],
    },
    {
      id: 'result',
      label: 'Result',
      type: 'category',
      options: ['Normal', 'Abnormal'],
    },
    { id: 'Gln', label: 'Gln', type: 'number' },
    { id: 'Citr', label: 'Citr', type: 'number' },
    { id: 'Ala', label: 'Ala', type: 'number' },
    { id: 'Arg', label: 'Arg', type: 'number' },
    { id: 'Leu', label: 'Leu', type: 'number' },
    { id: 'Val', label: 'Val', type: 'number' },
    { id: 'Phe', label: 'Phe', type: 'number' },
    { id: 'Tyr', label: 'Tyr', type: 'number' },
  ],
  msms: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    {
      id: 'specimenType',
      label: '檢體類別',
      type: 'category',
      options: ['DBS', 'Plasma'],
    },
    {
      id: 'result',
      label: 'Result',
      type: 'category',
      options: ['Normal', 'Abnormal'],
    },
    { id: 'Ala', label: 'Ala', type: 'number' },
    { id: 'Arg', label: 'Arg', type: 'number' },
    { id: 'Cit', label: 'Cit', type: 'number' },
    { id: 'Gly', label: 'Gly', type: 'number' },
    { id: 'Leu', label: 'Leu', type: 'number' },
    { id: 'Met', label: 'Met', type: 'number' },
    { id: 'Phe', label: 'Phe', type: 'number' },
    { id: 'Tyr', label: 'Tyr', type: 'number' },
    { id: 'Val', label: 'Val', type: 'number' },
    { id: 'C0', label: 'C0', type: 'number' },
    { id: 'C2', label: 'C2', type: 'number' },
    { id: 'C3', label: 'C3', type: 'number' },
    { id: 'C5', label: 'C5', type: 'number' },
  ],
  biomarker: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'dbsLysoGb3', label: 'DBS LysoGb3', type: 'number' },
    { id: 'dbsLysoGL1', label: 'DBS LysoGL1', type: 'number' },
    { id: 'dbsLysoSM', label: 'DBS Lyso-SM', type: 'number' },
    { id: 'plasmaLysoGb3', label: 'Plasma LysoGb3', type: 'number' },
    { id: 'plasmaLysoGL1', label: 'Plasma LysoGL1', type: 'number' },
    { id: 'plasmaLysoSM', label: 'Plasma Lyso-SM', type: 'number' },
  ],
  aadc: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'conc', label: '濃度 (Conc)', type: 'number' },
    { id: 'date', label: '日期', type: 'date' },
  ],
  ald: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'conc', label: '濃度 (Conc)', type: 'number' },
    { id: 'date', label: '日期', type: 'date' },
  ],
  mma: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'conc', label: '濃度 (Conc)', type: 'number' },
    { id: 'date', label: '日期', type: 'date' },
  ],
  mps2: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'MPS2', label: 'MPS2', type: 'number' },
    { id: 'TPP1', label: 'TPP1', type: 'number' },
    { id: 'MPS4A', label: 'MPS4A', type: 'number' },
    { id: 'MPS6', label: 'MPS6', type: 'number' },
  ],
  lsd: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    { id: 'GAA', label: 'GAA', type: 'number' },
    { id: 'GLA', label: 'GLA', type: 'number' },
    { id: 'ABG', label: 'ABG', type: 'number' },
    { id: 'IDUA', label: 'IDUA', type: 'number' },
    { id: 'ABG_GAA', label: 'ABG/GAA', type: 'number' },
  ],
  enzyme: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    {
      id: 'specimenType',
      label: '檢體類別',
      type: 'category',
      options: ['Leukocyte', 'Plasma', 'Fibroblast'],
    },
    {
      id: 'result',
      label: 'Result',
      type: 'category',
      options: ['Normal', 'Deficient', 'Intermediate'],
    },
    { id: 'MPS1', label: 'MPS1', type: 'number' },
    { id: 'enzymeMPS2', label: 'Enzyme-MPS2', type: 'number' },
  ],
  gag: [
    { id: 'sampleName', label: 'Sample Name', type: 'text' },
    {
      id: 'specimenType',
      label: '檢體類別',
      type: 'category',
      options: ['Urine', 'Plasma'],
    },
    {
      id: 'result',
      label: 'Result',
      type: 'category',
      options: ['Normal', 'Elevated', 'Borderline'],
    },
    { id: 'DMGGAG', label: 'DMGGAG', type: 'number' },
    { id: 'CREATININE', label: 'Creatinine', type: 'number' },
  ],
  dnabank: [
    { id: 'orderno', label: '訂單編號', type: 'text' },
    { id: 'order', label: '檢測項目', type: 'text' },
    { id: 'orderMemo', label: '備註', type: 'text' },
    { id: 'keyword', label: '關鍵字', type: 'text' },
    { id: 'specimenno', label: '檢體編號', type: 'text' },
    {
      id: 'specimen',
      label: '檢體類別',
      type: 'category',
      options: ['Whole blood', 'Fibroblast', 'Saliva'],
    },
  ],
  outbank: [
    { id: 'sampleno', label: '樣本編號', type: 'text' },
    { id: 'shipdate', label: '送驗日期', type: 'date' },
    { id: 'assay', label: 'Assay', type: 'text' },
    { id: 'result', label: '結果', type: 'text' },
  ],
};

export interface ConditionTemplate {
  id: string;
  name: string;
  description: string;
  conditions: Omit<ConditionRow, 'id'>[];
  logic: ConditionLogic;
}

export const CONDITION_TEMPLATES: ConditionTemplate[] = [
  {
    id: 'abnormal-biomarker',
    name: 'Biomarker 異常',
    description: '篩選 DBS LysoGb3 > 5 的病人',
    conditions: [
      {
        moduleId: 'biomarker',
        fieldId: 'dbsLysoGb3',
        operator: 'gt',
        value: '5',
        value2: '',
      },
    ],
    logic: 'AND',
  },
  {
    id: 'mps-related',
    name: 'MPS 相關異常',
    description: '篩選 MPS2 酵素活性低 或 GAG 偏高',
    conditions: [
      {
        moduleId: 'mps2',
        fieldId: 'MPS2',
        operator: 'lt',
        value: '5',
        value2: '',
      },
      {
        moduleId: 'gag',
        fieldId: 'DMGGAG',
        operator: 'gt',
        value: '200',
        value2: '',
      },
    ],
    logic: 'OR',
  },
  {
    id: 'phe-elevated',
    name: 'Phe 偏高（PKU 相關）',
    description: '篩選 AA 或 MS/MS 中 Phe > 120',
    conditions: [
      {
        moduleId: 'aa',
        fieldId: 'Phe',
        operator: 'gt',
        value: '120',
        value2: '',
      },
    ],
    logic: 'AND',
  },
  {
    id: 'recent-outbank',
    name: '最近外送檢體',
    description: '篩選送驗日期在 2025 年以後的外送檢體',
    conditions: [
      {
        moduleId: 'outbank',
        fieldId: 'shipdate',
        operator: 'after',
        value: '2025-01-01',
        value2: '',
      },
    ],
    logic: 'AND',
  },
  {
    id: 'enzyme-deficient',
    name: '酵素活性低下',
    description: '篩選 Enzyme result 為 Deficient 的病人',
    conditions: [
      {
        moduleId: 'enzyme',
        fieldId: 'result',
        operator: 'eq',
        value: 'Deficient',
        value2: '',
      },
    ],
    logic: 'AND',
  },
];
