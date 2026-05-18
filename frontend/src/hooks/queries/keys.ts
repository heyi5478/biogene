import type { ConditionRequest } from '@/services/patients';

export const queryKeys = {
  patients: {
    list: (q?: string, page?: number) =>
      ['patients', 'list', q ?? '', page ?? 1] as const,
    condition: (req: ConditionRequest, page?: number) =>
      ['patients', 'condition', req, page ?? 1] as const,
    detail: (patientId: string | undefined) =>
      ['patients', patientId ?? ''] as const,
    subResource: (patientId: string, name: string) =>
      ['patients', patientId, name] as const,
  },
};
