import { apiGet, apiPost } from '@/lib/api';
import type { Patient, PatientListItem } from '@/types/patient';
import type { ConditionRow, ConditionLogic } from '@/types/medical';

export interface ConditionRequest {
  conditions: ConditionRow[];
  logic: ConditionLogic;
}

export function fetchPatients(q?: string): Promise<PatientListItem[]> {
  if (q === undefined || q === '') {
    return apiGet<PatientListItem[]>('/patients');
  }
  return apiGet<PatientListItem[]>(`/patients?q=${encodeURIComponent(q)}`);
}

export function fetchPatient(patientId: string): Promise<Patient> {
  return apiGet<Patient>(`/patients/${encodeURIComponent(patientId)}`);
}

export function searchByConditions(
  req: ConditionRequest,
): Promise<PatientListItem[]> {
  return apiPost<PatientListItem[]>('/patients/condition-query', req);
}
