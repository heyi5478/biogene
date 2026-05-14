import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/server';
import { ApiError, apiGet, apiPost } from './api';

describe('apiGet', () => {
  it('resolves with parsed JSON on 200', async () => {
    server.use(
      http.get('http://localhost:8000/patients', () =>
        HttpResponse.json([{ patientId: 'p1' }]),
      ),
    );

    const result = await apiGet<Array<{ patientId: string }>>('/patients');

    expect(result).toEqual([{ patientId: 'p1' }]);
  });

  it('throws ApiError with status and code on 4xx', async () => {
    server.use(
      http.get('http://localhost:8000/patients/abc', () =>
        HttpResponse.json(
          { error: 'patient_not_found', patientId: 'abc' },
          { status: 404 },
        ),
      ),
    );

    await expect(apiGet('/patients/abc')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
      code: 'patient_not_found',
      body: { error: 'patient_not_found', patientId: 'abc' },
    });
  });

  it('throws ApiError(status=0) on network failure', async () => {
    server.use(
      http.get('http://localhost:8000/patients', () => HttpResponse.error()),
    );

    const error = await apiGet('/patients').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(0);
  });
});

describe('apiPost', () => {
  it('serialises the body as JSON with Content-Type application/json', async () => {
    let capturedBody: unknown;
    let capturedContentType: string | null = null;
    server.use(
      http.post(
        'http://localhost:8000/patients/condition-query',
        async ({ request }) => {
          capturedContentType = request.headers.get('Content-Type');
          capturedBody = await request.json();
          return HttpResponse.json([{ patientId: 'hit' }]);
        },
      ),
    );

    const result = await apiPost<Array<{ patientId: string }>>(
      '/patients/condition-query',
      { conditions: [], logic: 'AND' },
    );

    expect(result).toEqual([{ patientId: 'hit' }]);
    expect(capturedBody).toEqual({ conditions: [], logic: 'AND' });
    expect(capturedContentType).toBe('application/json');
  });

  it('throws ApiError with status and code on 4xx', async () => {
    server.use(
      http.post('http://localhost:8000/patients/condition-query', () =>
        HttpResponse.json(
          { error: 'bad_request', detail: 'unknown operator' },
          { status: 400 },
        ),
      ),
    );

    await expect(
      apiPost('/patients/condition-query', { conditions: [], logic: 'AND' }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      code: 'bad_request',
    });
  });

  it('throws ApiError(status=0) on network failure', async () => {
    server.use(
      http.post('http://localhost:8000/patients/condition-query', () =>
        HttpResponse.error(),
      ),
    );

    const error = await apiPost('/patients/condition-query', {
      conditions: [],
      logic: 'AND',
    }).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(0);
  });
});
