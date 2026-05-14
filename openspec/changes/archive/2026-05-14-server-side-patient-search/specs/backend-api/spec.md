## MODIFIED Requirements

### Requirement: Gateway SHALL aggregate patient bundles by fanning out to downstream services

For `GET /patients/{patientId}` (the detail endpoint), the gateway MUST fetch patient base records from `svc-patient`, lab records from `svc-lab`, and disease-module records from `svc-disease` in parallel using `httpx.AsyncClient`, then merge them into a `PatientBundle` whose shape is compatible with the frontend's `Patient` TypeScript type. The list endpoint `GET /patients` no longer returns merged bundles — see "Gateway list endpoint SHALL return a slim PatientListItem array".

#### Scenario: Single-patient aggregated response
- **WHEN** a client calls `GET /patients/{patientId}` with a known patientId
- **THEN** the gateway MUST return a single JSON object (not array) containing the patient's base fields AND nested arrays `aa`, `msms`, `biomarker`, `outbank`, `dnabank`, `opd`, and the relevant disease-module arrays (e.g. `aadc`, `ald`, `bd`, `cah`, `dmd`)
- **AND** the status MUST be 200

#### Scenario: Unknown patientId
- **WHEN** a client calls `GET /patients/{patientId}` with an id that is not present in svc-patient
- **THEN** the gateway MUST return HTTP 404 with an error body `{"error": "patient_not_found", "patientId": "<id>"}`

#### Scenario: Downstream service fails
- **WHEN** the gateway receives a 5xx or connection error from any of svc-patient, svc-lab, svc-disease during a detail aggregation
- **THEN** the gateway MUST return HTTP 502 with an error body identifying which downstream failed
- **AND** the gateway MUST NOT return a partial bundle

### Requirement: Gateway PatientBundle SHALL include opd visit records

The `PatientBundle` returned by `GET /patients/{patientId}` MUST include an `opd` array whose elements match `OpdRecord` (`patientId`, `visitDate`, `sex`, `birthday`, `diagCode`, `diagName`, optional `subDiag1`, optional `subDiag2`). Patients with no opd history MUST receive `opd: []`; the key MUST always be present.

#### Scenario: Single-patient response includes opd

- **WHEN** a client calls `GET http://localhost:8000/patients/{patientId}` with a known id
- **THEN** the returned JSON object MUST contain `opd`
- **AND** its length MUST equal the number of `opd` rows whose `patientId` matches in the seeded data

#### Scenario: Patient with no opd history

- **WHEN** a patient has no opd rows in any source schema
- **THEN** the response's `opd` field MUST be an empty array (not `null`, not absent)

## ADDED Requirements

### Requirement: Gateway list endpoint SHALL return a slim PatientListItem array

The endpoint `GET /patients` MUST return `PatientListItem[]`. Each element MUST contain the patient's base fields (`patientId`, `source`, `name`, `birthday`, `sex`, optional `chartno`, optional `externalChartno`, optional `nbsId`, optional `category`, `linkedPatientIds`, optional `diagnosis`, optional `diagnosis2`, optional `diagnosis3`) plus the summary fields `dnabankCount: int`, `outbankCount: int`, `lastVisitDate: string | null`. The response MUST NOT include any module detail array (no `aa`, `msms`, `biomarker`, `aadc`, `ald`, `mma`, `mps2`, `lsd`, `enzyme`, `gag`, `dnabank`, `outbank`, `opd`, `bd`, `cah`, `dmd`, `g6pd`, `smaScid`, `gcms`).

#### Scenario: List response shape
- **WHEN** a client calls `GET /patients`
- **THEN** every element MUST contain `dnabankCount`, `outbankCount`, and `lastVisitDate`
- **AND** no element MUST contain a key whose value is an array of module records

#### Scenario: Summary fields reflect underlying data
- **WHEN** a patient has 2 dnabank rows, 1 outbank row, and an opd visit on `2025-12-10`
- **THEN** that patient's list item MUST have `dnabankCount: 2`, `outbankCount: 1`, `lastVisitDate: "2025-12-10"`

#### Scenario: Patient with no opd
- **WHEN** a patient has no opd rows
- **THEN** that patient's list item MUST have `lastVisitDate: null`

### Requirement: Gateway SHALL support text search via the `q` query parameter on the list endpoint

The endpoint `GET /patients` MUST accept an optional `q` query parameter. When `q` is absent or empty, the response MUST contain every patient. When `q` is non-empty, the response MUST contain only patients whose `name`, `chartno`, `externalChartno`, or `nbsId` includes `q` (case-insensitive for the latin fields, exact substring for `name`).

#### Scenario: No q parameter
- **WHEN** a client calls `GET /patients`
- **THEN** the response MUST contain every patient known to svc-patient

#### Scenario: q matches a name substring
- **WHEN** the dataset includes a patient named `陳志明` and a client calls `GET /patients?q=陳`
- **THEN** the response MUST include that patient
- **AND** MUST NOT include patients whose name does not contain `陳` and whose chartno/externalChartno/nbsId also do not contain `陳`

#### Scenario: q matches a chartno prefix
- **WHEN** the dataset includes chartno `A1234567` and a client calls `GET /patients?q=A12`
- **THEN** the response MUST include the patient with that chartno

#### Scenario: q matches nothing
- **WHEN** a client calls `GET /patients?q=zzzz_no_match`
- **THEN** the response MUST be an empty array `[]` with status 200

### Requirement: Gateway SHALL accept structured condition search at POST /patients/condition-query

The endpoint `POST /patients/condition-query` MUST accept a JSON body of shape `{conditions: ConditionRow[], logic: "AND" | "OR"}` and return `PatientListItem[]` containing only patients whose data satisfies the conditions under the specified logic. Each `ConditionRow` MUST contain `moduleId`, `fieldId`, `operator` (one of `contains / eq / neq / gt / gte / lt / lte / between / before / after / has_data / no_data`), `value`, and `value2`. Each returned `PatientListItem` MUST also include a `conditionHits: string[]` field listing one human-readable summary per matched condition, formatted `{moduleCode}/{fieldLabel}={value}`.

#### Scenario: Empty condition list returns empty array
- **WHEN** a client posts `{"conditions": [], "logic": "AND"}` to `/patients/condition-query`
- **THEN** the response MUST be `[]` with status 200

#### Scenario: Single basic-module condition
- **WHEN** a client posts `{"conditions": [{"moduleId": "basic", "fieldId": "diagnosis", "operator": "contains", "value": "Fabry", "value2": ""}], "logic": "AND"}`
- **THEN** the response MUST contain every patient whose `diagnosis` includes "Fabry" (case-insensitive)
- **AND** every returned item MUST have `conditionHits` containing one entry referencing diagnosis

#### Scenario: AND logic across modules
- **WHEN** a client posts two conditions (e.g., `basic.diagnosis contains "Fabry"` AND `biomarker.dbsLysoGb3 > 5`) with `logic: "AND"`
- **THEN** the response MUST contain only patients matching both conditions
- **AND** the result set MUST be the intersection of each per-condition match set

#### Scenario: OR logic across modules
- **WHEN** the same two conditions are posted with `logic: "OR"`
- **THEN** the response MUST contain patients matching either condition
- **AND** the result set MUST be the union of each per-condition match set

#### Scenario: Downstream service fails
- **WHEN** any of svc-patient, svc-lab, svc-disease returns 5xx or a connection error during condition routing
- **THEN** the gateway MUST return HTTP 502 with body `{"error": "upstream_unavailable", "service": "<name>"}`

### Requirement: Each downstream service SHALL expose a condition-match endpoint

`svc-patient` MUST expose `POST /patients/condition-match`, `svc-lab` MUST expose `POST /labs/condition-match`, and `svc-disease` MUST expose `POST /diseases/condition-match`. Each endpoint MUST accept a `ConditionRequest` (the same shape as the gateway endpoint) and return `{conditionMatches: list[list[str]]}` where the outer list is parallel to the inbound `conditions` list and each inner list contains the `patientIds` matched by that condition. Conditions whose `moduleId` is not owned by the receiving service MUST be answered with the empty list (not an error). Operators MUST behave per `backend.shared.condition.eval_condition`.

#### Scenario: Service answers conditions for its modules only
- **WHEN** svc-lab receives a request with one condition on `aa.specimenType` and one condition on `basic.name`
- **THEN** the response MUST contain a non-empty inner list for the `aa` condition (if any patient matches) and an empty inner list for the `basic` condition

#### Scenario: Operator semantics match the evaluator
- **WHEN** any service receives a `between` condition with `value="0"` and `value2="10"` against a numeric field
- **THEN** the matched patientIds MUST be exactly the patientIds whose records have at least one row whose field value is between 0 and 10 inclusive

#### Scenario: Unknown moduleId returns empty
- **WHEN** any service receives a condition with `moduleId="unknown"` 
- **THEN** the response MUST contain an empty inner list for that condition (not an error)
