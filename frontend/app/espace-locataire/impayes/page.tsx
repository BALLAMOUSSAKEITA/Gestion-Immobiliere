"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchOverdues,
  formatCurrency,
  type OverdueItem,
  type OverdueSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

function SummaryCards({ summary }: { summary: OverdueSummary }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Total impayé</p>
        <p className="mt-1 text-2xl font-bold text-red-600">
          {formatCurrency(summary.total_overdue_amount)}
        </p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Mois en retard</p>
        <p className="mt-1 text-2xl font-bold">{summary.total_periods_overdue}</p>
      </div>
    </div>
  );
}

export default function TenantOverduesPage() {
  const [items, setItems] = useState<OverdueItem[]>([]);
  const [summary, setSummary] = useState<OverdueSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchOverdues(token, { page_size: 50 });
    setItems(data.items);
    setSummary(data.summary);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <div>
          <h1 className="text-3xl font-bold">Mes impayés</h1>
          <p className="mt-2 text-zinc-600">Consultez vos loyers en retard.</p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {summary && <SummaryCards summary={summary} />}

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Période</th>
                <th className="px-4 py-3">Reste dû</th>
                <th className="px-4 py-3">Retard</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-zinc-500">
                    Aucun impayé. Merci !
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b border-zinc-100">
                    <td className="px-4 py-3">
                      <div>{item.unit_code}</div>
                      <div className="text-xs text-zinc-500">{item.building_name}</div>
                    </td>
                    <td className="px-4 py-3">{item.period}</td>
                    <td className="px-4 py-3 font-medium text-red-600">
                      {formatCurrency(item.amount_remaining)}
                    </td>
                    <td className="px-4 py-3">{item.days_overdue} j</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <Button asChild variant="outline" className="w-fit">
          <Link href="/espace-locataire">Retour à l&apos;espace locataire</Link>
        </Button>
      </main>
    </ProtectedRoute>
  );
}
