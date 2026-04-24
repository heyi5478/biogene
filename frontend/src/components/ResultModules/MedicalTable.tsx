import React from 'react';

export function MedicalTable({
  headers,
  rows,
}: {
  headers: string[];
  rows: React.ReactNode[][];
}) {
  if (rows.length === 0)
    return (
      <div className="px-3 py-4 text-center text-xs text-muted-foreground">
        無資料
      </div>
    );
  return (
    <div className="thin-scrollbar overflow-x-auto">
      <table className="medical-table w-full">
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} className="whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            // eslint-disable-next-line react/no-array-index-key
            <tr key={i}>
              {row.map((cell, j) => (
                // eslint-disable-next-line react/no-array-index-key
                <td key={`${i}-${j}`} className="whitespace-nowrap">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
