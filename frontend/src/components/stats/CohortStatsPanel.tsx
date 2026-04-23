import { useMemo, useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { ModuleId, Patient } from '@/types/medical';
import { MODULE_DATE_FIELD, getRecordDate } from '@/utils/moduleDate';
import {
  AGE_BUCKETS,
  AgeBucket,
  ageInYears,
  bucketAge,
  formatCell,
  summarize,
} from '@/utils/statsUtils';
import {
  ModuleFieldPicker,
  ModuleFieldValue,
} from '@/components/stats/ModuleFieldPicker';

interface CohortStatsPanelProps {
  patients: Patient[];
}

type SexKey = '男' | '女';
const SEX_KEYS: SexKey[] = ['男', '女'];

type RowKey = AgeBucket | '全部年齡';
type ColKey = SexKey | '全部性別';

const ROW_KEYS: RowKey[] = [...AGE_BUCKETS, '全部年齡'];
const COL_KEYS: ColKey[] = [...SEX_KEYS, '全部性別'];

interface DataPoint {
  bucket: AgeBucket;
  sex: SexKey;
  value: number;
}

const cellKey = (r: RowKey, c: ColKey) => `${r}|${c}`;

function inDateRange(
  dateStr: string | null,
  hasDateField: boolean,
  min: string,
  max: string,
): boolean {
  if (!hasDateField) return true;
  if (min && (!dateStr || dateStr < min)) return false;
  if (max && (!dateStr || dateStr > max)) return false;
  return true;
}

function inValueRange(value: number, min: number | null, max: number | null) {
  if (min !== null && Number.isFinite(min) && value < min) return false;
  if (max !== null && Number.isFinite(max) && value > max) return false;
  return true;
}

export function CohortStatsPanel({ patients }: CohortStatsPanelProps) {
  const [picker, setPicker] = useState<ModuleFieldValue>({
    moduleId: '',
    fieldId: '',
  });
  const [dateMin, setDateMin] = useState('');
  const [dateMax, setDateMax] = useState('');
  const [valueMin, setValueMin] = useState('');
  const [valueMax, setValueMax] = useState('');

  const moduleId = picker.moduleId as ModuleId | '';
  const dateField = moduleId ? MODULE_DATE_FIELD[moduleId] : null;
  const isDateless = !!moduleId && dateField === null;

  const buckets = useMemo(() => {
    const map = new Map<string, number[]>();
    ROW_KEYS.forEach((r) => {
      COL_KEYS.forEach((c) => {
        map.set(cellKey(r, c), []);
      });
    });

    if (!moduleId || !picker.fieldId) return map;

    const minNum = valueMin === '' ? null : Number(valueMin);
    const maxNum = valueMax === '' ? null : Number(valueMax);
    const hasDateField = dateField !== null;

    const points: DataPoint[] = patients.flatMap((patient) => {
      const { sex } = patient;
      if (sex !== '男' && sex !== '女') return [];
      const arr = (patient as unknown as Record<string, unknown>)[moduleId];
      if (!Array.isArray(arr)) return [];

      return (arr as Record<string, unknown>[]).flatMap((rec) => {
        const dateStr = getRecordDate(moduleId, rec);
        if (!inDateRange(dateStr, hasDateField, dateMin, dateMax)) return [];

        const raw = rec[picker.fieldId];
        if (typeof raw !== 'number' || !Number.isFinite(raw)) return [];
        if (!inValueRange(raw, minNum, maxNum)) return [];

        const asOf = dateStr ? new Date(dateStr) : new Date();
        const age = ageInYears(patient.birthday, asOf);
        const bucket = bucketAge(age);
        if (!bucket) return [];

        return [{ bucket, sex, value: raw }];
      });
    });

    points.forEach(({ bucket, sex, value }) => {
      map.get(cellKey(bucket, sex))!.push(value);
      map.get(cellKey(bucket, '全部性別'))!.push(value);
      map.get(cellKey('全部年齡', sex))!.push(value);
      map.get(cellKey('全部年齡', '全部性別'))!.push(value);
    });

    return map;
  }, [
    patients,
    moduleId,
    picker.fieldId,
    dateField,
    dateMin,
    dateMax,
    valueMin,
    valueMax,
  ]);

  return (
    <div className="space-y-4">
      <ModuleFieldPicker value={picker} onChange={setPicker} />

      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="mb-1 text-xs font-medium text-muted-foreground">
            日期區間
          </div>
          <div className="flex gap-2">
            <Input
              type="date"
              value={dateMin}
              onChange={(e) => setDateMin(e.target.value)}
              disabled={isDateless || !moduleId}
            />
            <Input
              type="date"
              value={dateMax}
              onChange={(e) => setDateMax(e.target.value)}
              disabled={isDateless || !moduleId}
            />
          </div>
          {isDateless && (
            <p className="mt-1 text-[10px] text-muted-foreground">
              此模組資料無採檢日期欄位
            </p>
          )}
        </div>
        <div>
          <div className="mb-1 text-xs font-medium text-muted-foreground">
            數值區間
          </div>
          <div className="flex gap-2">
            <Input
              type="number"
              value={valueMin}
              onChange={(e) => setValueMin(e.target.value)}
              placeholder="min"
              disabled={!moduleId}
            />
            <Input
              type="number"
              value={valueMax}
              onChange={(e) => setValueMax(e.target.value)}
              placeholder="max"
              disabled={!moduleId}
            />
          </div>
        </div>
      </div>

      <div className="text-xs text-muted-foreground">
        共 {patients.length} 位病人
      </div>

      <div className="overflow-hidden rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="h-8 w-[100px] text-xs">
                年齡 \ 性別
              </TableHead>
              {COL_KEYS.map((c) => (
                <TableHead key={c} className="h-8 text-xs">
                  {c}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {ROW_KEYS.map((r) => (
              <TableRow key={r}>
                <TableCell className="text-xs font-medium">{r}</TableCell>
                {COL_KEYS.map((c) => {
                  const xs = buckets.get(cellKey(r, c)) ?? [];
                  return (
                    <TableCell key={c} className="text-xs">
                      {formatCell(summarize(xs))}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <p className="text-[10px] text-muted-foreground">
        年齡以該筆紀錄的日期減去病人生日為準；若該模組無紀錄日期則以今日為準
      </p>
    </div>
  );
}
