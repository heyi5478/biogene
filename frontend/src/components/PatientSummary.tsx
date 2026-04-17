import React from 'react';
import { Copy, Check, Calendar, Dna, ExternalLink } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Patient, ModuleId } from '@/types/medical';

function calcAge(birthday: string): number {
  const today = new Date();
  const birth = new Date(birthday);
  let age = today.getFullYear() - birth.getFullYear();
  const m = today.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
  return age;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
          className="inline-flex items-center text-muted-foreground hover:text-foreground ml-1"
        >
          {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
        </button>
      </TooltipTrigger>
      <TooltipContent className="text-xs">複製病歷號</TooltipContent>
    </Tooltip>
  );
}

interface PatientSummaryProps {
  patient: Patient;
  onJumpTo: (moduleId: ModuleId) => void;
}

export function PatientSummary({ patient, onJumpTo }: PatientSummaryProps) {
  const age = calcAge(patient.birthday);
  const hasDna = patient.dnabank.length > 0;
  const hasOutbank = patient.outbank.length > 0;
  const lastVisit = patient.opd.length > 0
    ? patient.opd.sort((a, b) => b.visitDate.localeCompare(a.visitDate))[0].visitDate
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
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <h2 className="text-lg font-bold text-foreground">{patient.name}</h2>
              <div className="flex items-center gap-1 font-mono-medical text-muted-foreground">
                <span>{patient.chartno}</span>
                <CopyButton text={patient.chartno} />
              </div>
              <Badge variant="outline" className="text-[10px] h-5">
                {patient.sex}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {patient.birthday} （{age} 歲）
              </span>
            </div>

            {/* Diagnoses */}
            <div className="space-y-0.5 mb-3">
              <div className="text-xs">
                <span className="text-muted-foreground mr-1.5">主診斷</span>
                <span className="font-medium">{patient.diagnosis}</span>
              </div>
              {patient.diagnosis2 && (
                <div className="text-xs">
                  <span className="text-muted-foreground mr-1.5">次診斷</span>
                  <span>{patient.diagnosis2}</span>
                </div>
              )}
              {patient.diagnosis3 && (
                <div className="text-xs">
                  <span className="text-muted-foreground mr-1.5">次診斷</span>
                  <span>{patient.diagnosis3}</span>
                </div>
              )}
            </div>

            {/* Status badges */}
            <div className="flex items-center gap-2 flex-wrap">
              {hasDna && (
                <Badge variant="secondary" className="text-[10px] h-5 gap-1">
                  <Dna className="h-3 w-3" />
                  DNA 樣本 {patient.dnabank.length} 筆
                </Badge>
              )}
              {hasOutbank && (
                <Badge variant="secondary" className="text-[10px] h-5 gap-1">
                  <ExternalLink className="h-3 w-3" />
                  外送檢體 {patient.outbank.length} 筆
                </Badge>
              )}
              {lastVisit && (
                <Badge variant="secondary" className="text-[10px] h-5 gap-1">
                  <Calendar className="h-3 w-3" />
                  最近門診 {lastVisit}
                </Badge>
              )}
            </div>
          </div>

          {/* Right: Quick jumps */}
          <div className="flex flex-wrap gap-1 max-w-[240px] justify-end">
            {jumpLinks.filter(l => l.count > 0).map((link) => (
              <Button
                key={link.moduleId}
                variant="outline"
                size="sm"
                className="h-6 text-[10px] px-2"
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
      <p className="text-sm text-muted-foreground">找到 {patients.length} 位病人，請選擇：</p>
      {patients.map((p) => (
        <button
          key={p.chartno}
          onClick={() => onSelect(p)}
          className="w-full text-left p-3 rounded-md border border-border bg-card hover:bg-accent/50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className="font-semibold text-sm">{p.name}</span>
            <span className="font-mono-medical text-xs text-muted-foreground">{p.chartno}</span>
            <Badge variant="outline" className="text-[10px] h-4">{p.sex}</Badge>
            <span className="text-xs text-muted-foreground">{p.birthday}</span>
            <span className="text-xs text-muted-foreground ml-auto truncate max-w-[300px]">{p.diagnosis}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
