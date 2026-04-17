import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Patient, ModuleId, MODULE_DEFINITIONS } from '@/types/medical';

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <button
      onClick={(e) => { e.stopPropagation(); navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      className="inline-flex text-muted-foreground hover:text-foreground"
    >
      {copied ? <Check className="h-3 w-3 text-emerald-600" /> : <Copy className="h-3 w-3" />}
    </button>
  );
}

interface ModuleSectionProps {
  id: string;
  title: string;
  count: number;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function ModuleSection({ id, title, count, defaultOpen = true, children }: ModuleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div id={`section-${id}`} className="border rounded-md bg-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium hover:bg-accent/30 transition-colors"
      >
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
        <span>{title}</span>
        <Badge variant="secondary" className="text-[10px] h-4 px-1.5">{count} 筆</Badge>
      </button>
      {open && <div className="border-t">{children}</div>}
    </div>
  );
}

function MedicalTable({ headers, rows }: { headers: string[]; rows: React.ReactNode[][] }) {
  if (rows.length === 0) return <div className="px-3 py-4 text-xs text-muted-foreground text-center">無資料</div>;
  return (
    <div className="overflow-x-auto thin-scrollbar">
      <table className="w-full medical-table">
        <thead>
          <tr>
            {headers.map((h, i) => <th key={i} className="whitespace-nowrap">{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => <td key={j} className="whitespace-nowrap">{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MonoVal({ val }: { val: number | undefined }) {
  if (val === undefined || val === null) return <span className="text-muted-foreground">—</span>;
  return <span className="font-mono-medical">{val}</span>;
}

interface ResultModulesProps {
  patient: Patient;
  activeModules: ModuleId[];
}

export function ResultModules({ patient, activeModules }: ResultModulesProps) {
  const show = (id: ModuleId) => activeModules.length === 0 || activeModules.includes(id);

  return (
    <div className="space-y-3">
      {/* Basic Info */}
      {show('basic') && (
        <ModuleSection id="basic" title="基本資料" count={1}>
          <div className="px-3 py-3 grid grid-cols-3 gap-x-6 gap-y-2 text-xs">
            <div><span className="text-muted-foreground">病歷號　</span><span className="font-mono-medical">{patient.chartno}</span> <CopyBtn text={patient.chartno} /></div>
            <div><span className="text-muted-foreground">生日　</span>{patient.birthday}</div>
            <div><span className="text-muted-foreground">性別　</span>{patient.sex}</div>
            <div className="col-span-3"><span className="text-muted-foreground">主診斷　</span><span className="font-medium">{patient.diagnosis}</span></div>
            {patient.diagnosis2 && <div className="col-span-3"><span className="text-muted-foreground">次診斷1　</span>{patient.diagnosis2}</div>}
            {patient.diagnosis3 && <div className="col-span-3"><span className="text-muted-foreground">次診斷2　</span>{patient.diagnosis3}</div>}
          </div>
        </ModuleSection>
      )}

      {/* OPD */}
      {show('opd') && patient.opd.length > 0 && (
        <ModuleSection id="opd" title="門診紀錄（OPD）" count={patient.opd.length}>
          <MedicalTable
            headers={['看診日', '主診斷碼', '主診斷名稱', '次診斷名稱1', '次診斷2']}
            rows={patient.opd
              .sort((a, b) => b.visitDate.localeCompare(a.visitDate))
              .map(r => [r.visitDate, r.diagCode, r.diagName, r.subDiag1 || '—', r.subDiag2 || '—'])}
          />
        </ModuleSection>
      )}

      {/* AA */}
      {show('aa') && patient.aa.length > 0 && (
        <ModuleSection id="aa" title="胺基酸分析（AA）" count={patient.aa.length}>
          <MedicalTable
            headers={['Sample', '檢體類別', 'Result', 'Gln', 'Citr', 'Ala', 'Arg', 'Leu', 'Val', 'Phe', 'Tyr']}
            rows={patient.aa.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              r.specimenType,
              <Badge variant={r.result === 'Abnormal' ? 'destructive' : 'secondary'} className="text-[10px] h-4">{r.result}</Badge>,
              <MonoVal val={r.Gln} />, <MonoVal val={r.Citr} />, <MonoVal val={r.Ala} />, <MonoVal val={r.Arg} />,
              <MonoVal val={r.Leu} />, <MonoVal val={r.Val} />, <MonoVal val={r.Phe} />, <MonoVal val={r.Tyr} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* MS/MS */}
      {show('msms') && patient.msms.length > 0 && (
        <ModuleSection id="msms" title="串聯質譜篩檢（MS/MS）" count={patient.msms.length}>
          <MedicalTable
            headers={['Sample', '檢體類別', 'Result', 'Ala', 'Arg', 'Cit', 'Gly', 'Leu', 'Met', 'Phe', 'Tyr', 'Val', 'C0', 'C2', 'C3', 'C5']}
            rows={patient.msms.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              r.specimenType,
              <Badge variant={r.result === 'Abnormal' ? 'destructive' : 'secondary'} className="text-[10px] h-4">{r.result}</Badge>,
              <MonoVal val={r.Ala} />, <MonoVal val={r.Arg} />, <MonoVal val={r.Cit} />, <MonoVal val={r.Gly} />,
              <MonoVal val={r.Leu} />, <MonoVal val={r.Met} />, <MonoVal val={r.Phe} />, <MonoVal val={r.Tyr} />,
              <MonoVal val={r.Val} />, <MonoVal val={r.C0} />, <MonoVal val={r.C2} />, <MonoVal val={r.C3} />, <MonoVal val={r.C5} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* Biomarker */}
      {show('biomarker') && patient.biomarker.length > 0 && (
        <ModuleSection id="biomarker" title="生物標記（Biomarker）" count={patient.biomarker.length}>
          <MedicalTable
            headers={['Sample', 'DBS LysoGb3', 'DBS LysoGL1', 'DBS Lyso-SM', 'Plasma LysoGb3', 'Plasma LysoGL1', 'Plasma Lyso-SM']}
            rows={patient.biomarker.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.dbsLysoGb3} />, <MonoVal val={r.dbsLysoGL1} />, <MonoVal val={r.dbsLysoSM} />,
              <MonoVal val={r.plasmaLysoGb3} />, <MonoVal val={r.plasmaLysoGL1} />, <MonoVal val={r.plasmaLysoSM} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* AADC */}
      {show('aadc') && patient.aadc.length > 0 && (
        <ModuleSection id="aadc" title="AADC 相關檢測" count={patient.aadc.length}>
          <MedicalTable
            headers={['Sample', '濃度 (Conc)', '日期']}
            rows={patient.aadc.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.conc} />,
              r.date || '—',
            ])}
          />
        </ModuleSection>
      )}

      {/* ALD */}
      {show('ald') && patient.ald.length > 0 && (
        <ModuleSection id="ald" title="ALD 相關檢測" count={patient.ald.length}>
          <MedicalTable
            headers={['Sample', '濃度 (Conc)', '日期']}
            rows={patient.ald.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.conc} />,
              r.date || '—',
            ])}
          />
        </ModuleSection>
      )}

      {/* MMA */}
      {show('mma') && patient.mma.length > 0 && (
        <ModuleSection id="mma" title="MMA 相關檢測" count={patient.mma.length}>
          <MedicalTable
            headers={['Sample', '濃度 (Conc)', '日期']}
            rows={patient.mma.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.conc} />,
              r.date || '—',
            ])}
          />
        </ModuleSection>
      )}

      {/* MPS2 */}
      {show('mps2') && patient.mps2.length > 0 && (
        <ModuleSection id="mps2" title="MPS / 相關 target panel" count={patient.mps2.length}>
          <MedicalTable
            headers={['Sample', 'MPS2', 'TPP1', 'MPS4A', 'MPS6']}
            rows={patient.mps2.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.MPS2} />, <MonoVal val={r.TPP1} />, <MonoVal val={r.MPS4A} />, <MonoVal val={r.MPS6} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* LSD */}
      {show('lsd') && patient.lsd.length > 0 && (
        <ModuleSection id="lsd" title="LSD 多重酵素 panel" count={patient.lsd.length}>
          <MedicalTable
            headers={['Sample', 'GAA', 'GLA', 'ABG', 'IDUA', 'ABG/GAA']}
            rows={patient.lsd.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              <MonoVal val={r.GAA} />, <MonoVal val={r.GLA} />, <MonoVal val={r.ABG} />, <MonoVal val={r.IDUA} />, <MonoVal val={r.ABG_GAA} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* Enzyme */}
      {show('enzyme') && patient.enzyme.length > 0 && (
        <ModuleSection id="enzyme" title="酵素檢驗（Enzyme）" count={patient.enzyme.length}>
          <MedicalTable
            headers={['Sample', '檢體類別', '技術人員', 'Result', 'MPS1', 'Enzyme-MPS2']}
            rows={patient.enzyme.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              r.specimenType, r.technician,
              <Badge variant={r.result === 'Deficient' ? 'destructive' : 'secondary'} className="text-[10px] h-4">{r.result}</Badge>,
              <MonoVal val={r.MPS1} />, <MonoVal val={r.enzymeMPS2} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* GAG */}
      {show('gag') && patient.gag.length > 0 && (
        <ModuleSection id="gag" title="GAG 定量" count={patient.gag.length}>
          <MedicalTable
            headers={['Sample', '檢體類別', '技術人員', 'Result', 'DMGGAG', 'CREATININE']}
            rows={patient.gag.map(r => [
              <span className="font-mono-medical">{r.sampleName}</span>,
              r.specimenType, r.technician,
              <Badge variant={r.result === 'Elevated' ? 'destructive' : 'secondary'} className="text-[10px] h-4">{r.result}</Badge>,
              <MonoVal val={r.DMGGAG} />, <MonoVal val={r.CREATININE} />,
            ])}
          />
        </ModuleSection>
      )}

      {/* DNAbank */}
      {show('dnabank') && patient.dnabank.length > 0 && (
        <ModuleSection id="dnabank" title="DNA 檢體庫（DNAbank）" count={patient.dnabank.length}>
          <MedicalTable
            headers={['Order No', 'Order', '備註', 'Keyword', 'Specimen No', 'Specimen']}
            rows={patient.dnabank.map(r => [
              <span className="font-mono-medical">{r.orderno} <CopyBtn text={r.orderno} /></span>,
              r.order, r.orderMemo || '—', r.keyword || '—',
              <span className="font-mono-medical">{r.specimenno} <CopyBtn text={r.specimenno} /></span>,
              r.specimen,
            ])}
          />
        </ModuleSection>
      )}

      {/* Outbank */}
      {show('outbank') && patient.outbank.length > 0 && (
        <ModuleSection id="outbank" title="外送檢體（Outbank）" count={patient.outbank.length}>
          <MedicalTable
            headers={['Sample No', '送驗日期', 'Assay', 'Result']}
            rows={patient.outbank.map(r => [
              <span className="font-mono-medical">{r.sampleno} <CopyBtn text={r.sampleno} /></span>,
              r.shipdate, r.assay,
              <span className={r.result === 'Pending' ? 'text-amber-600 font-medium' : ''}>{r.result}</span>,
            ])}
          />
        </ModuleSection>
      )}

      {/* Empty state for filtered modules with no data */}
      {activeModules.length > 0 && (() => {
        const moduleDataMap: Record<ModuleId, number> = {
          basic: 1, opd: patient.opd.length, aa: patient.aa.length, msms: patient.msms.length,
          biomarker: patient.biomarker.length, aadc: patient.aadc.length, ald: patient.ald.length,
          mma: patient.mma.length, mps2: patient.mps2.length, lsd: patient.lsd.length,
          enzyme: patient.enzyme.length, gag: patient.gag.length, dnabank: patient.dnabank.length,
          outbank: patient.outbank.length,
        };
        const emptyModules = activeModules.filter(id => id !== 'basic' && moduleDataMap[id] === 0);
        if (emptyModules.length === 0) return null;
        return (
          <div className="text-xs text-muted-foreground bg-muted/50 rounded-md px-3 py-2">
            以下已選模組無資料：{emptyModules.map(id => {
              const mod = MODULE_DEFINITIONS.find(m => m.id === id);
              return mod?.code || id;
            }).join('、')}
          </div>
        );
      })()}
    </div>
  );
}
