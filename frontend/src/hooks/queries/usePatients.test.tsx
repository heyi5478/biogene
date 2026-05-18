import { describe, expect, it, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import type { PatientListItem, PatientListPage } from '@/types/patient';
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

const stubPage = (items: PatientListItem[]): PatientListPage => ({
  items,
  total: items.length,
  limit: 50,
  offset: 0,
});

describe('usePatients', () => {
  it('goes loading → success and caches under queryKeys.patients.list(q, page)', async () => {
    server.use(
      http.get('http://localhost:8000/patients', () =>
        HttpResponse.json(stubPage([stubItem('p1')])),
      ),
    );
    const { client, wrapper } = makeWrapper();

    const { result } = renderHook(() => usePatients('q1', 1), { wrapper });

    expect(result.current.isPending).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toEqual([stubItem('p1')]);

    const cached = client.getQueryData(queryKeys.patients.list('q1', 1));
    expect(cached).toEqual(stubPage([stubItem('p1')]));
  });

  it('issues no request until a non-empty query is submitted', () => {
    const handler = vi.fn(() => HttpResponse.json(stubPage([])));
    server.use(http.get('http://localhost:8000/patients', handler));
    const { wrapper } = makeWrapper();

    const { result } = renderHook(() => usePatients('', 1), { wrapper });

    expect(result.current.status).toBe('pending');
    expect(result.current.fetchStatus).toBe('idle');
    expect(handler).not.toHaveBeenCalled();
  });

  it('forwards the page offset and keys distinctly per page', async () => {
    server.use(
      http.get('http://localhost:8000/patients', ({ request }) => {
        const offset = new URL(request.url).searchParams.get('offset');
        return HttpResponse.json(stubPage([stubItem(`hit-${offset}`)]));
      }),
    );
    const { client, wrapper } = makeWrapper();

    const first = renderHook(() => usePatients('陳', 1), { wrapper });
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));
    expect(first.result.current.data?.items[0].patientId).toBe('hit-0');

    const second = renderHook(() => usePatients('陳', 2), { wrapper });
    await waitFor(() => expect(second.result.current.isSuccess).toBe(true));
    expect(second.result.current.data?.items[0].patientId).toBe('hit-50');

    expect(client.getQueryData(queryKeys.patients.list('陳', 1))).toBeDefined();
    expect(client.getQueryData(queryKeys.patients.list('陳', 2))).toBeDefined();
    expect(client.getQueryData(queryKeys.patients.list('陳', 1))).not.toEqual(
      client.getQueryData(queryKeys.patients.list('陳', 2)),
    );
  });

  it('does not refetch within the staleTime window', async () => {
    const handler = vi.fn(() => HttpResponse.json(stubPage([stubItem('p1')])));
    server.use(http.get('http://localhost:8000/patients', handler));
    const { wrapper } = makeWrapper();

    const first = renderHook(() => usePatients('q', 1), { wrapper });
    await waitFor(() => expect(first.result.current.isSuccess).toBe(true));
    first.unmount();

    const second = renderHook(() => usePatients('q', 1), { wrapper });
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
      () => useConditionPatients({ conditions: [], logic: 'AND' }, false),
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
