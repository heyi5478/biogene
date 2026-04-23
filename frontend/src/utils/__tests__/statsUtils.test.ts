import { describe, expect, it } from 'vitest';
import {
  ageInYears,
  bucketAge,
  extractNumericField,
  filterByDateRange,
  filterByValueRange,
  formatCell,
  mean,
  stddev,
  summarize,
} from '@/utils/statsUtils';

describe('mean / stddev', () => {
  it('returns null for empty', () => {
    expect(mean([])).toBeNull();
    expect(stddev([])).toBeNull();
  });

  it('returns null for n<2 stddev', () => {
    expect(stddev([5])).toBeNull();
  });

  it('uses n-1 sample sd', () => {
    // [12,14,16] -> mean 14, deviations 2,0,2 squared = 8, /(3-1) = 4 -> sd 2
    expect(stddev([12, 14, 16])).toBe(2);
  });
});

describe('summarize', () => {
  it('handles three-value input', () => {
    expect(summarize([12, 14, 16])).toEqual({
      n: 3,
      mean: 14,
      sd: 2,
      min: 12,
      max: 16,
    });
  });

  it('handles empty input', () => {
    expect(summarize([])).toEqual({
      n: 0,
      mean: null,
      sd: null,
      min: null,
      max: null,
    });
  });

  it('handles single-value input (no SD)', () => {
    expect(summarize([42])).toEqual({
      n: 1,
      mean: 42,
      sd: null,
      min: 42,
      max: 42,
    });
  });
});

describe('ageInYears', () => {
  it('returns null for invalid birthday', () => {
    expect(ageInYears('not-a-date')).toBeNull();
  });

  it('computes age before birthday in year', () => {
    const asOf = new Date('2024-01-01');
    expect(ageInYears('2000-06-15', asOf)).toBe(23);
  });

  it('computes age after birthday in year', () => {
    const asOf = new Date('2024-12-31');
    expect(ageInYears('2000-01-01', asOf)).toBe(24);
  });
});

describe('bucketAge', () => {
  it('null in -> null out', () => {
    expect(bucketAge(null)).toBeNull();
  });

  it('boundaries are inclusive on upper edge', () => {
    expect(bucketAge(0)).toBe('0-17');
    expect(bucketAge(17)).toBe('0-17');
    expect(bucketAge(18)).toBe('18-39');
    expect(bucketAge(39)).toBe('18-39');
    expect(bucketAge(40)).toBe('40-59');
    expect(bucketAge(59)).toBe('40-59');
    expect(bucketAge(60)).toBe('60+');
    expect(bucketAge(100)).toBe('60+');
  });
});

describe('formatCell', () => {
  it('renders em-dash for n=0', () => {
    expect(
      formatCell({ n: 0, mean: null, sd: null, min: null, max: null }),
    ).toBe('—');
  });

  it('renders value(n=1) without ±', () => {
    const out = formatCell({ n: 1, mean: 42, sd: null, min: 42, max: 42 });
    expect(out).toContain('(n=1)');
    expect(out).toContain('42');
    expect(out).not.toContain('±');
  });

  it('renders mean ± sd (n=k) for n>=2', () => {
    const out = formatCell({ n: 3, mean: 14, sd: 2, min: 12, max: 16 });
    expect(out).toContain('±');
    expect(out).toContain('(n=3)');
  });
});

describe('filterByDateRange', () => {
  const recs = [
    { d: '2024-01-01' },
    { d: '2024-06-01' },
    { d: '2024-12-31' },
    { d: null as string | null },
  ];
  const getDate = (r: { d: string | null }) => r.d;

  it('returns all (including null) when no bounds', () => {
    expect(filterByDateRange(recs, getDate)).toHaveLength(4);
  });

  it('inclusive lower bound; drops null when bound provided', () => {
    expect(filterByDateRange(recs, getDate, '2024-06-01')).toEqual([
      { d: '2024-06-01' },
      { d: '2024-12-31' },
    ]);
  });

  it('inclusive upper bound', () => {
    expect(
      filterByDateRange(recs, getDate, '2024-01-01', '2024-06-01'),
    ).toEqual([{ d: '2024-01-01' }, { d: '2024-06-01' }]);
  });
});

describe('filterByValueRange', () => {
  const recs = [{ v: 1 }, { v: 5 }, { v: 10 }, { v: NaN }, { v: null }];
  const getVal = (r: { v: number | null }) => r.v;

  it('drops non-finite values', () => {
    expect(filterByValueRange(recs, getVal)).toEqual([
      { v: 1 },
      { v: 5 },
      { v: 10 },
    ]);
  });

  it('inclusive bounds', () => {
    expect(filterByValueRange(recs, getVal, 5, 10)).toEqual([
      { v: 5 },
      { v: 10 },
    ]);
  });
});

describe('extractNumericField', () => {
  it('drops undefined / null / NaN', () => {
    const recs = [
      { x: 1 },
      { x: 2 },
      { x: null },
      { x: undefined },
      { x: NaN },
      { x: 'str' as unknown as number },
    ];
    expect(extractNumericField(recs, 'x')).toEqual([1, 2]);
  });
});
