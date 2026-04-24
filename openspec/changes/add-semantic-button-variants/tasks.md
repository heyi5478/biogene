## 1. Token layer

- [x] 1.1 In `frontend/src/index.css`, change `--info` in `:root` from `205 75% 42%` to `190 70% 40%`
- [x] 1.2 In `frontend/src/index.css`, change `--info` in `.dark` from `205 70% 50%` to `190 65% 48%`
- [x] 1.3 In `frontend/tailwind.config.ts`, add `warning`, `success`, `info` entries (each with `DEFAULT` + `foreground`) to `theme.extend.colors`, placed after `destructive` to match existing ordering
- [x] 1.4 In `frontend/src/index.css`, add `--danger` / `--danger-foreground` to both `:root` (`20 90% 50%` / `0 0% 100%`) and `.dark` (`20 85% 55%` / `0 0% 100%`), using a red-orange hue distinct from `--destructive`
- [x] 1.5 In `frontend/tailwind.config.ts`, add a `danger` entry (`DEFAULT` + `foreground`) to `theme.extend.colors`, placed after `warning`

## 2. Button component

- [x] 2.1 In `frontend/src/components/ui/button.tsx`, append three new variants (`warning`, `success`, `info`) to the CVA `variants.variant` map, each using `bg-<token> text-<token>-foreground hover:bg-<token>/90` following the pattern of `default` / `destructive`
- [x] 2.2 Verify the `buttonVariants` export still type-checks (`VariantProps<typeof buttonVariants>` should automatically include the new variants — no manual type edits needed)
- [x] 2.3 In `frontend/src/components/ui/button.tsx`, append a fourth variant `danger` (`bg-danger text-danger-foreground hover:bg-danger/90`) after `warning`

## 3. Call-site updates

- [x] 3.1 In `frontend/src/components/FilterPanel.tsx` (the footer button rendering 「清除全部條件」, around line 366-373), change `variant="outline"` to `variant="destructive"`
- [x] 3.2 In `frontend/src/components/PatientSummary.tsx` (the 「統計」 button, around line 145-153), change `variant="outline"` to `variant="success"`
- [x] 3.3 In `frontend/src/components/PatientSummary.tsx` (the 「匯出」 button, around line 154-162), change `variant="outline"` to `variant="info"`
- [x] 3.4 Confirm no other `<Button variant="outline">` usages in the same files were changed (jump-links and other neutral actions must stay `outline`)
- [x] 3.5 In `frontend/src/components/ConditionBuilder.tsx` (the footer 「清除全部條件」 button, around line 341-348), change `variant="outline"` to `variant="destructive"`

## 4. Verification

- [x] 4.1 Run `npx tsc --noEmit` from `frontend/` to confirm types still compile
- [x] 4.2 Run `npm run lint` from `frontend/` with no new warnings or errors
- [x] 4.3 Run `npm run dev` and visually verify in the browser:
  - [x] 4.3.1 Sidebar footer「清除全部條件」renders as red filled button (destructive)
  - [x] 4.3.2 PatientSummary「統計」renders as green filled button
  - [x] 4.3.3 PatientSummary「匯出」renders as cyan filled button (distinctly different from any blue primary element nearby)
  - [x] 4.3.4 PatientSummary jump-links (門診 / MS/MS / AA / Enzyme / GAG / DNA / 外送) still render as outline (unchanged)
  - [x] 4.3.5 Toggle dark mode (if available in the UI) and confirm all buttons still have adequate contrast and legible text
- [x] 4.4 If the project has visual regression or unit tests covering these components, run them and resolve any snapshot diffs that reflect the intended variant change
- [x] 4.5 Run `openspec validate add-semantic-button-variants --strict` and fix any reported issues
