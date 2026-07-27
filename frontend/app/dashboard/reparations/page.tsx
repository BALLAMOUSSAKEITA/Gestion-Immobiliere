"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { RepairKanban } from "@/components/repairs/repair-kanban";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchRepairs,
  fetchRepairsSummary,
  type RepairSummary,
  type RepairSummaryStats,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

function SummaryCards({ summary }: { summary: RepairSummaryStats }) {
  return (
    <div className="grid gap-4 sm:grid-cols-3">
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">En cours</p>
        <p className="mt-1 text-2xl font-bold">{summary.in_progress_count}</p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Urgentes</p>
        <p className="mt-1 text-2xl font-bold text-red-600">{summary.urgent_count}</p>
      </div>
      <div className="rounded-xl border border-zinc-200 bg-white p-4">
        <p className="text-sm text-zinc-500">Terminées ce mois</p>
        <p className="mt-1 text-2xl font-bold text-green-600">{summary.completed_this_month}</p>
      </div>
    </div>
  );
}

export default function RepairsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<RepairSummary[]>([]);
  const [summary, setSummary] = useState<RepairSummaryStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"kanban" | "list">("kanban");

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const [list, stats] = await Promise.all([
      fetchRepairs(token, { page_size: 100 }),
      fetchRepairsSummary(token),
    ]);
    setItems(list.items);
    setSummary(stats);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Réparations</h1>
            <p className="mt-2 text-zinc-600">Suivi des demandes d&apos;intervention et maintenance.</p>
          </div>
          {canManage && (
            <Button asChild>
              <Link href="/dashboard/reparations/nouvelle">Nouvelle déclaration</Link>
            </Button>
          )}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {summary && <SummaryCards summary={summary} />}

        <div className="flex gap-2">
          <Button variant={view === "kanban" ? "default" : "outline"} onClick={() => setView("kanban")}>
            Kanban
          </Button>
          <Button variant={view === "list" ? "default" : "outline"} onClick={() => setView("list")}>
            Liste
          </Button>
        </div>

        {view === "kanban" ? (
          <RepairKanban items={items} />
        ) : (
          <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50">
                <tr>
                  <th className="px-4 py-3">Titre</th>
                  <th className="px-4 py-3">Logement</th>
                  <th className="px-4 py-3">Urgence</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="border-b border-zinc-100">
                    <td className="px-4 py-3">{item.title}</td>
                    <td className="px-4 py-3">{item.unit_code}</td>
                    <td className="px-4 py-3">{item.urgency}</td>
                    <td className="px-4 py-3">{item.status}</td>
                    <td className="px-4 py-3">
                      <Button asChild variant="outline">
                        <Link href={`/dashboard/reparations/${item.id}`}>Détail</Link>
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </ProtectedRoute>
  );
}
