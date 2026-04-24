import { Badge } from '@/components/ui/badge';
import { Patient } from '@/types/medical';

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
