import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/server';
import { ApiError, apiGet } from './api';

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
