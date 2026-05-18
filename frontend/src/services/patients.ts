import { apiGet, apiPost } from '@/lib/api';
import type {
  Patient,
  PatientListItem,
  PatientListPage,
} from '@/types/patient';
import type { ConditionRow, ConditionLogic } from '@/types/medical';

export const PATIENT_PAGE_SIZE = 50;

export interface ConditionRequest {
  conditions: ConditionRow[];
  logic: ConditionLogic;
}

export function fetchPatients(
  q: string,
  page: number,
): Promise<PatientListPage> {
  const params = new URLSearchParams({
    limit: String(PATIENT_PAGE_SIZE),
    offset: String((page - 1) * PATIENT_PAGE_SIZE),
  });
  if (q !== '') {
    params.set('q', q);
  }
  return apiGet<PatientListPage>(`/patients?${params.toString()}`);
}

export function fetchPatient(patientId: string): Promise<Patient> {
  return apiGet<Patient>(`/patients/${encodeURIComponent(patientId)}`);
}

export function searchByConditions(
  req: ConditionRequest,
): Promise<PatientListItem[]> {
  return apiPost<PatientListItem[]>('/patients/condition-query', req);
}
