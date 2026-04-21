import React from 'react';
import { ArrowLeft, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Patient,
  ConditionRow,
  ConditionLogic,
  MODULE_DEFINITIONS,
  MODULE_FIELDS,
} from '@/types/medical';

interface MatchedPatient {
  patient: Patient;
  hitSummary: string[];
}

interface ConditionResultsProps {
  conditions: ConditionRow[];
  logic: ConditionLogic;
  matchedPatients: MatchedPatient[];
  selectedPatient: Patient | null;
  onSelectPatient: (p: Patient) => void;
  onBackToList: () => void;
}

export function ConditionResults({
  conditions,
  logic,
  matchedPatients,
  selectedPatient,
  onSelectPatient,
  onBackToList,
}: ConditionResultsProps) {
  if (selectedPatient) return null; // handled by parent

  const conditionChips = conditions
    .filter((c) => c.moduleId && c.fieldId)
    .map((c) => {
      const mod = MODULE_DEFINITIONS.find((m) => m.id === c.moduleId);
      const field = c.moduleId
        ? MODULE_FIELDS[c.moduleId as keyof typeof MODULE_FIELDS]?.find(
            (f) => f.id === c.fieldId,
          )
        : null;
      return `${mod?.code || c.moduleId} / ${field?.label || c.fieldId} ${c.operator} ${c.value}${c.value2 ? `~${c.value2}` : ''}`;
    });

  return (
    <div className="space-y-3">
      {/* Condition summary */}
      <div className="flex flex-wrap items-center gap-2 px-1 py-2 text-xs">
        <span className="text-muted-foreground">
          條件查詢（{logic}）· 命中{' '}
          <span className="font-medium text-foreground">
            {matchedPatients.length}
          </span>{' '}
          位病人
        </span>
        {conditionChips.map((chip) => (
          <Badge key={chip} variant="secondary" className="h-5 text-[10px]">
            {chip}
          </Badge>
        ))}
      </div>

      {matchedPatients.length === 0 ? (
        <div className="flex h-[40vh] flex-col items-center justify-center text-center">
          <h3 className="mb-1 text-base font-semibold text-foreground">
            找不到符合條件的病人
          </h3>
          <p className="text-sm text-muted-foreground">
            請嘗試放寬條件或切換邏輯為 OR。
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="h-8 w-[100px] text-xs">病歷號</TableHead>
                <TableHead className="h-8 w-[80px] text-xs">姓名</TableHead>
                <TableHead className="h-8 w-[40px] text-xs">性別</TableHead>
                <TableHead className="h-8 w-[90px] text-xs">生日</TableHead>
                <TableHead className="h-8 text-xs">主診斷</TableHead>
                <TableHead className="h-8 text-xs">命中摘要</TableHead>
                <TableHead className="h-8 w-[70px] text-xs">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {matchedPatients.map(({ patient, hitSummary }) => (
                <TableRow key={patient.chartno} className="hover:bg-accent/30">
                  <TableCell className="font-mono text-xs">
                    {patient.chartno}
                  </TableCell>
                  <TableCell className="text-xs font-medium">
                    {patient.name}
                  </TableCell>
                  <TableCell className="text-xs">{patient.sex}</TableCell>
                  <TableCell className="text-xs">{patient.birthday}</TableCell>
                  <TableCell className="max-w-[200px] truncate text-xs">
                    {patient.diagnosis}
                  </TableCell>
                  <TableCell className="text-[10px] text-muted-foreground">
                    {hitSummary.map((s) => (
                      <Badge
                        key={s}
                        variant="outline"
                        className="mb-0.5 mr-1 h-4 text-[9px]"
                      >
                        {s}
                      </Badge>
                    ))}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-[10px]"
                      onClick={() => onSelectPatient(patient)}
                    >
                      <Eye className="mr-1 h-3 w-3" />
                      查看
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

// ==========================================
// Condition evaluation engine
// ==========================================

function getModuleData(
  patient: Patient,
  moduleId: string,
): Record<string, any>[] {
  switch (moduleId) {
    case 'basic':
      return [patient];
    case 'opd':
      return patient.opd;
    case 'aa':
      return patient.aa;
    case 'msms':
      return patient.msms;
    case 'biomarker':
      return patient.biomarker;
    case 'aadc':
      return patient.aadc;
    case 'ald':
      return patient.ald;
    case 'mma':
      return patient.mma;
    case 'mps2':
      return patient.mps2;
    case 'lsd':
      return patient.lsd;
    case 'enzyme':
      return patient.enzyme;
    case 'gag':
      return patient.gag;
    case 'dnabank':
      return patient.dnabank;
    case 'outbank':
      return patient.outbank;
    default:
      return [];
  }
}

function evalCondition(
  row: ConditionRow,
  records: Record<string, any>[],
): boolean {
  if (!row.moduleId || !row.fieldId) return false;

  return records.some((rec) => {
    const val = rec[row.fieldId];

    switch (row.operator) {
      case 'has_data':
        return val !== undefined && val !== null && val !== '';
      case 'no_data':
        return val === undefined || val === null || val === '';
      case 'eq':
        return String(val) === row.value;
      case 'neq':
        return String(val) !== row.value;
      case 'contains':
        return String(val ?? '')
          .toLowerCase()
          .includes(row.value.toLowerCase());
      case 'gt':
        return Number(val) > Number(row.value);
      case 'gte':
        return Number(val) >= Number(row.value);
      case 'lt':
        return Number(val) < Number(row.value);
      case 'lte':
        return Number(val) <= Number(row.value);
      case 'between': {
        const n = Number(val);
        return n >= Number(row.value) && n <= Number(row.value2);
      }
      case 'after':
        return String(val) > row.value;
      case 'before':
        return String(val) < row.value;
      default:
        return false;
    }
  });
}

function getHitSummary(
  row: ConditionRow,
  records: Record<string, any>[],
): string | null {
  if (!row.moduleId || !row.fieldId) return null;
  const mod = MODULE_DEFINITIONS.find((m) => m.id === row.moduleId);
  const field = MODULE_FIELDS[row.moduleId as keyof typeof MODULE_FIELDS]?.find(
    (f) => f.id === row.fieldId,
  );

  const matchedRec = records.find((rec) => {
    const val = rec[row.fieldId];
    if (val === undefined || val === null) return false;
    return true;
  });

  if (!matchedRec) return null;
  const val = matchedRec[row.fieldId];
  return `${mod?.code}/${field?.label}=${val}`;
}

export function evaluateConditions(
  patients: Patient[],
  conditions: ConditionRow[],
  logic: ConditionLogic,
): MatchedPatient[] {
  const validConditions = conditions.filter((c) => c.moduleId && c.fieldId);
  if (validConditions.length === 0) return [];

  return patients
    .map((patient) => {
      const results = validConditions.map((cond) => {
        const records = getModuleData(patient, cond.moduleId);
        return {
          match: evalCondition(cond, records),
          summary: getHitSummary(cond, records),
        };
      });

      const matched =
        logic === 'AND'
          ? results.every((r) => r.match)
          : results.some((r) => r.match);

      if (!matched) return null;

      return {
        patient,
        hitSummary: results
          .filter((r) => r.match && r.summary)
          .map((r) => r.summary!),
      };
    })
    .filter(Boolean) as MatchedPatient[];
}
