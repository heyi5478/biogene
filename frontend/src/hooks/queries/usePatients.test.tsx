import { describe, expect, it, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import type { PatientListItem } from '@/types/patient';
import { server } from '@/test/server';
import { queryKeys } from './keys';
import { usePatients, useConditionPatients } from './usePatients';

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

const stubItem = (id: string): PatientListItem => ({
  patientId: id,
  source: 'main',
  name: `Patient ${id}`,
  birthday: '2000-01-01',
  sex: '男',
  dnabankCount: 0,
  outbankCount: 0,
  lastVisitDate: null,
});

describe('usePatients', () => {
  it('goes loading → success and caches under queryKeys.patients.list("")', async () => {
    server.use(
      http.get('http://localhost:8000/patients', () =>
        HttpResponse.json([stubItem('p1')]),
      ),
    );
    const { client, wrapper } = makeWrapper();

    const { result } = renderHook(() => usePatients(), { wrapper });

    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([stubItem('p1')]);

    const cached = client.getQueryData(queryKeys.patients.list());
    expect(cached).toEqual([stubItem('p1')]);
  });

  it('forwards q to the request URL and keys distinctly per q', async () => {
    server.use(
      http.get('http://localhost:8000/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q');
        return HttpResponse.json(q ? [stubItem(`hit-${q}`)] : []);
      }),
    );
    const { client, wrapper } = makeWrapper();

    const first = renderHook(() => usePatients('陳'), { wrapper });
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));
    expect(first.result.current.data?.[0].patientId).toBe('hit-陳');

    const second = renderHook(() => usePatients('A12'), { wrapper });
    await waitFor(() => expect(second.result.current.isSuccess).toBe(true));
    expect(second.result.current.data?.[0].patientId).toBe('hit-A12');

    expect(client.getQueryData(queryKeys.patients.list('陳'))).toBeDefined();
    expect(client.getQueryData(queryKeys.patients.list('A12'))).toBeDefined();
    expect(
      client.getQueryData(queryKeys.patients.list('陳')),
    ).not.toEqual(client.getQueryData(queryKeys.patients.list('A12')));
  });

  it('does not refetch within the staleTime window', async () => {
    const handler = vi.fn(() => HttpResponse.json([stubItem('p1')]));
    server.use(http.get('http://localhost:8000/patients', handler));
    const { wrapper } = makeWrapper();

    const first = renderHook(() => usePatients('q'), { wrapper });
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));
    first.unmount();

    const second = renderHook(() => usePatients('q'), { wrapper });
    await waitFor(() => expect(second.result.current.isSuccess).toBe(true));

    expect(handler).toHaveBeenCalledTimes(1);
  });
});

describe('useConditionPatients', () => {
  it('does not fire while enabled is false', () => {
    const handler = vi.fn(() => HttpResponse.json([]));
    server.use(
      http.post('http://localhost:8000/patients/condition-query', handler),
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () =>
        useConditionPatients({ conditions: [], logic: 'AND' }, false),
      { wrapper },
    );

    expect(result.current.fetchStatus).toBe('idle');
    expect(result.current.status).toBe('pending');
    expect(handler).not.toHaveBeenCalled();
  });

  it('fires when enabled and returns the resolved list', async () => {
    server.use(
      http.post('http://localhost:8000/patients/condition-query', () =>
        HttpResponse.json([stubItem('hit')]),
      ),
    );
    const { wrapper } = makeWrapper();

    const { result } = renderHook(
      () =>
        useConditionPatients(
          {
            conditions: [
              {
                id: 'c1',
                moduleId: 'basic',
                fieldId: 'diagnosis',
                operator: 'contains',
                value: 'Fabry',
                value2: '',
              },
            ],
            logic: 'AND',
          },
          true,
        ),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([stubItem('hit')]);
  });
});
