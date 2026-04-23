import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface SparklinePoint {
  date: string;
  value: number;
}

interface StatsSparklineProps {
  data: SparklinePoint[];
}

export function StatsSparkline({ data }: StatsSparklineProps) {
  const sorted = useMemo(
    () =>
      data
        .filter((d) => d.date && Number.isFinite(d.value))
        .slice()
        .sort((a, b) => a.date.localeCompare(b.date)),
    [data],
  );

  if (sorted.length < 2) return null;

  return (
    <div style={{ width: 320, height: 120 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={sorted}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            dot={{ r: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
