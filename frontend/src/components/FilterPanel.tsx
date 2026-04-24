import React, { useState } from 'react';
import {
  Search,
  X,
  User,
  FlaskConical,
  Microscope,
  TestTube,
  ChevronDown,
  Filter,
} from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ModuleId,
  MODULE_DEFINITIONS,
  PRESETS,
  ConditionRow,
  ConditionLogic,
} from '@/types/medical';
import { ConditionBuilder } from '@/components/ConditionBuilder';

const presetIcons = {
  user: User,
  flask: FlaskConical,
  microscope: Microscope,
  tube: TestTube,
};

const groupLabels: Record<string, string> = {
  patient: 'A. 病人資料',
  disease: 'B. 疾病 / 專案模組',
  lab: 'C. 檢驗模組',
  specimen: 'D. 檢體 / 樣本管理',
};

const groupColors: Record<string, string> = {
  patient: 'bg-primary/10 text-primary',
  disease: 'bg-purple-100 text-purple-700',
  lab: 'bg-emerald-100 text-emerald-700',
  specimen: 'bg-amber-100 text-amber-700',
};

export type QueryMode = 'patient' | 'condition';

interface FilterPanelProps {
  queryMode: QueryMode;
  onQueryModeChange: (mode: QueryMode) => void;
  // Patient mode
  searchQuery: string;
  onSearchQueryChange: (q: string) => void;
  onSearch: () => void;
  selectedModules: ModuleId[];
  onModulesChange: (modules: ModuleId[]) => void;
  onClearAll: () => void;
  // Condition mode
  conditions: ConditionRow[];
  conditionLogic: ConditionLogic;
  onConditionsChange: (conditions: ConditionRow[]) => void;
  onConditionLogicChange: (logic: ConditionLogic) => void;
  onConditionSearch: () => void;
  onConditionClear: () => void;
}

export function FilterPanel({
  queryMode,
  onQueryModeChange,
  searchQuery,
  onSearchQueryChange,
  onSearch,
  selectedModules,
  onModulesChange,
  onClearAll,
  conditions,
  conditionLogic,
  onConditionsChange,
  onConditionLogicChange,
  onConditionSearch,
  onConditionClear,
}: FilterPanelProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const toggleModule = (id: ModuleId) => {
    if (selectedModules.includes(id)) {
      onModulesChange(selectedModules.filter((m) => m !== id));
    } else {
      onModulesChange([...selectedModules, id]);
    }
  };

  const applyPreset = (modules: ModuleId[]) => {
    onModulesChange(modules);
  };

  const groups = ['patient', 'disease', 'lab', 'specimen'] as const;

  return (
    <aside className="flex h-full w-[300px] min-w-[300px] flex-col overflow-hidden border-r border-border bg-card">
      {/* Header with mode toggle */}
      <div className="space-y-2 border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-foreground">篩選條件</h2>
        <div className="flex overflow-hidden rounded-md border border-border">
          <button
            onClick={() => onQueryModeChange('patient')}
            className={`flex-1 py-1.5 text-xs font-medium transition-colors ${
              queryMode === 'patient'
                ? 'bg-primary text-primary-foreground'
                : 'bg-card text-muted-foreground hover:bg-accent'
            }`}
          >
            病人查詢
          </button>
          <button
            onClick={() => onQueryModeChange('condition')}
            className={`flex-1 py-1.5 text-xs font-medium transition-colors ${
              queryMode === 'condition'
                ? 'bg-primary text-primary-foreground'
                : 'bg-card text-muted-foreground hover:bg-accent'
            }`}
          >
            條件查詢
          </button>
        </div>
      </div>

      <div className="thin-scrollbar flex-1 space-y-4 overflow-y-auto px-4 py-3">
        {queryMode === 'patient' ? (
          <>
            {/* Search */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">病人搜尋</Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="輸入病人姓名或病歷號"
                  value={searchQuery}
                  onChange={(e) => onSearchQueryChange(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && onSearch()}
                  className="h-9 pl-9 pr-8 text-sm"
                />
                {searchQuery && (
                  <button
                    onClick={() => {
                      onSearchQueryChange('');
                    }}
                    className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <Button
                onClick={onSearch}
                size="sm"
                className="h-8 w-full text-xs"
              >
                <Search className="mr-1 h-3.5 w-3.5" />
                搜尋
              </Button>
            </div>

            {/* Presets */}
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">快捷查詢</Label>
              <div className="grid grid-cols-2 gap-1.5">
                {PRESETS.map((preset) => {
                  const Icon =
                    presetIcons[preset.icon as keyof typeof presetIcons] ||
                    User;
                  const isActive =
                    preset.modules.every((m) => selectedModules.includes(m)) &&
                    preset.modules.length > 0;
                  return (
                    <button
                      key={preset.id}
                      onClick={() => applyPreset(preset.modules)}
                      className={`flex items-center gap-1.5 rounded-md border px-2.5 py-2 text-xs font-medium transition-colors ${
                        isActive
                          ? 'border-primary bg-primary text-primary-foreground'
                          : 'border-border bg-card text-foreground hover:bg-accent'
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">{preset.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Module Checkboxes */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label className="text-xs text-muted-foreground">
                  資料模組
                </Label>
                {selectedModules.length > 0 && (
                  <button
                    onClick={() => onModulesChange([])}
                    className="text-[10px] text-primary hover:underline"
                  >
                    清除全部
                  </button>
                )}
              </div>
              <Accordion
                type="multiple"
                defaultValue={['patient', 'disease', 'lab', 'specimen']}
                className="space-y-0.5"
              >
                {groups.map((group) => {
                  const modules = MODULE_DEFINITIONS.filter(
                    (m) => m.group === group,
                  );
                  const selectedCount = modules.filter((m) =>
                    selectedModules.includes(m.id),
                  ).length;
                  return (
                    <AccordionItem
                      key={group}
                      value={group}
                      className="overflow-hidden rounded-md border"
                    >
                      <AccordionTrigger className="px-2.5 py-2 text-xs font-medium hover:no-underline">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant="outline"
                            className={`h-4 px-1.5 py-0 text-[10px] ${groupColors[group]}`}
                          >
                            {selectedCount}/{modules.length}
                          </Badge>
                          <span>{groupLabels[group]}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-2.5 pb-2 pt-0">
                        <div className="space-y-1.5">
                          {modules.map((mod) => (
                            <Tooltip key={mod.id}>
                              <TooltipTrigger asChild>
                                {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
                                <label className="flex cursor-pointer items-start gap-2 rounded px-1.5 py-1 transition-colors hover:bg-accent/50">
                                  <Checkbox
                                    checked={selectedModules.includes(mod.id)}
                                    onCheckedChange={() => toggleModule(mod.id)}
                                    className="mt-0.5 h-3.5 w-3.5"
                                  />
                                  <div className="min-w-0">
                                    <div className="text-xs font-medium leading-tight">
                                      {mod.code}{' '}
                                      {mod.name !== mod.code
                                        ? `— ${mod.name}`
                                        : ''}
                                    </div>
                                    <div className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
                                      {mod.description}
                                    </div>
                                  </div>
                                </label>
                              </TooltipTrigger>
                              <TooltipContent
                                side="right"
                                className="max-w-[200px] text-xs"
                              >
                                {mod.tooltip}
                              </TooltipContent>
                            </Tooltip>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </div>

            {/* Advanced Filters */}
            <div className="space-y-2">
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex w-full items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
              >
                <Filter className="h-3.5 w-3.5" />
                <span>進階篩選</span>
                <ChevronDown
                  className={`ml-auto h-3 w-3 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
                />
              </button>
              {showAdvanced && (
                <div className="space-y-3 pt-1">
                  <div>
                    <Label className="text-[10px] text-muted-foreground">
                      性別
                    </Label>
                    <Select>
                      <SelectTrigger className="mt-1 h-8 text-xs">
                        <SelectValue placeholder="不限" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">不限</SelectItem>
                        <SelectItem value="male">男</SelectItem>
                        <SelectItem value="female">女</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">
                      主診斷關鍵字
                    </Label>
                    <Input
                      placeholder="如 Fabry、MPS"
                      className="mt-1 h-8 text-xs"
                    />
                  </div>
                  <div>
                    <Label className="text-[10px] text-muted-foreground">
                      看診日期區間
                    </Label>
                    <div className="mt-1 flex gap-1.5">
                      <Input type="date" className="h-8 flex-1 text-xs" />
                      <span className="self-center text-xs text-muted-foreground">
                        ~
                      </span>
                      <Input type="date" className="h-8 flex-1 text-xs" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Condition mode */
          <ConditionBuilder
            conditions={conditions}
            logic={conditionLogic}
            onConditionsChange={onConditionsChange}
            onLogicChange={onConditionLogicChange}
            onSearch={onConditionSearch}
            onClear={onConditionClear}
          />
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-border px-4 py-2">
        <Button
          variant="destructive"
          size="sm"
          onClick={queryMode === 'patient' ? onClearAll : onConditionClear}
          className="h-7 w-full text-xs"
        >
          清除全部條件
        </Button>
      </div>
    </aside>
  );
}
