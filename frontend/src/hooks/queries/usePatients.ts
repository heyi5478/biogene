import { useQuery } from '@tanstack/react-query';
import {
  fetchPatients,
  searchByConditions,
  type ConditionRequest,
} from '@/services/patients';
import { queryKeys } from './keys';

const STALE_TIME = 5 * 60 * 1000;
const GC_TIME = 30 * 60 * 1000;

export function usePatients(q?: string) {
  return useQuery({
    queryKey: queryKeys.patients.list(q),
    queryFn: () => fetchPatients(q),
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}

export function useConditionPatients(req: ConditionRequest, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.patients.condition(req),
    queryFn: () => searchByConditions(req),
    enabled,
    staleTime: STALE_TIME,
    gcTime: GC_TIME,
  });
}
