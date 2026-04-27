export function uniqueSheetName(base: string, used: Set<string>): string {
  const trimmed = base.slice(0, 31);
  if (!used.has(trimmed)) {
    used.add(trimmed);
    return trimmed;
  }
  let i = 2;
  // bounded by reasonable module count; loop guard with explicit cap
  while (i < 1000) {
    const suffix = `_${i}`;
    const candidate = base.slice(0, 31 - suffix.length) + suffix;
    if (!used.has(candidate)) {
      used.add(candidate);
      return candidate;
    }
    i += 1;
  }
  throw new Error('Could not derive unique sheet name');
}
