import { ModuleId } from '@/types/medical';

export const MODULE_DATE_FIELD: Record<ModuleId, string | null> = {
  basic: 'birthday',
  opd: 'visitDate',
  aadc: 'date',
  ald: 'date',
  mma: 'date',
  outbank: 'shipdate',
  bd: 'collectDate',
  cah: 'collectDate',
  dmd: 'collectDate',
  g6pd: 'collectDate',
  smaScid: 'collectDate',
  aa: null,
  msms: null,
  biomarker: null,
  enzyme: null,
  lsd: null,
  mps2: null,
  gag: null,
  dnabank: null,
};

export function getRecordDate(moduleId: ModuleId, rec: unknown): string | null {
  const field = MODULE_DATE_FIELD[moduleId];
  if (!field) return null;
  if (typeof rec !== 'object' || rec === null) return null;
  const value = (rec as Record<string, unknown>)[field];
  if (typeof value !== 'string' || value.length === 0) return null;
  return value;
}
