import React from 'react';
import { BarChart3, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Patient } from '@/types/medical';
import { StatsDialog } from '@/components/stats/StatsDialog';
import { ExportDialog } from '@/components/export/ExportDialog';

export function PatientActions({ patient }: { patient: Patient }) {
  const [statsOpen, setStatsOpen] = React.useState(false);
  const [exportOpen, setExportOpen] = React.useState(false);

  return (
    <>
      <div className="flex shrink-0 items-center gap-1">
        <Button
          variant="success"
          size="sm"
          className="h-6 px-2 text-[10px]"
          onClick={() => setStatsOpen(true)}
        >
          <BarChart3 className="mr-1 h-3 w-3" />
          統計
        </Button>
        <Button
          variant="info"
          size="sm"
          className="h-6 px-2 text-[10px]"
          onClick={() => setExportOpen(true)}
        >
          <Download className="mr-1 h-3 w-3" />
          匯出
        </Button>
      </div>
      <StatsDialog
        open={statsOpen}
        onOpenChange={setStatsOpen}
        patient={patient}
      />
      <ExportDialog
        open={exportOpen}
        onOpenChange={setExportOpen}
        patient={patient}
      />
    </>
  );
}
