"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ExpenseStatusBadge } from "@/components/expenses/expense-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchExpenses,
  formatCurrency,
  rejectExpense,
  validateExpense,
  type ExpenseSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";

export default function ExpenseValidationPage() {
  const [items, setItems] = useState<ExpenseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchExpenses(token, {
      status: "pending_validation",
      page_size: 50,
    });
    setItems(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleValidate(expenseId: string) {
    const token = getAccessToken();
    if (!token) return;
    setProcessingId(expenseId);
    setError(null);
    try {
      await validateExpense(token, expenseId);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Validation impossible");
    } finally {
      setProcessingId(null);
    }
  }

  async function handleReject(expenseId: string) {
    const token = getAccessToken();
    if (!token) return;
    setProcessingId(expenseId);
    setError(null);
    try {
      await rejectExpense(token, expenseId);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Rejet impossible");
    } finally {
      setProcessingId(null);
    }
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/depenses">← Retour aux dépenses</Link>
        </Button>

        <div>
          <h1 className="text-3xl font-bold">Validation des dépenses</h1>
          <p className="mt-2 text-zinc-600">
            Dépenses importantes (≥ 500 000 FCFA) en attente de votre validation.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="space-y-4">
          {items.length === 0 ? (
            <p className="rounded-xl border border-zinc-200 bg-white px-4 py-8 text-center text-zinc-500">
              Aucune dépense en attente de validation.
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold">{item.category_label}</p>
                    <ExpenseStatusBadge status={item.status} />
                  </div>
                  <p className="mt-1 text-sm text-zinc-600">{item.description}</p>
                  <p className="mt-2 text-lg font-bold">{formatCurrency(item.amount)}</p>
                  <p className="text-xs text-zinc-500">
                    {item.building_name ?? "Sans immeuble"} — {item.expense_date}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    disabled={processingId === item.id}
                    onClick={() => handleReject(item.id)}
                  >
                    Rejeter
                  </Button>
                  <Button
                    disabled={processingId === item.id}
                    onClick={() => handleValidate(item.id)}
                  >
                    Valider
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </main>
    </ProtectedRoute>
  );
}
