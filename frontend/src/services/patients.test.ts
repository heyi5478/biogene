import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import type { Patient, PatientListItem } from '@/types/patient';
import { server } from '@/test/server';
import { ApiError } from '@/lib/api';
import { fetchPatient, fetchPatients, searchByConditions } from './patients';

const makeListItem = (id: string): PatientListItem => ({
  patientId: id,
  source: 'main',
  name: `Patient ${id}`,
  birthday: '2000-01-01',
  sex: '男',
  dnabankCount: 0,
  outbankCount: 0,
  lastVisitDate: null,
});

const makePatient = (id: string): Patient => ({
  patientId: id,
  source: 'main',
  name: `Patient ${id}`,
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
});

describe('fetchPatients', () => {
  it('returns slim patient list when no q is supplied', async () => {
    const payload = [makeListItem('p1'), makeListItem('p2')];
    server.use(
      http.get('http://localhost:8000/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q');
        // No q on the request URL — verifies the query string was omitted.
        if (q === null) return HttpResponse.json(payload);
        return HttpResponse.json([]);
      }),
    );

    const result = await fetchPatients();

    expect(result).toEqual(payload);
  });

  it('forwards q as URL-encoded query string', async () => {
    server.use(
      http.get('http://localhost:8000/patients', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q');
        if (q === '陳') return HttpResponse.json([makeListItem('陳-id')]);
        return HttpResponse.json([]);
      }),
    );

    const result = await fetchPatients('陳');

    expect(result).toHaveLength(1);
    expect(result[0].patientId).toBe('陳-id');
  });
});

describe('fetchPatient', () => {
  it('returns the full patient bundle from gateway /patients/:id', async () => {
    const payload = makePatient('p1');
    server.use(
      http.get('http://localhost:8000/patients/p1', () =>
        HttpResponse.json(payload),
      ),
    );

    const result = await fetchPatient('p1');

    expect(result).toEqual(payload);
    expect(result.aa).toEqual([]);
    expect(result.opd).toEqual([]);
  });

  it('propagates 404 as ApiError with code', async () => {
    server.use(
      http.get('http://localhost:8000/patients/missing', () =>
        HttpResponse.json(
          { error: 'patient_not_found', patientId: 'missing' },
          { status: 404 },
        ),
      ),
    );

    const error = await fetchPatient('missing').catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(404);
    expect((error as ApiError).code).toBe('patient_not_found');
  });
});

describe('searchByConditions', () => {
  it('POSTs the condition request to /patients/condition-query and returns slim items', async () => {
    const payload = [
      { ...makeListItem('hit'), conditionHits: ['基本資料/主診斷=Fabry'] },
    ];
    let capturedBody: unknown;
    server.use(
      http.post(
        'http://localhost:8000/patients/condition-query',
        async ({ request }) => {
          capturedBody = await request.json();
          return HttpResponse.json(payload);
        },
      ),
    );

    const req = {
      conditions: [
        {
          id: 'c1',
          moduleId: 'basic' as const,
          fieldId: 'diagnosis',
          operator: 'contains' as const,
          value: 'Fabry',
          value2: '',
        },
      ],
      logic: 'AND' as const,
    };
    const result = await searchByConditions(req);

    expect(result).toEqual(payload);
    expect(capturedBody).toEqual(req);
  });
});
