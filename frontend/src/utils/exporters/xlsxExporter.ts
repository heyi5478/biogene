import { MODULE_FIELDS, ModuleId, Patient } from '@/types/medical';
import { uniqueSheetName } from './_sheetName';

export async function exportXlsx(
  patient: Patient,
  modules: ModuleId[],
  filename: string,
) {
  const XLSX = await import('xlsx');
  const wb = XLSX.utils.book_new();
  const used = new Set<string>();

  modules.forEach((moduleId) => {
    const arr = (patient as unknown as Record<string, unknown>)[moduleId];
    const records = Array.isArray(arr)
      ? (arr as Record<string, unknown>[])
      : [];
    const fields = MODULE_FIELDS[moduleId] ?? [];
    const labels = fields.map((f) => f.label);
    const rows = records.map((rec) => {
      const row: Record<string, unknown> = {};
      fields.forEach((f) => {
        row[f.label] = rec[f.id] ?? '';
      });
      return row;
    });
    const ws =
      rows.length > 0
        ? XLSX.utils.json_to_sheet(rows, { header: labels })
        : XLSX.utils.aoa_to_sheet([labels]);
    const sheetName = uniqueSheetName(moduleId, used);
    XLSX.utils.book_append_sheet(wb, ws, sheetName);
  });

  XLSX.writeFile(wb, filename);
}
