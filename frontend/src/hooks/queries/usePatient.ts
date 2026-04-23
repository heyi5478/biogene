import { useQuery } from '@tanstack/react-query';
import { fetchPatient } from '@/services/patients';
import { queryKeys } from './keys';

export function usePatient(patientId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.patients.detail(patientId ?? ''),
    queryFn: () => fetchPatient(patientId!),
    enabled: Boolean(patientId),
  });
}
