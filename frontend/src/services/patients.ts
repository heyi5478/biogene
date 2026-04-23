import { apiGet } from '@/lib/api';
import type { Patient } from '@/types/patient';

export function fetchPatients(): Promise<Patient[]> {
  return apiGet<Patient[]>('/patients');
}

export function fetchPatient(patientId: string): Promise<Patient> {
  return apiGet<Patient>(`/patients/${encodeURIComponent(patientId)}`);
}
