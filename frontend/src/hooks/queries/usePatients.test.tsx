import { describe, expect, it } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import type { Patient } from '@/types/patient';
import { server } from '@/test/server';
import { queryKeys } from './keys';
import { usePatients } from './usePatients';

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const Wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return { client, wrapper: Wrapper };
}

const stubPatient: Patient = {
  patientId: 'p1',
  source: 'main',
  name: 'Patient p1',
  birthday: '2000-01-01',
  sex: '男',
  opd: [],
  aa: [],
  msms: [],
  biomarker: [],
  aadc: [],
  ald: [],
  mma: [],
  mps2: [],
  lsd: [],
  enzyme: [],
  gag: [],
  dnabank: [],
  outbank: [],
  bd: [],
  cah: [],
  dmd: [],
  g6pd: [],
  smaScid: [],
};

describe('usePatients', () => {
  it('goes loading → success and uses queryKeys.patients.all', async () => {
    server.use(
      http.get('http://localhost:8000/patients', () =>
        HttpResponse.json([stubPatient]),
      ),
    );
    const { client, wrapper } = makeWrapper();

    const { result } = renderHook(() => usePatients(), { wrapper });

    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([stubPatient]);

    const cached = client.getQueryData(queryKeys.patients.all);
    expect(cached).toEqual([stubPatient]);
  });
});
