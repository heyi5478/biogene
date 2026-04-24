import { Copy, Check } from 'lucide-react';
import { useCopyToClipboard } from '@/hooks/use-copy-to-clipboard';

export function CopyBtn({ text }: { text: string }) {
  const { copied, copy } = useCopyToClipboard();
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        copy(text);
      }}
      className="inline-flex text-muted-foreground hover:text-foreground"
    >
      {copied ? (
        <Check className="h-3 w-3 text-emerald-600" />
      ) : (
        <Copy className="h-3 w-3" />
      )}
    </button>
  );
}
