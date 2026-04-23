export const queryKeys = {
  patients: {
    all: ['patients'] as const,
    detail: (patientId: string) => ['patients', patientId] as const,
    subResource: (patientId: string, name: string) =>
      ['patients', patientId, name] as const,
  },
};
