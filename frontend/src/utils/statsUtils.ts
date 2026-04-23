export type AgeBucket = '0-17' | '18-39' | '40-59' | '60+';

export const AGE_BUCKETS: AgeBucket[] = ['0-17', '18-39', '40-59', '60+'];

export interface SummaryStats {
  n: number;
  mean: number | null;
  sd: number | null;
  min: number | null;
  max: number | null;
}

export function mean(xs: number[]): number | null {
  if (xs.length === 0) return null;
  const sum = xs.reduce((acc, x) => acc + x, 0);
  return sum / xs.length;
}

export function stddev(xs: number[]): number | null {
  if (xs.length < 2) return null;
  const m = mean(xs) as number;
  const acc = xs.reduce((a, x) => a + (x - m) * (x - m), 0);
  return Math.sqrt(acc / (xs.length - 1));
}

export function summarize(xs: number[]): SummaryStats {
  if (xs.length === 0) {
    return { n: 0, mean: null, sd: null, min: null, max: null };
  }
  const min = xs.reduce((a, x) => (x < a ? x : a), xs[0]);
  const max = xs.reduce((a, x) => (x > a ? x : a), xs[0]);
  return {
    n: xs.length,
    mean: mean(xs),
    sd: stddev(xs),
    min,
    max,
  };
}

export function ageInYears(
  birthday: string,
  asOf: Date = new Date(),
): number | null {
  const birth = new Date(birthday);
  if (Number.isNaN(birth.getTime())) return null;
  if (Number.isNaN(asOf.getTime())) return null;
  let age = asOf.getFullYear() - birth.getFullYear();
  const m = asOf.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && asOf.getDate() < birth.getDate())) age -= 1;
  return age;
}

export function bucketAge(age: number | null): AgeBucket | null {
  if (age === null || Number.isNaN(age)) return null;
  if (age < 0) return null;
  if (age <= 17) return '0-17';
  if (age <= 39) return '18-39';
  if (age <= 59) return '40-59';
  return '60+';
}

export function filterByDateRange<T>(
  records: T[],
  getDate: (r: T) => string | null,
  min?: string,
  max?: string,
): T[] {
  if (!min && !max) return records.slice();
  return records.filter((r) => {
    const d = getDate(r);
    if (!d) return false;
    if (min && d < min) return false;
    if (max && d > max) return false;
    return true;
  });
}

export function filterByValueRange<T>(
  records: T[],
  getValue: (r: T) => number | null | undefined,
  min?: number,
  max?: number,
): T[] {
  return records.filter((r) => {
    const v = getValue(r);
    if (v === undefined || v === null || !Number.isFinite(v)) return false;
    if (min !== undefined && v < min) return false;
    if (max !== undefined && v > max) return false;
    return true;
  });
}

export function extractNumericField<T>(
  records: T[],
  fieldId: string,
): number[] {
  return records.reduce<number[]>((acc, rec) => {
    const v = (rec as Record<string, unknown>)[fieldId];
    if (typeof v === 'number' && Number.isFinite(v)) acc.push(v);
    return acc;
  }, []);
}

function fmt(value: number, digits: number): string {
  return value.toFixed(digits);
}

export function formatCell(s: SummaryStats, digits = 2): string {
  if (s.n === 0 || s.mean === null) return '—';
  if (s.n === 1 || s.sd === null) {
    return `${fmt(s.mean, digits)} (n=${s.n})`;
  }
  return `${fmt(s.mean, digits)} ± ${fmt(s.sd, digits)} (n=${s.n})`;
}
