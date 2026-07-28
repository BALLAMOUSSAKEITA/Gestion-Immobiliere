"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type OccupancyChartProps = {
  points: { label: string; occupancy_rate: number }[];
};

export function OccupancyChart({ points }: OccupancyChartProps) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
          <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
          <Tooltip formatter={(value) => `${value}%`} />
          <Line type="monotone" dataKey="occupancy_rate" stroke="#222222" name="Occupation" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
