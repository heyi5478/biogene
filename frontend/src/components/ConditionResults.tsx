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
import { PatientListPager } from '@/components/PatientListPager';

interface ConditionResultsProps {
  conditions: ConditionRow[];
  logic: ConditionLogic;
  matchedPatients: PatientListItem[];
  total: number;
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
  onSelectPatient: (patientId: string) => void;
}

export function ConditionResults({
  conditions,
  logic,
  matchedPatients,
  total,
  page,
  pageCount,
  onPageChange,
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
          <span className="font-medium text-foreground">{total}</span> 位病人
        </span>
        {conditionChips.map((chip) => (
          <Badge key={chip} variant="secondary" className="h-5 text-[10px]">
            {chip}
          </Badge>
        ))}
        <div className="ml-auto flex items-center gap-1.5">
          <span className="text-[10px] text-muted-foreground">
            僅供參考：僅含目前頁面
          </span>
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2 text-[10px]"
            disabled={total === 0}
            onClick={() => setExportOpen(true)}
          >
            <Download className="mr-1 h-3 w-3" />
            匯出比較報告
          </Button>
        </div>
      </div>

      {total === 0 ? (
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
      {pageCount > 1 && (
        <PatientListPager
          page={page}
          pageCount={pageCount}
          onPageChange={onPageChange}
        />
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
          <p className="mb-2 px-1 text-xs text-muted-foreground">
            僅供參考：以下統計僅涵蓋目前結果頁面的病人，非完整符合條件的族群。
          </p>
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
