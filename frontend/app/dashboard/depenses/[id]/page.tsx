"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { ExpenseStatusBadge } from "@/components/expenses/expense-status-badge";
import { AppHeader } from "@/components/layout/app-header";
import { Button } from "@/components/ui/button";
import {
  ApiError,
  fetchExpense,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  uploadExpenseReceipt,
  type ExpenseDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";

export default function ExpenseDetailPage() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const [expense, setExpense] = useState<ExpenseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setExpense(await fetchExpense(token, params.id));
  }, [params.id]);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  async function handleUpload(file: File) {
    const token = getAccessToken();
    if (!token || !params.id) return;
    setUploading(true);
    setError(null);
    try {
      const updated = await uploadExpenseReceipt(token, params.id, file);
      setExpense(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload impossible");
    } finally {
      setUploading(false);
    }
  }

  return (
    <ProtectedRoute>
      <AppHeader />
      <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-10">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/depenses">← Retour aux dépenses</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {expense && (
          <>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-3xl font-bold">Détail dépense</h1>
                <p className="mt-2 text-zinc-600">{expense.category_label}</p>
              </div>
              <ExpenseStatusBadge status={expense.status} />
            </div>

            <div className="grid gap-4 rounded-xl border border-zinc-200 bg-white p-6 sm:grid-cols-2">
              <div>
                <p className="text-sm text-zinc-500">Montant</p>
                <p className="text-xl font-bold">{formatCurrency(expense.amount)}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Date</p>
                <p className="font-medium">{expense.expense_date}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Immeuble</p>
                <p className="font-medium">{expense.building_name ?? "—"}</p>
              </div>
              <div>
                <p className="text-sm text-zinc-500">Mode de paiement</p>
                <p className="font-medium">{PAYMENT_METHOD_LABELS[expense.payment_method]}</p>
              </div>
              <div className="sm:col-span-2">
                <p className="text-sm text-zinc-500">Description</p>
                <p className="font-medium">{expense.description}</p>
              </div>
              {expense.supplier_name && (
                <div>
                  <p className="text-sm text-zinc-500">Fournisseur</p>
                  <p className="font-medium">{expense.supplier_name}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-zinc-500">Enregistré par</p>
                <p className="font-medium">{expense.recorded_by_name}</p>
              </div>
              {expense.validated_by_name && (
                <div>
                  <p className="text-sm text-zinc-500">Validé par</p>
                  <p className="font-medium">{expense.validated_by_name}</p>
                </div>
              )}
            </div>

            {expense.receipt_url ? (
              <div className="rounded-xl border border-zinc-200 bg-white p-4">
                <p className="text-sm text-zinc-500">Justificatif</p>
                <a
                  href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}${expense.receipt_url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-sm font-medium text-blue-600 hover:underline"
                >
                  Voir le justificatif
                </a>
              </div>
            ) : canManage && expense.status !== "validated" && expense.status !== "rejected" ? (
              <div className="rounded-xl border border-zinc-200 bg-white p-6">
                <p className="mb-3 text-sm font-medium">Joindre un justificatif (PDF ou image)</p>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  disabled={uploading}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleUpload(file);
                  }}
                  className="text-sm"
                />
              </div>
            ) : null}
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
