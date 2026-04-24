## Context

The frontend is React 19 + TypeScript + Vite, styled with Tailwind 3.4 and shadcn/ui primitives. Button variants are declared centrally with `class-variance-authority` (CVA) in `frontend/src/components/ui/button.tsx`, and color tokens are declared as HSL CSS custom properties in `frontend/src/index.css` then bridged into Tailwind via `frontend/tailwind.config.ts`.

The project already defined semantic tokens `--warning`, `--success`, `--info` (and their `-foreground` counterparts) for both light and dark themes, but:

1. `tailwind.config.ts` never registered these tokens, so `bg-warning` / `text-success-foreground` / etc. do not compile.
2. No button variant consumes them, so callers who want a warning-colored button must inline Tailwind classes, bypassing CVA.
3. `--info` and `--primary` resolve to the **same** HSL (`205 75% 42%` light, `205 70% 50%` dark), so an `info` button would be indistinguishable from the default primary button.

Three specific buttons — clear-all, stats, export — need distinct visual weight today; many more similar cases are likely to arise as the app grows (success toasts, warning confirmations, info banners). A single, reusable, variant-based solution is cheaper than per-site inline styling.

## Goals / Non-Goals

**Goals:**
- Make `warning` / `success` / `info` usable as Tailwind utilities AND as Button variants, once, in a way every future caller can reuse.
- Re-color the three specific buttons named in the proposal to signal action semantics.
- Preserve existing dark-mode support end-to-end.
- Leave every other caller of `<Button>` visually unchanged.

**Non-Goals:**
- Do NOT redesign the outline/secondary/ghost/link variants.
- Do NOT introduce new button **sizes**, shapes, or icon conventions.
- Do NOT migrate the ad-hoc inline `<button>` elements in `FilterPanel.tsx` (mode toggle, preset pills) to the `Button` component — that is a larger refactor out of scope.
- Do NOT touch the backend, API client, or any data flow.

## Decisions

### Decision 1: Add variants via CVA, not via ad-hoc className
Extend the existing `buttonVariants` CVA table with three new filled variants following the exact same pattern as `default` and `destructive`:

```ts
warning: 'bg-warning text-warning-foreground hover:bg-warning/90',
success: 'bg-success text-success-foreground hover:bg-success/90',
info:    'bg-info text-info-foreground hover:bg-info/90',
```

**Why:** CVA gives type-safe `variant="..."` props automatically (via `VariantProps<typeof buttonVariants>`), integrates with the existing `cn()` merger, and keeps every color decision in a single source of truth. Alternatives considered:

- *Inline Tailwind classes at each call site* — rejected because it duplicates hover logic, breaks discoverability, and fragments the visual system.
- *A second component (e.g., `SemanticButton`)* — rejected as needless abstraction; CVA variants are precisely the mechanism for this.

### Decision 2: Register colors in Tailwind, do not write plugin CSS
Add three entries to `theme.extend.colors` in `tailwind.config.ts`, mirroring the shape already used for `primary` / `destructive`:

```ts
warning: { DEFAULT: 'hsl(var(--warning))', foreground: 'hsl(var(--warning-foreground))' },
success: { DEFAULT: 'hsl(var(--success))', foreground: 'hsl(var(--success-foreground))' },
info:    { DEFAULT: 'hsl(var(--info))',    foreground: 'hsl(var(--info-foreground))' },
```

**Why:** Matches the established pattern; requires zero new tooling. Alternative (writing a Tailwind plugin) was rejected as over-engineering.

### Decision 3: Shift `--info` hue so it is distinct from `--primary`
Change `--info` in `src/index.css`:
- Light (`:root`): `205 75% 42%` → `190 70% 40%` (cyan-leaning)
- Dark (`.dark`): `205 70% 50%` → `190 65% 48%` (cyan-leaning)

**Why:** A `variant="info"` button that looks identical to a `variant="default"` button has negative value. A 15° hue shift into cyan produces a clearly distinguishable color while still reading as a "blue family" info signal. Alternatives considered:

- *Use `--module-disease` (purple)* — rejected; purple overloads an existing module semantic.
- *Use `--success`-like green for both stats and export* — rejected; collapses two semantics into one.
- *Leave `--info = --primary` and pick a different token for export* — rejected; would require inventing a new ad-hoc token just for one button.

### Decision 4: `success` for 統計, `info` for 匯出
**Why:** Stats/analytics read as "positive informational insight" — green communicates completeness and positivity better than a neutral color. Export is a data-movement action; the cyan `info` hue signals "informational action" without the severity of warning or destructive. Both choices keep the warning amber exclusively for destructive/irreversible clear operations, preserving its signal strength.

## Risks / Trade-offs

- **Risk:** Developers unfamiliar with the change may keep inlining `bg-yellow-500` style classes instead of using `variant="warning"`. → **Mitigation:** Document the available variants at the top of `button.tsx` (already a compact file) and mention the variants in spec file so future changes reference them.
- **Risk:** Shifting `--info` hue could surprise any future code that depends on `--info === --primary`. → **Mitigation:** A full-repo grep confirmed `--info` / `var(--info)` is not referenced anywhere outside `index.css` today, so there are no existing consumers to break.
- **Risk:** The three newly-colored buttons sit near outline neighbors; some designers may find the contrast jarring. → **Mitigation:** This is the intended effect — the whole point is to separate "actions" from "navigation." If rejected at review, reverting is a one-line change per call site.
- **Trade-off:** Filled colored buttons draw more attention than outline. In PatientSummary the 統計/匯出 buttons are small (`h-6 px-2 text-[10px]`) so the saturation remains low-key; this was verified visually against the existing `variant="destructive"` rendering at comparable size.

## Migration Plan

This change is a straightforward forward-only edit — no feature flag, no data migration, no backwards compatibility shim needed.

1. Merge `tailwind.config.ts` + `index.css` + `button.tsx` edits together (the config/token layer).
2. Merge the two call-site edits (`FilterPanel.tsx`, `PatientSummary.tsx`).
3. Run `npm run lint` and `npx tsc --noEmit` to confirm type and lint correctness.
4. Spot-check in dev server: light mode and dark mode, with at least one patient loaded.

**Rollback:** Revert the commits. No persistent state is affected.

## Open Questions

None.
