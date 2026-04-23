import Papa from 'papaparse';
import { MODULE_FIELDS, ModuleId, Patient } from '@/types/medical';

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

function moduleToCsv(
  moduleId: ModuleId,
  records: Record<string, unknown>[],
): string {
  const fields = MODULE_FIELDS[moduleId] ?? [];
  const labels = fields.map((f) => f.label);
  const data = records.map((rec) => {
    const row: Record<string, unknown> = {};
    fields.forEach((f, idx) => {
      row[labels[idx]] = rec[f.id] ?? '';
    });
    return row;
  });
  return Papa.unparse(data, { columns: labels });
}

export async function exportCsvZip(
  patient: Patient,
  modules: ModuleId[],
  filename: string,
) {
  const { default: JSZip } = await import('jszip');
  const zip = new JSZip();

  modules.forEach((moduleId) => {
    const arr = (patient as unknown as Record<string, unknown>)[moduleId];
    const records = Array.isArray(arr)
      ? (arr as Record<string, unknown>[])
      : [];
    const csv = moduleToCsv(moduleId, records);
    zip.file(`${moduleId}.csv`, csv);
  });

  const manifest = {
    patientId: patient.patientId,
    name: patient.name,
    sex: patient.sex,
    birthday: patient.birthday,
    chartno: patient.chartno ?? null,
    externalChartno: patient.externalChartno ?? null,
    nbsId: patient.nbsId ?? null,
    diagnosis: patient.diagnosis ?? null,
    modules,
    exportedAt: new Date().toISOString(),
  };
  zip.file('manifest.json', JSON.stringify(manifest, null, 2));

  const blob = await zip.generateAsync({ type: 'blob' });
  downloadBlob(blob, filename);
}
