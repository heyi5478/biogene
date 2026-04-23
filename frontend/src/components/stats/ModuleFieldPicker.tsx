import { useMemo } from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MODULE_DEFINITIONS, ModuleId, Patient } from '@/types/medical';
import { numericFieldsFor } from '@/utils/numericFields';

export interface ModuleFieldValue {
  moduleId: ModuleId | '';
  fieldId: string;
}

interface ModuleFieldPickerProps {
  value: ModuleFieldValue;
  onChange: (next: ModuleFieldValue) => void;
  patient?: Patient;
  availableModules?: ModuleId[];
  disabled?: boolean;
}

export function ModuleFieldPicker({
  value,
  onChange,
  patient,
  availableModules,
  disabled,
}: ModuleFieldPickerProps) {
  const moduleOptions = useMemo(() => {
    const baseIds: ModuleId[] =
      availableModules ?? MODULE_DEFINITIONS.map((m) => m.id);

    return MODULE_DEFINITIONS.filter((mod) => baseIds.includes(mod.id))
      .filter((mod) => numericFieldsFor(mod.id).length > 0)
      .filter((mod) => {
        if (!patient) return true;
        const arr = (patient as unknown as Record<string, unknown>)[mod.id];
        return Array.isArray(arr) && arr.length > 0;
      });
  }, [availableModules, patient]);

  const fieldOptions = useMemo(() => {
    if (!value.moduleId) return [];
    return numericFieldsFor(value.moduleId);
  }, [value.moduleId]);

  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <div className="mb-1 text-xs font-medium text-muted-foreground">
          模組
        </div>
        <Select
          value={value.moduleId || undefined}
          onValueChange={(v) =>
            onChange({ moduleId: v as ModuleId, fieldId: '' })
          }
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue placeholder="選擇模組" />
          </SelectTrigger>
          <SelectContent>
            {moduleOptions.map((mod) => (
              <SelectItem key={mod.id} value={mod.id}>
                {mod.code} · {mod.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div>
        <div className="mb-1 text-xs font-medium text-muted-foreground">
          數值欄位
        </div>
        <Select
          value={value.fieldId || undefined}
          onValueChange={(v) =>
            onChange({ moduleId: value.moduleId, fieldId: v })
          }
          disabled={disabled || !value.moduleId}
        >
          <SelectTrigger>
            <SelectValue placeholder="選擇欄位" />
          </SelectTrigger>
          <SelectContent>
            {fieldOptions.map((f) => (
              <SelectItem key={f.id} value={f.id}>
                {f.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
