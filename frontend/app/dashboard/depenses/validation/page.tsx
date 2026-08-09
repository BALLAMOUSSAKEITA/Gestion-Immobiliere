"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ExpenseStatusBadge } from "@/components/expenses/expense-status-badge";
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
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm, modifyConfirm } from "@/lib/confirm-presets";

export default function ExpenseValidationPage() {
  const confirm = useConfirm();
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
    if (!(await confirm(modifyConfirm("Valider cette dépense ?")))) return;
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
    if (!(await confirm(modifyConfirm("Rejeter cette dépense ?")))) return;
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
      <div className="flex flex-col gap-6">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/depenses">← Retour aux dépenses</Link>
        </Button>

        <div>
          <h1 className="text-3xl font-bold">Validation des dépenses</h1>
          <p className="mt-2 text-muted-foreground">
            Dépenses importantes (≥ 500 000 FG) en attente de votre validation.
          </p>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="space-y-4">
          {items.length === 0 ? (
            <p className="rounded-xl border border-border bg-card shadow-sm px-4 py-8 text-center text-muted-foreground">
              Aucune dépense en attente de validation.
            </p>
          ) : (
            items.map((item) => (
              <div
                key={item.id}
                className="flex flex-col gap-4 rounded-xl border border-border bg-card shadow-sm p-5 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold">{item.category_label}</p>
                    <ExpenseStatusBadge status={item.status} />
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                  <p className="mt-2 text-lg font-bold">{formatCurrency(item.amount)}</p>
                  <p className="text-xs text-muted-foreground">
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
      </div>
  );
}
