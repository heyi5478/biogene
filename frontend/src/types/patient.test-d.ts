// Compile-time assertion: PatientListItem MUST NOT declare any module
// detail array property. If a future edit to patient.ts adds e.g. `aa:
// AaSample[]` to PatientListItem, the type below stops being `never`
// and `_NoModuleArrays` flips to `false`, failing the compile.
//
// This file is .test-d.ts so vitest ignores it as a runtime test; it
// exists purely to be type-checked by tsc (covered by `npm run typecheck`).

import type { PatientListItem } from '@/types/patient';

type _ModuleKeys =
  | 'opd'
  | 'aa'
  | 'msms'
  | 'biomarker'
  | 'aadc'
  | 'ald'
  | 'mma'
  | 'mps2'
  | 'lsd'
  | 'enzyme'
  | 'gag'
  | 'dnabank'
  | 'outbank'
  | 'gcms'
  | 'bd'
  | 'cah'
  | 'dmd'
  | 'g6pd'
  | 'smaScid';

type _ListItemModuleArrays = Extract<keyof PatientListItem, _ModuleKeys>;

// If PatientListItem grows a module-array key, this assertion fails.
type _NoModuleArrays = _ListItemModuleArrays extends never ? true : false;

export const _patientListItemHasNoModuleArrays: _NoModuleArrays = true;
