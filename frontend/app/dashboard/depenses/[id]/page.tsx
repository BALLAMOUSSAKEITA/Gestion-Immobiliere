"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ExpenseStatusBadge } from "@/components/expenses/expense-status-badge";
import { Button } from "@/components/ui/button";
import { FileInput } from "@/components/ui/file-input";
import {
  ApiError,
  deleteExpense,
  fetchExpense,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  uploadExpenseReceipt,
  type ExpenseDetail,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { deleteConfirm, modifyConfirm } from "@/lib/confirm-presets";

export default function ExpenseDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const confirm = useConfirm();
  const [expense, setExpense] = useState<ExpenseDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";
  const isSuperAdmin = user?.role.code === "super_admin";

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
    if (!(await confirm(modifyConfirm("Joindre ce justificatif à la dépense ?")))) return;
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
      <div className="flex flex-col gap-6">
        <Button asChild variant="outline" className="w-fit">
          <Link href="/dashboard/depenses">← Retour aux dépenses</Link>
        </Button>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {expense && (
          <>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-3xl font-bold">Détail dépense</h1>
                <p className="mt-2 text-muted-foreground">{expense.category_label}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <ExpenseStatusBadge status={expense.status} />
                {isSuperAdmin && (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={async () => {
                      if (
                        !(await confirm(
                          deleteConfirm(`la dépense « ${expense.description} »`),
                        ))
                      ) {
                        return;
                      }
                      const token = getAccessToken();
                      if (!token) return;
                      setError(null);
                      try {
                        await deleteExpense(token, expense.id);
                        router.push("/dashboard/depenses");
                      } catch (err) {
                        setError(
                          err instanceof ApiError
                            ? err.message
                            : "Suppression impossible",
                        );
                      }
                    }}
                  >
                    Supprimer
                  </Button>
                )}
              </div>
            </div>

            <div className="grid gap-4 rounded-xl border border-border bg-card shadow-sm p-6 sm:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground">Montant</p>
                <p className="text-xl font-bold">{formatCurrency(expense.amount)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Date</p>
                <p className="font-medium">{expense.expense_date}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Immeuble</p>
                <p className="font-medium">{expense.building_name ?? "—"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Mode de paiement</p>
                <p className="font-medium">{PAYMENT_METHOD_LABELS[expense.payment_method]}</p>
              </div>
              <div className="sm:col-span-2">
                <p className="text-sm text-muted-foreground">Description</p>
                <p className="font-medium">{expense.description}</p>
              </div>
              {expense.supplier_name && (
                <div>
                  <p className="text-sm text-muted-foreground">Fournisseur</p>
                  <p className="font-medium">{expense.supplier_name}</p>
                </div>
              )}
              <div>
                <p className="text-sm text-muted-foreground">Enregistré par</p>
                <p className="font-medium">{expense.recorded_by_name}</p>
              </div>
              {expense.validated_by_name && (
                <div>
                  <p className="text-sm text-muted-foreground">Validé par</p>
                  <p className="font-medium">{expense.validated_by_name}</p>
                </div>
              )}
            </div>

            {expense.receipt_url ? (
              <div className="rounded-xl border border-border bg-card shadow-sm p-4">
                <p className="text-sm text-muted-foreground">Justificatif</p>
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
              <div className="rounded-xl border border-border bg-card shadow-sm p-6">
                <p className="mb-3 text-sm font-medium">Joindre un justificatif</p>
                <FileInput
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  disabled={uploading}
                  hint="PDF ou image — max. 10 Mo"
                  label={uploading ? "Envoi en cours…" : "Choisir un justificatif"}
                  onChange={(files) => {
                    const file = files[0];
                    if (file) void handleUpload(file);
                  }}
                />
              </div>
            ) : null}
          </>
        )}
      </div>
  );
}
