import { useQueries } from '@tanstack/react-query';
import { fetchPatient } from '@/services/patients';
import type { Patient } from '@/types/patient';
import { queryKeys } from './keys';

const STALE_TIME = 5 * 60 * 1000;
const GC_TIME = 30 * 60 * 1000;

export interface FetchedPatientsResult {
  patients: Patient[];
  isPending: boolean;
  isError: boolean;
}

/**
 * Fan-out detail fetch — needed by cohort stats / cohort export, since
 * `ConditionResults` only carries `PatientListItem` (no module arrays)
 * after the server-side-search rewire.
 *
 * Each id gets its own React Query entry keyed by `queryKeys.patients.detail(id)`,
 * so a previously-viewed patient is served from cache instantly.
 */
export function useFetchedPatients(
  patientIds: string[],
): FetchedPatientsResult {
  const results = useQueries({
    queries: patientIds.map((id) => ({
      queryKey: queryKeys.patients.detail(id),
      queryFn: () => fetchPatient(id),
      enabled: Boolean(id),
      staleTime: STALE_TIME,
      gcTime: GC_TIME,
    })),
  });

  return {
    patients: results
      .map((r) => r.data)
      .filter((p): p is Patient => Boolean(p)),
    isPending: results.some((r) => r.isPending && r.fetchStatus !== 'idle'),
    isError: results.some((r) => r.isError),
  };
}
