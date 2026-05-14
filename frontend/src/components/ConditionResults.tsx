import { useState } from 'react';
import { Download, Eye } from 'lucide-react';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  PatientListItem,
  ConditionRow,
  ConditionLogic,
  MODULE_DEFINITIONS,
  MODULE_FIELDS,
} from '@/types/medical';
import { CohortStatsPanel } from '@/components/stats/CohortStatsPanel';
import { CohortExportDialog } from '@/components/export/CohortExportDialog';

interface ConditionResultsProps {
  conditions: ConditionRow[];
  logic: ConditionLogic;
  matchedPatients: PatientListItem[];
  onSelectPatient: (patientId: string) => void;
}

export function ConditionResults({
  conditions,
  logic,
  matchedPatients,
  onSelectPatient,
}: ConditionResultsProps) {
  const [exportOpen, setExportOpen] = useState(false);

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

  const listContent = (
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
        <Button
          variant="outline"
          size="sm"
          className="ml-auto h-6 px-2 text-[10px]"
          disabled={matchedPatients.length === 0}
          onClick={() => setExportOpen(true)}
        >
          <Download className="mr-1 h-3 w-3" />
          匯出比較報告
        </Button>
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
              {matchedPatients.map((patient) => (
                <TableRow
                  key={patient.patientId}
                  className="hover:bg-accent/30"
                >
                  <TableCell className="font-mono text-xs">
                    {patient.chartno ??
                      patient.externalChartno ??
                      patient.nbsId ??
                      '—'}
                  </TableCell>
                  <TableCell className="text-xs font-medium">
                    {patient.name}
                  </TableCell>
                  <TableCell className="text-xs">{patient.sex}</TableCell>
                  <TableCell className="text-xs">{patient.birthday}</TableCell>
                  <TableCell className="max-w-[200px] truncate text-xs">
                    {patient.diagnosis ?? '—'}
                  </TableCell>
                  <TableCell className="text-[10px] text-muted-foreground">
                    {(patient.conditionHits ?? []).map((s) => (
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
                      onClick={() => onSelectPatient(patient.patientId)}
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

  return (
    <>
      <Tabs defaultValue="list" className="space-y-2">
        <TabsList>
          <TabsTrigger value="list">名單</TabsTrigger>
          <TabsTrigger value="cohort">族群統計</TabsTrigger>
        </TabsList>
        <TabsContent value="list">{listContent}</TabsContent>
        <TabsContent value="cohort">
          <CohortStatsPanel patients={matchedPatients} />
        </TabsContent>
      </Tabs>
      <CohortExportDialog
        open={exportOpen}
        onOpenChange={setExportOpen}
        patients={matchedPatients}
      />
    </>
  );
}
