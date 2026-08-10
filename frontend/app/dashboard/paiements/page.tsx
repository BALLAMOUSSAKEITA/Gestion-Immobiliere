"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ApiError,
  deletePayment,
  fetchPayments,
  formatCurrency,
  PAYMENT_METHOD_LABELS,
  type PaymentSummary,
} from "@/lib/api";
import { getAccessToken } from "@/lib/auth-storage";
import { useAuth } from "@/contexts/auth-context";
import { useConfirm } from "@/contexts/confirm-context";
import { dangerConfirm } from "@/lib/confirm-presets";

export default function PaymentsPage() {
  const { user } = useAuth();
  const confirm = useConfirm();
  const [payments, setPayments] = useState<PaymentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const canManage =
    user?.role.code === "super_admin" ||
    user?.role.code === "admin_familial" ||
    user?.role.code === "gestionnaire";
  const isSuperAdmin = user?.role.code === "super_admin";

  const load = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    const data = await fetchPayments(token, { page_size: 50 });
    setPayments(data.items);
  }, []);

  useEffect(() => {
    load().catch((err) =>
      setError(err instanceof ApiError ? err.message : "Chargement impossible"),
    );
  }, [load]);

  return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Paiements</h1>
            <p className="mt-2 text-muted-foreground">Historique des encaissements de loyers.</p>
          </div>
          {canManage && (
            <Button asChild>
              <Link href="/dashboard/paiements/nouveau">Enregistrer un paiement</Link>
            </Button>
          )}
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/50">
              <tr>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Locataire</th>
                <th className="px-4 py-3">Logement</th>
                <th className="px-4 py-3">Montant</th>
                <th className="px-4 py-3">Mode</th>
                <th className="px-4 py-3">Enregistré par</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {payments.map((payment) => (
                <tr key={payment.id} className="border-b border-border">
                  <td className="px-4 py-3">{payment.payment_date}</td>
                  <td className="px-4 py-3">{payment.tenant_name}</td>
                  <td className="px-4 py-3">{payment.unit_code}</td>
                  <td className="px-4 py-3">{formatCurrency(payment.amount)}</td>
                  <td className="px-4 py-3">
                    {PAYMENT_METHOD_LABELS[payment.payment_method]}
                  </td>
                  <td className="px-4 py-3">{payment.recorded_by_name}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <Link
                        href={`/dashboard/paiements/${payment.id}`}
                        className="font-medium underline"
                      >
                        Détail
                      </Link>
                      {isSuperAdmin && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={async () => {
                            if (
                              !(await confirm(
                                dangerConfirm(
                                  "Supprimer le paiement",
                                  `Cette action supprime définitivement le paiement de ${payment.tenant_name} et le reçu associé. Cette opération est irréversible.`,
                                  "Supprimer le paiement",
                                ),
                              ))
                            ) {
                              return;
                            }
                            const token = getAccessToken();
                            if (!token) return;
                            setError(null);
                            try {
                              await deletePayment(token, payment.id);
                              await load();
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {payments.length === 0 && !error && (
            <p className="p-6 text-center text-muted-foreground">Aucun paiement.</p>
          )}
        </div>
      </div>
  );
}
