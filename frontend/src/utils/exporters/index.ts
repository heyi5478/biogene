import { ModuleId, Patient } from '@/types/medical';
import { exportJson } from './jsonExporter';
import { exportCsvZip } from './csvExporter';
import { exportXlsx } from './xlsxExporter';
import { exportCohortXlsx } from './cohortXlsxExporter';

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

export type CohortExportFormat = 'xlsx';

export interface CohortExportOptions {
  format: CohortExportFormat;
  modules: ModuleId[];
  filenamePrefix: string;
}

export async function exportPatients(
  patients: Patient[],
  { format, modules, filenamePrefix }: CohortExportOptions,
): Promise<void> {
  switch (format) {
    case 'xlsx':
      await exportCohortXlsx(patients, modules, `${filenamePrefix}.xlsx`);
      return;
    default: {
      const exhaustive: never = format;
      throw new Error(`Unknown cohort export format: ${exhaustive as string}`);
    }
  }
}
