## ADDED Requirements

### Requirement: Gateway PatientBundle SHALL include opd visit records

The `PatientBundle` returned by `GET /patients` and `GET /patients/{patientId}` MUST include an `opd` array whose elements match `OpdRecord` (`patientId`, `visitDate`, `sex`, `birthday`, `diagCode`, `diagName`, optional `subDiag1`, optional `subDiag2`). Patients with no opd history MUST receive `opd: []`; the key MUST always be present.

#### Scenario: List response includes opd for every patient

- **WHEN** a client calls `GET http://localhost:8000/patients`
- **THEN** every element in the response array MUST contain the key `opd`
- **AND** for patients whose `patientId` appears in `db_{main,external,nbs}/opd.json`, the array MUST contain one element per matching row

#### Scenario: Single-patient response includes opd

- **WHEN** a client calls `GET http://localhost:8000/patients/{patientId}` with a known id
- **THEN** the returned JSON object MUST contain `opd`
- **AND** its length MUST equal the number of `opd.json` rows whose `patientId` matches

#### Scenario: Patient with no opd history

- **WHEN** a patient has no entry in any `opd.json`
- **THEN** the response's `opd` field MUST be an empty array (not `null`, not absent)

### Requirement: svc-patient SHALL expose opd visit endpoints

`svc-patient` (port 8001) MUST load `db_{main,external,nbs}/opd.json` at startup into an in-memory index keyed by `patientId`, and MUST expose:

- `GET /opd/{patient_id}` returning an `OpdBundle` (`{ "opd": [...] }`) — empty bundle if the id has no opd rows
- `POST /opd/batch` accepting `{ "patientIds": [...] }` and returning `dict[patientId, OpdBundle]` — patients with no rows receive an empty bundle

Response shape MUST mirror `svc-lab` / `svc-disease` bundle conventions so the gateway can flat-merge via `{**patient, **opd, **labs, **diseases}`.

#### Scenario: Single opd lookup

- **WHEN** the gateway calls `GET http://localhost:8001/opd/{patientId}`
- **THEN** svc-patient MUST return `{"opd": [...]}` where each row has the `patientId` matching the request

#### Scenario: Batch opd lookup

- **WHEN** the gateway calls `POST http://localhost:8001/opd/batch` with `{ "patientIds": ["a", "b"] }`
- **THEN** svc-patient MUST return `{"a": {"opd": [...]}, "b": {"opd": [...]}}`
- **AND** an unknown id in the request MUST receive an empty bundle `{"opd": []}`, not an error

### Requirement: Gateway SHALL fan out to svc-patient opd endpoints in parallel with lab and disease calls

The gateway's aggregation MUST include opd fetches in the same `asyncio.gather` critical path as lab and disease fetches, so the added fan-out does not lengthen the request tail.

#### Scenario: List endpoint concurrency

- **WHEN** the gateway handles `GET /patients`
- **THEN** opd, lab, and disease batch calls MUST be awaited together via `asyncio.gather`
- **AND** the overall latency MUST be bounded by the slowest of the three, not their sum

#### Scenario: Upstream opd failure surfaces as 502

- **WHEN** svc-patient returns 5xx or connection error on `/opd/batch` (or `/opd/{id}`)
- **THEN** the gateway MUST return HTTP 502 with body `{"error": "upstream_unavailable", "service": "svc-patient"}`
- **AND** MUST NOT return a partial bundle
