import { MODULE_FIELDS, ModuleId, Patient } from '@/types/medical';
import { uniqueSheetName } from './_sheetName';

const IDENTIFIER_HEADERS = ['patientId', 'name', 'chartno'] as const;

function chartnoOf(patient: Patient): string {
  return (
    patient.chartno ||
    patient.externalChartno ||
    patient.nbsId ||
    patient.patientId
  );
}

function identifierCells(patient: Patient): Record<string, unknown> {
  return {
    patientId: patient.patientId,
    name: patient.name,
    chartno: chartnoOf(patient),
  };
}

export async function exportCohortXlsx(
  patients: Patient[],
  modules: ModuleId[],
  filename: string,
): Promise<void> {
  const XLSX = await import('xlsx');
  const wb = XLSX.utils.book_new();
  const used = new Set<string>();

  modules.forEach((moduleId) => {
    const fields = MODULE_FIELDS[moduleId] ?? [];
    const labels = fields.map((f) => f.label);
    const header = [...IDENTIFIER_HEADERS, ...labels];

    const rows: Record<string, unknown>[] = [];

    if (moduleId === 'basic') {
      patients.forEach((patient) => {
        const row: Record<string, unknown> = identifierCells(patient);
        const patientRec = patient as unknown as Record<string, unknown>;
        fields.forEach((f) => {
          row[f.label] = patientRec[f.id] ?? '';
        });
        rows.push(row);
      });
    } else {
      patients.forEach((patient) => {
        const arr = (patient as unknown as Record<string, unknown>)[moduleId];
        const records = Array.isArray(arr)
          ? (arr as Record<string, unknown>[])
          : [];
        if (records.length === 0) {
          const row: Record<string, unknown> = identifierCells(patient);
          fields.forEach((f) => {
            row[f.label] = '';
          });
          rows.push(row);
        } else {
          records.forEach((rec) => {
            const row: Record<string, unknown> = identifierCells(patient);
            fields.forEach((f) => {
              row[f.label] = rec[f.id] ?? '';
            });
            rows.push(row);
          });
        }
      });
    }

    const ws =
      rows.length > 0
        ? XLSX.utils.json_to_sheet(rows, { header })
        : XLSX.utils.aoa_to_sheet([header]);
    const sheetName = uniqueSheetName(moduleId, used);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
  });

  XLSX.writeFile(wb, filename);
}
