import React from 'react';
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ModuleId, MODULE_DEFINITIONS } from '@/types/medical';

interface SearchSummaryProps {
  query: string;
  patientCount: number;
  selectedModules: ModuleId[];
  onRemoveModule: (id: ModuleId) => void;
  onClearAll: () => void;
}

export function SearchSummary({
  query,
  patientCount,
  selectedModules,
  onRemoveModule,
  onClearAll,
}: SearchSummaryProps) {
  if (!query && selectedModules.length === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-2 px-1 py-2 text-xs">
      {query && (
        <span className="text-muted-foreground">
          搜尋「<span className="font-medium text-foreground">{query}</span>」 ·
          命中{' '}
          <span className="font-medium text-foreground">{patientCount}</span>{' '}
          位病人
        </span>
      )}
      {selectedModules.length > 0 && (
        <>
          <span className="text-muted-foreground">· 已選模組：</span>
          {selectedModules.map((id) => {
            const mod = MODULE_DEFINITIONS.find((m) => m.id === id);
            return (
              <Badge
                key={id}
                variant="secondary"
                className="h-5 gap-0.5 pr-1 text-[10px]"
              >
                {mod?.code || id}
                <button
                  onClick={() => onRemoveModule(id)}
                  className="ml-0.5 hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            );
          })}
        </>
      )}
      {(query || selectedModules.length > 0) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-5 px-2 text-[10px] text-muted-foreground"
        >
          清除全部
        </Button>
      )}
    </div>
  );
}
