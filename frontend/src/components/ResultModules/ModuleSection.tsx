import React, { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ModuleSectionProps {
  id: string;
  title: string;
  count: number;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

export function ModuleSection({
  id,
  title,
  count,
  defaultOpen = true,
  children,
}: ModuleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div
      id={`section-${id}`}
      className="overflow-hidden rounded-md border bg-card"
    >
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-3 py-2 text-xs font-medium transition-colors hover:bg-accent/30"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <span>{title}</span>
        <Badge variant="secondary" className="h-4 px-1.5 text-[10px]">
          {count} 筆
        </Badge>
      </button>
      {open && <div className="border-t">{children}</div>}
    </div>
  );
}
