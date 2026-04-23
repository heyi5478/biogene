import { useQuery } from '@tanstack/react-query';
import { fetchPatients } from '@/services/patients';
import { queryKeys } from './keys';

export function usePatients() {
  return useQuery({
    queryKey: queryKeys.patients.all,
    queryFn: fetchPatients,
  });
}
