import { Calendar, Dna, ExternalLink } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Patient, ModuleId } from '@/types/medical';
import { ageInYears } from '@/utils/statsUtils';
import { CopyButton } from '@/components/CopyButton';

interface PatientSummaryProps {
  patient: Patient;
  onJumpTo: (moduleId: ModuleId) => void;
}

export function PatientSummary({ patient, onJumpTo }: PatientSummaryProps) {
  const age = ageInYears(patient.birthday) ?? '—';
  const displayChartno =
    patient.chartno ?? patient.externalChartno ?? patient.nbsId ?? '—';
  const hasDna = patient.dnabank.length > 0;
  const hasOutbank = patient.outbank.length > 0;
  const lastVisit =
    patient.opd.length > 0
      ? patient.opd.sort((a, b) => b.visitDate.localeCompare(a.visitDate))[0]
          .visitDate
      : null;

  const jumpLinks: { label: string; moduleId: ModuleId; count: number }[] = [
    { label: '門診', moduleId: 'opd', count: patient.opd.length },
    { label: 'MS/MS', moduleId: 'msms', count: patient.msms.length },
    { label: 'AA', moduleId: 'aa', count: patient.aa.length },
    { label: 'Enzyme', moduleId: 'enzyme', count: patient.enzyme.length },
    { label: 'GAG', moduleId: 'gag', count: patient.gag.length },
    { label: 'DNA', moduleId: 'dnabank', count: patient.dnabank.length },
    { label: '外送', moduleId: 'outbank', count: patient.outbank.length },
  ];

  return (
    <Card className="border-l-4 border-l-primary shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Main info */}
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex items-center gap-3">
              <h2 className="text-lg font-bold text-foreground">
                {patient.name}
              </h2>
              <div className="font-mono-medical flex items-center gap-1 text-muted-foreground">
                <span>{displayChartno}</span>
                <CopyButton text={displayChartno} />
              </div>
              <Badge variant="outline" className="h-5 text-[10px]">
                {patient.sex}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {patient.birthday} （{age} 歲）
              </span>
            </div>

            {/* Diagnoses */}
            <div className="mb-3 space-y-0.5">
              <div className="text-xs">
                <span className="mr-1.5 text-muted-foreground">主診斷</span>
                <span className="font-medium">{patient.diagnosis ?? '—'}</span>
              </div>
              {patient.diagnosis2 && (
                <div className="text-xs">
                  <span className="mr-1.5 text-muted-foreground">次診斷</span>
                  <span>{patient.diagnosis2}</span>
                </div>
              )}
              {patient.diagnosis3 && (
                <div className="text-xs">
                  <span className="mr-1.5 text-muted-foreground">次診斷</span>
                  <span>{patient.diagnosis3}</span>
                </div>
              )}
            </div>

            {/* Status badges */}
            <div className="flex flex-wrap items-center gap-2">
              {hasDna && (
                <Badge variant="secondary" className="h-5 gap-1 text-[10px]">
                  <Dna className="h-3 w-3" />
                  DNA 樣本 {patient.dnabank.length} 筆
                </Badge>
              )}
              {hasOutbank && (
                <Badge variant="secondary" className="h-5 gap-1 text-[10px]">
                  <ExternalLink className="h-3 w-3" />
                  外送檢體 {patient.outbank.length} 筆
                </Badge>
              )}
              {lastVisit && (
                <Badge variant="secondary" className="h-5 gap-1 text-[10px]">
                  <Calendar className="h-3 w-3" />
                  最近門診 {lastVisit}
                </Badge>
              )}
            </div>
          </div>

          {/* Right: Quick jumps + actions */}
          <div className="flex max-w-[260px] flex-wrap justify-end gap-1">
            {jumpLinks
              .filter((l) => l.count > 0)
              .map((link) => (
                <Button
                  key={link.moduleId}
                  variant="outline"
                  size="sm"
                  className="h-6 px-2 text-[10px]"
                  onClick={() => onJumpTo(link.moduleId)}
                >
                  {link.label} ({link.count})
                </Button>
              ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface PatientListProps {
  patients: Patient[];
  onSelect: (patient: Patient) => void;
}

export function PatientList({ patients, onSelect }: PatientListProps) {
  return (
    <div className="space-y-2">
      <p className="text-sm text-muted-foreground">
        找到 {patients.length} 位病人，請選擇：
      </p>
      {patients.map((p) => (
        <button
          key={p.patientId}
          onClick={() => onSelect(p)}
          className="w-full rounded-md border border-border bg-card p-3 text-left transition-colors hover:bg-accent/50"
        >
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold">{p.name}</span>
            <span className="font-mono-medical text-xs text-muted-foreground">
              {p.chartno ?? p.externalChartno ?? p.nbsId ?? '—'}
            </span>
            <Badge variant="outline" className="h-4 text-[10px]">
              {p.sex}
            </Badge>
            <span className="text-xs text-muted-foreground">{p.birthday}</span>
            <span className="ml-auto max-w-[300px] truncate text-xs text-muted-foreground">
              {p.diagnosis ?? '—'}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
