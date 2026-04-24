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
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { MODULE_DEFINITIONS, ModuleId, Patient } from '@/types/medical';
import { ExportFormat, exportPatient } from '@/utils/exporters';

interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  patient: Patient;
}

const EXPORTABLE_MODULES: ModuleId[] = MODULE_DEFINITIONS.map(
  (m) => m.id,
).filter((id) => id !== 'basic');

function todayStamp(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}${m}${day}`;
}

function defaultPrefix(patient: Patient): string {
  const ident =
    patient.chartno ||
    patient.externalChartno ||
    patient.nbsId ||
    patient.patientId;
  return `${ident}_${todayStamp()}`;
}

function defaultSelectedModules(patient: Patient): ModuleId[] {
  return EXPORTABLE_MODULES.filter((id) => {
    const arr = (patient as unknown as Record<string, unknown>)[id];
    return Array.isArray(arr) && arr.length > 0;
  });
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

export function ExportDialog({
  open,
  onOpenChange,
  patient,
}: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>('csv');
  const [selected, setSelected] = useState<Set<ModuleId>>(
    () => new Set(defaultSelectedModules(patient)),
  );
  const [prefix, setPrefix] = useState(() => defaultPrefix(patient));

  const [, submitAction] = useActionState(async () => {
    try {
      await exportPatient(patient, {
        format,
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
      setSelected(new Set(defaultSelectedModules(patient)));
      setPrefix(defaultPrefix(patient));
      setFormat('csv');
    }
  }, [open, patient]);

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
            <DialogTitle>匯出 — {patient.name}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label className="mb-2 block text-xs font-medium text-muted-foreground">
                格式
              </Label>
              <RadioGroup
                value={format}
                onValueChange={(v) => setFormat(v as ExportFormat)}
                className="flex gap-4"
              >
                <div className="flex items-center gap-2 text-sm">
                  <RadioGroupItem id="export-format-csv" value="csv" />
                  <Label htmlFor="export-format-csv" className="text-sm">
                    CSV (zip)
                  </Label>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <RadioGroupItem id="export-format-json" value="json" />
                  <Label htmlFor="export-format-json" className="text-sm">
                    JSON
                  </Label>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <RadioGroupItem id="export-format-xlsx" value="xlsx" />
                  <Label htmlFor="export-format-xlsx" className="text-sm">
                    XLSX
                  </Label>
                </div>
              </RadioGroup>
            </div>

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
                  const arr = (patient as unknown as Record<string, unknown>)[
                    id
                  ];
                  const count = Array.isArray(arr) ? arr.length : 0;
                  const checkboxId = `export-module-${id}`;
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
                htmlFor="export-filename"
                className="mb-1 block text-xs font-medium text-muted-foreground"
              >
                檔名前綴
              </Label>
              <Input
                id="export-filename"
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
