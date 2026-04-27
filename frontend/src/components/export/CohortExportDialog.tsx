import { useActionState, useEffect, useMemo, useState } from 'react';
import { useFormStatus } from 'react-dom';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { MODULE_DEFINITIONS, ModuleId, Patient } from '@/types/medical';
import { exportPatients } from '@/utils/exporters';
import { todayStamp } from '@/utils/dateStamp';

interface CohortExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patients: Patient[];
}

const EXPORTABLE_MODULES: ModuleId[] = MODULE_DEFINITIONS.map(
  (m) => m.id,
).filter((id) => id !== 'basic');

function cohortRecordCount(patients: Patient[], moduleId: ModuleId): number {
  return patients.reduce((total, patient) => {
    const arr = (patient as unknown as Record<string, unknown>)[moduleId];
    return total + (Array.isArray(arr) ? arr.length : 0);
  }, 0);
}

function defaultSelectedModules(patients: Patient[]): ModuleId[] {
  return EXPORTABLE_MODULES.filter((id) => cohortRecordCount(patients, id) > 0);
}

function defaultPrefix(): string {
  return `cohort_${todayStamp()}`;
}

function CancelButton({ onCancel }: { onCancel: () => void }) {
  const { pending } = useFormStatus();
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onCancel}
      disabled={pending}
    >
      取消
    </Button>
  );
}

function SubmitButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={disabled || pending}>
      {pending ? '處理中…' : '匯出'}
    </Button>
  );
}

export function CohortExportDialog({
  open,
  onOpenChange,
  patients,
}: CohortExportDialogProps) {
  const [selected, setSelected] = useState<Set<ModuleId>>(
    () => new Set(defaultSelectedModules(patients)),
  );
  const [prefix, setPrefix] = useState(() => defaultPrefix());

  const [, submitAction] = useActionState(async () => {
    try {
      await exportPatients(patients, {
        format: 'xlsx',
        modules: EXPORTABLE_MODULES.filter((id) => selected.has(id)),
        filenamePrefix: prefix.trim(),
      });
      onOpenChange(false);
      return null;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '匯出失敗，請稍後再試';
      toast.error(`匯出失敗：${message}`);
      return message;
    }
  }, null);

  useEffect(() => {
    if (open) {
      setSelected(new Set(defaultSelectedModules(patients)));
      setPrefix(defaultPrefix());
    }
  }, [open, patients]);

  const counts = useMemo(() => {
    const map = new Map<ModuleId, number>();
    EXPORTABLE_MODULES.forEach((id) => {
      map.set(id, cohortRecordCount(patients, id));
    });
    return map;
  }, [patients]);

  const allChecked = useMemo(
    () => EXPORTABLE_MODULES.every((id) => selected.has(id)),
    [selected],
  );

  const toggleAll = () => {
    if (allChecked) {
      setSelected(new Set());
    } else {
      setSelected(new Set(EXPORTABLE_MODULES));
    }
  };

  const toggleOne = (id: ModuleId) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const canConfirm = selected.size > 0 && prefix.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <form action={submitAction}>
          <DialogHeader>
            <DialogTitle>匯出比較報告 — {patients.length} 位病人</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between">
                <Label className="text-xs font-medium text-muted-foreground">
                  模組
                </Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-[10px]"
                  onClick={toggleAll}
                >
                  {allChecked ? '全不選' : '全選'}
                </Button>
              </div>
              <div className="grid max-h-60 grid-cols-2 gap-1 overflow-y-auto rounded-md border border-border p-2">
                {EXPORTABLE_MODULES.map((id) => {
                  const def = MODULE_DEFINITIONS.find((m) => m.id === id);
                  const count = counts.get(id) ?? 0;
                  const checkboxId = `cohort-export-module-${id}`;
                  return (
                    <div
                      key={id}
                      className="flex items-center gap-2 rounded px-1 py-1 text-xs hover:bg-accent/40"
                    >
                      <Checkbox
                        id={checkboxId}
                        checked={selected.has(id)}
                        onCheckedChange={() => toggleOne(id)}
                      />
                      <Label
                        htmlFor={checkboxId}
                        className="flex-1 cursor-pointer text-xs font-normal"
                      >
                        {def?.code ?? id}{' '}
                        <span className="text-muted-foreground">({count})</span>
                      </Label>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <Label
                htmlFor="cohort-export-filename"
                className="mb-1 block text-xs font-medium text-muted-foreground"
              >
                檔名前綴
              </Label>
              <Input
                id="cohort-export-filename"
                value={prefix}
                onChange={(e) => setPrefix(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <CancelButton onCancel={() => onOpenChange(false)} />
            <SubmitButton disabled={!canConfirm} />
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
