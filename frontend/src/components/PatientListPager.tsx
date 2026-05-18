import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

interface PatientListPagerProps {
  page: number;
  pageCount: number;
  onPageChange: (page: number) => void;
}

// Page links to show: always the first and last page, plus a one-page window
// around the current page. A run of two-or-more hidden pages collapses to an
// ellipsis; a single hidden page is rendered as its number instead.
function buildPageItems(
  page: number,
  pageCount: number,
): (number | 'ellipsis')[] {
  const shown = new Set<number>([1, pageCount]);
  for (let p = page - 1; p <= page + 1; p += 1) {
    if (p >= 1 && p <= pageCount) shown.add(p);
  }
  const sorted = [...shown].sort((a, b) => a - b);
  const items: (number | 'ellipsis')[] = [];
  let prev = 0;
  for (const p of sorted) {
    if (p - prev === 2) {
      items.push(prev + 1);
    } else if (p - prev > 2) {
      items.push('ellipsis');
    }
    items.push(p);
    prev = p;
  }
  return items;
}

export function PatientListPager({
  page,
  pageCount,
  onPageChange,
}: PatientListPagerProps) {
  if (pageCount <= 1) return null;

  const items = buildPageItems(page, pageCount);
  const isFirst = page <= 1;
  const isLast = page >= pageCount;

  const go = (target: number) => {
    const clamped = Math.min(Math.max(target, 1), pageCount);
    if (clamped !== page) onPageChange(clamped);
  };

  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            aria-disabled={isFirst}
            className={
              isFirst ? 'pointer-events-none opacity-50' : 'cursor-pointer'
            }
            onClick={(e) => {
              e.preventDefault();
              if (!isFirst) go(page - 1);
            }}
          />
        </PaginationItem>
        {items.map((item, i) =>
          item === 'ellipsis' ? (
            // eslint-disable-next-line react/no-array-index-key
            <PaginationItem key={`ellipsis-${i}`}>
              <PaginationEllipsis />
            </PaginationItem>
          ) : (
            <PaginationItem key={item}>
              <PaginationLink
                isActive={item === page}
                className="cursor-pointer"
                onClick={(e) => {
                  e.preventDefault();
                  go(item);
                }}
              >
                {item}
              </PaginationLink>
            </PaginationItem>
          ),
        )}
        <PaginationItem>
          <PaginationNext
            aria-disabled={isLast}
            className={
              isLast ? 'pointer-events-none opacity-50' : 'cursor-pointer'
            }
            onClick={(e) => {
              e.preventDefault();
              if (!isLast) go(page + 1);
            }}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
