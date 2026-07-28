"use client";

import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatCurrency, type MonthlySeriesPoint } from "@/lib/api";

type RevenueExpenseChartProps = {
  points: MonthlySeriesPoint[];
};

export function RevenueExpenseChart({ points }: RevenueExpenseChartProps) {
  const data = points.map((point) => ({
    name: point.label,
    revenus: Number(point.revenue),
    depenses: Number(point.expenses),
    benefice: Number(point.net_profit),
  }));

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
          <Tooltip formatter={(value) => formatCurrency(Number(value))} />
          <Legend />
          <Bar dataKey="revenus" fill="#222222" name="Revenus" />
          <Line dataKey="depenses" stroke="#6a6a6a" name="Dépenses" />
          <Line dataKey="benefice" stroke="#222222" strokeDasharray="4 4" name="Bénéfice" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
