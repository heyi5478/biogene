import { ModuleId, Patient } from '@/types/medical';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

const MODULE_KEYS: ModuleId[] = [
  'opd',
  'aa',
  'msms',
  'biomarker',
  'aadc',
  'ald',
  'mma',
  'mps2',
  'lsd',
  'enzyme',
  'gag',
  'dnabank',
  'outbank',
  'bd',
  'cah',
  'dmd',
  'g6pd',
  'smaScid',
];

export function exportJson(
  patient: Patient,
  modules: ModuleId[],
  filename: string,
) {
  const subset: Record<string, unknown> = { ...patient };
  const selected = new Set(modules);
  MODULE_KEYS.forEach((key) => {
    if (!selected.has(key)) {
      subset[key] = [];
    }
  });
  const blob = new Blob([JSON.stringify(subset, null, 2)], {
    type: 'application/json',
  });
  downloadBlob(blob, filename);
}
