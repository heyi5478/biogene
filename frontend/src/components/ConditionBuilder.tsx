import React from 'react';
import { Plus, Trash2, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  ConditionRow,
  ConditionLogic,
  ModuleId,
  MODULE_DEFINITIONS,
  MODULE_FIELDS,
  OPERATORS_BY_TYPE,
  FieldDefinition,
  CONDITION_TEMPLATES,
} from '@/types/medical';

interface ConditionBuilderProps {
  conditions: ConditionRow[];
  logic: ConditionLogic;
  onConditionsChange: (conditions: ConditionRow[]) => void;
  onLogicChange: (logic: ConditionLogic) => void;
  onSearch: () => void;
  onClear: () => void;
}

let conditionIdCounter = 0;
function newConditionId() {
  conditionIdCounter += 1;
  return `cond-${conditionIdCounter}`;
}

function inputTypeFor(fieldType: FieldDefinition['type']) {
  if (fieldType === 'number') return 'number';
  if (fieldType === 'date') return 'date';
  return 'text';
}

export function ConditionBuilder({
  conditions,
  logic,
  onConditionsChange,
  onLogicChange,
  onSearch,
  onClear,
}: ConditionBuilderProps) {
  const updateRow = (id: string, patch: Partial<ConditionRow>) => {
    onConditionsChange(
      conditions.map((c) => (c.id === id ? { ...c, ...patch } : c)),
    );
  };

  const addRow = () => {
    onConditionsChange([
      ...conditions,
      {
        id: newConditionId(),
        moduleId: '',
        fieldId: '',
        operator: 'eq',
        value: '',
        value2: '',
      },
    ]);
  };

  const removeRow = (id: string) => {
    onConditionsChange(conditions.filter((c) => c.id !== id));
  };

  const applyTemplate = (template: (typeof CONDITION_TEMPLATES)[0]) => {
    onConditionsChange(
      template.conditions.map((c) => ({ ...c, id: newConditionId() })),
    );
    onLogicChange(template.logic);
  };

  const getFieldDef = (
    moduleId: ModuleId | '',
    fieldId: string,
  ): FieldDefinition | undefined => {
    if (!moduleId) return undefined;
    return MODULE_FIELDS[moduleId as ModuleId]?.find((f) => f.id === fieldId);
  };

  return (
    <div className="space-y-4">
      {/* Templates */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">常用條件模板</Label>
        <div className="space-y-1">
          {CONDITION_TEMPLATES.map((t) => (
            <button
              key={t.id}
              onClick={() => applyTemplate(t)}
              className="flex w-full items-start gap-2 rounded-md border border-border px-2.5 py-2 text-left text-xs transition-colors hover:bg-accent/50"
            >
              <Zap className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
              <div className="min-w-0">
                <div className="font-medium">{t.name}</div>
                <div className="mt-0.5 text-[10px] text-muted-foreground">
                  {t.description}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Logic toggle */}
      <div className="space-y-2">
        <Label className="text-xs text-muted-foreground">條件邏輯</Label>
        <div className="flex gap-1">
          <button
            onClick={() => onLogicChange('AND')}
            className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
              logic === 'AND'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-accent'
            }`}
          >
            AND（全部符合）
          </button>
          <button
            onClick={() => onLogicChange('OR')}
            className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
              logic === 'OR'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-accent'
            }`}
          >
            OR（任一符合）
          </button>
        </div>
      </div>

      {/* Condition rows */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label className="text-xs text-muted-foreground">查詢條件</Label>
          <Badge variant="outline" className="h-4 text-[10px]">
            {conditions.length} 條
          </Badge>
        </div>

        <div className="space-y-2">
          {conditions.map((row, idx) => {
            const fields = row.moduleId
              ? MODULE_FIELDS[row.moduleId as ModuleId] || []
              : [];
            const fieldDef = getFieldDef(row.moduleId, row.fieldId);
            const operators = fieldDef ? OPERATORS_BY_TYPE[fieldDef.type] : [];
            const currentOp = operators.find((o) => o.id === row.operator);

            return (
              <div
                key={row.id}
                className="space-y-1.5 rounded-md border border-border bg-background p-2.5"
              >
                {idx > 0 && (
                  <div className="-mt-1 mb-1 text-center text-[10px] font-medium text-muted-foreground">
                    {logic}
                  </div>
                )}

                {/* Module select */}
                <Select
                  value={row.moduleId}
                  onValueChange={(v) =>
                    updateRow(row.id, {
                      moduleId: v as ModuleId,
                      fieldId: '',
                      operator: 'eq',
                      value: '',
                      value2: '',
                    })
                  }
                >
                  <SelectTrigger className="h-7 text-xs">
                    <SelectValue placeholder="選擇模組" />
                  </SelectTrigger>
                  <SelectContent>
                    {MODULE_DEFINITIONS.map((m) => (
                      <SelectItem key={m.id} value={m.id} className="text-xs">
                        {m.code} — {m.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Field select */}
                {row.moduleId && (
                  <Select
                    value={row.fieldId}
                    onValueChange={(v) => {
                      const fd = fields.find((f) => f.id === v);
                      const defaultOp = fd
                        ? OPERATORS_BY_TYPE[fd.type][0]?.id || 'eq'
                        : 'eq';
                      updateRow(row.id, {
                        fieldId: v,
                        operator: defaultOp,
                        value: '',
                        value2: '',
                      });
                    }}
                  >
                    <SelectTrigger className="h-7 text-xs">
                      <SelectValue placeholder="選擇欄位" />
                    </SelectTrigger>
                    <SelectContent>
                      {fields.map((f) => (
                        <SelectItem key={f.id} value={f.id} className="text-xs">
                          {f.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}

                {/* Operator + value */}
                {fieldDef && (
                  <div className="flex gap-1.5">
                    <Select
                      value={row.operator}
                      onValueChange={(v) =>
                        updateRow(row.id, { operator: v as any })
                      }
                    >
                      <SelectTrigger className="h-7 w-[90px] shrink-0 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {operators.map((op) => (
                          <SelectItem
                            key={op.id}
                            value={op.id}
                            className="text-xs"
                          >
                            {op.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>

                    {currentOp &&
                      currentOp.valueCount >= 1 &&
                      (fieldDef.type === 'category' && fieldDef.options ? (
                        <Select
                          value={row.value}
                          onValueChange={(v) => updateRow(row.id, { value: v })}
                        >
                          <SelectTrigger className="h-7 flex-1 text-xs">
                            <SelectValue placeholder="選擇..." />
                          </SelectTrigger>
                          <SelectContent>
                            {fieldDef.options.map((opt) => (
                              <SelectItem
                                key={opt}
                                value={opt}
                                className="text-xs"
                              >
                                {opt}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          type={inputTypeFor(fieldDef.type)}
                          value={row.value}
                          onChange={(e) =>
                            updateRow(row.id, { value: e.target.value })
                          }
                          placeholder="值"
                          className="h-7 flex-1 text-xs"
                        />
                      ))}

                    {currentOp && currentOp.valueCount === 2 && (
                      <>
                        <span className="self-center text-xs text-muted-foreground">
                          ~
                        </span>
                        <Input
                          type={fieldDef.type === 'number' ? 'number' : 'date'}
                          value={row.value2}
                          onChange={(e) =>
                            updateRow(row.id, { value2: e.target.value })
                          }
                          placeholder="值2"
                          className="h-7 flex-1 text-xs"
                        />
                      </>
                    )}
                  </div>
                )}

                {/* Delete */}
                <div className="flex justify-end">
                  <button
                    onClick={() => removeRow(row.id)}
                    className="p-0.5 text-muted-foreground transition-colors hover:text-destructive"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={addRow}
          className="h-7 w-full text-xs"
        >
          <Plus className="mr-1 h-3.5 w-3.5" />
          新增條件
        </Button>
      </div>

      {/* Search button */}
      <div className="space-y-1.5">
        <Button
          onClick={onSearch}
          size="sm"
          className="h-8 w-full text-xs"
          disabled={conditions.length === 0}
        >
          執行條件查詢
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={onClear}
          className="h-7 w-full text-xs"
        >
          清除全部條件
        </Button>
      </div>
    </div>
  );
}
