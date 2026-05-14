import type { ConditionRequest } from '@/services/patients';

export const queryKeys = {
  patients: {
    list: (q?: string) => ['patients', 'list', q ?? ''] as const,
    condition: (req: ConditionRequest) =>
      ['patients', 'condition', req] as const,
    detail: (patientId: string | undefined) =>
      ['patients', patientId ?? ''] as const,
    subResource: (patientId: string, name: string) =>
      ['patients', patientId, name] as const,
  },
};
