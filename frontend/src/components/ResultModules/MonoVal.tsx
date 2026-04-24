export function MonoVal({ val }: { val: number | undefined }) {
  if (val === undefined || val === null)
    return <span className="text-muted-foreground">—</span>;
  return <span className="font-mono-medical">{val}</span>;
}
