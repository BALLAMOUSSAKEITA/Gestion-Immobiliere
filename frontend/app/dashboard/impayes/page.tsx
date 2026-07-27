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
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Total impayé</p>
        <p className="mt-1 text-2xl font-bold text-red-600">
          {formatCurrency(summary.total_overdue_amount)}
        </p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Locataires concernés</p>
        <p className="mt-1 text-2xl font-bold">{summary.total_tenants_affected}</p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Mois en retard</p>
        <p className="mt-1 text-2xl font-bold">{summary.total_periods_overdue}</p>
      </div>
    </div>
  );
}

export default function OverduesPage() {
  const [items, setItems] = useState<OverdueItem[]>([]);
  const [summary, setSummary] = useState<OverdueSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sort, setSort] = useState("days_overdue");

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchOverdues(token, { page_size: 50, sort });
    setItems(data.items);
    setSummary(data.summary);
  }, [sort]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Impayés</h1>
            <p className="mt-2 text-zinc-600">Suivi des loyers en retard et créances ouvertes.</p>
          </div>
          <div className="flex gap-2">
            <Button asChild variant="outline">
              <Link href="/dashboard/relances">Historique des relances</Link>
            </Button>
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {summary && <SummaryCards summary={summary} />}

        <div className="flex items-center gap-2">
          <label htmlFor="sort" className="text-sm text-zinc-600">
            Trier par
          </label>
          <select
            id="sort"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-md border border-zinc-300 px-3 py-2 text-sm"
          >
            <option value="days_overdue">Jours de retard</option>
            <option value="amount">Montant</option>
            <option value="tenant_name">Locataire</option>
          </select>
        </div>

        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-zinc-200 bg-zinc-50">
              <tr>
                <th className="px-4 py-3">Locataire</th>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Période</th>
                <th className="px-4 py-3">Reste dû</th>
                <th className="px-4 py-3">Retard</th>
                <th className="px-4 py-3">Relances</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-zinc-500">
                    Aucun impayé en cours.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b border-zinc-100">
                    <td className="px-4 py-3">
                      <div className="font-medium">{item.tenant.full_name}</div>
                      <div className="text-xs text-zinc-500">{item.tenant.phone}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div>{item.unit_code}</div>
                      <div className="text-xs text-zinc-500">{item.building_name}</div>
                    </td>
                    <td className="px-4 py-3">{item.period}</td>
                    <td className="px-4 py-3 font-medium text-red-600">
                      {formatCurrency(item.amount_remaining)}
                    </td>
                    <td className="px-4 py-3">{item.days_overdue} j</td>
                    <td className="px-4 py-3">{item.reminders_count}</td>
                    <td className="px-4 py-3">
                      <Button asChild variant="outline">
                        <Link href={`/dashboard/impayes/${item.id}`}>Détail</Link>
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </ProtectedRoute>
  );
}
