import { useMemo, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { ModuleId, Patient } from '@/types/medical';
import { MODULE_DATE_FIELD, getRecordDate } from '@/utils/moduleDate';
import {
  extractNumericField,
  filterByDateRange,
  filterByValueRange,
  formatCell,
  summarize,
} from '@/utils/statsUtils';
import {
  ModuleFieldPicker,
  ModuleFieldValue,
} from '@/components/stats/ModuleFieldPicker';
import { StatsSparkline } from '@/components/stats/StatsSparkline';

interface StatsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient: Patient;
}

export function StatsDialog({ open, onOpenChange, patient }: StatsDialogProps) {
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

  const records = useMemo<Record<string, unknown>[]>(() => {
    if (!moduleId) return [];
    const arr = (patient as unknown as Record<string, unknown>)[moduleId];
    return Array.isArray(arr) ? (arr as Record<string, unknown>[]) : [];
  }, [moduleId, patient]);

  const filtered = useMemo(() => {
    if (!moduleId || !picker.fieldId) return [];
    let xs = records.slice();
    if (dateField) {
      xs = filterByDateRange(
        xs,
        (r) => getRecordDate(moduleId, r),
        dateMin || undefined,
        dateMax || undefined,
      );
    }
    const minNum = valueMin === '' ? undefined : Number(valueMin);
    const maxNum = valueMax === '' ? undefined : Number(valueMax);
    xs = filterByValueRange(
      xs,
      (r) => {
        const v = (r as Record<string, unknown>)[picker.fieldId];
        return typeof v === 'number' ? v : null;
      },
      Number.isFinite(minNum) ? minNum : undefined,
      Number.isFinite(maxNum) ? maxNum : undefined,
    );
    return xs;
  }, [
    records,
    moduleId,
    picker.fieldId,
    dateField,
    dateMin,
    dateMax,
    valueMin,
    valueMax,
  ]);

  const values = useMemo(
    () => extractNumericField(filtered, picker.fieldId),
    [filtered, picker.fieldId],
  );

  const stats = useMemo(() => summarize(values), [values]);

  const sparklineData = useMemo(() => {
    if (!moduleId || !dateField) return [];
    return filtered
      .map((r) => {
        const date = getRecordDate(moduleId, r);
        const raw = (r as Record<string, unknown>)[picker.fieldId];
        const value = typeof raw === 'number' ? raw : NaN;
        if (!date || !Number.isFinite(value)) return null;
        return { date, value };
      })
      .filter((p): p is { date: string; value: number } => p !== null);
  }, [filtered, moduleId, dateField, picker.fieldId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>單病人統計 — {patient.name}</DialogTitle>
        </DialogHeader>

        <ModuleFieldPicker
          value={picker}
          onChange={setPicker}
          patient={patient}
        />

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

        <div className="rounded-md border border-border p-3">
          <div className="mb-1 text-xs font-medium text-muted-foreground">
            統計輸出
          </div>
          {(() => {
            if (!moduleId || !picker.fieldId) {
              return (
                <p className="text-sm text-muted-foreground">
                  請選擇模組與欄位
                </p>
              );
            }
            if (stats.n === 0) {
              return (
                <p className="text-sm text-muted-foreground">無資料符合條件</p>
              );
            }
            return (
              <div className="grid grid-cols-5 gap-2 text-sm">
                <div>
                  <div className="text-[10px] text-muted-foreground">n</div>
                  <div className="font-medium">{stats.n}</div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">mean</div>
                  <div className="font-medium">
                    {stats.mean !== null ? stats.mean.toFixed(2) : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">sd</div>
                  <div className="font-medium">
                    {stats.sd !== null ? stats.sd.toFixed(2) : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">min</div>
                  <div className="font-medium">
                    {stats.min !== null ? stats.min.toFixed(2) : '—'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] text-muted-foreground">max</div>
                  <div className="font-medium">
                    {stats.max !== null ? stats.max.toFixed(2) : '—'}
                  </div>
                </div>
              </div>
            );
          })()}
          <div className="mt-2 text-[11px] text-muted-foreground">
            {stats.n >= 2 && formatCell(stats)}
          </div>
        </div>

        {dateField && stats.n >= 2 && (
          <div>
            <div className="mb-1 text-xs font-medium text-muted-foreground">
              時序
            </div>
            <StatsSparkline data={sparklineData} />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
