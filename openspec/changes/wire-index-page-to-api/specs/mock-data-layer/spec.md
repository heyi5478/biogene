## REMOVED Requirements

### Requirement: Frontend SHALL load JSON mock data via Vite JSON imports and join by patientId

**Reason**: Frontend now sources patient data from the backend gateway (`GET /patients`) via the `usePatients()` React Query hook, introduced by the `add-fastapi-microservices-skeleton` and `add-frontend-api-client-layer` changes. Vite JSON imports from `backend/mock-data/**` are no longer part of the frontend's runtime. Mock-data JSON files remain authoritative **as a backend data source only**.

**Migration**: Any frontend code previously importing from `@/data/mockData` MUST migrate to:
- For patient list data: `import { usePatients } from '@/hooks/queries/usePatients'`
- For single patient lookup: `import { usePatient } from '@/hooks/queries/usePatient'`
- For the `Patient` type and sub-types: `import type { Patient } from '@/types/patient'`

The `mock-data-layer` capability continues to govern JSON file layout, UUID v5 generation, FK integrity, and NBS sub-table structure — those requirements remain unchanged. Only the frontend-consumption clause is retired.
