import { ModuleId, Patient } from '@/types/medical';
import { exportJson } from './jsonExporter';
import { exportCsvZip } from './csvExporter';
import { exportXlsx } from './xlsxExporter';

export type ExportFormat = 'csv' | 'json' | 'xlsx';

export interface ExportOptions {
  format: ExportFormat;
  modules: ModuleId[];
  filenamePrefix: string;
}

export async function exportPatient(
  patient: Patient,
  { format, modules, filenamePrefix }: ExportOptions,
): Promise<void> {
  switch (format) {
    case 'json':
      exportJson(patient, modules, `${filenamePrefix}.json`);
      return;
    case 'csv':
      await exportCsvZip(patient, modules, `${filenamePrefix}.zip`);
      return;
    case 'xlsx':
      await exportXlsx(patient, modules, `${filenamePrefix}.xlsx`);
      return;
    default: {
      const exhaustive: never = format;
      throw new Error(`Unknown export format: ${exhaustive as string}`);
    }
  }
}
