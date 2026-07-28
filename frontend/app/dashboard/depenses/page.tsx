"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ExpenseStatusBadge } from "@/components/expenses/expense-status-badge";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchExpenses,
  fetchExpensesSummary,
  formatCurrency,
  type ExpenseSummary,
  type ExpenseSummaryStats,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

function SummaryCards({ summary }: { summary: ExpenseSummaryStats }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-border bg-card shadow-sm p-4">
        <p className="text-sm text-muted-foreground">Total validé / enregistré</p>
        <p className="mt-1 text-2xl font-bold">{formatCurrency(summary.total_amount)}</p>
      </div>
      <div className="rounded-xl border border-border bg-card shadow-sm p-4">
        <p className="text-sm text-muted-foreground">Nombre de dépenses</p>
        <p className="mt-1 text-2xl font-bold">{summary.count}</p>
      </div>
      <div className="rounded-xl border border-border bg-card shadow-sm p-4">
        <p className="mb-2 text-sm text-muted-foreground">Par catégorie</p>
        <ul className="space-y-1 text-sm">
          {summary.by_category.slice(0, 3).map((item) => (
            <li key={item.category} className="flex justify-between gap-2">
              <span>{item.category}</span>
              <span className="font-medium">{formatCurrency(item.amount)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function ExpensesPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<ExpenseSummary[]>([]);
  const [summary, setSummary] = useState<ExpenseSummaryStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [supplier, setSupplier] = useState("");

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const params: Record<string, string | number | undefined> = { page_size: 50 };
    if (status) params.status = status;
    if (supplier) params.supplier = supplier;
    const [list, stats] = await Promise.all([
      fetchExpenses(token, params),
      fetchExpensesSummary(token, { year: new Date().getFullYear() }),
    ]);
    setItems(list.items);
    setSummary(stats);
  }, [status, supplier]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dépenses</h1>
            <p className="mt-2 text-muted-foreground">Suivi des charges et justificatifs du patrimoine.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {user?.role.code === "super_admin" && (
              <Button asChild variant="outline">
                <Link href="/dashboard/depenses/validation">Validation</Link>
              </Button>
            )}
            {canManage && (
              <Button asChild>
                <Link href="/dashboard/depenses/nouvelle">Nouvelle dépense</Link>
              </Button>
            )}
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {summary && <SummaryCards summary={summary} />}

        <div className="grid gap-3 rounded-xl border border-border bg-card shadow-sm p-4 sm:grid-cols-3">
          <div>
            <label htmlFor="status" className="mb-1 block text-sm text-muted-foreground">
              Statut
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            >
              <option value="">Tous</option>
              <option value="recorded">Enregistrée</option>
              <option value="pending_validation">En attente</option>
              <option value="validated">Validée</option>
              <option value="rejected">Rejetée</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label htmlFor="supplier" className="mb-1 block text-sm text-muted-foreground">
              Fournisseur
            </label>
            <input
              id="supplier"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              placeholder="Rechercher un fournisseur…"
              className="w-full rounded-md border border-input px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Catégorie</th>
                <th className="px-4 py-3">Immeuble</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Montant</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Aucune dépense trouvée.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b border-border">
                    <td className="px-4 py-3">{item.expense_date}</td>
                    <td className="px-4 py-3">{item.category_label}</td>
                    <td className="px-4 py-3">{item.building_name ?? "—"}</td>
                    <td className="max-w-xs truncate px-4 py-3" title={item.description}>
                      {item.description}
                    </td>
                    <td className="px-4 py-3">{formatCurrency(item.amount)}</td>
                    <td className="px-4 py-3">
                      <ExpenseStatusBadge status={item.status} />
                    </td>
                    <td className="px-4 py-3">
                      <Button asChild variant="outline">
                        <Link href={`/dashboard/depenses/${item.id}`}>Détail</Link>
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
  );
}
