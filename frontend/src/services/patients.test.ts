import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import type { Patient } from '@/types/patient';
import { server } from '@/test/server';
import { ApiError } from '@/lib/api';
import { fetchPatient, fetchPatients } from './patients';

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
  it('returns parsed patient array from gateway /patients', async () => {
    const payload = [makePatient('p1'), makePatient('p2')];
    server.use(
      http.get('http://localhost:8000/patients', () =>
        HttpResponse.json(payload),
      ),
    );

    const result = await fetchPatients();

    expect(result).toEqual(payload);
  });
});

describe('fetchPatient', () => {
  it('returns the parsed patient from gateway /patients/:id', async () => {
    const payload = makePatient('p1');
    server.use(
      http.get('http://localhost:8000/patients/p1', () =>
        HttpResponse.json(payload),
      ),
    );

    const result = await fetchPatient('p1');

    expect(result).toEqual(payload);
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
