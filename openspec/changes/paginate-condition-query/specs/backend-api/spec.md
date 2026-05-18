## MODIFIED Requirements

### Requirement: Gateway SHALL accept structured condition search at POST /patients/condition-query

The endpoint `POST /patients/condition-query` MUST accept a JSON body of shape `{conditions: ConditionRow[], logic: "AND" | "OR"}` and MUST accept `limit` (default 50, minimum 1, maximum 200) and `offset` (default 0, minimum 0) query parameters; out-of-range values MUST be rejected with HTTP 422. Each `ConditionRow` MUST contain `moduleId`, `fieldId`, `operator` (one of `contains / eq / neq / gt / gte / lt / lte / between / before / after / has_data / no_data`), `value`, and `value2`.

The endpoint MUST return a paginated envelope of shape `{ "items": PatientListItem[], "total": int, "limit": int, "offset": int }` describing the patients whose data satisfies the conditions under the specified logic. `total` MUST be the count of all matching patients across every page, not the page size. The matching patients MUST be ordered deterministically (by `patientId`) before slicing, so the same `(conditions, logic, limit, offset)` always yields the same page. `items` MUST contain at most `limit` elements — the `offset`-based page of that ordered match set. `limit` and `offset` MUST echo the effective values used. Each element of `items` MUST include a `conditionHits: string[]` field listing one human-readable summary per matched condition, formatted `{moduleCode}/{fieldLabel}={value}`.

#### Scenario: Empty condition list returns an empty page
- **WHEN** a client posts `{"conditions": [], "logic": "AND"}` to `/patients/condition-query`
- **THEN** the response MUST be `{"items": [], "total": 0, "limit": 50, "offset": 0}` with status 200

#### Scenario: Single basic-module condition
- **WHEN** a client posts `{"conditions": [{"moduleId": "basic", "fieldId": "diagnosis", "operator": "contains", "value": "Fabry", "value2": ""}], "logic": "AND"}`
- **THEN** `items` MUST contain patients whose `diagnosis` includes "Fabry" (case-insensitive), and `total` MUST be the full count of such patients
- **AND** every element of `items` MUST have `conditionHits` containing one entry referencing diagnosis

#### Scenario: AND logic across modules
- **WHEN** a client posts two conditions (e.g., `basic.diagnosis contains "Fabry"` AND `biomarker.dbsLysoGb3 > 5`) with `logic: "AND"`
- **THEN** the patients counted by `total` MUST be only those matching both conditions
- **AND** that match set MUST be the intersection of each per-condition match set

#### Scenario: OR logic across modules
- **WHEN** the same two conditions are posted with `logic: "OR"`
- **THEN** the patients counted by `total` MUST be those matching either condition
- **AND** that match set MUST be the union of each per-condition match set

#### Scenario: Paginated condition response
- **WHEN** a condition matches more patients than `limit` and a client posts it with `?limit=50&offset=0`
- **THEN** `items` MUST contain at most 50 elements
- **AND** `total` MUST be the full match count across every page
- **AND** posting the same conditions with `?limit=50&offset=50` MUST return a page whose `items` are disjoint from the first page

#### Scenario: Offset past the end yields an empty page
- **WHEN** a client posts a condition with an `offset` greater than or equal to `total`
- **THEN** `items` MUST be an empty array
- **AND** `total` MUST still report the full match count
- **AND** the status MUST be 200

#### Scenario: Invalid pagination parameters are rejected
- **WHEN** a client posts to `/patients/condition-query?limit=0`, `?limit=5000`, or `?offset=-1`
- **THEN** the gateway MUST respond with HTTP 422

#### Scenario: Downstream service fails
- **WHEN** any of svc-patient, svc-lab, svc-disease returns 5xx or a connection error during condition routing
- **THEN** the gateway MUST return HTTP 502 with body `{"error": "upstream_unavailable", "service": "<name>"}`
