# nbs-screening-modules Specification

## Purpose
TBD - created by archiving change restructure-mockdata-for-db-alignment. Update Purpose after archive.
## Requirements

### Requirement: Type system SHALL define five NBS-specific module types

`frontend/src/types/medical.ts` MUST extend `ModuleId` with the literals `'bd' | 'cah' | 'dmd' | 'g6pd' | 'smaScid'` and define corresponding sample interfaces `BdSample`, `CahSample`, `DmdSample`, `G6pdSample`, `SmaScidSample`. `CahSample` MUST include an optional `tgal?: TgalSubSample[]` array; `DmdSample` MUST include an optional `tsh?: TshSubSample[]` array. The Patient interface MUST add `bd: BdSample[]`, `cah: CahSample[]`, `dmd: DmdSample[]`, `g6pd: G6pdSample[]`, `smaScid: SmaScidSample[]` fields.

#### Scenario: TypeScript compilation accepts new module fields
- **WHEN** `npx tsc --noEmit` runs in `frontend/`
- **THEN** the compilation MUST succeed
- **AND** code that reads `patient.bd[0].biotinidaseActivity` MUST type-check

#### Scenario: Sub-table is reachable through parent
- **WHEN** code accesses `patient.cah[0].tgal?.[0].totalGalactose`
- **THEN** the access MUST be type-safe and the value MUST come from the corresponding `cah_tgal.json` row joined under its parent `cah` row

### Requirement: Module metadata SHALL register the five NBS modules under a new "nbs" group

`MODULE_DEFINITIONS` in `frontend/src/types/medical.ts` MUST contain one `ModuleInfo` entry per new ModuleId (`bd`, `cah`, `dmd`, `g6pd`, `smaScid`), each with `group: 'nbs'`. The `ModuleInfo['group']` union type MUST be extended to include `'nbs'`. `MODULE_FIELDS` MUST contain corresponding entries with at minimum `sampleId`, `collectDate`, `result`, and the module-specific analyte fields per the design document.

#### Scenario: ConditionBuilder shows new modules
- **WHEN** the user opens the ConditionBuilder module dropdown
- **THEN** the five NBS modules MUST appear under a section labeled for the `'nbs'` group

#### Scenario: User builds a condition on a new module
- **WHEN** the user selects `bd / biotinidaseActivity < 5` and submits
- **THEN** `evaluateConditions` MUST return only patients whose `bd` array contains a sample meeting the condition

### Requirement: Sub-tables tgal and tsh SHALL NOT be exposed as standalone ConditionBuilder modules

The literals `'tgal'` and `'tsh'` MUST NOT be added to `ModuleId`. They MUST NOT appear in `MODULE_FIELDS`, `MODULE_DEFINITIONS`, or any UI module selector. Their data MUST only be reachable as nested arrays inside their parent `cah` / `dmd` records.

#### Scenario: ConditionBuilder dropdown does not list sub-tables
- **WHEN** the user opens the ConditionBuilder module dropdown
- **THEN** "tgal" and "tsh" MUST NOT appear as options

#### Scenario: Sub-table data is rendered as nested rows
- **WHEN** `ResultModules` renders the `cah` section for a patient with `tgal` sub-rows
- **THEN** the `tgal` rows MUST appear as a nested table beneath the parent `cah` row, not as a separate top-level section

### Requirement: ResultModules SHALL render NBS module sections for patients from any source

When a patient's `bd`, `cah`, `dmd`, `g6pd`, or `smaScid` array is non-empty, `ResultModules` MUST render a corresponding section displaying the rows. When the array is empty, the section MUST NOT be rendered (no empty headers).

#### Scenario: NBS patient with cah and tgal data
- **WHEN** `ResultModules` renders an NBS patient whose `cah` array contains one record with two `tgal` sub-records
- **THEN** the rendered output MUST show the `cah` row followed by two indented `tgal` rows

#### Scenario: Main DB patient with no NBS data
- **WHEN** a `db_main` patient is rendered and `patient.bd` is `[]`
- **THEN** no `bd` section header MUST be rendered

### Requirement: Patient query SHALL provide an "nbs" tab grouping the five NBS modules

`Index.tsx`'s `tabModuleMap` MUST include a `'nbs'` entry mapping to the five NBS ModuleIds. The UI MUST render an "nbs" tab in addition to the existing tabs.

#### Scenario: User clicks the nbs tab
- **WHEN** the user selects the "nbs" tab on the patient query view
- **THEN** only the `bd`, `cah`, `dmd`, `g6pd`, `smaScid` sections MUST be visible
