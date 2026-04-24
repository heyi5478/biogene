# shared-ui-buttons Specification

## Purpose
TBD - created by archiving change add-semantic-button-variants. Update Purpose after archive.
## Requirements
### Requirement: Shared Button component SHALL expose a fixed set of semantic variants

The shared `Button` component at `frontend/src/components/ui/button.tsx` SHALL expose the following ten variants via its `variant` prop, each mapped to tokens defined in `frontend/src/index.css` and exposed through `frontend/tailwind.config.ts`:

- `default` — filled, uses `--primary` / `--primary-foreground`
- `destructive` — filled, uses `--destructive` / `--destructive-foreground`
- `outline` — bordered transparent, uses `--input` border, `--accent` hover
- `secondary` — filled muted, uses `--secondary` / `--secondary-foreground`
- `ghost` — transparent, uses `--accent` hover
- `link` — text-only, uses `--primary` text color
- `warning` — filled, uses `--warning` / `--warning-foreground`
- `success` — filled, uses `--success` / `--success-foreground`
- `info` — filled, uses `--info` / `--info-foreground`
- `danger` — filled, uses `--danger` / `--danger-foreground`

When the `variant` prop is omitted, the component SHALL default to `default`.

#### Scenario: Rendering the warning variant
- **WHEN** a caller renders `<Button variant="warning">清除</Button>`
- **THEN** the rendered element MUST have a background using `hsl(var(--warning))` and text color using `hsl(var(--warning-foreground))`
- **AND** hovering MUST reduce the background opacity to 90% (matching the existing filled-variant hover pattern used by `default` and `destructive`)

#### Scenario: Rendering the success variant
- **WHEN** a caller renders `<Button variant="success">`
- **THEN** the rendered element MUST use `hsl(var(--success))` background and `hsl(var(--success-foreground))` text

#### Scenario: Rendering the info variant
- **WHEN** a caller renders `<Button variant="info">`
- **THEN** the rendered element MUST use `hsl(var(--info))` background and `hsl(var(--info-foreground))` text

#### Scenario: Rendering the danger variant
- **WHEN** a caller renders `<Button variant="danger">`
- **THEN** the rendered element MUST use `hsl(var(--danger))` background and `hsl(var(--danger-foreground))` text

#### Scenario: Existing variants remain unchanged
- **WHEN** a caller renders `<Button variant="outline">` or any other pre-existing variant
- **THEN** the rendered classes MUST be identical to the pre-change behavior (no regression for the six existing variants)

### Requirement: The `info` semantic color SHALL be visually distinguishable from `primary`

The CSS custom property `--info` (defined in `frontend/src/index.css` for both `:root` and `.dark`) SHALL resolve to a hue that is visually distinguishable from `--primary` so that a `variant="info"` button is not mistaken for a `variant="default"` button when placed adjacent to one.

#### Scenario: Info and primary are not identical
- **WHEN** the application is rendered in either light or dark mode
- **THEN** the HSL values of `--info` and `--primary` MUST differ by at least 10 degrees in hue OR by at least 10 percentage points in either saturation or lightness

### Requirement: The `danger` semantic color SHALL be visually distinguishable from `destructive`

The CSS custom property `--danger` (defined in `frontend/src/index.css` for both `:root` and `.dark`) SHALL resolve to a hue that is visually distinguishable from `--destructive` so that a `variant="danger"` button (irreversible-but-recoverable actions such as clearing user input) is not mistaken for a `variant="destructive"` button (permanent deletion).

#### Scenario: Danger and destructive are not identical
- **WHEN** the application is rendered in either light or dark mode
- **THEN** the HSL values of `--danger` and `--destructive` MUST differ by at least 10 degrees in hue OR by at least 10 percentage points in either saturation or lightness

### Requirement: Tailwind SHALL expose semantic color tokens as utility classes

`frontend/tailwind.config.ts` SHALL register `warning`, `success`, `info`, and `danger` (each with a `DEFAULT` and `foreground` pair) in its `theme.extend.colors` map, bound to the corresponding `hsl(var(--...))` CSS custom properties.

#### Scenario: Warning utility classes are available
- **WHEN** a developer writes `className="bg-warning text-warning-foreground"` in any `.tsx` file under `frontend/src/`
- **THEN** Tailwind MUST compile these classes without error
- **AND** the resulting styles MUST resolve to the values defined by `--warning` / `--warning-foreground`

#### Scenario: Success, info, and danger utility classes are available
- **WHEN** a developer writes `className="bg-success"`, `className="text-success-foreground"`, `className="bg-info"`, `className="text-info-foreground"`, `className="bg-danger"`, or `className="text-danger-foreground"`
- **THEN** Tailwind MUST compile these classes without error

### Requirement: Designated action buttons SHALL use the matching semantic variant

The following user-facing buttons SHALL render with the indicated semantic variant so their color communicates the nature of the action:

- The「清除全部條件」button in `frontend/src/components/FilterPanel.tsx` (sidebar footer) SHALL use `variant="destructive"`.
- The「清除全部條件」button in `frontend/src/components/ConditionBuilder.tsx` (condition-builder footer) SHALL use `variant="destructive"`.
- The「統計」button in `frontend/src/components/PatientSummary.tsx` (right-hand toolbar of the patient summary card) SHALL use `variant="success"`.
- The「匯出」button in `frontend/src/components/PatientSummary.tsx` (right-hand toolbar, adjacent to 統計) SHALL use `variant="info"`.

The surrounding jump-link buttons in `PatientSummary.tsx` (門診 / MS/MS / AA / Enzyme / GAG / DNA / 外送) SHALL continue to use `variant="outline"` and MUST NOT be recolored by this change.

#### Scenario: Clear-all button uses destructive
- **WHEN** the FilterPanel renders its footer
- **THEN** the「清除全部條件」button MUST be rendered via `<Button variant="destructive">`

#### Scenario: Condition-builder clear-all button uses destructive
- **WHEN** the ConditionBuilder renders its footer
- **THEN** the「清除全部條件」button MUST be rendered via `<Button variant="destructive">`

#### Scenario: Stats button uses success
- **WHEN** PatientSummary renders with a selected patient
- **THEN** the「統計」button MUST be rendered via `<Button variant="success">`

#### Scenario: Export button uses info
- **WHEN** PatientSummary renders with a selected patient
- **THEN** the「匯出」button MUST be rendered via `<Button variant="info">`

#### Scenario: Jump links remain outline
- **WHEN** PatientSummary renders jump-link buttons for modules with `count > 0`
- **THEN** every such jump-link button MUST be rendered via `<Button variant="outline">`

